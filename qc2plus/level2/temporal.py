"""
2QC+ Level 2 Temporal Analysis
ML-powered temporal pattern and seasonality anomaly detection
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from scipy import stats
from scipy.signal import find_peaks
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
import warnings

from qc2plus.core.connection import ConnectionManager


DB_LEVEL2_FUNCTIONS = {
    'postgresql': {
        'current_date': lambda: "CURRENT_DATE",
        'date_sub': lambda date_col, days: f"{date_col} - INTERVAL '{days} days'",
        'date_trunc_day': lambda col: f"DATE_TRUNC('day', {col})",
        'date_trunc_week': lambda col: f"DATE_TRUNC('week', {col})",
        'date_trunc_month': lambda col: f"DATE_TRUNC('month', {col})",
        'cast_date': lambda col: f"CAST({col} AS DATE)",
    },
    'bigquery': {
        'current_date': lambda: "CURRENT_DATE()",
        'date_sub': lambda date_col, days: f"DATE_SUB({date_col}, INTERVAL {days} DAY)",
        'date_trunc_day': lambda col: f"DATE_TRUNC(CAST({col} AS DATE), DAY)",
        'date_trunc_week': lambda col: f"DATE_TRUNC(CAST({col} AS DATE), WEEK(MONDAY))",
        'date_trunc_month': lambda col: f"DATE_TRUNC(CAST({col} AS DATE), MONTH)",
        'cast_date': lambda col: f"CAST({col} AS DATE)",
    },

    'snowflake': {
        'current_date': lambda: "CURRENT_DATE()",
        'date_sub': lambda date_col, days: f"DATEADD(day, -{days}, {date_col})",
        'date_trunc_day': lambda col: f"DATE_TRUNC('DAY', {col})",
        'date_trunc_week': lambda col: f"DATE_TRUNC('WEEK', {col})",
        'date_trunc_month': lambda col: f"DATE_TRUNC('MONTH', {col})",
        'cast_date': lambda col: f"CAST({col} AS DATE)",
    },
}
class TemporalAnalyzer:
    """Analyzes temporal patterns and detects time-series anomalies"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        
    def analyze(self, model_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform temporal analysis"""
        
        try:
            # Extract configuration
            date_column = config.get('date_column', 'created_at')
            metrics = config.get('metrics', ['count'])
            seasonality_check = config.get('seasonality_check', True)
            trend_check = config.get('trend_check', True)
            anomaly_detection = config.get('anomaly_detection', True)
            window_days = config.get('window_days', 90)
            frequency = config.get('frequency', 'daily')  # daily, weekly, monthly
            
            # Get temporal data
            data = self._get_temporal_data(model_name, date_column, metrics, window_days, frequency)
        
            if data.empty or len(data) < 7:

                return {
                    'passed': True,
                    'anomalies_count': 0,
                    'message': f'Insufficient data for temporal analysis (need 7+ points, got {len(data)})',
                    'details': {}
                }
            
            # Run analyses
            results = {
                'passed': True,
                'anomalies_count': 0,
                'analyses': {}
            }
            
            for metric in metrics:
                if metric not in data.columns:
                    continue
                    
                metric_results = self._analyze_metric(
                    data, metric, seasonality_check, trend_check, anomaly_detection, frequency
                )
                results['analyses'][metric] = metric_results
                
                if not metric_results['passed']:
                    results['passed'] = False
                    results['anomalies_count'] += metric_results.get('anomalies_count', 0)
            
            return {
                'passed': results['passed'],
                'anomalies_count': results['anomalies_count'],
                'message': self._generate_summary_message(results),
                'details': {
                    'window_days': window_days,
                    'frequency': frequency,
                    'data_points': len(data),
                    'metrics_analyzed': metrics,
                    'individual_analyses': results['analyses']
                }
            }
            
        except Exception as e:
            logging.error(f"Temporal analysis failed for {model_name}: {str(e)}")
            return {
                'passed': False,
                'error': str(e),
                'anomalies_count': 1,
                'message': f'Temporal analysis failed: {str(e)}'
            }
    
    def _get_temporal_data(self, model_name: str, date_column: str, metrics: List[str],
                          window_days: int, frequency: str) -> pd.DataFrame:
        """Get temporal data aggregated by specified frequency"""
        
        schema = self.connection_manager.config.get('schema', 'public')
        db_type = self.connection_manager.db_type
        #funcs = DB_LEVEL2_FUNCTIONS.get(self.connection_manager.db_type, DB_LEVEL2_FUNCTIONS['postgresql'])
        
        if db_type in DB_LEVEL2_FUNCTIONS:
            funcs = DB_LEVEL2_FUNCTIONS[db_type]
        else:
            logging.warning(f"Unknown db_type '{db_type}', defaulting to PostgreSQL syntax")
            funcs = DB_LEVEL2_FUNCTIONS['postgresql']
        
        funcs = DB_LEVEL2_FUNCTIONS.get(db_type)
        
        if frequency == 'daily':
            interval_clause = funcs['date_trunc_day'](date_column)
        elif frequency == 'weekly':
            interval_clause = funcs['date_trunc_week'](date_column)
        elif frequency == 'monthly':
            interval_clause = funcs['date_trunc_month'](date_column)
        else:
            # Default to daily
            interval_clause = funcs['date_trunc_day'](date_column)
        
        # Build metric aggregations
        metric_clauses = []
        for metric in metrics:
            if metric == 'count':
                metric_clauses.append('COUNT(*) as count')
            elif metric.startswith('avg_'):
                column = metric.replace('avg_', '')
                metric_clauses.append(f'AVG({column}) as {metric}')
            elif metric.startswith('sum_'):
                column = metric.replace('sum_', '')
                metric_clauses.append(f'SUM({column}) as {metric}')
            elif metric.startswith('max_'):
                column = metric.replace('max_', '')
                metric_clauses.append(f'MAX({column}) as {metric}')
            elif metric.startswith('min_'):
                column = metric.replace('min_', '')
                metric_clauses.append(f'MIN({column}) as {metric}')
            else:
                # Assume it's a column name for sum
                metric_clauses.append(f'SUM({metric}) as {metric}')

        
        current_date_expr = funcs['current_date']()
        cast_date_col = funcs['cast_date'](date_column)

        query = f"""
            SELECT 
                {interval_clause} as period_date,
                {', '.join(metric_clauses)}
            FROM {schema}.{model_name}
            WHERE {cast_date_col} >= {funcs['date_sub'](current_date_expr, window_days)}
            GROUP BY {interval_clause}
            ORDER BY period_date
        """
        
        return self.connection_manager.execute_query(query)
    
    def _analyze_metric(self, data: pd.DataFrame, metric: str, seasonality_check: bool,
                       trend_check: bool, anomaly_detection: bool, frequency: str) -> Dict[str, Any]:
        """Analyze a single metric for temporal patterns"""
        results = {
            'passed': True,
            'anomalies_count': 0,
            'anomalies': []
        }        
        try:
            # Prepare time series
            ts_data = data.set_index('period_date')[metric].fillna(0)
            # Seasonality analysis
            if seasonality_check and len(ts_data) >= 14:
                seasonality_result = self._check_seasonality(ts_data, metric, frequency)
                results['seasonality'] = seasonality_result
                
                if not seasonality_result['passed']:
                    results['passed'] = False
                    results['anomalies_count'] += seasonality_result.get('anomalies_count', 0)
                    results['anomalies'].extend(seasonality_result.get('anomalies', []))
            
            # Trend analysis
            if trend_check:
                trend_result = self._check_trend_anomalies(ts_data, metric)
                results['trend'] = trend_result
                
                if not trend_result['passed']:
                    results['passed'] = False
                    results['anomalies_count'] += trend_result.get('anomalies_count', 0)
                    results['anomalies'].extend(trend_result.get('anomalies', []))
            
            # Point anomaly detection
            if anomaly_detection:
                anomaly_result = self._detect_point_anomalies(ts_data, metric)
                results['point_anomalies'] = anomaly_result
                
                if not anomaly_result['passed']:
                    results['passed'] = False
                    results['anomalies_count'] += anomaly_result.get('anomalies_count', 0)
                    results['anomalies'].extend(anomaly_result.get('anomalies', []))
            
            # Stationarity check
            stationarity_result = self._check_stationarity(ts_data, metric)
            results['stationarity'] = stationarity_result
            
        except Exception as e:
            logging.error(f"Error analyzing metric {metric}: {str(e)}")
            results['error'] = str(e)
            results['passed'] = False
        
        return results
    
    def _check_seasonality(self, ts_data: pd.Series, metric: str, frequency: str) -> Dict[str, Any]:
        """Check for seasonality anomalies"""
        
        results = {
            'passed': True,
            'anomalies_count': 0,
            'anomalies': []
        }
        
        try:
            # Perform seasonal decomposition
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                if frequency == 'daily':
                    period = 7   # Weekly seasonality (7 days)                        
                elif frequency == 'weekly': 
                    # Weekly data - look for monthly/quarterly patterns
                    if len(ts_data) >= 52:
                        period = 52   # Yearly seasonality (52 weeks)
                    elif len(ts_data) >= 12:
                        period = 4   # Monthly pattern
                    else:
                        return results 
                elif frequency == 'monthly':
                    # Monthly data - look for quarterly/yearly patterns
                    if len(ts_data) >= 12:
                        period = 12  # Yearly seasonality (12 months)
                    else:
                        return results
                else:
                    return results
                
                if len(ts_data) < 2 * period:
                    return results
                
                decomposition = seasonal_decompose(
                    ts_data, 
                    model='additive', 
                    period=period,
                    extrapolate_trend='freq'
                )
                
                seasonal_component = decomposition.seasonal
                residual_component = decomposition.residual
                
                # Check for unusual seasonal patterns
                seasonal_std = seasonal_component.std()
                seasonal_mean = seasonal_component.mean()
                
                # Detect seasonal anomalies
                seasonal_threshold = 2 * seasonal_std
                seasonal_anomalies = seasonal_component[
                    abs(seasonal_component - seasonal_mean) > seasonal_threshold
                ]
                
                if len(seasonal_anomalies) > 0:
                    results['passed'] = False
                    results['anomalies_count'] = len(seasonal_anomalies)
                    
                    for date, value in seasonal_anomalies.items():
                        results['anomalies'].append({
                            'type': 'seasonal_anomaly',
                            'date': str(date),
                            'metric': metric,
                            'seasonal_value': value,
                            'threshold': seasonal_threshold,
                            'severity': 'medium'
                        })
                
                # Store decomposition results
                results['seasonal_strength'] = seasonal_std / (ts_data.std() + 1e-8)
                results['period_detected'] = period
                
                # Check for missing seasonality where expected
                if results['seasonal_strength'] < 0.1 and len(ts_data) >= 21:
                    results['anomalies'].append({
                        'type': 'weak_seasonality',
                        'metric': metric,
                        'seasonal_strength': results['seasonal_strength'],
                        'message': 'Expected seasonality not detected',
                        'severity': 'low'
                    })
                    results['anomalies_count'] += 1
                    results['passed'] = False
                
        except Exception as e:
            logging.warning(f"Seasonality check failed for {metric}: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def _check_trend_anomalies(self, ts_data: pd.Series, metric: str) -> Dict[str, Any]:
        """Check for trend anomalies"""
        
        results = {
            'passed': True,
            'anomalies_count': 0,
            'anomalies': []
        }
        
        try:
            # Calculate rolling trend
            window = min(7, len(ts_data) // 3)
            if window < 2:
                return results
            
            # Calculate moving averages
            short_ma = ts_data.rolling(window=window).mean()
            long_ma = ts_data.rolling(window=window*2).mean()
            
            # Calculate trend slope using linear regression
            x = np.arange(len(ts_data))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, ts_data.values)
            
            results['trend_slope'] = slope
            results['trend_r_squared'] = r_value ** 2
            results['trend_p_value'] = p_value
            
            # Detect trend breaks
            trend_changes = self._detect_trend_breaks(ts_data)
            
            if len(trend_changes) > 0:
                # Check if trend changes are significant
                significant_changes = [
                    change for change in trend_changes 
                    if abs(change['magnitude']) > 2 * ts_data.std()
                ]
                
                if len(significant_changes) > 0:
                    results['passed'] = False
                    results['anomalies_count'] = len(significant_changes)
                    
                    for change in significant_changes:
                        results['anomalies'].append({
                            'type': 'trend_break',
                            'date': str(change['date']),
                            'metric': metric,
                            'magnitude': change['magnitude'],
                            'direction': 'increase' if change['magnitude'] > 0 else 'decrease',
                            'severity': 'high' if abs(change['magnitude']) > 3 * ts_data.std() else 'medium'
                        })
            
            # Check for excessive volatility
            volatility = ts_data.rolling(window=window).std().mean()
            if volatility > ts_data.mean():
                results['anomalies'].append({
                    'type': 'high_volatility',
                    'metric': metric,
                    'volatility': volatility,
                    'mean': ts_data.mean(),
                    'message': 'High volatility detected in time series',
                    'severity': 'medium'
                })
                results['anomalies_count'] += 1
                results['passed'] = False
        
        except Exception as e:
            logging.warning(f"Trend analysis failed for {metric}: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def _detect_point_anomalies(self, ts_data: pd.Series, metric: str) -> Dict[str, Any]:
        """Detect point anomalies in time series"""
        
        results = {
            'passed': True,
            'anomalies_count': 0,
            'anomalies': []
        }
        
        try:
            # Statistical approach: Z-score based detection
            z_scores = np.abs(stats.zscore(ts_data.fillna(ts_data.mean())))
            z_threshold = 1.5
            
            # IQR approach
            Q1 = ts_data.quantile(0.25)
            Q3 = ts_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Combine both approaches
            z_anomalies = ts_data.index[z_scores > z_threshold]
            iqr_anomalies = ts_data.index[(ts_data < lower_bound) | (ts_data > upper_bound)]

            # Union of anomalies
            all_anomalies = set(z_anomalies) | set(iqr_anomalies)
            if len(all_anomalies) > 0:
                results['passed'] = False
                results['anomalies_count'] = len(all_anomalies)
                
                for date in all_anomalies:
                    value = ts_data[date]
                    z_score = z_scores[ts_data.index.get_loc(date)]
                    
                    results['anomalies'].append({
                        'type': 'point_anomaly',
                        'date': str(date),
                        'metric': metric,
                        'value': int(value),
                        'z_score': float(z_score),
                        'expected_range': f"[{lower_bound:.2f}, {upper_bound:.2f}]",
                        'severity': 'high' if z_score > 4 else 'medium'
                    })
        
        except Exception as e:
            logging.warning(f"Point anomaly detection failed for {metric}: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def _check_stationarity(self, ts_data: pd.Series, metric: str) -> Dict[str, Any]:
        """Check time series stationarity using Augmented Dickey-Fuller test"""
        
        results = {
            'is_stationary': False,
            'adf_statistic': None,
            'p_value': None,
            'critical_values': {}
        }
        
        try:
            # Perform Augmented Dickey-Fuller test
            adf_result = adfuller(ts_data.dropna())
            
            results['adf_statistic'] = adf_result[0]
            results['p_value'] = adf_result[1]
            results['critical_values'] = adf_result[4]
            results['is_stationary'] = adf_result[1] < 0.05
            
        except Exception as e:
            logging.warning(f"Stationarity test failed for {metric}: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def _detect_trend_breaks(self, ts_data: pd.Series) -> List[Dict[str, Any]]:
        """Detect structural breaks in trend"""
        
        trend_breaks = []
        
        try:
            # Simple approach: detect significant changes in local slope
            window = min(5, len(ts_data) // 4)
            if window < 2:
                return trend_breaks
            
            slopes = []
            dates = []
            
            for i in range(window, len(ts_data) - window):
                # Calculate local slope
                local_data = ts_data.iloc[i-window:i+window]
                x = np.arange(len(local_data))
                slope, _, _, _, _ = stats.linregress(x, local_data.values)
                slopes.append(slope)
                dates.append(ts_data.index[i])
            
            if len(slopes) > 2:
                # Detect significant slope changes
                slope_changes = np.diff(slopes)
                slope_std = np.std(slope_changes)
                
                for i, change in enumerate(slope_changes):
                    if abs(change) > 2 * slope_std:
                        trend_breaks.append({
                            'date': dates[i+1],
                            'magnitude': change,
                            'previous_slope': slopes[i],
                            'new_slope': slopes[i+1]
                        })
        
        except Exception as e:
            logging.warning(f"Trend break detection failed: {str(e)}")
        
        return trend_breaks
    
    def _generate_summary_message(self, results: Dict[str, Any]) -> str:
        """Generate summary message for temporal analysis"""
        
        if results['passed']:
            return "All temporal patterns are normal"
        
        total_anomalies = results['anomalies_count']
        metric_count = len(results['analyses'])
        
        return f"{total_anomalies} temporal anomalies detected across {metric_count} metrics"
    
    def get_forecast(self, model_name: str, metric: str, date_column: str = 'created_at',
                    periods: int = 7, method: str = 'linear') -> Dict[str, Any]:
        """Generate simple forecast for a metric"""
        
        try:
            # Get historical data
            data = self._get_temporal_data(model_name, date_column, [metric], 90, 'daily')
            
            if data.empty or len(data) < 7:
                return {'error': 'Insufficient data for forecasting'}
            
            ts_data = data.set_index('period_date')[metric].fillna(0)
            
            if method == 'linear':
                # Simple linear trend extrapolation
                x = np.arange(len(ts_data))
                slope, intercept, _, _, _ = stats.linregress(x, ts_data.values)
                
                # Generate forecast
                forecast_x = np.arange(len(ts_data), len(ts_data) + periods)
                forecast_values = slope * forecast_x + intercept
                
                # Generate future dates
                last_date = ts_data.index[-1]
                forecast_dates = pd.date_range(
                    start=last_date + pd.Timedelta(days=1),
                    periods=periods,
                    freq='D'
                )
                
                return {
                    'dates': [str(d.date()) for d in forecast_dates],
                    'values': forecast_values.tolist(),
                    'method': 'linear_trend',
                    'confidence_interval': None  # Could add this with more sophisticated models
                }
            
            else:
                return {'error': f'Forecasting method {method} not supported'}
                
        except Exception as e:
            return {'error': f'Forecasting failed: {str(e)}'}

