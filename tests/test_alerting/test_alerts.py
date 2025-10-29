# tests/test_alerting/test_alerts.py
"""
Tests pour qc2plus.alerting.alerts
"""

import pytest
from unittest.mock import patch, MagicMock
from qc2plus.alerting.alerts import AlertManager


@pytest.fixture
def basic_alerting_config():
    """Configuration de base pour les alertes"""
    return {
        'enabled_channels': ['slack'],
        'email': {
            'enabled': True,
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@test.com',
            'password': 'test_password',
            'from_email': 'qc2plus@test.com',
            'to_emails': ['admin@test.com']
        },
        'slack': {
            'enabled': True,
            'webhook_url': 'https://hooks.slack.com/test/webhook'
        },
        'teams': {
            'enabled': False,
            'webhook_url': 'https://test.webhook.office.com'
        },
        'thresholds': {
            'critical_failure_threshold': 1,
            'failure_rate_threshold': 0.2
        }
    }


class TestAlertManager:
    
    @patch('requests.post')
    def test_send_slack_alert_individual(self, mock_post, basic_alerting_config):
        """Test envoi d'alerte Slack individuelle"""
        alert_manager = AlertManager(basic_alerting_config)
    
        # Mock de la réponse HTTP
        mock_post.return_value.raise_for_status = MagicMock()

        alert_data = {
            'alert_type': 'individual',
            'severity': 'critical',
            'model': 'customers',
            'test': 'unique_customer_id',
            'message': 'Duplicate IDs found',
            'timestamp': '2024-01-15T10:00:00',
            'run_id': 'test-run-123',
            'target': 'dev',
            'failed_rows': 5,
            'total_rows': 100,
            'test_type': 'level1',
            'explanation': 'Test for unique values',
            'examples': ['example1', 'example2'],
            'query': 'SELECT * FROM customers'
        }

        alert_manager._send_slack_alert(alert_data, individual=True)

        # Vérifier que la requête POST a été faite
        mock_post.assert_called_once()
        call_args = mock_post.call_args

        # ✅ FIX 1: Vérifier avec le nouveau format de message
        expected_text = '🚨 CRITICAL: 2QC+ Test Failure ON MODEL CUSTOMERS'
        assert call_args[1]['json']['text'] == expected_text
    
    def test_create_slack_summary_payload(self, basic_alerting_config):
        """Test création du payload Slack pour résumé"""
        alert_manager = AlertManager(basic_alerting_config)

        alert_data = {
            'target': 'prod',
            'severity': 'medium',
            'total_tests': 100,
            'passed_tests': 95,
            'failed_tests': 5,
            'critical_failures': 0,
            'high_failures': 2,      # ✅ FIX 2: Ajouter high_failures
            'medium_failures': 3,    # ✅ FIX 2: Ajouter medium_failures
            'execution_duration': 45,
            'run_id': 'prod-run-456',
            'failure_details': {     # ✅ FIX 2: Ajouter failure_details
                'level1_failures': [],
                'level2_anomalies': [],
                'total_anomalies': 0
            }
        }

        payload = alert_manager._create_slack_summary_payload(alert_data)

        # Vérifier la structure du payload
        assert 'text' in payload
        assert 'attachments' in payload
        assert len(payload['attachments']) > 0
        
        # Vérifier les champs
        fields = payload['attachments'][0]['fields']
        field_titles = [f['title'] for f in fields]
        
        assert '📊 Total Tests' in field_titles
        assert '✅ Success Rate' in field_titles
        assert '🚨 Critical' in field_titles
    
    def test_analyze_results_for_alerting(self, basic_alerting_config):
        """Test analyse des résultats pour alerting"""
        alert_manager = AlertManager(basic_alerting_config)
        
        results = {
            'run_id': 'test-123',
            'target': 'dev',
            'total_tests': 10,
            'passed_tests': 7,
            'failed_tests': 3,
            'models': {
                'customers': {
                    'level1': {
                        'unique_id': {
                            'passed': False,
                            'severity': 'critical',
                            'message': 'Duplicates found',
                            'failed_rows': 5,
                            'total_rows': 100
                        }
                    },
                    'level2': {
                        'correlation': {
                            'passed': True,
                            'anomalies_count': 0
                        }
                    }
                }
            }
        }
        
        alert_info = alert_manager._analyze_results_for_alerting(results)
        
        assert 'should_alert' in alert_info
        assert 'critical_failures' in alert_info
        assert len(alert_info['critical_failures']) == 1
    
    def test_determine_level2_severity(self, basic_alerting_config):
        """Test détermination de la sévérité Level 2"""
        alert_manager = AlertManager(basic_alerting_config)
        
        # Anomalie avec haute sévérité
        analyzer_result = {
            'details': {
                'static_correlation': {
                    'anomalies': [
                        {'severity': 'high', 'correlation': 0.2}
                    ]
                }
            }
        }
        
        severity = alert_manager._determine_level2_severity(analyzer_result, 5)
        assert severity in ['critical', 'high', 'medium', 'low']
    
    def test_get_level2_explanation(self, basic_alerting_config):
        """Test génération d'explication Level 2"""
        alert_manager = AlertManager(basic_alerting_config)
        
        analyzer_result = {
            'details': {
                'static_correlation': {
                    'anomalies': [
                        {'variable_pair': 'sales_vs_marketing'}
                    ]
                },
                'variables_analyzed': ['sales', 'marketing']
            },
            'anomalies_count': 1
        }
        
        explanation = alert_manager._get_level2_explanation('correlation', analyzer_result)
        
        assert 'Correlation analysis' in explanation
        assert '1' in explanation and 'anomal' in explanation.lower()
    
    def test_extract_level2_examples(self, basic_alerting_config):
        """Test extraction d'exemples Level 2"""
        alert_manager = AlertManager(basic_alerting_config)
        
        analyzer_result = {
            'details': {
                'static_correlation': {
                    'anomalies': [
                        {
                            'variable_pair': 'sales_vs_marketing',
                            'correlation': 0.3,
                            'expected_correlation': 0.8,
                            'reason': 'Below threshold'
                        }
                    ]
                }
            }
        }
        
        examples = alert_manager._extract_level2_examples(analyzer_result)
        
        assert len(examples) > 0
        assert 'sales_vs_marketing' in examples[0]