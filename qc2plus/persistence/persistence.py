"""
2QC+ Persistence Manager
Saves quality test results to database tables for Power BI integration
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from qc2plus.core.connection import ConnectionManager


class PersistenceManager:
    """Manages persistence of quality test results to database"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.schema = connection_manager.config.get('schema', 'public')
    
    def save_run_summary(self, results: Dict[str, Any]) -> None:
        """Save run summary to quality_run_summary table"""
        
        try:
            # Prepare data
            run_data = {
                'run_id': results.get('run_id', str(uuid.uuid4())),
                'project_name': results.get('project_name', 'unknown'),
                'execution_time': datetime.now(),
                'target_environment': results.get('target', 'unknown'),
                'total_models': len(results.get('models', {})),
                'total_tests': results.get('total_tests', 0),
                'passed_tests': results.get('passed_tests', 0),
                'failed_tests': results.get('failed_tests', 0),
                'critical_failures': results.get('critical_failures', 0),
                'execution_duration_seconds': results.get('execution_duration', 0),
                'status': results.get('status', 'unknown')
            }
            
            # Build insert SQL
            columns = ', '.join(run_data.keys())
            placeholders = ', '.join(['%s'] * len(run_data))
            
            sql = f"""
                INSERT INTO {self.schema}.quality_run_summary 
                ({columns}) 
                VALUES ({placeholders})
            """
            
            # Adapt for different databases
            if self.connection_manager.db_type == 'bigquery':
                # BigQuery uses different parameter syntax
                placeholders = ', '.join([f'@param{i}' for i in range(len(run_data))])
                sql = f"""
                    INSERT INTO {self.schema}.quality_run_summary 
                    ({columns}) 
                    VALUES ({placeholders})
                """
            
            # Execute insert
            self.connection_manager.execute_sql(sql, list(run_data.values()))
            
            logging.info(f"Run summary saved: {run_data['run_id']}")
            
        except Exception as e:
            logging.error(f"Failed to save run summary: {str(e)}")
            raise
    
    def save_test_results(self, results: Dict[str, Any]) -> None:
        """Save individual test results to quality_test_results table"""
        
        try:
            test_records = []
            
            # Extract test results from each model
            for model_name, model_results in results.get('models', {}).items():
                
                # Level 1 test results
                for test_name, test_result in model_results.get('level1', {}).items():
                    if isinstance(test_result, dict):
                        record = {
                            'test_id': str(uuid.uuid4()),
                            'model_name': model_name,
                            'test_name': test_name,
                            'test_type': self._extract_test_type(test_name),
                            'level': 'Level 1',
                            'severity': test_result.get('severity', 'medium'),
                            'status': 'passed' if test_result.get('passed', False) else 'failed',
                            'message': test_result.get('message', ''),
                            'failed_rows': test_result.get('failed_rows', 0),
                            'total_rows': test_result.get('total_rows', 0),
                            'execution_time': datetime.now(),
                            'target_environment': results.get('target', 'unknown')
                        }
                        test_records.append(record)
                
                # Level 2 test results
                for analyzer_name, analyzer_result in model_results.get('level2', {}).items():
                    if isinstance(analyzer_result, dict):
                        record = {
                            'test_id': str(uuid.uuid4()),
                            'model_name': model_name,
                            'test_name': analyzer_name,
                            'test_type': analyzer_name,
                            'level': 'Level 2',
                            'severity': 'medium',  # Level 2 anomalies are typically medium
                            'status': 'passed' if analyzer_result.get('passed', False) else 'failed',
                            'message': analyzer_result.get('message', ''),
                            'failed_rows': analyzer_result.get('anomalies_count', 0),
                            'total_rows': 1,  # Level 2 tests are typically binary pass/fail
                            'execution_time': datetime.now(),
                            'target_environment': results.get('target', 'unknown')
                        }
                        test_records.append(record)
            
            # Batch insert test records
            if test_records:
                self._batch_insert_test_results(test_records)
                logging.info(f"Saved {len(test_records)} test results")
            
        except Exception as e:
            logging.error(f"Failed to save test results: {str(e)}")
            raise
    
    def save_anomalies(self, results: Dict[str, Any]) -> None:
        """Save Level 2 anomaly details to quality_anomalies table"""
        
        try:
            anomaly_records = []
            
            # Extract anomalies from Level 2 results
            for model_name, model_results in results.get('models', {}).items():
                
                for analyzer_name, analyzer_result in model_results.get('level2', {}).items():
                    if isinstance(analyzer_result, dict) and not analyzer_result.get('passed', True):
                        
                        details = analyzer_result.get('details', {})
                        
                        # Extract specific anomalies based on analyzer type
                        if analyzer_name == 'correlation':
                            anomalies = self._extract_correlation_anomalies(details, model_name, analyzer_name)
                        elif analyzer_name == 'temporal':
                            anomalies = self._extract_temporal_anomalies(details, model_name, analyzer_name)
                        elif analyzer_name == 'multivariate':
                            anomalies = self._extract_multivariate_anomalies(details, model_name, analyzer_name)
                        elif analyzer_name == 'distribution':
                            anomalies = self._extract_distribution_anomalies(details, model_name, analyzer_name)
                        else:
                            # Generic anomaly
                            anomalies = [{
                                'anomaly_id': str(uuid.uuid4()),
                                'model_name': model_name,
                                'analyzer_type': analyzer_name,
                                'anomaly_type': 'generic',
                                'anomaly_score': 1.0,
                                'affected_columns': '',
                                'anomaly_details': json.dumps(analyzer_result),
                                'detection_time': datetime.now(),
                                'severity': 'medium',
                                'target_environment': results.get('target', 'unknown')
                            }]
                        
                        anomaly_records.extend(anomalies)
            
            # Batch insert anomaly records
            if anomaly_records:
                self._batch_insert_anomalies(anomaly_records)
                logging.info(f"Saved {len(anomaly_records)} anomaly records")
            
        except Exception as e:
            logging.error(f"Failed to save anomalies: {str(e)}")
            raise
    
    def _extract_test_type(self, test_name: str) -> str:
        """Extract test type from test name"""
        
        # Common test types
        test_types = {
            'unique': 'unique',
            'not_null': 'not_null',
            'email_format': 'email_format',
            'foreign_key': 'foreign_key',
            'future_date': 'future_date',
            'statistical_threshold': 'statistical_threshold',
            'accepted_values': 'accepted_values',
            'range_check': 'range_check'
        }
        
        for test_type, type_name in test_types.items():
            if test_type in test_name.lower():
                return type_name
        
        return 'custom'
    
    def _batch_insert_test_results(self, test_records: List[Dict[str, Any]]) -> None:
        """Batch insert test results"""
        
        if not test_records:
            return
        
        # Build batch insert SQL
        columns = list(test_records[0].keys())
        columns_str = ', '.join(columns)
        
        values_list = []
        for record in test_records:
            values = [record[col] for col in columns]
            values_list.append(values)
        
        # Create placeholders
        if self.connection_manager.db_type == 'bigquery':
            # BigQuery batch insert
            placeholders = ', '.join(['%s'] * len(columns))
            sql = f"""
                INSERT INTO {self.schema}.quality_test_results 
                ({columns_str}) 
                VALUES ({placeholders})
            """
        else:
            # Standard SQL batch insert
            placeholders = ', '.join(['%s'] * len(columns))
            sql = f"""
                INSERT INTO {self.schema}.quality_test_results 
                ({columns_str}) 
                VALUES ({placeholders})
            """
        
        # Execute batch insert
        for values in values_list:
            self.connection_manager.execute_sql(sql, values)
    
    def _batch_insert_anomalies(self, anomaly_records: List[Dict[str, Any]]) -> None:
        """Batch insert anomaly records"""
        
        if not anomaly_records:
            return
        
        # Build batch insert SQL
        columns = list(anomaly_records[0].keys())
        columns_str = ', '.join(columns)
        
        values_list = []
        for record in anomaly_records:
            values = [record[col] for col in columns]
            values_list.append(values)
        
        # Create placeholders
        placeholders = ', '.join(['%s'] * len(columns))
        sql = f"""
            INSERT INTO {self.schema}.quality_anomalies 
            ({columns_str}) 
            VALUES ({placeholders})
        """
        
        # Execute batch insert
        for values in values_list:
            self.connection_manager.execute_sql(sql, values)
    
    def _extract_correlation_anomalies(self, details: Dict[str, Any], model_name: str, 
                                     analyzer_name: str) -> List[Dict[str, Any]]:
        """Extract correlation-specific anomalies"""
        
        anomalies = []
        
        # Static correlation anomalies
        static_results = details.get('static_correlation', {})
        for anomaly in static_results.get('anomalies', []):
            anomalies.append({
                'anomaly_id': str(uuid.uuid4()),
                'model_name': model_name,
                'analyzer_type': analyzer_name,
                'anomaly_type': 'correlation_deviation',
                'anomaly_score': abs(anomaly.get('correlation', 0)),
                'affected_columns': anomaly.get('variable_pair', ''),
                'anomaly_details': json.dumps(anomaly),
                'detection_time': datetime.now(),
                'severity': anomaly.get('severity', 'medium'),
                'target_environment': 'unknown'  # Will be set by caller
            })
        
        # Temporal correlation anomalies
        temporal_results = details.get('temporal_correlation', {})
        for anomaly in temporal_results.get('anomalies', []):
            anomalies.append({
                'anomaly_id': str(uuid.uuid4()),
                'model_name': model_name,
                'analyzer_type': analyzer_name,
                'anomaly_type': anomaly.get('anomaly_type', 'temporal_correlation'),
                'anomaly_score': anomaly.get('correlation_std', 0),
                'affected_columns': anomaly.get('variable_pair', ''),
                'anomaly_details': json.dumps(anomaly),
                'detection_time': datetime.now(),
                'severity': anomaly.get('severity', 'medium'),
                'target_environment': 'unknown'
            })
        
        return anomalies
    
    def _extract_temporal_anomalies(self, details: Dict[str, Any], model_name: str, 
                                  analyzer_name: str) -> List[Dict[str, Any]]:
        """Extract temporal-specific anomalies"""
        
        anomalies = []
        
        # Extract from individual analyses
        individual_analyses = details.get('individual_analyses', {})
        
        for metric, metric_results in individual_analyses.items():
            for anomaly in metric_results.get('anomalies', []):
                anomalies.append({
                    'anomaly_id': str(uuid.uuid4()),
                    'model_name': model_name,
                    'analyzer_type': analyzer_name,
                    'anomaly_type': anomaly.get('type', 'temporal'),
                    'anomaly_score': anomaly.get('z_score', anomaly.get('magnitude', 1.0)),
                    'affected_columns': metric,
                    'anomaly_details': json.dumps(anomaly),
                    'detection_time': datetime.now(),
                    'severity': anomaly.get('severity', 'medium'),
                    'target_environment': 'unknown'
                })
        
        return anomalies
    
    def _extract_multivariate_anomalies(self, details: Dict[str, Any], model_name: str, 
                                       analyzer_name: str) -> List[Dict[str, Any]]:
        """Extract multivariate-specific anomalies"""
        
        anomalies = []
        
        # Extract consensus anomalies
        consensus_anomalies = details.get('consensus_anomalies', {})
        
        for anomaly in consensus_anomalies.get('anomalies', []):
            feature_values = anomaly.get('feature_values', {})
            affected_columns = ', '.join(feature_values.keys()) if feature_values else ''
            
            anomalies.append({
                'anomaly_id': str(uuid.uuid4()),
                'model_name': model_name,
                'analyzer_type': analyzer_name,
                'anomaly_type': 'multivariate_outlier',
                'anomaly_score': anomaly.get('confidence', 1.0),
                'affected_columns': affected_columns,
                'anomaly_details': json.dumps(anomaly),
                'detection_time': datetime.now(),
                'severity': 'high' if anomaly.get('confidence', 0) > 0.8 else 'medium',
                'target_environment': 'unknown'
            })
        
        return anomalies
    
    def _extract_distribution_anomalies(self, details: Dict[str, Any], model_name: str, 
                                      analyzer_name: str) -> List[Dict[str, Any]]:
        """Extract distribution-specific anomalies"""
        
        anomalies = []
        
        # Extract from individual segment analyses
        individual_analyses = details.get('individual_analyses', {})
        
        for segment, segment_results in individual_analyses.items():
            for anomaly in segment_results.get('anomalies', []):
                anomalies.append({
                    'anomaly_id': str(uuid.uuid4()),
                    'model_name': model_name,
                    'analyzer_type': analyzer_name,
                    'anomaly_type': 'distribution_change',
                    'anomaly_score': 1 - anomaly.get('p_value', 0.5),
                    'affected_columns': f"{segment}:{anomaly.get('metric', '')}",
                    'anomaly_details': json.dumps(anomaly),
                    'detection_time': datetime.now(),
                    'severity': anomaly.get('severity', 'medium'),
                    'target_environment': 'unknown'
                })
        
        # Extract cross-segment anomalies
        cross_segment = details.get('cross_segment_analysis', {})
        for anomaly in cross_segment.get('anomalies', []):
            anomalies.append({
                'anomaly_id': str(uuid.uuid4()),
                'model_name': model_name,
                'analyzer_type': analyzer_name,
                'anomaly_type': anomaly.get('type', 'cross_segment'),
                'anomaly_score': anomaly.get('concentration_change', 1.0),
                'affected_columns': f"{anomaly.get('segment', '')}:{anomaly.get('segment_value', '')}",
                'anomaly_details': json.dumps(anomaly),
                'detection_time': datetime.now(),
                'severity': anomaly.get('severity', 'medium'),
                'target_environment': 'unknown'
            })
        
        return anomalies
    
    def get_quality_history(self, model_name: Optional[str] = None, 
                          days: int = 30) -> Dict[str, Any]:
        """Get quality test history for analysis"""
        
        try:
            # Build base query
            where_clause = f"execution_time >= CURRENT_DATE - INTERVAL '{days} days'"
            if model_name:
                where_clause += f" AND model_name = '{model_name}'"
            
            # Get run summaries
            run_summary_sql = f"""
                SELECT 
                    run_id,
                    execution_time,
                    target_environment,
                    total_tests,
                    passed_tests,
                    failed_tests,
                    critical_failures,
                    status
                FROM {self.schema}.quality_run_summary
                WHERE {where_clause}
                ORDER BY execution_time DESC
            """
            
            # Get test results
            test_results_sql = f"""
                SELECT 
                    model_name,
                    test_type,
                    level,
                    severity,
                    status,
                    execution_time,
                    COUNT(*) as test_count
                FROM {self.schema}.quality_test_results
                WHERE {where_clause}
                GROUP BY model_name, test_type, level, severity, status, execution_time
                ORDER BY execution_time DESC
            """
            
            # Get anomalies
            anomalies_sql = f"""
                SELECT 
                    model_name,
                    analyzer_type,
                    anomaly_type,
                    severity,
                    detection_time,
                    COUNT(*) as anomaly_count
                FROM {self.schema}.quality_anomalies
                WHERE detection_time >= CURRENT_DATE - INTERVAL '{days} days'
                {"AND model_name = '" + model_name + "'" if model_name else ""}
                GROUP BY model_name, analyzer_type, anomaly_type, severity, detection_time
                ORDER BY detection_time DESC
            """
            
            # Adapt for different databases
            if self.connection_manager.db_type == 'bigquery':
                run_summary_sql = run_summary_sql.replace('CURRENT_DATE', 'CURRENT_DATE()')
                run_summary_sql = run_summary_sql.replace("INTERVAL '", "INTERVAL ")
                run_summary_sql = run_summary_sql.replace(" days'", " DAY")
                
                test_results_sql = test_results_sql.replace('CURRENT_DATE', 'CURRENT_DATE()')
                test_results_sql = test_results_sql.replace("INTERVAL '", "INTERVAL ")
                test_results_sql = test_results_sql.replace(" days'", " DAY")
                
                anomalies_sql = anomalies_sql.replace('CURRENT_DATE', 'CURRENT_DATE()')
                anomalies_sql = anomalies_sql.replace("INTERVAL '", "INTERVAL ")
                anomalies_sql = anomalies_sql.replace(" days'", " DAY")
            
            # Execute queries
            run_summaries = self.connection_manager.execute_query(run_summary_sql)
            test_results = self.connection_manager.execute_query(test_results_sql)
            anomalies = self.connection_manager.execute_query(anomalies_sql)
            
            return {
                'run_summaries': run_summaries.to_dict('records'),
                'test_results': test_results.to_dict('records'),
                'anomalies': anomalies.to_dict('records'),
                'period_days': days,
                'model_filter': model_name
            }
            
        except Exception as e:
            logging.error(f"Failed to get quality history: {str(e)}")
            return {'error': str(e)}
    
    def get_quality_trends(self, days: int = 90) -> Dict[str, Any]:
        """Get quality trends over time"""
        
        try:
            trends_sql = f"""
                WITH daily_summary AS (
                    SELECT 
                        DATE(execution_time) as date,
                        target_environment,
                        AVG(CAST(passed_tests AS FLOAT) / NULLIF(total_tests, 0)) as success_rate,
                        SUM(critical_failures) as daily_critical_failures,
                        COUNT(*) as daily_runs
                    FROM {self.schema}.quality_run_summary
                    WHERE execution_time >= CURRENT_DATE - INTERVAL '{days} days'
                    GROUP BY DATE(execution_time), target_environment
                )
                SELECT 
                    date,
                    target_environment,
                    success_rate,
                    daily_critical_failures,
                    daily_runs,
                    AVG(success_rate) OVER (
                        PARTITION BY target_environment 
                        ORDER BY date 
                        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                    ) as rolling_7day_success_rate
                FROM daily_summary
                ORDER BY target_environment, date
            """
            
            # Adapt for different databases
            if self.connection_manager.db_type == 'bigquery':
                trends_sql = trends_sql.replace('CURRENT_DATE', 'CURRENT_DATE()')
                trends_sql = trends_sql.replace("INTERVAL '", "INTERVAL ")
                trends_sql = trends_sql.replace(" days'", " DAY")
            elif self.connection_manager.db_type == 'snowflake':
                trends_sql = trends_sql.replace('CURRENT_DATE', 'CURRENT_DATE()')
                trends_sql = trends_sql.replace(" days'", " DAY'")
            
            trends_data = self.connection_manager.execute_query(trends_sql)
            
            return {
                'trends': trends_data.to_dict('records'),
                'period_days': days
            }
            
        except Exception as e:
            logging.error(f"Failed to get quality trends: {str(e)}")
            return {'error': str(e)}
    
    def cleanup_old_data(self, retention_days: int = 365) -> Dict[str, int]:
        """Clean up old quality data beyond retention period"""
        
        try:
            cleanup_results = {}
            
            # Clean up run summaries
            run_cleanup_sql = f"""
                DELETE FROM {self.schema}.quality_run_summary
                WHERE execution_time < CURRENT_DATE - INTERVAL '{retention_days} days'
            """
            
            # Clean up test results
            test_cleanup_sql = f"""
                DELETE FROM {self.schema}.quality_test_results
                WHERE execution_time < CURRENT_DATE - INTERVAL '{retention_days} days'
            """
            
            # Clean up anomalies
            anomaly_cleanup_sql = f"""
                DELETE FROM {self.schema}.quality_anomalies
                WHERE detection_time < CURRENT_DATE - INTERVAL '{retention_days} days'
            """
            
            # Adapt for different databases
            if self.connection_manager.db_type == 'bigquery':
                run_cleanup_sql = run_cleanup_sql.replace('CURRENT_DATE', 'CURRENT_DATE()')
                run_cleanup_sql = run_cleanup_sql.replace("INTERVAL '", "INTERVAL ")
                run_cleanup_sql = run_cleanup_sql.replace(" days'", " DAY")
                
                test_cleanup_sql = test_cleanup_sql.replace('CURRENT_DATE', 'CURRENT_DATE()')
                test_cleanup_sql = test_cleanup_sql.replace("INTERVAL '", "INTERVAL ")
                test_cleanup_sql = test_cleanup_sql.replace(" days'", " DAY")
                
                anomaly_cleanup_sql = anomaly_cleanup_sql.replace('CURRENT_DATE', 'CURRENT_DATE()')
                anomaly_cleanup_sql = anomaly_cleanup_sql.replace("INTERVAL '", "INTERVAL ")
                anomaly_cleanup_sql = anomaly_cleanup_sql.replace(" days'", " DAY")
            
            # Execute cleanup
            run_result = self.connection_manager.execute_sql(run_cleanup_sql)
            cleanup_results['run_summaries_deleted'] = run_result.rowcount if hasattr(run_result, 'rowcount') else 0
            
            test_result = self.connection_manager.execute_sql(test_cleanup_sql)
            cleanup_results['test_results_deleted'] = test_result.rowcount if hasattr(test_result, 'rowcount') else 0
            
            anomaly_result = self.connection_manager.execute_sql(anomaly_cleanup_sql)
            cleanup_results['anomalies_deleted'] = anomaly_result.rowcount if hasattr(anomaly_result, 'rowcount') else 0
            
            logging.info(f"Cleanup completed: {cleanup_results}")
            
            return cleanup_results
            
        except Exception as e:
            logging.error(f"Failed to cleanup old data: {str(e)}")
            return {'error': str(e)}
    
    def export_quality_report(self, model_name: Optional[str] = None, 
                            days: int = 30, format: str = 'json') -> Dict[str, Any]:
        """Export comprehensive quality report"""
        
        try:
            # Get all data
            history = self.get_quality_history(model_name, days)
            trends = self.get_quality_trends(days)
            
            if 'error' in history or 'error' in trends:
                return {'error': 'Failed to retrieve quality data'}
            
            # Compile comprehensive report
            report = {
                'report_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'model_filter': model_name,
                    'period_days': days,
                    'format': format
                },
                'summary_statistics': self._calculate_summary_stats(history),
                'historical_data': history,
                'trend_analysis': trends,
                'top_failing_tests': self._get_top_failing_tests(history),
                'anomaly_patterns': self._analyze_anomaly_patterns(history)
            }
            
            if format == 'json':
                return report
            elif format == 'csv':
                # Convert to CSV-friendly format
                return self._convert_report_to_csv(report)
            else:
                return {'error': f'Unsupported format: {format}'}
                
        except Exception as e:
            logging.error(f"Failed to export quality report: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_summary_stats(self, history: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics from historical data"""
        
        run_summaries = history.get('run_summaries', [])
        test_results = history.get('test_results', [])
        anomalies = history.get('anomalies', [])
        
        if not run_summaries:
            return {'error': 'No run summaries available'}
        
        # Calculate overall statistics
        total_runs = len(run_summaries)
        total_tests = sum(run.get('total_tests', 0) for run in run_summaries)
        total_passed = sum(run.get('passed_tests', 0) for run in run_summaries)
        total_failed = sum(run.get('failed_tests', 0) for run in run_summaries)
        total_critical = sum(run.get('critical_failures', 0) for run in run_summaries)
        
        success_rate = (total_passed / max(total_tests, 1)) * 100
        
        return {
            'total_runs': total_runs,
            'total_tests': total_tests,
            'overall_success_rate': round(success_rate, 2),
            'total_failures': total_failed,
            'critical_failures': total_critical,
            'total_anomalies': len(anomalies),
            'unique_models_tested': len(set(test.get('model_name', '') for test in test_results))
        }
    
    def _get_top_failing_tests(self, history: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get most frequently failing tests"""
        
        test_results = history.get('test_results', [])
        
        # Count failures by test type
        failure_counts = {}
        for test in test_results:
            if test.get('status') == 'failed':
                test_key = f"{test.get('model_name', '')}:{test.get('test_type', '')}"
                failure_counts[test_key] = failure_counts.get(test_key, 0) + test.get('test_count', 1)
        
        # Sort by failure count
        top_failures = sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return [{'test': test, 'failure_count': count} for test, count in top_failures]
    
    def _analyze_anomaly_patterns(self, history: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in anomalies"""
        
        anomalies = history.get('anomalies', [])
        
        if not anomalies:
            return {'message': 'No anomalies found in the specified period'}
        
        # Group by analyzer type
        analyzer_counts = {}
        for anomaly in anomalies:
            analyzer = anomaly.get('analyzer_type', 'unknown')
            analyzer_counts[analyzer] = analyzer_counts.get(analyzer, 0) + anomaly.get('anomaly_count', 1)
        
        # Group by severity
        severity_counts = {}
        for anomaly in anomalies:
            severity = anomaly.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + anomaly.get('anomaly_count', 1)
        
        return {
            'anomalies_by_analyzer': analyzer_counts,
            'anomalies_by_severity': severity_counts,
            'total_anomalies': sum(anomaly.get('anomaly_count', 1) for anomaly in anomalies)
        }
    
    def _convert_report_to_csv(self, report: Dict[str, Any]) -> Dict[str, str]:
        """Convert report to CSV format"""
        
        # This is a simplified CSV conversion
        # In practice, you might want to use pandas for better CSV handling
        
        csv_data = {}
        
        # Convert run summaries to CSV
        run_summaries = report.get('historical_data', {}).get('run_summaries', [])
        if run_summaries:
            headers = list(run_summaries[0].keys())
            csv_lines = [','.join(headers)]
            
            for run in run_summaries:
                row = [str(run.get(header, '')) for header in headers]
                csv_lines.append(','.join(row))
            
            csv_data['run_summaries.csv'] = '\n'.join(csv_lines)
        
        # Convert summary stats to CSV
        summary_stats = report.get('summary_statistics', {})
        if summary_stats and 'error' not in summary_stats:
            csv_lines = ['metric,value']
            for key, value in summary_stats.items():
                csv_lines.append(f'{key},{value}')
            
            csv_data['summary_statistics.csv'] = '\n'.join(csv_lines)
        
        return csv_data
