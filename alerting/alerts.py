"""
2QC+ Alerting System
Multi-channel alerting for Email, Slack, Teams
"""

import logging
import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Any, Optional
from datetime import datetime


class AlertManager:
    """Manages multi-channel alerting for quality test results"""
    
    def __init__(self, alerting_config: Dict[str, Any]):
        self.config = alerting_config
        self.enabled_channels = alerting_config.get('enabled_channels', [])
        
        # Email configuration
        self.email_config = alerting_config.get('email', {})
        
        # Slack configuration
        self.slack_config = alerting_config.get('slack', {})
        
        # Teams configuration
        self.teams_config = alerting_config.get('teams', {})
        
        # Alert thresholds
        self.thresholds = alerting_config.get('thresholds', {
            'critical_failure_threshold': 1,
            'failure_rate_threshold': 0.2,
            'individual_alerts': ['critical'],
            'summary_alerts': ['high', 'medium', 'low']
        })
    
    def send_alerts(self, results: Dict[str, Any]) -> None:
        """Send alerts based on test results"""
        
        try:
            # Determine alert severity and type
            alert_info = self._analyze_results_for_alerting(results)
            
            if not alert_info['should_alert']:
                logging.info("No alerts needed based on current thresholds")
                return
            
            # Send individual alerts for critical failures
            if alert_info['critical_failures']:
                self._send_individual_alerts(alert_info['critical_failures'], results)
            
            # Send summary alert
            if alert_info['summary_needed']:
                self._send_summary_alert(alert_info, results)
                
        except Exception as e:
            logging.error(f"Failed to send alerts: {str(e)}")
    
    def _analyze_results_for_alerting(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze results to determine what alerts to send"""
        
        critical_failures = []
        high_failures = []
        medium_failures = []
        
        # Extract failures by severity
        for model_name, model_results in results.get('models', {}).items():
            
            # Level 1 failures
            for test_name, test_result in model_results.get('level1', {}).items():
                if not test_result.get('passed', True):
                    severity = test_result.get('severity', 'medium')
                    failure_info = {
                        'model': model_name,
                        'test': test_name,
                        'type': 'level1',
                        'severity': severity,
                        'message': test_result.get('message', ''),
                        'failed_rows': test_result.get('failed_rows', 0),
                        'total_rows': test_result.get('total_rows', 0)
                    }
                    
                    if severity == 'critical':
                        critical_failures.append(failure_info)
                    elif severity == 'high':
                        high_failures.append(failure_info)
                    else:
                        medium_failures.append(failure_info)
            
            # Level 2 failures (anomalies)
            for analyzer_name, analyzer_result in model_results.get('level2', {}).items():
                if not analyzer_result.get('passed', True):
                    anomalies_count = analyzer_result.get('anomalies_count', 0)
                    if anomalies_count > 0:
                        failure_info = {
                            'model': model_name,
                            'test': analyzer_name,
                            'type': 'level2',
                            'severity': 'medium',  # Level 2 anomalies are typically medium severity
                            'message': analyzer_result.get('message', ''),
                            'anomalies_count': anomalies_count
                        }
                        medium_failures.append(failure_info)
        
        # Determine alerting needs
        total_failures = len(critical_failures) + len(high_failures) + len(medium_failures)
        failure_rate = total_failures / max(results.get('total_tests', 1), 1)
        
        should_alert = (
            len(critical_failures) >= self.thresholds['critical_failure_threshold'] or
            failure_rate >= self.thresholds['failure_rate_threshold']
        )
        
        return {
            'should_alert': should_alert,
            'critical_failures': critical_failures,
            'high_failures': high_failures,
            'medium_failures': medium_failures,
            'total_failures': total_failures,
            'failure_rate': failure_rate,
            'summary_needed': should_alert
        }
    
    def _send_individual_alerts(self, critical_failures: List[Dict[str, Any]], 
                              results: Dict[str, Any]) -> None:
        """Send individual alerts for critical failures"""
        
        for failure in critical_failures:
            alert_data = {
                'alert_type': 'individual',
                'severity': 'critical',
                'model': failure['model'],
                'test': failure['test'],
                'message': failure['message'],
                'timestamp': datetime.now().isoformat(),
                'run_id': results.get('run_id', ''),
                'target': results.get('target', '')
            }
            
            # Send to enabled channels
            if 'email' in self.enabled_channels:
                self._send_email_alert(alert_data, individual=True)
            
            if 'slack' in self.enabled_channels:
                self._send_slack_alert(alert_data, individual=True)
            
            if 'teams' in self.enabled_channels:
                self._send_teams_alert(alert_data, individual=True)
    
    def _send_summary_alert(self, alert_info: Dict[str, Any], results: Dict[str, Any]) -> None:
        """Send summary alert with overall results"""
        
        alert_data = {
            'alert_type': 'summary',
            'severity': self._determine_summary_severity(alert_info),
            'run_id': results.get('run_id', ''),
            'target': results.get('target', ''),
            'timestamp': datetime.now().isoformat(),
            'total_tests': results.get('total_tests', 0),
            'passed_tests': results.get('passed_tests', 0),
            'failed_tests': results.get('failed_tests', 0),
            'critical_failures': len(alert_info['critical_failures']),
            'high_failures': len(alert_info['high_failures']),
            'medium_failures': len(alert_info['medium_failures']),
            'failure_rate': alert_info['failure_rate'],
            'execution_duration': results.get('execution_duration', 0),
            'model_count': len(results.get('models', {}))
        }
        
        # Send to enabled channels
        if 'email' in self.enabled_channels:
            self._send_email_alert(alert_data, individual=False)
        
        if 'slack' in self.enabled_channels:
            self._send_slack_alert(alert_data, individual=False)
        
        if 'teams' in self.enabled_channels:
            self._send_teams_alert(alert_data, individual=False)
    
    def _determine_summary_severity(self, alert_info: Dict[str, Any]) -> str:
        """Determine overall severity for summary alert"""
        
        if alert_info['critical_failures']:
            return 'critical'
        elif alert_info['high_failures']:
            return 'high'
        elif alert_info['failure_rate'] > 0.5:
            return 'high'
        else:
            return 'medium'
    
    def _send_email_alert(self, alert_data: Dict[str, Any], individual: bool = False) -> None:
        """Send email alert"""
        
        try:
            if not self.email_config.get('enabled', False):
                return
            
            smtp_server = self.email_config['smtp_server']
            smtp_port = self.email_config.get('smtp_port', 587)
            username = self.email_config['username']
            password = self.email_config['password']
            from_email = self.email_config.get('from_email', username)
            to_emails = self.email_config['to_emails']
            
            # Create message
            msg = MIMEMultipart('alternative')
            
            if individual:
                subject = f"🚨 CRITICAL: 2QC+ Test Failure - {alert_data['model']}"
                html_content = self._create_individual_email_html(alert_data)
            else:
                severity_emoji = {'critical': '🚨', 'high': '⚠️', 'medium': '📊'}
                emoji = severity_emoji.get(alert_data['severity'], '📊')
                subject = f"{emoji} 2QC+ Quality Report - {alert_data['target']} ({alert_data['failed_tests']} failures)"
                html_content = self._create_summary_email_html(alert_data)
            
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = ', '.join(to_emails)
            
            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
            
            logging.info(f"Email alert sent successfully ({'individual' if individual else 'summary'})")
            
        except Exception as e:
            logging.error(f"Failed to send email alert: {str(e)}")
    
    def _send_slack_alert(self, alert_data: Dict[str, Any], individual: bool = False) -> None:
        """Send Slack alert"""
        
        try:
            if not self.slack_config.get('enabled', False):
                return
            
            webhook_url = self.slack_config['webhook_url']
            
            if individual:
                payload = self._create_slack_individual_payload(alert_data)
            else:
                payload = self._create_slack_summary_payload(alert_data)
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logging.info(f"Slack alert sent successfully ({'individual' if individual else 'summary'})")
            
        except Exception as e:
            logging.error(f"Failed to send Slack alert: {str(e)}")
    
    def _send_teams_alert(self, alert_data: Dict[str, Any], individual: bool = False) -> None:
        """Send Microsoft Teams alert"""
        
        try:
            if not self.teams_config.get('enabled', False):
                return
            
            webhook_url = self.teams_config['webhook_url']
            
            if individual:
                payload = self._create_teams_individual_payload(alert_data)
            else:
                payload = self._create_teams_summary_payload(alert_data)
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            logging.info(f"Teams alert sent successfully ({'individual' if individual else 'summary'})")
            
        except Exception as e:
            logging.error(f"Failed to send Teams alert: {str(e)}")
    
    def _create_individual_email_html(self, alert_data: Dict[str, Any]) -> str:
        """Create HTML content for individual email alert"""
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="background-color: #ff4444; color: white; padding: 15px; border-radius: 5px;">
                <h2>🚨 CRITICAL QUALITY TEST FAILURE</h2>
            </div>
            
            <div style="margin: 20px 0;">
                <h3>Test Details</h3>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Model:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert_data['model']}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Test:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert_data['test']}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Environment:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert_data['target']}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Time:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert_data['timestamp']}</td></tr>
                </table>
            </div>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
    def _create_individual_email_html(self, alert_data: Dict[str, Any]) -> str:
        """Create HTML content for individual email alert"""
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="background-color: #ff4444; color: white; padding: 15px; border-radius: 5px;">
                <h2>🚨 CRITICAL QUALITY TEST FAILURE</h2>
            </div>
            
            <div style="margin: 20px 0;">
                <h3>Test Details</h3>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Model:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert_data['model']}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Test:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert_data['test']}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Environment:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert_data['target']}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Time:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert_data['timestamp']}</td></tr>
                </table>
            </div>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
                <h4>Error Message</h4>
                <p style="font-family: monospace; background-color: white; padding: 10px; border-left: 4px solid #ff4444;">
                    {alert_data['message']}
                </p>
            </div>
            
            <div style="margin: 20px 0;">
                <p><strong>Run ID:</strong> {alert_data['run_id']}</p>
                <p><em>This is an automated alert from 2QC+ Data Quality Framework</em></p>
            </div>
        </body>
        </html>
        """
    
    def _create_summary_email_html(self, alert_data: Dict[str, Any]) -> str:
        """Create HTML content for summary email alert"""
        
        severity_colors = {
            'critical': '#ff4444',
            'high': '#ff8800',
            'medium': '#ffcc00'
        }
        
        color = severity_colors.get(alert_data['severity'], '#ffcc00')
        success_rate = (alert_data['passed_tests'] / max(alert_data['total_tests'], 1)) * 100
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="background-color: {color}; color: white; padding: 15px; border-radius: 5px;">
                <h2>📊 2QC+ Quality Report Summary</h2>
            </div>
            
            <div style="margin: 20px 0;">
                <h3>Execution Summary</h3>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Environment:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert_data['target']}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Run ID:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert_data['run_id']}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Execution Time:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert_data['execution_duration']}s</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Models Tested:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert_data['model_count']}</td></tr>
                </table>
            </div>
            
            <div style="margin: 20px 0;">
                <h3>Test Results</h3>
                <div style="display: flex; gap: 20px; margin: 15px 0;">
                    <div style="background-color: #4CAF50; color: white; padding: 15px; border-radius: 5px; text-align: center; flex: 1;">
                        <h4 style="margin: 0;">Passed</h4>
                        <p style="font-size: 24px; margin: 5px 0;">{alert_data['passed_tests']}</p>
                    </div>
                    <div style="background-color: #f44336; color: white; padding: 15px; border-radius: 5px; text-align: center; flex: 1;">
                        <h4 style="margin: 0;">Failed</h4>
                        <p style="font-size: 24px; margin: 5px 0;">{alert_data['failed_tests']}</p>
                    </div>
                    <div style="background-color: #2196F3; color: white; padding: 15px; border-radius: 5px; text-align: center; flex: 1;">
                        <h4 style="margin: 0;">Success Rate</h4>
                        <p style="font-size: 24px; margin: 5px 0;">{success_rate:.1f}%</p>
                    </div>
                </div>
            </div>
            
            <div style="margin: 20px 0;">
                <h3>Failure Breakdown</h3>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr><td style="padding: 8px; border: 1px solid #ddd; background-color: #ff4444; color: white;"><strong>Critical:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert_data['critical_failures']}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd; background-color: #ff8800; color: white;"><strong>High:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert_data['high_failures']}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd; background-color: #ffcc00;"><strong>Medium:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{alert_data['medium_failures']}</td></tr>
                </table>
            </div>
            
            <div style="margin: 20px 0;">
                <p><em>Generated at: {alert_data['timestamp']}</em></p>
                <p><em>This is an automated report from 2QC+ Data Quality Framework</em></p>
            </div>
        </body>
        </html>
        """
    
    def _create_slack_individual_payload(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Slack payload for individual alert"""
        
        return {
            "text": f"🚨 CRITICAL: 2QC+ Test Failure",
            "attachments": [
                {
                    "color": "danger",
                    "fields": [
                        {"title": "Model", "value": alert_data['model'], "short": True},
                        {"title": "Test", "value": alert_data['test'], "short": True},
                        {"title": "Environment", "value": alert_data['target'], "short": True},
                        {"title": "Run ID", "value": alert_data['run_id'], "short": True},
                        {"title": "Error", "value": alert_data['message'], "short": False}
                    ],
                    "footer": "2QC+ Data Quality Framework",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
    
    def _create_slack_summary_payload(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Slack payload for summary alert"""
        
        color_map = {'critical': 'danger', 'high': 'warning', 'medium': 'good'}
        color = color_map.get(alert_data['severity'], 'good')
        
        success_rate = (alert_data['passed_tests'] / max(alert_data['total_tests'], 1)) * 100
        
        return {
            "text": f"📊 2QC+ Quality Report - {alert_data['target']}",
            "attachments": [
                {
                    "color": color,
                    "fields": [
                        {"title": "Total Tests", "value": str(alert_data['total_tests']), "short": True},
                        {"title": "Success Rate", "value": f"{success_rate:.1f}%", "short": True},
                        {"title": "Critical Failures", "value": str(alert_data['critical_failures']), "short": True},
                        {"title": "Execution Time", "value": f"{alert_data['execution_duration']}s", "short": True},
                        {"title": "Run ID", "value": alert_data['run_id'], "short": False}
                    ],
                    "footer": "2QC+ Data Quality Framework",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
    
    def _create_teams_individual_payload(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Microsoft Teams payload for individual alert"""
        
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000",
            "summary": "Critical 2QC+ Test Failure",
            "sections": [
                {
                    "activityTitle": "🚨 CRITICAL: 2QC+ Test Failure",
                    "activitySubtitle": f"Model: {alert_data['model']} | Test: {alert_data['test']}",
                    "facts": [
                        {"name": "Environment", "value": alert_data['target']},
                        {"name": "Run ID", "value": alert_data['run_id']},
                        {"name": "Timestamp", "value": alert_data['timestamp']},
                        {"name": "Error Message", "value": alert_data['message']}
                    ],
                    "markdown": True
                }
            ]
        }
    
    def _create_teams_summary_payload(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Microsoft Teams payload for summary alert"""
        
        color_map = {'critical': 'FF0000', 'high': 'FF8800', 'medium': 'FFCC00'}
        theme_color = color_map.get(alert_data['severity'], 'FFCC00')
        
        success_rate = (alert_data['passed_tests'] / max(alert_data['total_tests'], 1)) * 100
        
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": "2QC+ Quality Report Summary",
            "sections": [
                {
                    "activityTitle": "📊 2QC+ Quality Report Summary",
                    "activitySubtitle": f"Environment: {alert_data['target']} | Success Rate: {success_rate:.1f}%",
                    "facts": [
                        {"name": "Total Tests", "value": str(alert_data['total_tests'])},
                        {"name": "Passed", "value": str(alert_data['passed_tests'])},
                        {"name": "Failed", "value": str(alert_data['failed_tests'])},
                        {"name": "Critical Failures", "value": str(alert_data['critical_failures'])},
                        {"name": "High Failures", "value": str(alert_data['high_failures'])},
                        {"name": "Medium Failures", "value": str(alert_data['medium_failures'])},
                        {"name": "Execution Duration", "value": f"{alert_data['execution_duration']}s"},
                        {"name": "Run ID", "value": alert_data['run_id']}
                    ],
                    "markdown": True
                }
            ]
        }
    
    def test_alert_channels(self) -> Dict[str, bool]:
        """Test all configured alert channels"""
        
        test_results = {}
        
        test_alert_data = {
            'alert_type': 'test',
            'severity': 'medium',
            'model': 'test_model',
            'test': 'test_connection',
            'message': 'This is a test alert from 2QC+ framework',
            'timestamp': datetime.now().isoformat(),
            'run_id': 'test_run_12345',
            'target': 'test',
            'total_tests': 10,
            'passed_tests': 8,
            'failed_tests': 2,
            'critical_failures': 0,
            'high_failures': 1,
            'medium_failures': 1,
            'execution_duration': 15,
            'model_count': 3
        }
        
        # Test email
        if 'email' in self.enabled_channels:
            try:
                self._send_email_alert(test_alert_data, individual=False)
                test_results['email'] = True
            except Exception as e:
                logging.error(f"Email test failed: {str(e)}")
                test_results['email'] = False
        
        # Test Slack
        if 'slack' in self.enabled_channels:
            try:
                self._send_slack_alert(test_alert_data, individual=False)
                test_results['slack'] = True
            except Exception as e:
                logging.error(f"Slack test failed: {str(e)}")
                test_results['slack'] = False
        
        # Test Teams
        if 'teams' in self.enabled_channels:
            try:
                self._send_teams_alert(test_alert_data, individual=False)
                test_results['teams'] = True
            except Exception as e:
                logging.error(f"Teams test failed: {str(e)}")
                test_results['teams'] = False
        
        return test_results
