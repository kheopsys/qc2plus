"""
2QC+ Level 2 Correlation Analysis
ML-powered correlation anomaly detection
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from scipy.stats import pearsonr, spearmanr
from sklearn.preprocessing import StandardScaler
import warnings

from qc2plus.core.connection import ConnectionManager


class CorrelationAnalyzer:
    """Analyzes correlations between variables and detects anomalies"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.scaler = StandardScaler()
    
    def analyze(self, model_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform correlation analysis"""
        
        try:
            # Extract configuration
            variables = config.get('variables', [])
            expected_correlation = config.get('expected_correlation')
            threshold = config.get('threshold', 0.2)
            correlation_type = config.get('correlation_type', 'pearson')
            date_column = config.get('date_column', 'created_at')
            window_days = config.get('window_days', 30)
            
            # Validate configuration
            if len(variables) < 2:
                raise ValueError("At least 2 variables required for correlation analysis")
            
            # Get data
            data = self._get_correlation_data(model_name, variables, date_column, window_days)
            
            if data.empty:
                return {
                    'passed': True,
                    'anomalies_count': 0,
                    'message': 'No data available for correlation analysis',
                    'details': {}
                }
            
            # Perform correlation analysis
            results = self._perform_correlation_analysis(
                data, variables, expected_correlation, threshold, correlation_type
            )
            
            # Detect temporal correlation changes
            temporal_results = self._detect_temporal_correlation_changes(
                model_name, variables, date_column, correlation_type
            )
            
            # Combine results
            anomalies_detected = not results['passed'] or not temporal_results['passed']
            total_anomalies = results.get('anomalies_count', 0) + temporal_results.get('anomalies_count', 0)
            
            return {
                'passed': not anomalies_detected,
                'anomalies_count': total_anomalies,
                'message': self._generate_summary_message(results, temporal_results),
                'details': {
                    'static_correlation': results,
                    'temporal_correlation': temporal_results,
                    'variables_analyzed': variables,
                    'data_points': len(data)
                }
            }
            
        except Exception as e:
            logging.error(f"Correlation analysis failed for {model_name}: {str(e)}")
            return {
                'passed': False,
                'error': str(e),
                'anomalies_count': 1,
                'message': f'Correlation analysis failed: {str(e)}'
            }
    
    def _get_correlation_data(self, model_name: str, variables: List[str], 
                            date_column: str, window_days: int) -> pd.DataFrame:
        """Get data for correlation analysis"""
        
        schema = self.connection_manager.config.get('schema', 'public')
        
        # Build query to get aggregated daily data
        query = f"""
            SELECT 
                DATE({date_column}) as analysis_date,
                {', '.join([f'SUM({var}) as {var}' for var in variables])}
            FROM {schema}.{model_name}
            WHERE {date_column} >= CURRENT_DATE - INTERVAL '{window_days} days'
            GROUP BY DATE({date_column})
            ORDER BY analysis_date
        """
        
        # Adapt query for different databases
        if self.connection_manager.db_type == 'bigquery':
            query = query.replace('CURRENT_DATE', 'CURRENT_DATE()')
            query = query.replace("INTERVAL '", "INTERVAL ")
            query = query.replace(" days'", " DAY")
        elif self.connection_manager.db_type == 'snowflake':
            query = query.replace('CURRENT_DATE', 'CURRENT_DATE()')
            query = query.replace(" days'", " DAY'")
        
        return self.connection_manager.execute_query(query)
    
    def _perform_correlation_analysis(self, data: pd.DataFrame, variables: List[str],
                                    expected_correlation: Optional[float], threshold: float,
                                    correlation_type: str) -> Dict[str, Any]:
        """Perform static correlation analysis"""
        
        results = {
            'passed': True,
            'anomalies_count': 0,
            'correlations': {},
            'anomalies': []
        }
        
        # Calculate correlations for all variable pairs
        for i in range(len(variables)):
            for j in range(i + 1, len(variables)):
                var1, var2 = variables[i], variables[j]
                
                if var1 not in data.columns or var2 not in data.columns:
                    continue
                
                # Remove rows with NaN values
                clean_data = data[[var1, var2]].dropna()
                
                if len(clean_data) < 3:
                    continue
                
                # Calculate correlation
                try:
                    if correlation_type == 'pearson':
                        corr_coef, p_value = pearsonr(clean_data[var1], clean_data[var2])
                    elif correlation_type == 'spearman':
                        corr_coef, p_value = spearmanr(clean_data[var1], clean_data[var2])
                    else:
                        corr_coef = np.corrcoef(clean_data[var1], clean_data[var2])[0, 1]
                        p_value = None
                
                except Exception as e:
                    logging.warning(f"Failed to calculate correlation for {var1} vs {var2}: {str(e)}")
                    continue
                
                pair_name = f"{var1}_vs_{var2}"
                results['correlations'][pair_name] = {
                    'correlation': corr_coef,
                    'p_value': p_value,
                    'sample_size': len(clean_data)
                }
                
                # Check for anomalies
                anomaly_detected = False
                anomaly_reason = ""
                
                if expected_correlation is not None:
                    # Check if correlation deviates from expected
                    deviation = abs(corr_coef - expected_correlation)
                    if deviation > threshold:
                        anomaly_detected = True
                        anomaly_reason = f"Correlation {corr_coef:.3f} deviates from expected {expected_correlation:.3f} by {deviation:.3f}"
                
                # Check for very weak correlations when strong correlation expected
                if expected_correlation and abs(expected_correlation) > 0.5 and abs(corr_coef) < 0.3:
                    anomaly_detected = True
                    anomaly_reason = f"Unexpectedly weak correlation {corr_coef:.3f} (expected {expected_correlation:.3f})"
                
                # Check for very strong unexpected correlations
                if not expected_correlation and abs(corr_coef) > 0.9:
                    anomaly_detected = True
                    anomaly_reason = f"Unexpectedly strong correlation {corr_coef:.3f}"
                
                if anomaly_detected:
                    results['passed'] = False
                    results['anomalies_count'] += 1
                    results['anomalies'].append({
                        'variable_pair': pair_name,
                        'correlation': corr_coef,
                        'expected_correlation': expected_correlation,
                        'reason': anomaly_reason,
                        'severity': 'medium'
                    })
        
        return
