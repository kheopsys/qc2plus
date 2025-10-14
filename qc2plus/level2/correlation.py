"""
2QC+ Level 2 Correlation Analysis
ML-powered correlation anomaly detection
"""

from qc2plus.sql.db_functions import DB_LEVEL2_FUNCTIONS

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
            date_column = config.get('date_column', None)
            window_days = config.get('window_days', None)  # for temporal correlation analysis
            sample_size = config.get('sample_size', 10000) #  used for calculating correlation with no time windows
            warnings.filterwarnings("ignore", category=RuntimeWarning)  # Suppress warnings from correlation calculations
            # Validate configuration
            if len(variables) < 2:
                raise ValueError("At least 2 variables required for correlation analysis")
            
            # Get data
            data = self._get_correlation_data(model_name, variables, date_column, window_days, sample_size)
            
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

            # Detect temporal correlation changes (seulement si date_column existe)
            temporal_results = {'passed': True, 'anomalies_count': 0, 'anomalies': []}
            if date_column:
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
                            date_column: str, window_days: int, sample_size: int) -> pd.DataFrame:
        """Get data for correlation analysis"""
        
        schema = self.connection_manager.config.get('schema', 'public')
        db_type = self.connection_manager.db_type
        funcs = DB_LEVEL2_FUNCTIONS.get(db_type, DB_LEVEL2_FUNCTIONS['postgresql'])
        
        # Build query to get aggregated daily data

        if date_column and window_days:
            current_date_expr = funcs['current_date']()
            #weekly aggregation query
            query = f"""
            SELECT 
                {funcs['date_trunc_week'](date_column)} AS analysis_date,
                {', '.join([f'SUM({var}) AS {var}' for var in variables])}
            FROM {schema}.{model_name}
            WHERE CAST({date_column} AS DATE) >= {funcs['date_sub'](current_date_expr, window_days)}
              AND {' AND '.join([f'{var} IS NOT NULL' for var in variables])}
            GROUP BY {funcs['date_trunc_week'](date_column)}
            ORDER BY analysis_date
            """
            
        else:
            # Simple random sample query
            query = f"""
                SELECT 
                    {', '.join(variables)}
                FROM {schema}.{model_name}
                WHERE {' AND '.join([f'{var} IS NOT NULL' for var in variables])}
                LIMIT {sample_size}
            """
            
            if db_type in ('postgresql', 'redshift', 'snowflake', 'sqlite'):
                query = query.replace('LIMIT', 'ORDER BY RANDOM() LIMIT')
            elif db_type in ('mysql', 'bigquery'):
                query = query.replace('LIMIT', 'ORDER BY RAND() LIMIT')


        
        return self.connection_manager.execute_query(query)
    
    def _perform_correlation_analysis(self, data: pd.DataFrame, variables: List[str],
                                    expected_correlation: Optional[float], threshold: float,
                                    correlation_type: str) -> Dict[str, Any]:
        """Perform static correlation analysis"""
        # Vérification préalable : toutes les variables doivent être numériques
        non_numeric_vars = [
            var for var in variables 
            if var in data.columns and not pd.api.types.is_numeric_dtype(data[var])
        ]

        if non_numeric_vars:
            raise ValueError(
                f"Non-numeric variables detected: {', '.join(non_numeric_vars)}. "
                f"Correlation analysis requires only numeric variables. "
                f"Please exclude or cast them before running the test."
            )

        results = {
            'passed': True,
            'anomalies_count': 0,
            'correlations': {},
            'anomalies': []
        }
        # Coerce columns to numeric globally (safety net)
        for c in variables:
            if c in data.columns:
                data[c] = pd.to_numeric(data[c], errors='coerce')

        
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
                    'correlation': float(corr_coef),
                    'p_value': p_value,
                    'sample_size': int(len(clean_data))
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
                if not expected_correlation and abs(corr_coef) > 0.7:
                    anomaly_detected = True
                    anomaly_reason = f"Unexpectedly strong correlation {corr_coef:.3f}"
                
                if anomaly_detected:
                    results['passed'] = False
                    results['anomalies_count'] += 1
                    results['anomalies'].append({
                        'variable_pair': pair_name,
                        'correlation': float(corr_coef),
                        'expected_correlation': expected_correlation,
                        'reason': anomaly_reason,
                        'severity': 'medium'
                    })
        
        return results

    def _detect_temporal_correlation_changes(self, model_name: str, variables: List[str],
                                           date_column: str, correlation_type: str) -> Dict[str, Any]:
        """Detect changes in correlation over time"""

        results = {
            'passed': True,
            'anomalies_count': 0,
            'temporal_trends': {},
            'anomalies': []
        }
        
        try:
            # Get historical correlation data (weekly windows over last 3 months)
            schema = self.connection_manager.config.get('schema', 'public')
            db_type = self.connection_manager.db_type
            funcs = DB_LEVEL2_FUNCTIONS.get(db_type, DB_LEVEL2_FUNCTIONS['postgresql'])
            
            query = f"""
                WITH weekly_data AS (
                    SELECT 
                        {funcs['date_trunc_week'](date_column)} AS week_start,
                        {', '.join([f'SUM({var}) AS {var}' for var in variables])}
                    FROM {schema}.{model_name}
                    WHERE CAST({date_column} AS DATE) >= {funcs['date_sub'](funcs['current_date'](), 90)}
                    GROUP BY {funcs['date_trunc_week'](date_column)}
                    ORDER BY week_start
                )
                SELECT * FROM weekly_data
                WHERE week_start IS NOT NULL
            """
            
    
            historical_data = self.connection_manager.execute_query(query)
            
            if len(historical_data) < 4:  # Need at least 4 weeks for trend analysis
                return results
            
            # Calculate rolling correlations
            for i in range(len(variables)):
                for j in range(i + 1, len(variables)):
                    var1, var2 = variables[i], variables[j]
                    
                    if var1 not in historical_data.columns or var2 not in historical_data.columns:
                        continue
                    
                    # Calculate correlation for each time window
                    correlations = []
                    dates = []
                    
                    for idx in range(len(historical_data) - 2):  # Use 3-week rolling window
                        window_data = historical_data.iloc[idx:idx+3]
                        clean_window = window_data[[var1, var2]].dropna()
                        
                        if len(clean_window) >= 2:
                            try:
                                if correlation_type == 'pearson':
                                    corr, _ = pearsonr(clean_window[var1], clean_window[var2])
                                elif correlation_type == 'spearman':
                                    corr, _ = spearmanr(clean_window[var1], clean_window[var2])
                                else:
                                    corr = np.corrcoef(clean_window[var1], clean_window[var2])[0, 1]
                                
                                if not np.isnan(corr):
                                    correlations.append(corr)
                                    dates.append(historical_data.iloc[idx+2]['week_start'])
                            except:
                                continue
                    
                    if len(correlations) >= 3:
                        pair_name = f"{var1}_vs_{var2}"
                        
                        # Detect trends and anomalies
                        correlation_std = np.std(correlations)
                        correlation_mean = np.mean(correlations)
                        recent_corr = correlations[-1]
                        
                        results['temporal_trends'][pair_name] = {
                            'correlations': correlations,
                            'dates': [str(d) for d in dates],
                            'mean_correlation': float(correlation_mean),
                            'std_correlation': float(correlation_std),
                            'recent_correlation': float(recent_corr)
                        }
                        
                        # Check for anomalies
                        # 1. High volatility in correlation
                        if correlation_std > 0.3:
                            results['passed'] = False
                            results['anomalies_count'] += 1
                            results['anomalies'].append({
                                'variable_pair': pair_name,
                                'anomaly_type': 'high_volatility',
                                'correlation_std': correlation_std,
                                'reason': f"High correlation volatility (std: {correlation_std:.3f})",
                                'severity': 'medium'
                            })
                        
                        # 2. Significant recent change
                        if len(correlations) >= 2:
                            recent_change = abs(correlations[-1] - correlations[-2])
                            if recent_change > 0.4:
                                results['passed'] = False
                                results['anomalies_count'] += 1
                                results['anomalies'].append({
                                    'variable_pair': pair_name,
                                    'anomaly_type': 'sudden_change',
                                    'recent_change': recent_change,
                                    'reason': f"Sudden correlation change: {recent_change:.3f}",
                                    'severity': 'high'
                                })
                        
                        # 3. Correlation degradation
                        if len(correlations) >= 4:
                            early_corr = np.mean(correlations[:2])
                            late_corr = np.mean(correlations[-2:])
                            degradation = early_corr - late_corr
                            
                            if (abs(early_corr) > 0.5 or abs(late_corr) > 0.5) and abs(degradation) > 0.3:
                                results['passed'] = False
                                results['anomalies_count'] += 1
                                results['anomalies'].append({
                                    'variable_pair': pair_name,
                                    'anomaly_type': 'correlation_degradation',
                                    'degradation': degradation,
                                    'early_correlation': early_corr,
                                    'recent_correlation': late_corr,
                                    'reason': f"Correlation degradation: {degradation:.3f}",
                                    'severity': 'high'
                                })
        
        except Exception as e:
            logging.warning(f"Temporal correlation analysis failed: {str(e)}")
            # Don't fail the entire analysis for temporal issues
            
        return results

    def _generate_summary_message(self, static_results: Dict[str, Any], 
                                temporal_results: Dict[str, Any]) -> str:
        """Generate summary message for correlation analysis"""
        
        messages = []
        
        if not static_results['passed']:
            messages.append(f"Static correlation anomalies: {static_results['anomalies_count']}")
        
        if not temporal_results['passed']:
            messages.append(f"Temporal correlation anomalies: {temporal_results['anomalies_count']}")
        
        if not messages:
            return "All correlation checks passed"
        
        return "; ".join(messages)
