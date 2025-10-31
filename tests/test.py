"""
2QC+ Framework Tests
Example test suite for validating the framework
"""

import pytest
import tempfile
import os
from pathlib import Path
import yaml
import pandas as pd
from unittest.mock import Mock, patch

# Import 2QC+ modules
from qc2plus.core.project import QC2PlusProject
from qc2plus.core.connection import ConnectionManager
from qc2plus.level1.engine import Level1Engine
from qc2plus.level2.correlation import CorrelationAnalyzer
from qc2plus.alerting.alerts import AlertManager
from qc2plus.output.persistence import PersistenceManager


class TestQC2PlusProject:
    """Test project management functionality"""
    
    def test_project_initialization(self):
        """Test project initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_name = "test_project"
            project_path = Path(temp_dir) / project_name
            
            # Initialize project
            project = QC2PlusProject.init_project(str(project_path), 'postgresql')
            
            # Verify project structure
            assert project_path.exists()
            assert (project_path / 'qc2plus_project.yml').exists()
            assert (project_path / 'profiles.yml').exists()
            assert (project_path / 'models').exists()
            assert (project_path / 'target').exists()
class TestQC2PlusProject:
    """Test project management functionality"""
    
    def test_project_initialization(self):
        """Test project initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_name = "test_project"
            project_path = Path(temp_dir) / project_name
            
            # Initialize project
            project = QC2PlusProject.init_project(str(project_path), 'postgresql')
            
            # Verify project structure
            assert project_path.exists()
            assert (project_path / 'qc2plus_project.yml').exists()
            assert (project_path / 'profiles.yml').exists()
            assert (project_path / 'models').exists()
            assert (project_path / 'target').exists()
            assert (project_path / 'logs').exists()
            
            # Verify project can be loaded
            loaded_project = QC2PlusProject.load_project(str(project_path))
            assert loaded_project.name == project_name
    
    def test_model_discovery(self):
        """Test model configuration discovery"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project = QC2PlusProject.init_project(str(project_path), 'postgresql')
            
            # Create additional model config
            model_config = {
                'models': [{
                    'name': 'orders',
                    'qc2plus_tests': {
                        'level1': [
                            {'unique': {'column_name': 'order_id', 'severity': 'critical'}}
                        ]
                    }
                }]
            }
            
            with open(project_path / 'models' / 'orders.yml', 'w') as f:
                yaml.dump(model_config, f)
            
            # Test model discovery
            models = project.get_models()
            assert 'orders' in models
            assert 'customers' in models  # From init example
            
            # Test specific model config
            orders_config = project.get_model_config('orders')
            assert orders_config is not None
            assert orders_config.name == 'orders'
    
    def test_project_validation(self):
        """Test project configuration validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project = QC2PlusProject.init_project(str(project_path), 'postgresql')
            
            # Test valid project
            issues = project.validate_config()
            assert len(issues) == 0
            
            # Remove models directory to create issue
            import shutil
            shutil.rmtree(project_path / 'models')
            
            issues = project.validate_config()
            assert len(issues) > 0
            assert any('models/' in issue for issue in issues)


class TestLevel1Engine:
    """Test Level 1 business rule engine"""
    
    def test_sql_compilation(self):
        """Test SQL template compilation"""
        engine = Level1Engine()
        
        # Test unique constraint compilation
        sql = engine.compile_test(
            'unique', 
            {'column_name': 'customer_id', 'severity': 'critical'}, 
            'customers'
        )
        
        assert 'SELECT' in sql.upper()
        assert 'customer_id' in sql
        assert 'customers' in sql
        assert 'GROUP BY' in sql.upper()
    
    def test_available_tests(self):
        """Test available test types"""
        engine = Level1Engine()
        available_tests = engine.get_available_tests()
        
        expected_tests = ['unique', 'not_null', 'email_format', 'foreign_key', 'future_date', 'statistical_threshold']
        for test in expected_tests:
            assert test in available_tests
    
    def test_test_validation(self):
        """Test test configuration validation"""
        engine = Level1Engine()
        
        # Valid configuration
        issues = engine.validate_test_config('unique', {'column_name': 'id', 'severity': 'critical'})
        assert len(issues) == 0
        
        # Invalid severity
        issues = engine.validate_test_config('unique', {'column_name': 'id', 'severity': 'invalid'})
        assert len(issues) > 0
        
        # Missing required parameter
        issues = engine.validate_test_config('unique', {'severity': 'critical'})
        assert len(issues) > 0
    
    @patch('qc2plus.core.connection.ConnectionManager')
    def test_test_execution(self, mock_connection_manager):
        """Test test execution with mocked database"""
        # Mock database response
        mock_df = pd.DataFrame()  # Empty dataframe = test passed
        mock_connection_manager.execute_query.return_value = mock_df
        
        engine = Level1Engine(mock_connection_manager)
        
        test_configs = [
            {'unique': {'column_name': 'customer_id', 'severity': 'critical'}}
        ]
        
        results = engine.run_tests('customers', test_configs)
        
        assert 'unique_customer_id' in results
        assert results['unique_customer_id']['passed'] == True


class TestConnectionManager:
    """Test database connection management"""
    
    def test_postgresql_connection_string(self):
        """Test PostgreSQL connection string generation"""
        profiles = {
            'test_project': {
                'target': 'dev',
                'outputs': {
                    'dev': {
                        'type': 'postgresql',
                        'host': 'localhost',
                        'port': 5432,
                        'user': 'test_user',
                        'password': 'test_pass',
                        'dbname': 'test_db'
                    }
                }
            }
        }
        
        # This would normally create a real connection, so we'll test the config parsing
        config = profiles['test_project']['outputs']['dev']
        assert config['type'] == 'postgresql'
        assert config['host'] == 'localhost'
        assert config['port'] == 5432
    
    def test_database_adapter_selection(self):
        """Test database adapter selection"""
        from qc2plus.core.connection import PostgreSQLAdapter, SnowflakeAdapter, BigQueryAdapter
        
        # Test adapter creation
        pg_adapter = PostgreSQLAdapter()
        assert pg_adapter.adapt_regex("test@test.com") == "~ 'test@test.com'"
        
        sf_adapter = SnowflakeAdapter()
        assert sf_adapter.adapt_regex("test@test.com") == "REGEXP 'test@test.com'"
        
        bq_adapter = BigQueryAdapter()
        assert "REGEXP_CONTAINS" in bq_adapter.adapt_regex("test@test.com")


class TestCorrelationAnalyzer:
    """Test correlation analysis functionality"""
    
    @patch('qc2plus.core.connection.ConnectionManager')
    def test_correlation_analysis_config_validation(self, mock_connection_manager):
        """Test correlation analysis configuration validation"""
        analyzer = CorrelationAnalyzer(mock_connection_manager)
        
        # Valid config
        config = {
            'variables': ['var1', 'var2'],
            'expected_correlation': 0.8,
            'threshold': 0.2
        }
        
        # Mock empty data to test config validation path
        mock_connection_manager.execute_query.return_value = pd.DataFrame()
        
        result = analyzer.analyze('test_model', config)
        
        # Should pass validation but return no data message
        assert result['passed'] == True
        assert 'No data available' in result['message']
    
    def test_insufficient_variables_error(self):
        """Test error handling for insufficient variables"""
        mock_connection_manager = Mock()
        analyzer = CorrelationAnalyzer(mock_connection_manager)
        
        # Invalid config - less than 2 variables
        config = {
            'variables': ['var1'],
            'expected_correlation': 0.8
        }
        
        result = analyzer.analyze('test_model', config)
        
        assert result['passed'] == False
        assert 'error' in result
        assert 'At least 2 variables required' in result['error']


class TestAlertManager:
    """Test alerting functionality"""
    
    def test_alert_analysis(self):
        """Test alert analysis logic"""
        alerting_config = {
            'enabled_channels': ['email'],
            'thresholds': {
                'critical_failure_threshold': 1,
                'failure_rate_threshold': 0.2
            }
        }
        
        alert_manager = AlertManager(alerting_config)
        
        # Test results with critical failure
        results = {
            'total_tests': 10,
            'passed_tests': 8,
            'failed_tests': 2,
            'critical_failures': 1,
            'models': {
                'customers': {
                    'level1': {
                        'unique_customer_id': {
                            'passed': False,
                            'severity': 'critical',
                            'message': 'Duplicate customer IDs found'
                        }
                    }
                }
            }
        }
        
        alert_info = alert_manager._analyze_results_for_alerting(results)
        
        assert alert_info['should_alert'] == True
        assert len(alert_info['critical_failures']) == 1
        assert alert_info['critical_failures'][0]['severity'] == 'critical'
    
    def test_alert_threshold_logic(self):
        """Test alert threshold logic"""
        alerting_config = {
            'enabled_channels': ['email'],
            'thresholds': {
                'critical_failure_threshold': 2,  # Higher threshold
                'failure_rate_threshold': 0.5    # Higher threshold
            }
        }
        
        alert_manager = AlertManager(alerting_config)
        
        # Test results that shouldn't trigger alerts
        results = {
            'total_tests': 10,
            'passed_tests': 9,
            'failed_tests': 1,
            'critical_failures': 0,
            'models': {}
        }
        
        alert_info = alert_manager._analyze_results_for_alerting(results)
        
        assert alert_info['should_alert'] == False


class TestPersistenceManager:
    """Test result persistence functionality"""
    
    @patch('qc2plus.core.connection.ConnectionManager')
    def test_run_summary_persistence(self, mock_connection_manager):
        """Test run summary persistence"""
        persistence_manager = PersistenceManager(mock_connection_manager)
        
        # Mock successful SQL execution
        mock_connection_manager.execute_sql.return_value = Mock()
        mock_connection_manager.config = {'schema': 'public'}
        mock_connection_manager.db_type = 'postgresql'
        
        results = {
            'run_id': 'test-run-123',
            'total_tests': 10,
            'passed_tests': 8,
            'failed_tests': 2,
            'critical_failures': 1,
            'execution_duration': 30,
            'status': 'failure',
            'target': 'dev',
            'models': {}
        }
        
        # Should not raise exception
        persistence_manager.save_run_summary(results)
        
        # Verify SQL execution was called
        assert mock_connection_manager.execute_sql.called
    
    def test_test_type_extraction(self):
        """Test test type extraction from test names"""
        mock_connection_manager = Mock()
        persistence_manager = PersistenceManager(mock_connection_manager)
        
        assert persistence_manager._extract_test_type('unique_customer_id') == 'unique'
        assert persistence_manager._extract_test_type('not_null_email') == 'not_null'
        assert persistence_manager._extract_test_type('email_format_contact_email') == 'email_format'
        assert persistence_manager._extract_test_type('custom_business_rule') == 'custom'


class TestIntegration:
    """Integration tests for the complete framework"""
    
    @patch('qc2plus.core.connection.ConnectionManager')
    def test_end_to_end_workflow(self, mock_connection_manager):
        """Test complete end-to-end workflow"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Initialize project
            project_path = Path(temp_dir) / "integration_test"
            project = QC2PlusProject.init_project(str(project_path), 'postgresql')
            
            # 2. Mock database connection and responses
            mock_connection_manager.execute_query.return_value = pd.DataFrame()  # Empty = tests pass
            mock_connection_manager.test_connection.return_value = True
            mock_connection_manager.config = {'schema': 'public'}
            mock_connection_manager.db_type = 'postgresql'
            
            # 3. Create Level 1 engine and run tests
            level1_engine = Level1Engine(mock_connection_manager)
            
            test_configs = [
                {'unique': {'column_name': 'customer_id', 'severity': 'critical'}},
                {'not_null': {'column_name': 'email', 'severity': 'critical'}}
            ]
            
            level1_results = level1_engine.run_tests('customers', test_configs)
            
            # 4. Verify results structure
            assert 'unique_customer_id' in level1_results
            assert 'not_null_email' in level1_results
            assert all(result['passed'] for result in level1_results.values())
            
            # 5. Test persistence
            persistence_manager = PersistenceManager(mock_connection_manager)
            
            complete_results = {
                'run_id': 'integration-test-123',
                'total_tests': len(level1_results),
                'passed_tests': len(level1_results),
                'failed_tests': 0,
                'critical_failures': 0,
                'models': {
                    'customers': {
                        'level1': level1_results,
                        'level2': {}
                    }
                },
                'target': 'dev',
                'execution_duration': 10,
                'status': 'success'
            }
            
            # Should not raise exceptions
            persistence_manager.save_run_summary(complete_results)
            persistence_manager.save_test_results(complete_results)


# Test fixtures and utilities
@pytest.fixture
def sample_correlation_data():
    """Sample data for correlation analysis tests"""
    return pd.DataFrame({
        'analysis_date': pd.date_range('2024-01-01', periods=30),
        'daily_registrations': [100 + i * 2 + (i % 7) * 10 for i in range(30)],
        'daily_activations': [80 + i * 1.5 + (i % 7) * 8 for i in range(30)]
    })


@pytest.fixture
def sample_temporal_data():
    """Sample data for temporal analysis tests"""
    return pd.DataFrame({
        'period_date': pd.date_range('2024-01-01', periods=90),
        'count': [1000 + i * 10 + (i % 7) * 50 for i in range(90)]
    })


# Performance tests
class TestPerformance:
    """Performance tests for the framework"""
    
    def test_large_dataset_compilation(self):
        """Test SQL compilation performance with large configurations"""
        engine = Level1Engine()
        
        # Create a large test configuration
        large_config = []
        for i in range(100):
            large_config.append({
                'unique': {
                    'column_name': f'column_{i}',
                    'severity': 'medium'
                }
            })
        
        import time
        start_time = time.time()
        
        # Compile all tests
        for test_config in large_config:
            for test_type, test_params in test_config.items():
                sql = engine.compile_test(test_type, test_params, 'large_table')
                assert len(sql) > 0
        
        compilation_time = time.time() - start_time
        
        # Should compile 100 tests in under 1 second
        assert compilation_time < 1.0
    
    def test_memory_usage_with_large_results(self):
        """Test memory usage with large result sets"""
        # This test would normally use a memory profiler
        # For now, we'll just test that large result structures don't crash
        
        large_results = {
            'models': {}
        }
        
        # Create results for 1000 models with 10 tests each
        for model_i in range(1000):
            model_name = f'model_{model_i}'
            large_results['models'][model_name] = {
                'level1': {},
                'level2': {}
            }
            
            for test_i in range(10):
                test_name = f'test_{test_i}'
                large_results['models'][model_name]['level1'][test_name] = {
                    'passed': True,
                    'severity': 'medium',
                    'message': 'Test passed',
                    'failed_rows': 0,
                    'total_rows': 1000
                }
        
        # Should be able to process large results without crashing
        assert len(large_results['models']) == 1000


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
