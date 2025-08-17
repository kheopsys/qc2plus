"""
2QC+ Test Runner
Orchestrates execution of Level 1 and Level 2 quality tests
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed

from qc2plus.core.project import QC2PlusProject
from qc2plus.core.connection import ConnectionManager
from qc2plus.level1.engine import Level1Engine
from qc2plus.level2.correlation import CorrelationAnalyzer
from qc2plus.level2.temporal import TemporalAnalyzer
from qc2plus.level2.distribution import DistributionAnalyzer
from qc2plus.level2.anomaly_filter import AnomalyFilter
from qc2plus.alerting.alerts import AlertManager
from qc2plus.persistence.persistence import PersistenceManager


class QC2PlusRunner:
    """Main test runner orchestrating all quality checks"""
    
    def __init__(self, project: QC2PlusProject, target: str, profiles_dir: str = '.'):
        self.project = project
        self.target = target
        self.profiles_dir = Path(profiles_dir)
        
        # Load profiles
        profiles_path = self.profiles_dir / 'profiles.yml'
        with open(profiles_path, 'r') as f:
            self.profiles = yaml.safe_load(f)
        
        # Initialize connection manager
        self.connection_manager = ConnectionManager(self.profiles, target)
        
        # Initialize engines and analyzers
        self.level1_engine = Level1Engine(self.connection_manager)
        self.correlation_analyzer = CorrelationAnalyzer(self.connection_manager)
        self.temporal_analyzer = TemporalAnalyzer(self.connection_manager)
        self.distribution_analyzer = DistributionAnalyzer(self.connection_manager)
        
        # Initialize alerting and persistence
        self.alert_manager = AlertManager(self.project.config.get('alerting', {}))
        self.persistence_manager = PersistenceManager(self.connection_manager)
        
        # Ensure quality tables exist
        self.connection_manager.create_quality_tables()
    
    def run(self, models: Optional[List[str]] = None, level: str = 'all', 
            fail_fast: bool = False, threads: int = 1) -> Dict[str, Any]:
        """Run quality tests"""
        
        run_id = str(uuid.uuid4())
        start_time = time.time()
        
        logging.info(f"Starting 2QC+ run {run_id} for target: {self.target}")
        
        # Get models to test
        all_models = self.project.get_models()
        if models:
            test_models = {name: config for name, config in all_models.items() if name in models}
        else:
            test_models = all_models
        
        if not test_models:
            logging.warning("No models found to test")
            return self._create_empty_result(run_id, start_time)
        
        # Run tests
        results = {
            'run_id': run_id,
            'status': 'success',
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'critical_failures': 0,
            'models': {},
            'execution_time': start_time,
            'target': self.target
        }
        
        if threads > 1:
            results = self._run_parallel(test_models, level, fail_fast, threads, results)
        else:
            results = self._run_sequential(test_models, level, fail_fast, results)
        
        # Calculate final statistics
        execution_duration = int(time.time() - start_time)
        results['execution_duration'] = execution_duration

        # Filter False anomaly
        #results = apply_anomaly_filtering(results, self.connection_manager)
        
        # Determine overall status
        if results['critical_failures'] > 0:
            results['status'] = 'critical_failure'
        elif results['failed_tests'] > 0:
            results['status'] = 'failure'
        else:
            results['status'] = 'success'
        
        # Persist results
        self._persist_results(results)
        
        # Send alerts
        self._send_alerts(results)
        
        logging.info(f"Completed 2QC+ run {run_id} in {execution_duration}s")
        
        return results
    
    def _run_sequential(self, test_models: Dict[str, Any], level: str, 
                       fail_fast: bool, results: Dict[str, Any]) -> Dict[str, Any]:
        """Run tests sequentially"""
        
        for model_name, model_config in test_models.items():
            logging.info(f"Testing model: {model_name}")
            
            model_results = self._test_model(model_name, model_config, level)
            results['models'][model_name] = model_results
            
            # Update counters
            self._update_counters(results, model_results)
            
            # Check fail-fast condition
            if fail_fast and model_results.get('has_critical_failure', False):
                logging.error(f"Critical failure in {model_name}, stopping execution")
                results['status'] = 'critical_failure'
                break
        
        return results
    
    def _run_parallel(self, test_models: Dict[str, Any], level: str, 
                     fail_fast: bool, threads: int, results: Dict[str, Any]) -> Dict[str, Any]:
        """Run tests in parallel"""
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            # Submit all model tests
            future_to_model = {
                executor.submit(self._test_model, model_name, model_config, level): model_name
                for model_name, model_config in test_models.items()
            }
            
            # Collect results
            for future in as_completed(future_to_model):
                model_name = future_to_model[future]
                try:
                    model_results = future.result()
                    results['models'][model_name] = model_results
                    
                    # Update counters
                    self._update_counters(results, model_results)
                    
                    # Check fail-fast condition
                    if fail_fast and model_results.get('has_critical_failure', False):
                        logging.error(f"Critical failure in {model_name}, cancelling remaining tests")
                        # Cancel remaining futures
                        for f in future_to_model:
                            f.cancel()
                        results['status'] = 'critical_failure'
                        break
                        
                except Exception as e:
                    logging.error(f"Error testing model {model_name}: {str(e)}")
                    results['models'][model_name] = {
                        'status': 'error',
                        'error': str(e),
                        'has_critical_failure': True
                    }
                    results['failed_tests'] += 1
                    results['critical_failures'] += 1
        
        return results
    
    def _test_model(self, model_name: str, model_config: Dict[str, Any], level: str) -> Dict[str, Any]:
        """Test a single model"""
        model_results = {
            'status': 'success',
            'has_critical_failure': False,
            'level1': {},
            'level2': {}
        }
        
        qc2plus_tests = model_config.get('qc2plus_tests', {})
        
        # Run Level 1 tests
        if level in ['1', 'all'] and 'level1' in qc2plus_tests:
            try:
                level1_results = self.level1_engine.run_tests(model_name, qc2plus_tests['level1'])
                model_results['level1'] = level1_results
                
                # Check for critical failures
                for test_name, test_result in level1_results.items():
                    if not test_result['passed'] and test_result.get('severity') == 'critical':
                        model_results['has_critical_failure'] = True
                        
            except Exception as e:
                logging.error(f"Level 1 tests failed for {model_name}: {str(e)}")
                model_results['level1'] = {'error': str(e)}
                model_results['status'] = 'error'
        
        # Run Level 2 tests
        if level in ['2', 'all'] and 'level2' in qc2plus_tests:
            try:
                level2_results = self._run_level2_tests(model_name, qc2plus_tests['level2'])
                model_results['level2'] = level2_results
                
            except Exception as e:
                logging.error(f"Level 2 tests failed for {model_name}: {str(e)}")
                model_results['level2'] = {'error': str(e)}
                model_results['status'] = 'error'
        
        return model_results
    
    def _run_level2_tests(self, model_name: str, level2_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run Level 2 ML-based tests"""
        level2_results = {}
        
        # Correlation analysis
        if 'correlation_analysis' in level2_config:
            try:
                correlation_result = self.correlation_analyzer.analyze(
                    model_name, 
                    level2_config['correlation_analysis']
                )
                level2_results['correlation'] = correlation_result
            except Exception as e:
                logging.error(f"Correlation analysis failed for {model_name}: {str(e)}")
                level2_results['correlation'] = {'error': str(e), 'passed': False}
        
        # Temporal analysis
        if 'temporal_analysis' in level2_config:
            try:
                temporal_result = self.temporal_analyzer.analyze(
                    model_name, 
                    level2_config['temporal_analysis']
                )
                level2_results['temporal'] = temporal_result
            except Exception as e:
                logging.error(f"Temporal analysis failed for {model_name}: {str(e)}")
                level2_results['temporal'] = {'error': str(e), 'passed': False}
        
        # Distribution analysis
        if 'distribution_analysis' in level2_config:
            try:
                distribution_result = self.distribution_analyzer.analyze(
                    model_name, 
                    level2_config['distribution_analysis']
                )
                level2_results['distribution'] = distribution_result
            except Exception as e:
                logging.error(f"Distribution analysis failed for {model_name}: {str(e)}")
                level2_results['distribution'] = {'error': str(e), 'passed': False}
        
        return level2_results
    
    def _update_counters(self, results: Dict[str, Any], model_results: Dict[str, Any]) -> None:
        """Update test counters"""
        
        # Count Level 1 tests
        for test_name, test_result in model_results.get('level1', {}).items():
            if test_name != 'error':
                results['total_tests'] += 1
                if test_result.get('passed', False):
                    results['passed_tests'] += 1
                else:
                    results['failed_tests'] += 1
                    if test_result.get('severity') == 'critical':
                        results['critical_failures'] += 1
        
        # Count Level 2 tests
        for analyzer_name, analyzer_result in model_results.get('level2', {}).items():
            if analyzer_name != 'error':
                results['total_tests'] += 1
                if analyzer_result.get('passed', False):
                    results['passed_tests'] += 1
                else:
                    results['failed_tests'] += 1
                    # Level 2 anomalies are typically not critical
    
    def apply_anomaly_filtering(results: Dict[str, Any], connection_manager: ConnectionManager) -> Dict[str, Any]:
        """Apply anomaly filtering to test results"""
        
        try:
            anomaly_filter = AnomalyFilter(connection_manager)
            
            # Apply filtering to each model
            filtered_results = results.copy()
            
            for model_name in results.get('models', {}):
                filtered_results = anomaly_filter.filter_anomalies(filtered_results, model_name)
            
            # Add filtering metadata
            filtered_results['anomaly_filtering'] = {
                'applied': True,
                'timestamp': datetime.now().isoformat(),
                'filters_used': ['seasonal_context', 'correlation_analysis']
            }
            
            return filtered_results
            
        except Exception as e:
            logging.error(f"Anomaly filtering failed: {str(e)}")
            # Return original results if filtering fails
            results['anomaly_filtering'] = {
                'applied': False,
                'error': str(e)
            }
            return results
    
    def _persist_results(self, results: Dict[str, Any]) -> None:
        """Persist results to database"""
        try:
            self.persistence_manager.save_run_summary(results)
            self.persistence_manager.save_test_results(results)
            self.persistence_manager.save_anomalies(results)
        except Exception as e:
            logging.error(f"Failed to persist results: {str(e)}")
    
    def _send_alerts(self, results: Dict[str, Any]) -> None:
        """Send alerts based on results"""
        try:
            self.alert_manager.send_alerts(results)
        except Exception as e:
            logging.error(f"Failed to send alerts: {str(e)}")
    
    def _create_empty_result(self, run_id: str, start_time: float) -> Dict[str, Any]:
        """Create empty result structure"""
        return {
            'run_id': run_id,
            'status': 'success',
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'critical_failures': 0,
            'models': {},
            'execution_time': start_time,
            'execution_duration': int(time.time() - start_time),
            'target': self.target
        }
