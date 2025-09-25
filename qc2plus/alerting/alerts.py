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
                        'total_rows': test_result.get('total_rows', 0),
                        'explanation': test_result.get('explanation', ''), 
                        'examples': test_result.get('examples', []),      
                        'query': test_result.get('query', '')               
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
                        print(f"DEBUG: Level 2 anomaly - analyzer: {analyzer_name}, severity: {self._determine_level2_severity(analyzer_result, anomalies_count)}")

                        failure_info = {
                            'model': model_name,
                            'test': analyzer_name,
                            'type': 'level2',
                            'severity': "medium",  # Temporarily set to medium for testing
                            #self._determine_level2_severity(analyzer_result, anomalies_count),  # Level 2 anomalies are typically medium severity
                            'message': analyzer_result.get('message', ''),
                            'anomalies_count': anomalies_count,  

                            # AJOUTEZ CES LIGNES :
                            'failed_rows': anomalies_count,
                            'total_rows': 1,    # Level 2 tests are typically binary pass/fail  
                            'explanation': self._get_level2_explanation(analyzer_name, analyzer_result),
                            'examples': self._extract_level2_examples(analyzer_result),
                            'query': '',  # Level 2 doesn't use SQL queries
                            'anomalies_count': anomalies_count
                        }

                        severity = failure_info['severity']
                        if severity == 'critical':
                            critical_failures.append(failure_info)
                        elif severity == 'high':
                            high_failures.append(failure_info)
                        else:
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
                'severity': failure['severity'],
                'model': failure['model'],
                'test': failure['test'],
                'message': failure['message'],
                'timestamp': datetime.now().isoformat(),
                'run_id': results.get('run_id', ''),   
                'target': results.get('target', ''),
               #'failed_rows': failure['failed_rows'],
                #'total_rows': failure.get('total_rows', 0),
                'explanation': failure.get('explanation', 'No explication available'),
                'examples': failure.get('examples', []),
                'query': failure.get('query', ''),
                'failed_rows': failure.get('failed_rows', 0),
                'total_rows': failure.get('total_rows', 0),
                'test_type': failure.get('type', '')
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
        failure_details = self._collect_failure_details(alert_info, results)
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
            'model_count': len(results.get('models', {})),
            'failure_details': failure_details    # AJOUTÉ
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
        
        html = '''
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="background-color: #ff4444; color: white; padding: 15px; border-radius: 5px;">
                <h2>CRITICAL QUALITY TEST FAILURE</h2>
            </div>
            
            <div style="margin: 20px 0;">
                <h3>Test Details</h3>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Model:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Test:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Environment:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{}</td></tr>
                    <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Time:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{}</td></tr>
                </table>
            </div>
            
            <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px;">
                <h4>Error Message</h4>
                <p style="font-family: monospace; background-color: white; padding: 10px; border-left: 4px solid #ff4444;">
                    {}
                </p>
            </div>
            
            <div style="margin: 20px 0;">
                <p><strong>Run ID:</strong> {}</p>
                <p><em>This is an automated alert from 2QC Plus Data Quality Framework</em></p>
            </div>
        </body>
        </html>
        '''
        
        return html.format(
            alert_data['model'],
            alert_data['test'], 
            alert_data['target'],
            alert_data['timestamp'],
            alert_data['message'],
            alert_data['run_id']
        )
    
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
                <h2>2QC+ Quality Report Summary</h2>
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
                <p><em>This is an automated report from 2QC Plus Data Quality Framework</em></p>
            </div>
        </body>
        </html>
        """
    
    def _create_slack_individual_payload(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
            """Create Slack payload for individual alert"""
            test_type_display = "Level 1" if alert_data.get('test_type') == 'level1' else "Level 2"

            fields = [
                {"title": "Model", "value": alert_data['model'], "short": True},
                {"title": "Test", "value": alert_data['test'], "short": True},
                {"title": "Environment", "value": alert_data['target'], "short": True},
                {"title": "Test Type", "value": test_type_display, "short": True},
                {"title": "Failed/Total", "value": f"{alert_data.get('failed_rows', 0)}/{alert_data.get('total_rows', 0)}", "short": True},
                {"title": "Run ID", "value": alert_data['run_id'], "short": True},
                {"title": "Error", "value": alert_data['message'], "short": False}
            ]
            
            if alert_data.get('explanation'):
                fields.append({"title": "Test Definition", "value": alert_data['explanation'], "short": False})
            
            if alert_data.get('examples'):
                examples_text = "\n".join([f"• {ex}" for ex in alert_data['examples'][:3]])
                fields.append({"title": "Fail cause", "value": examples_text, "short": False})
            
            if alert_data.get('query') and alert_data.get('test_type') == 'level1':
                query_text = alert_data['query'][:500] + ("..." if len(alert_data['query']) > 500 else "")
                fields.append({"title": "Query", "value": f"```sql\n{query_text}\n```", "short": False})
            severity_text = alert_data['severity'].upper()
            emoji_map = {'critical': '🚨', 'high': '⚠️', 'medium': '📊'}
            emoji = emoji_map.get(alert_data['severity'], '⚠️')
            return {
                "text": f"{emoji} {severity_text}: 2QC+ Test Failure ON MODEL {alert_data['model'].upper()}", 
                "attachments": [
                    {
                        "color": "danger",
                        "fields": fields,
                        "footer": "2QC Plus Data Quality Framework",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
    
    def _create_slack_summary_payload(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Slack payload for summary alert"""
        emoji_map = {
        'critical': '🚨',
        'high': '⚠️', 
        'medium': '📊',
        'low': '✅'
        }
        
        color_map = {'critical': 'danger', 'high': 'warning', 'medium': 'good'}
        color = color_map.get(alert_data['severity'], 'good')
        
        success_rate = (alert_data['passed_tests'] / max(alert_data['total_tests'], 1)) * 100


        fields = [
        {"title": "📊 Total Tests", "value": str(alert_data['total_tests']), "short": True},
        {"title": "✅ Success Rate", "value": f"{success_rate:.1f}%", "short": True},
        {"title": "🚨 Critical", "value": str(alert_data['critical_failures']), "short": True},
        {"title": "⚠️ High", "value": str(alert_data['high_failures']), "short": True},
        {"title": "📋 Medium", "value": str(alert_data['medium_failures']), "short": True},
        {"title": "⏱️ Duration", "value": f"{alert_data['execution_duration']}", "short": True},
        {"title": "🔍 Run ID", "value": alert_data['run_id'], "short": False}
    ]

        failure_details = alert_data.get('failure_details', {})
        level1_failures = failure_details.get('level1_failures', [])
        level2_anomalies = failure_details.get('level2_anomalies', [])
        #        level2_details = alert_data.get('level2_details', {})
        #level2_anomalies = level2_details.get('anomalies', [])
        
        if level1_failures:
            failures_summary = []
            for failure in level1_failures[:3]:
                summary_line = f"• **{failure['model']}.{failure['test']}**: {failure['failed_rows']}/{failure['total_rows']} failed"
                failures_summary.append(summary_line)
            fields.append({
                "title": "Level 1 Failed Tests", 
                "value": "\n".join(failures_summary),
                "short": False
            })
            for failure in level1_failures[:2]:  # Limite à 2 au lieu de 3
                details = f"**Issue**: {failure['message']}\n"
                if failure.get('explanation'):
                    details += f"**Rule**: {failure['explanation'][:80]}...\n"
                if failure.get('examples') and len(failure['examples']) > 0:
                    example = str(failure['examples'][0]).replace("'", "").replace("{", "").replace("}", "")
                    details += f"**Example**: {example[:70]}..."
                
                fields.append({
                    "title": f"Details: {failure['model']}.{failure['test']}",
                    "value": details,
                    "short": True  # Côte à côte pour économiser l'espace
                })
            """
            for failure in level1_failures[:3]:  # Limit to 3
                failure_text = f"**{failure['model']}.{failure['test']}** ({failure['level']} - {failure['severity']})\n"
                failure_text += f"• {failure['message']}\n"
                failure_text += f"• Failed: {failure['failed_rows']}/{failure['total_rows']} rows\n"
                
                if failure.get('explanation'):
                    failure_text += f"• {failure['explanation'][:100]}...\n"
                
                if failure.get('examples'):
                    failure_text += "• Examples:\n"
                    for example in failure['examples']:
                        example_str = str(example).replace("'", "").replace("{", "").replace("}", "")
                        failure_text += f"  - {example_str[:60]}...\n"
                    
                fields.append({
                    "title": "Test Failure Details",
                    "value": failure_text,
                    "short": False
                })
        """
        
        # Add Level 2 anomalies
        if level2_anomalies:
            fields.append({
                "title": "🤖 Level 2 Anomalies", 
                "value": f"**{failure_details.get('total_anomalies', 0)} anomalies** detected across {len(level2_anomalies)} analyzer(s)",

                #"value": f"Total anomalies detected: {failure_details.get('total_anomalies', 0)}", 
                "short": False
            })
            
            # Add details for each Level 2 analyzer
            """
            for anomaly in level2_anomalies[:3]:  # Limit to 3 to avoid message too long
                level_display = "Level 2"
                analyzer_text = f"**{anomaly['model']}.{anomaly['analyzer']}** ({level_display} - {anomaly['severity']})\n"
                analyzer_text += f"• {anomaly['message']}\n"
                
                if anomaly.get('explanation'):
                    analyzer_text += f"• Explanation: {anomaly['explanation'][:100]}...\n"
                
                if anomaly.get('examples'):
                    analyzer_text += "• Examples:\n"
                    for example in anomaly['examples']:
                        example_str = str(example).replace("'", "").replace("{", "").replace("}", "")
                        analyzer_text += f"  - {example_str[:60]}...\n"
                
                fields.append({
                    "title": "Anomaly Details",
                    "value": analyzer_text,
                    "short": False
                })
                """
            for anomaly in level2_anomalies[:2]:  # Limite à 2
                details = f"**Type**: {anomaly['analyzer']} analysis\n"
                details += f"**Finding**: {anomaly['message']}\n"
                if anomaly.get('examples') and len(anomaly['examples']) > 0:
                    details += f"**Key Example**: {str(anomaly['examples'][0])[:60]}..."
                
                fields.append({
                    "title": f"🎯 {anomaly['model']} Anomaly",
                    "value": details,
                    "short": True
                })
        
        return {
            #"text": f"2QC+ Quality Report - {alert_data['target']}",
            "text": f"📈 2QC+ Quality Report - {alert_data['target']} Environment",
            "attachments": [
                {
                    "color": color,
                    "fields": fields,
                    "footer": "2QC Plus Data Quality Framework",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        
        """
        return {
            "text": f"2QC+ Quality Report - {alert_data['target']}",
            "attachments": [
                {
                    "color": color,
                    "fields": [
                        {"title": "Total Tests", "value": str(alert_data['total_tests']), "short": True},
                        {"title": "Success Rate", "value": f"{success_rate:.1f}%", "short": True},
                        {"title": "Critical Failures", "value": str(alert_data['critical_failures']), "short": True},
                        {"title": "Medium Failures", "value": str(alert_data['medium_failures']), "short": True}, 
                        {"title": "High Failures", "value": str(alert_data['high_failures']), "short": True},
                        {"title": "Execution Time", "value": f"{alert_data['execution_duration']}s", "short": True},
                        {"title": "Run ID", "value": alert_data['run_id'], "short": False}
                    ],
                    "footer": "2QC Plus Data Quality Framework",
                    "ts": int(datetime.now().timestamp())
                }
            ]
        }
        """
    def _create_teams_individual_payload(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Microsoft Teams payload for individual alert"""

        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000",
            "summary": "🚨 Critical 2QC+ Test Failure",
            "sections": [
                {
                    "activityTitle": " 🚨 CRITICAL: 2QC+ Test Failure",
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
                    "activityTitle": "2QC+ Quality Report Summary",
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
            'message': 'This is a test alert from 2QC Plus framework',
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



    # Level2 anomalies alerts are typically medium severity

    # Ajoutez ces méthodes à votre classe AlertManager

    def _determine_level2_severity(self, analyzer_result: Dict[str, Any], anomalies_count: int) -> str:
        """Determine severity for Level 2 anomalies based on count and type"""
        
        details = analyzer_result.get('details', {})
        
        # Check for high severity anomalies in the details
        high_severity_indicators = []
        
        # Static correlation anomalies
        static_anomalies = details.get('static_correlation', {}).get('anomalies', [])
        for anomaly in static_anomalies:
            if anomaly.get('severity') == 'high':
                high_severity_indicators.append('high_correlation_deviation')
        
        # Temporal correlation anomalies
        temporal_anomalies = details.get('temporal_correlation', {}).get('anomalies', [])
        for anomaly in temporal_anomalies:
            if anomaly.get('severity') == 'high' or anomaly.get('anomaly_type') == 'sudden_change':
                high_severity_indicators.append('sudden_correlation_change')
            if anomaly.get('anomaly_type') == 'correlation_degradation':
                high_severity_indicators.append('correlation_degradation')
        
        # Determine severity based on indicators and count
        if len(high_severity_indicators) >= 2 or anomalies_count >= 10:
            return 'critical'
        elif len(high_severity_indicators) >= 1 or anomalies_count >= 3:
            return 'high'
        elif anomalies_count >= 1:
            return 'medium'
        else:
            return 'low'

    def _get_level2_explanation(self, analyzer_name: str, analyzer_result: Dict[str, Any]) -> str:
        """Generate human-readable explanation for Level 2 anomalies"""
        
        details = analyzer_result.get('details', {})
        
        # Detailed explanations based on analyzer type and results
        if analyzer_name == 'correlation':
            return self._get_correlation_explanation(details)
        
        explanations = {
            'temporal': "Identifies temporal anomalies in data patterns over time. This includes unusual spikes, drops, or trend changes that deviate from expected behavior.",
            'distribution': "Analyzes distribution changes in data segments compared to historical distributions. Significant shifts may indicate data collection issues or business changes.",
            'drift': "Monitors data drift by comparing current data characteristics with baseline patterns. High drift scores indicate potential data quality degradation.",
            'outliers': "Identifies statistical outliers that fall outside normal data ranges. These may represent data entry errors or legitimate exceptional cases.",
            'completeness': "Monitors data completeness patterns over time. Sudden changes in null rates or missing data patterns may indicate upstream issues.",
            'consistency': "Checks for consistency violations in data relationships and business rules. Inconsistencies may indicate process breakdowns or data integration issues."
        }
        
        base_explanation = explanations.get(analyzer_name, f"Level 2 anomaly analysis of type '{analyzer_name}' detected unusual patterns in the data.")
        
        # Add specific context if available
        anomalies_count = analyzer_result.get('anomalies_count', 0)
        if anomalies_count > 0:
            base_explanation += f" {anomalies_count} anomalies were detected that require investigation."
        
        return base_explanation

    def _get_correlation_explanation(self, details: Dict[str, Any]) -> str:
        """Get detailed explanation for correlation anomalies"""
        
        static_count = len(details.get('static_correlation', {}).get('anomalies', []))
        temporal_count = len(details.get('temporal_correlation', {}).get('anomalies', []))
        variables_count = len(details.get('variables_analyzed', []))
        
        explanation = f"Correlation analysis of {variables_count} variables detected unusual patterns. "
        
        if static_count > 0:
            explanation += f"Found {static_count} static correlation anomalies (unexpected correlation strengths or deviations from expected patterns). "
        
        if temporal_count > 0:
            explanation += f"Found {temporal_count} temporal correlation anomalies (correlation changes over time, volatility, or degradation). "
        
        explanation += "These anomalies may indicate data quality issues, process changes, or underlying business shifts that require investigation."
        
        return explanation

    def _extract_level2_examples(self, analyzer_result: Dict[str, Any]) -> List[str]:
        """Extract examples from Level 2 anomaly results"""
        
        examples = []
        
        try:
            details = analyzer_result.get('details', {})
            
            # For correlation anomalies - Static correlation
            if 'static_correlation' in details:
                static_anomalies = details['static_correlation'].get('anomalies', [])
                for anomaly in static_anomalies[:3]:  # Limit to 3 examples
                    var_pair = anomaly.get('variable_pair', 'Unknown variables')
                    correlation = anomaly.get('correlation', 0)
                    expected = anomaly.get('expected_correlation', 'N/A')
                    reason = anomaly.get('reason', 'Unknown reason')
                    examples.append(f"{var_pair}: {correlation:.3f} (expected: {expected}) - {reason}")
            
            # For correlation anomalies - Temporal correlation
            if 'temporal_correlation' in details:
                temporal_anomalies = details['temporal_correlation'].get('anomalies', [])
                for anomaly in temporal_anomalies[:3]:  # Limit to 3 examples
                    var_pair = anomaly.get('variable_pair', 'Unknown variables')
                    anomaly_type = anomaly.get('anomaly_type', 'unknown')
                    reason = anomaly.get('reason', 'Unknown reason')
                    
                    if anomaly_type == 'sudden_change':
                        change = anomaly.get('recent_change', 0)
                        examples.append(f"{var_pair}: Sudden change of {change:.3f}")
                    elif anomaly_type == 'high_volatility':
                        std = anomaly.get('correlation_std', 0)
                        examples.append(f"{var_pair}: High volatility (std: {std:.3f})")
                    elif anomaly_type == 'correlation_degradation':
                        degradation = anomaly.get('degradation', 0)
                        examples.append(f"{var_pair}: Degradation of {degradation:.3f}")
                    else:
                        examples.append(f"{var_pair}: {reason}")
            
            # For temporal analysis (general)
            elif 'individual_analyses' in details:
                individual = details['individual_analyses']
                for metric, results in list(individual.items())[:3]:  # Limit to 3 metrics
                    anomalies = results.get('anomalies', [])
                    if anomalies:
                        anomaly = anomalies[0]  # Take first anomaly for this metric
                        z_score = anomaly.get('z_score', anomaly.get('magnitude', 0))
                        anomaly_type = anomaly.get('type', 'anomaly')
                        examples.append(f"{metric}: {anomaly_type} (z-score: {z_score:.2f})")
            
            # For distribution anomalies
            elif 'cross_segment_analysis' in details:
                cross_segment = details['cross_segment_analysis']
                anomalies = cross_segment.get('anomalies', [])
                for anomaly in anomalies[:3]:  # Limit to 3 examples
                    segment = anomaly.get('segment', 'Unknown segment')
                    segment_value = anomaly.get('segment_value', '')
                    change = anomaly.get('concentration_change', 0)
                    examples.append(f"{segment} ({segment_value}): concentration change = {change:.3f}")
            
            # Generic fallback for any 'anomalies' list in details
            if not examples:
                for key, value in details.items():
                    if isinstance(value, dict) and 'anomalies' in value:
                        generic_anomalies = value['anomalies'][:3]
                        for i, anomaly in enumerate(generic_anomalies):
                            if isinstance(anomaly, dict):
                                score = anomaly.get('score', anomaly.get('magnitude', anomaly.get('correlation', i+1)))
                                var_pair = anomaly.get('variable_pair', anomaly.get('variable', f'Item {i+1}'))
                                examples.append(f"{var_pair}: score = {score}")
                            else:
                                examples.append(f"Anomaly {i+1}: {str(anomaly)[:50]}")
                        break
            
            # Final fallback
            if not examples:
                message = analyzer_result.get('message', '')
                if message:
                    examples = [message]
                else:
                    examples = ["No specific examples available"]
        
        except Exception as e:
            logging.warning(f"Could not extract Level 2 examples: {str(e)}")
            examples = [f"Unable to extract examples: {str(e)[:100]}"]
        
        return examples
    
    def _collect_failure_details(self, alert_info: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Collect failure details from both Level 1 and Level 2"""
        
        failure_details = {
            'level1_failures': [],
            'level2_anomalies': [],
            'total_anomalies': 0
        }
        print(f"DEBUG: critical_failures count: {len(alert_info['critical_failures'])}")
        print(f"DEBUG: high_failures count: {len(alert_info['high_failures'])}")
        print(f"DEBUG: medium_failures count: {len(alert_info['medium_failures'])}")
        # Collect from all severity levels
        all_failures = (
                    alert_info['high_failures'] + 
                    alert_info['medium_failures'])


        print(f"DEBUG: total all_failures count: {len(all_failures)}")
        
        for failure in all_failures:
            print(f"DEBUG: Processing failure - type: {failure.get('type')}, model: {failure.get('model')}")

            if failure.get('type') == 'level1':
                level1_info = {
                    'model': failure['model'],
                    'test': failure['test'],
                    'level': 'Level 1',
                    'severity': failure['severity'],
                    'message': failure['message'],
                    'explanation': failure.get('explanation', ''),
                    'examples': failure.get('examples', [])[:2],
                    'failed_rows': failure.get('failed_rows', 0),
                    'total_rows': failure.get('total_rows', 0)
                }
                failure_details['level1_failures'].append(level1_info)
                
            elif failure.get('type') == 'level2':
                level2_info = {
                    'model': failure['model'],
                    'analyzer': failure['test'],
                    'level': 'Level 2',
                    'severity': failure['severity'],
                    'message': failure['message'],
                    'explanation': failure.get('explanation', ''),
                    'examples': failure.get('examples', [])[:2],
                    'anomalies_count': failure.get('anomalies_count', 0)
                }
                failure_details['level2_anomalies'].append(level2_info)
                failure_details['total_anomalies'] += failure.get('anomalies_count', 0)


        
        return failure_details
