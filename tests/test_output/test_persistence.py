# tests/test_output/test_persistence.py
"""
Tests pour qc2plus.output.persistence
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
import json
from datetime import datetime
from qc2plus.output.persistence import PersistenceManager


class TestPersistenceManager:
    """Tests pour le gestionnaire de persistence"""
    
    @pytest.fixture
    def mock_connection_manager(self):
        """Mock du gestionnaire de connexion"""
        mock = Mock()
        mock.config = {'schema': 'public'}
        mock.db_type = 'postgresql'
        mock.execute_sql = MagicMock()
        mock.execute_query = MagicMock()
        return mock
    
    @pytest.fixture
    def sample_results(self):
        """Résultats d'exemple pour les tests"""
        return {
            'run_id': 'test-run-123',
            'project_name': 'test_project',
            'target': 'dev',
            'total_tests': 5,
            'passed_tests': 3,
            'failed_tests': 2,
            'critical_failures': 1,
            'execution_duration': 45,
            'status': 'failure',
            'models': {
                'customers': {
                    'level1': {
                        'unique_customer_id': {
                            'passed': False,
                            'severity': 'critical',
                            'message': 'Duplicates found',
                            'failed_rows': 5,
                            'total_rows': 1000
                        },
                        'not_null_email': {
                            'passed': True,
                            'severity': 'medium',
                            'message': 'Test passed',
                            'failed_rows': 0,
                            'total_rows': 1000
                        }
                    },
                    'level2': {
                        'correlation': {
                            'passed': False,
                            'anomalies_count': 3,
                            'message': 'Correlation anomalies detected',
                            'details': {
                                'static_correlation': {
                                    'anomalies': [
                                        {
                                            'variable_pair': 'var1_vs_var2',
                                            'correlation': 0.2,
                                            'expected_correlation': 0.8,
                                            'severity': 'high'
                                        }
                                    ]
                                }
                            }
                        },
                        'temporal': {
                            'passed': True,
                            'anomalies_count': 0,
                            'message': 'No temporal anomalies'
                        }
                    }
                }
            }
        }
    
    def test_persistence_manager_initialization(self, mock_connection_manager):
        """Test d'initialisation du gestionnaire de persistence"""
        persistence_manager = PersistenceManager(mock_connection_manager)
        
        assert persistence_manager.connection_manager == mock_connection_manager
        assert persistence_manager.schema == 'public'
    
    def test_save_run_summary(self, mock_connection_manager, sample_results):
        """Test sauvegarde du résumé d'exécution"""
        persistence_manager = PersistenceManager(mock_connection_manager)
        
        persistence_manager.save_run_summary(sample_results)
        
        # Vérifier que execute_sql a été appelé
        mock_connection_manager.execute_sql.assert_called_once()
        
        # Vérifier le SQL généré
        call_args = mock_connection_manager.execute_sql.call_args
        sql = call_args[0][0]
        
        assert 'INSERT INTO public.quality_run_summary' in sql
        assert 'run_id' in sql
        assert 'total_tests' in sql
        assert 'execution_duration_seconds' in sql
    
    def test_save_test_results(self, mock_connection_manager, sample_results):
        """Test sauvegarde des résultats de tests"""
        persistence_manager = PersistenceManager(mock_connection_manager)
        
        persistence_manager.save_test_results(sample_results)
        
        # Vérifier que execute_sql a été appelé plusieurs fois (une par test)
        assert mock_connection_manager.execute_sql.call_count >= 3  # Au moins 3 tests
        
        # Vérifier qu'au moins un appel concerne quality_test_results
        sql_calls = [call[0][0] for call in mock_connection_manager.execute_sql.call_args_list]
        test_results_calls = [sql for sql in sql_calls if 'quality_test_results' in sql]
        assert len(test_results_calls) > 0
    
    def test_save_anomalies(self, mock_connection_manager, sample_results):
        """Test sauvegarde des anomalies"""
        persistence_manager = PersistenceManager(mock_connection_manager)
        
        persistence_manager.save_anomalies(sample_results)
        
        # Vérifier que execute_sql a été appelé pour les anomalies
        sql_calls = [call[0][0] for call in mock_connection_manager.execute_sql.call_args_list]
        anomaly_calls = [sql for sql in sql_calls if 'quality_anomalies' in sql]
        assert len(anomaly_calls) > 0
    
    def test_extract_test_type(self, mock_connection_manager):
        """Test extraction du type de test"""
        persistence_manager = PersistenceManager(mock_connection_manager)
        
        # Tests des extractions de types
        assert persistence_manager._extract_test_type('unique_customer_id') == 'unique'
        assert persistence_manager._extract_test_type('not_null_email') == 'not_null'
        assert persistence_manager._extract_test_type('email_format_contact') == 'email_format'
        assert persistence_manager._extract_test_type('foreign_key_customer_ref') == 'foreign_key'
        assert persistence_manager._extract_test_type('statistical_threshold_daily_count') == 'statistical_threshold'
        assert persistence_manager._extract_test_type('custom_business_rule') == 'custom'
    
    def test_extract_correlation_anomalies(self, mock_connection_manager):
        """Test extraction des anomalies de corrélation"""
        persistence_manager = PersistenceManager(mock_connection_manager)
        
        details = {
            'static_correlation': {
                'anomalies': [
                    {
                        'variable_pair': 'sales_vs_marketing',
                        'correlation': 0.3,
                        'expected_correlation': 0.8,
                        'reason': 'Correlation below threshold',
                        'severity': 'high'
                    }
                ]
            },
            'temporal_correlation': {
                'anomalies': [
                    {
                        'variable_pair': 'users_vs_revenue',
                        'anomaly_type': 'sudden_change',
                        'recent_change': 0.5,
                        'severity': 'medium'
                    }
                ]
            }
        }
        
        anomalies = persistence_manager._extract_correlation_anomalies(
            details, 'test_model', 'correlation'
        )
        
        assert len(anomalies) == 2
        assert anomalies[0]['anomaly_type'] == 'correlation_deviation'
        assert anomalies[0]['affected_columns'] == 'sales_vs_marketing'
        assert anomalies[1]['anomaly_type'] == 'sudden_change'
        assert anomalies[1]['affected_columns'] == 'users_vs_revenue'
    
    def test_get_quality_history(self, mock_connection_manager):
        """Test récupération de l'historique qualité"""
        # Mock des retours de requêtes
        mock_connection_manager.execute_query.side_effect = [
            pd.DataFrame({  # run_summaries
                'run_id': ['run1', 'run2'],
                'total_tests': [10, 15],
                'passed_tests': [8, 12],
                'failed_tests': [2, 3]
            }),
            pd.DataFrame({  # test_results
                'model_name': ['customers', 'orders'],
                'test_type': ['unique', 'not_null'],
                'status': ['failed', 'passed'],
                'test_count': [1, 1]
            }),
            pd.DataFrame({  # anomalies
                'model_name': ['customers'],
                'analyzer_type': ['correlation'],
                'anomaly_count': [2]
            })
        ]
        
        persistence_manager = PersistenceManager(mock_connection_manager)
        
        history = persistence_manager.get_quality_history('customers', 30)
        
        assert 'run_summaries' in history
        assert 'test_results' in history
        assert 'anomalies' in history
        assert history['period_days'] == 30
        assert history['model_filter'] == 'customers'
        
        # Vérifier que 3 requêtes ont été exécutées
        assert mock_connection_manager.execute_query.call_count == 3
    
    def test_get_quality_trends(self, mock_connection_manager):
        """Test récupération des tendances qualité"""
        # Mock du retour de requête
        mock_connection_manager.execute_query.return_value = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'target_environment': ['dev', 'dev'],
            'success_rate': [0.9, 0.85],
            'daily_critical_failures': [0, 1],
            'rolling_7day_success_rate': [0.9, 0.875]
        })
        
        persistence_manager = PersistenceManager(mock_connection_manager)
        
        trends = persistence_manager.get_quality_trends(90)
        
        assert 'trends' in trends
        assert trends['period_days'] == 90
        assert len(trends['trends']) == 2
        
        # Vérifier que la requête contient les éléments attendus
        call_args = mock_connection_manager.execute_query.call_args
        sql = call_args[0][0]
        assert 'WITH daily_summary AS' in sql
        assert 'rolling_7day_success_rate' in sql
    
    def test_cleanup_old_data(self, mock_connection_manager):
        """Test nettoyage des anciennes données"""
        # Mock des retours de delete
        mock_result = Mock()
        mock_result.rowcount = 5
        mock_connection_manager.execute_sql.return_value = mock_result
        
        persistence_manager = PersistenceManager(mock_connection_manager)
        
        cleanup_results = persistence_manager.cleanup_old_data(365)
        
        # Vérifier que 3 requêtes de nettoyage ont été exécutées
        assert mock_connection_manager.execute_sql.call_count == 3
        
        # Vérifier les résultats
        assert 'run_summaries_deleted' in cleanup_results
        assert 'test_results_deleted' in cleanup_results
        assert 'anomalies_deleted' in cleanup_results
        
        # Vérifier que les requêtes DELETE sont bien générées
        sql_calls = [call[0][0] for call in mock_connection_manager.execute_sql.call_args_list]
        delete_calls = [sql for sql in sql_calls if 'DELETE FROM' in sql]
        assert len(delete_calls) == 3
    
    def test_export_quality_report_json(self, mock_connection_manager):
        """Test export de rapport qualité en JSON"""
        with patch.object(PersistenceManager, 'get_quality_history') as mock_history, \
             patch.object(PersistenceManager, 'get_quality_trends') as mock_trends:
            
            # Mock des données d'historique et tendances
            mock_history.return_value = {
                'run_summaries': [{'run_id': 'test1', 'total_tests': 10}],
                'test_results': [{'model_name': 'customers', 'status': 'passed'}],
                'anomalies': []
            }
            
            mock_trends.return_value = {
                'trends': [{'date': '2024-01-01', 'success_rate': 0.9}]
            }
            
            persistence_manager = PersistenceManager(mock_connection_manager)
            
            report = persistence_manager.export_quality_report('customers', 30, 'json')
            
            assert 'report_metadata' in report
            assert 'summary_statistics' in report
            assert 'historical_data' in report
            assert 'trend_analysis' in report
            assert report['report_metadata']['format'] == 'json'
            assert report['report_metadata']['model_filter'] == 'customers'
    
    def test_calculate_summary_stats(self, mock_connection_manager):
        """Test calcul des statistiques de résumé"""
        persistence_manager = PersistenceManager(mock_connection_manager)
        
        history = {
            'run_summaries': [
                {'total_tests': 10, 'passed_tests': 8, 'failed_tests': 2, 'critical_failures': 1},
                {'total_tests': 15, 'passed_tests': 12, 'failed_tests': 3, 'critical_failures': 0}
            ],
            'test_results': [
                {'model_name': 'customers'},
                {'model_name': 'orders'},
                {'model_name': 'customers'}
            ],
            'anomalies': [
                {'anomaly_count': 2},
                {'anomaly_count': 1}
            ]
        }
        
        stats = persistence_manager._calculate_summary_stats(history)
        
        assert stats['total_runs'] == 2
        assert stats['total_tests'] == 25  # 10 + 15
        assert stats['total_failures'] == 5  # 2 + 3
        assert stats['critical_failures'] == 1  # 1 + 0
        assert stats['overall_success_rate'] == 80.0  # (8+12)/(10+15) * 100
        assert stats['unique_models_tested'] == 2  # customers, orders
    
    def test_database_adaptation_bigquery(self, mock_connection_manager):
        """Test adaptation pour BigQuery"""
        mock_connection_manager.db_type = 'bigquery'
        
        persistence_manager = PersistenceManager(mock_connection_manager)
        
        sample_results = {
            'run_id': 'test',
            'total_tests': 10,
            'passed_tests': 8,
            'failed_tests': 2,
            'critical_failures': 0,
            'execution_duration': 30,
            'status': 'success',
            'target': 'dev',
            'models': {}
        }
        
        persistence_manager.save_run_summary(sample_results)
        
        # Vérifier que la requête a été adaptée pour BigQuery
        call_args = mock_connection_manager.execute_sql.call_args
        sql = call_args[0][0]
        
        # BigQuery utilise des paramètres différents
        # (Le test exact dépend de l'implémentation spécifique)
        assert 'INSERT INTO' in sql
        assert mock_connection_manager.execute_sql.called
