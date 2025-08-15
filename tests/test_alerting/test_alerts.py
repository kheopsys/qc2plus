# tests/test_alerting/test_alerts.py
"""
Tests pour qc2plus.alerting.alerts
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from qc2plus.alerting.alerts import AlertManager


class TestAlertManager:
    """Tests pour le gestionnaire d'alertes"""
    
    @pytest.fixture
    def basic_alerting_config(self):
        """Configuration d'alertes basique"""
        return {
            'enabled_channels': ['email', 'slack'],
            'thresholds': {
                'critical_failure_threshold': 1,
                'failure_rate_threshold': 0.2,
                'individual_alerts': ['critical'],
                'summary_alerts': ['high', 'medium', 'low']
            },
            'email': {
                'enabled': True,
                'smtp_server': 'smtp.test.com',
                'smtp_port': 587,
                'username': 'test@test.com',
                'password': 'test_password',
                'from_email': 'qc2plus@test.com',
                'to_emails': ['team@test.com']
            },
            'slack': {
                'enabled': True,
                'webhook_url': 'https://hooks.slack.com/test/webhook'
            },
            'teams': {
                'enabled': False,
                'webhook_url': 'https://test.webhook.office.com'
            }
        }
    
    @pytest.fixture
    def sample_results_with_critical_failure(self):
        """Résultats de tests avec échec critique"""
        return {
            'run_id': 'test-run-123',
            'target': 'dev',
            'total_tests': 10,
            'passed_tests': 8,
            'failed_tests': 2,
            'critical_failures': 1,
            'execution_duration': 30,
            'models': {
                'customers': {
                    'level1': {
                        'unique_customer_id': {
                            'passed': False,
                            'severity': 'critical',
                            'message': 'Duplicate customer IDs found',
                            'failed_rows': 5,
                            'total_rows': 1000
                        },
                        'not_null_email': {
                            'passed': False,
                            'severity': 'medium',
                            'message': 'Null emails found',
                            'failed_rows': 3,
                            'total_rows': 1000
                        }
                    },
                    'level2': {
                        'correlation': {
                            'passed': True,
                            'anomalies_count': 0,
                            'message': 'All correlations normal'
                        }
                    }
                }
            }
        }
    
    def test_alert_manager_initialization(self, basic_alerting_config):
        """Test d'initialisation du gestionnaire d'alertes"""
        alert_manager = AlertManager(basic_alerting_config)
        
        assert alert_manager.enabled_channels == ['email', 'slack']
        assert alert_manager.email_config['enabled'] == True
        assert alert_manager.slack_config['enabled'] == True
        assert alert_manager.teams_config['enabled'] == False
    
    def test_analyze_results_for_alerting_critical_failure(self, basic_alerting_config, sample_results_with_critical_failure):
        """Test analyse des résultats avec échec critique"""
        alert_manager = AlertManager(basic_alerting_config)
        
        alert_info = alert_manager._analyze_results_for_alerting(sample_results_with_critical_failure)
        
        assert alert_info['should_alert'] == True
        assert len(alert_info['critical_failures']) == 1
        assert len(alert_info['medium_failures']) == 1
        assert alert_info['critical_failures'][0]['severity'] == 'critical'
        assert alert_info['critical_failures'][0]['model'] == 'customers'
        assert alert_info['critical_failures'][0]['test'] == 'unique_customer_id'
    
    def test_analyze_results_no_alert_needed(self, basic_alerting_config):
        """Test analyse des résultats sans besoin d'alerte"""
        alert_manager = AlertManager(basic_alerting_config)
        
        good_results = {
            'total_tests': 10,
            'passed_tests': 10,
            'failed_tests': 0,
            'critical_failures': 0,
            'models': {}
        }
        
        alert_info = alert_manager._analyze_results_for_alerting(good_results)
        
        assert alert_info['should_alert'] == False
        assert len(alert_info['critical_failures']) == 0
        assert alert_info['failure_rate'] == 0.0
    
    def test_determine_summary_severity(self, basic_alerting_config):
        """Test détermination de la sévérité du résumé"""
        alert_manager = AlertManager(basic_alerting_config)
        
        # Test avec échecs critiques
        alert_info_critical = {
            'critical_failures': [{'test': 'test1'}],
            'high_failures': [],
            'failure_rate': 0.1
        }
        severity = alert_manager._determine_summary_severity(alert_info_critical)
        assert severity == 'critical'
        
        # Test avec échecs élevés
        alert_info_high = {
            'critical_failures': [],
            'high_failures': [{'test': 'test1'}],
            'failure_rate': 0.1
        }
        severity = alert_manager._determine_summary_severity(alert_info_high)
        assert severity == 'high'
        
        # Test avec taux d'échec élevé
        alert_info_high_rate = {
            'critical_failures': [],
            'high_failures': [],
            'failure_rate': 0.6
        }
        severity = alert_manager._determine_summary_severity(alert_info_high_rate)
        assert severity == 'high'
    
    @patch('smtplib.SMTP')
    def test_send_email_alert_individual(self, mock_smtp, basic_alerting_config):
        """Test envoi d'alerte email individuelle"""
        alert_manager = AlertManager(basic_alerting_config)
        
        # Mock du serveur SMTP
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        alert_data = {
            'alert_type': 'individual',
            'severity': 'critical',
            'model': 'customers',
            'test': 'unique_customer_id',
            'message': 'Duplicate IDs found',
            'timestamp': '2024-01-15T10:00:00',
            'run_id': 'test-run-123',
            'target': 'dev'
        }
        
        alert_manager._send_email_alert(alert_data, individual=True)
        
        # Vérifier que le serveur SMTP a été appelé
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.send_message.assert_called_once()
    
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
            'target': 'dev'
        }
        
        alert_manager._send_slack_alert(alert_data, individual=True)
        
        # Vérifier que la requête POST a été faite
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        assert call_args[1]['json']['text'] == '🚨 CRITICAL: 2QC+ Test Failure'
        assert 'attachments' in call_args[1]['json']
    
    @patch('requests.post')
    def test_send_teams_alert_summary(self, mock_post, basic_alerting_config):
        """Test envoi d'alerte Teams résumé"""
        # Activer Teams pour ce test
        config = basic_alerting_config.copy()
        config['teams']['enabled'] = True
        config['enabled_channels'] = ['teams']
        
        alert_manager = AlertManager(config)
        
        # Mock de la réponse HTTP
        mock_post.return_value.raise_for_status = MagicMock()
        
        alert_data = {
            'alert_type': 'summary',
            'severity': 'high',
            'run_id': 'test-run-123',
            'target': 'dev',
            'timestamp': '2024-01-15T10:00:00',
            'total_tests': 10,
            'passed_tests': 8,
            'failed_tests': 2,
            'critical_failures': 1,
            'high_failures': 0,
            'medium_failures': 1,
            'failure_rate': 0.2,
            'execution_duration': 30,
            'model_count': 2
        }
        
        alert_manager._send_teams_alert(alert_data, individual=False)
        
        # Vérifier que la requête POST a été faite
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        
        payload = call_args[1]['json']
        assert payload['@type'] == 'MessageCard'
        assert payload['themeColor'] == 'FF8800'  # Orange pour 'high'
        assert 'sections' in payload
    
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
            'execution_duration': 45,
            'run_id': 'prod-run-456'
        }
        
        payload = alert_manager._create_slack_summary_payload(alert_data)
        
        assert payload['text'] == '📊 2QC+ Quality Report - prod'
        assert len(payload['attachments']) == 1
        
        attachment = payload['attachments'][0]
        assert attachment['color'] == 'good'  # Medium = good color
        
        # Vérifier les champs
        fields = {field['title']: field['value'] for field in attachment['fields']}
        assert fields['Total Tests'] == '100'
        assert fields['Success Rate'] == '95.0%'
        assert fields['Execution Time'] == '45s'
    
    def test_test_alert_channels(self, basic_alerting_config):
        """Test de test des canaux d'alertes"""
        with patch('qc2plus.alerting.alerts.AlertManager._send_email_alert') as mock_email, \
             patch('qc2plus.alerting.alerts.AlertManager._send_slack_alert') as mock_slack:
            
            alert_manager = AlertManager(basic_alerting_config)
            
            # Mock successful sends
            mock_email.return_value = None
            mock_slack.return_value = None
            
            test_results = alert_manager.test_alert_channels()
            
            assert test_results['email'] == True
            assert test_results['slack'] == True
            assert 'teams' not in test_results  # Not enabled
    
    def test_email_html_generation(self, basic_alerting_config):
        """Test génération HTML pour emails"""
        alert_manager = AlertManager(basic_alerting_config)
        
        # Test email individuel
        alert_data = {
            'model': 'orders',
            'test': 'foreign_key_customer_id',
            'target': 'prod',
            'timestamp': '2024-01-15T14:30:00',
            'message': 'Invalid foreign key references found',
            'run_id': 'prod-run-789'
        }
        
        html = alert_manager._create_individual_email_html(alert_data)
        
        assert '<html>' in html
        assert 'CRITICAL QUALITY TEST FAILURE' in html
        assert 'orders' in html
        assert 'foreign_key_customer_id' in html
        assert 'Invalid foreign key references found' in html
        
        # Test email résumé
        summary_data = {
            'target': 'staging',
            'severity': 'high',
            'total_tests': 50,
            'passed_tests': 45,
            'failed_tests': 5,
            'critical_failures': 2,
            'high_failures': 2,
            'medium_failures': 1,
            'execution_duration': 120,
            'model_count': 8,
            'timestamp': '2024-01-15T14:30:00',
            'run_id': 'staging-run-101'
        }
        
        html = alert_manager._create_summary_email_html(summary_data)
        
        assert 'Quality Report Summary' in html
        assert 'staging' in html
        assert '90.0%' in html  # Success rate calculation
        assert '120s' in html
