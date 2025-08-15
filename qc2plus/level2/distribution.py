"""
2QC+ Level 2 Distribution Analysis
ML-powered distribution anomaly detection by segments
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from scipy import stats
from scipy.stats import ks_2samp, chi2_contingency
from sklearn.preprocessing import StandardScaler
import warnings

from qc2plus.core.connection import ConnectionManager


class DistributionAnalyzer:
    """Analyzes data distributions and detects anomalies by segments"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        
    def analyze(self, model_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform distribution analysis"""
        
        try:
            # Extract configuration
            segments = config.get('segments', [])
            metrics = config.get('metrics', ['count'])
            reference_period = config.get('reference_period', 30)
            comparison_period = config.get('comparison_period', 7)
            date_column = config.get('date_column', 'created_at')
            distribution_tests = config.get('distribution_tests', ['ks_test', 'chi2_test'])
            
            # Validate configuration
            if not segments:
                raise ValueError("At least one segment required for distribution analysis")
            
            # Get segmented data
            reference_data = self._get_segmented_data(
                model_name, segments, metrics, date_column, reference_period, 'reference'
            )
            
            comparison_data = self._get_segmented_data(
                model_name, segments, metrics, date_column, comparison_period, 'comparison'
            )
            
            if reference_data.empty or comparison_data.empty:
                return {
                    'passed': True,
                    'anomalies_count': 0,
                    'message': 'Insufficient data for distribution analysis',
                    'details': {}
                }
            
            # Perform distribution analysis
            results = {
                'passed': True,
                'anomalies_count': 0,
                'segment_analyses': {}
            }
            
            # Analyze each segment
            segment_combinations = self._get_segment_combinations(reference_data, segments)
            
            for segment_key in segment_combinations:
                segment_results = self._analyze_segment_distribution(
                    reference_data, comparison_data, segment_key, segments, 
                    metrics, distribution_tests
                )
                
                results['segment_analyses'][segment_key] = segment_results
                
                if not segment_results['passed']:
                    results['passed'] = False
                    results['anomalies_count'] += segment_results.get('anomalies_count', 0)
            
            # Cross-segment analysis
            cross_segment_results = self._analyze_cross_segment_patterns(
                reference_data, comparison_data, segments, metrics
            )
            results['cross_segment_analysis'] = cross_segment_results
            
            if not cross_segment_results['passed']:
                results['passed'] = False
                results['anomalies_count'] += cross_segment_results.get('anomalies_count', 0)
            
            return {
                'passed': results['passed'],
                'anomalies_count': results['anomalies_count'],
                'message': self._generate_summary_message(results),
                'details': {
                    'segments_analyzed': segments,
                    'metrics_analyzed': metrics,
                    'reference_period_days': reference_period,
                    'comparison_period_days': comparison_period,
                    'distribution_tests': distribution_tests,
                    'segment_count': len(segment_combinations),
                    'individual_analyses': results['segment_analyses'],
                    'cross_segment_analysis': cross_segment_results
                }
            }
            
        except Exception as e:
            logging.error(f"Distribution analysis failed for {model_name}: {str(e)}")
            return {
                'passed': False,
                'error': str(e),
                'anomalies_count': 1,
                'message': f'Distribution analysis failed: {str(e)}'
            }
    
    def _get_segmented_data(self, model_name: str, segments: List[str], metrics: List[str],
                           date_column: str, days: int, period_type: str) -> pd.DataFrame:
        """Get segmented data for specified period"""
        
        schema = self.connection_manager.config.get('schema', 'public')
        
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
            elif metric.startswith('std_'):
                column = metric.replace('std_', '')
                metric_clauses.append(f'STDDEV({column}) as {metric}')
            else:
                # Assume it's a column name for sum
                metric_clauses.append(f'SUM({metric}) as {metric}')
        
        # Determine date range
        if period_type == 'comparison':
            date_condition = f"{date_column} >= CURRENT_DATE - INTERVAL '{days} days'"
        else:  # reference
            date_condition = f"""
                {date_column} >= CURRENT_DATE - INTERVAL '{days + 7} days' 
                AND {date_column} < CURRENT_DATE - INTERVAL '7 days'
            """
        
        query = f"""
            SELECT 
                {', '.join(segments)},
                {', '.join(metric_clauses)}
            FROM {schema}.{model_name}
            WHERE {date_condition}
            AND {' AND '.join([f'{segment} IS NOT NULL' for segment in segments])}
            GROUP BY {', '.join(segments)}
            ORDER BY {', '.join(segments)}
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
    
    def _get_segment_combinations(self, data: pd.DataFrame, segments: List[str]) -> List[str]:
        """Get all unique segment combinations"""
        
        if len(segments) == 1:
            return data[segments[0]].astype(str).unique().tolist()
        else:
            # Create combination keys
            combinations = []
            for _, row in data.iterrows():
                combo_key = '|'.join([str(row[segment]) for segment in segments])
                if combo_key not in combinations:
                    combinations.append(combo_key)
            return combinations
    
    def _analyze_segment_distribution(self, reference_data: pd.DataFrame, comparison_data: pd.DataFrame,
                                    segment_key: str, segments: List[str], metrics: List[str],
                                    distribution_tests: List[str]) -> Dict[str, Any]:
        """Analyze distribution for a specific segment"""
        
        results = {
            'passed': True,
            'anomalies_count': 0,
            'anomalies': [],
            'tests': {}
        }
        
        try:
            # Filter data for this segment
            ref_segment_data = self._filter_segment_data(reference_data, segment_key, segments)
            comp_segment_data = self._filter_segment_data(comparison_data, segment_key, segments)
            
            if ref_segment_data.empty or comp_segment_data.empty:
                return results
            
            # Test each metric
            for metric in metrics:
                if metric not in ref_segment_data.columns or metric not in comp_segment_data.columns:
                    continue
                
                ref_values = ref_segment_data[metric].dropna()
                comp_values = comp_segment_data[metric].dropna()
                
                if len(ref_values) < 3 or len(comp_values) < 3:
                    continue
                
                metric_results = self._perform_distribution_tests(
                    ref_values, comp_values, metric, distribution_tests
                )
                
                results['tests'][metric] = metric_results
                
                # Check for significant distribution changes
                for test_name, test_result in metric_results.items():
                    if test_result.get('significant_change', False):
                        results['passed'] = False
                        results['anomalies_count'] += 1
                        results['anomalies'].append({
                            'segment': segment_key,
                            'metric': metric,
                            'test': test_name,
                            'p_value': test_result.get('p_value'),
                            'statistic': test_result.get('statistic'),
                            'severity': self._determine_severity(test_result),
                            'description': test_result.get('description', '')
                        })
        
        except Exception as e:
            logging.error(f"Segment analysis failed for {segment_key}: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def _filter_segment_data(self, data: pd.DataFrame, segment_key: str, segments: List[str]) -> pd.DataFrame:
        """Filter data for specific segment combination"""
        
        if len(segments) == 1:
            return data[data[segments[0]].astype(str) == segment_key]
        else:
            # Parse combination key
            segment_values = segment_key.split('|')
            
            # Filter by each segment
            filtered_data = data.copy()
            for i, segment in enumerate(segments):
                filtered_data = filtered_data[filtered_data[segment].astype(str) == segment_values[i]]
            
            return filtered_data
    
    def _perform_distribution_tests(self, ref_values: pd.Series, comp_values: pd.Series,
                                  metric: str, distribution_tests: List[str]) -> Dict[str, Any]:
        """Perform statistical tests to compare distributions"""
        
        test_results = {}
        
        # Kolmogorov-Smirnov Test
        if 'ks_test' in distribution_tests:
            try:
                ks_stat, ks_p = ks_2samp(ref_values, comp_values)
                test_results['ks_test'] = {
                    'statistic': ks_stat,
                    'p_value': ks_p,
                    'significant_change': ks_p < 0.05,
                    'description': f'KS test p-value: {ks_p:.4f}, statistic: {ks_stat:.4f}'
                }
            except Exception as e:
                test_results['ks_test'] = {'error': str(e)}
        
        # Chi-square test (for categorical-like data)
        if 'chi2_test' in distribution_tests:
            try:
                # Bin the continuous data for chi-square test
                ref_binned, comp_binned = self._bin_data_for_chi2(ref_values, comp_values)
                
                if len(ref_binned) > 1 and len(comp_binned) > 1:
                    contingency_table = np.array([ref_binned, comp_binned])
                    chi2_stat, chi2_p, dof, expected = chi2_contingency(contingency_table)
                    
                    test_results['chi2_test'] = {
                        'statistic': chi2_stat,
                        'p_value': chi2_p,
                        'degrees_of_freedom': dof,
                        'significant_change': chi2_p < 0.05,
                        'description': f'Chi-square test p-value: {chi2_p:.4f}, statistic: {chi2_stat:.4f}'
                    }
            except Exception as e:
                test_results['chi2_test'] = {'error': str(e)}
        
        # Mann-Whitney U Test (non-parametric)
        if 'mann_whitney' in distribution_tests:
            try:
                from scipy.stats import mannwhitneyu
                mw_stat, mw_p = mannwhitneyu(ref_values, comp_values, alternative='two-sided')
                test_results['mann_whitney'] = {
                    'statistic': mw_stat,
                    'p_value': mw_p,
                    'significant_change': mw_p < 0.05,
                    'description': f'Mann-Whitney U test p-value: {mw_p:.4f}'
                }
            except Exception as e:
                test_results['mann_whitney'] = {'error': str(e)}
        
        # T-test for means
        if 'ttest' in distribution_tests:
            try:
                t_stat, t_p = stats.ttest_ind(ref_values, comp_values)
                test_results['ttest'] = {
                    'statistic': t_stat,
                    'p_value': t_p,
                    'significant_change': t_p < 0.05,
                    'ref_mean': ref_values.mean(),
                    'comp_mean': comp_values.mean(),
                    'description': f'T-test p-value: {t_p:.4f}, means: {ref_values.mean():.2f} vs {comp_values.mean():.2f}'
                }
            except Exception as e:
                test_results['ttest'] = {'error': str(e)}
        
        # Effect size calculations
        try:
            # Cohen's d for effect size
            pooled_std = np.sqrt(((len(ref_values) - 1) * ref_values.var() + 
                                (len(comp_values) - 1) * comp_values.var()) / 
                               (len(ref_values) + len(comp_values) - 2))
            
            if pooled_std > 0:
                cohens_d = (ref_values.mean() - comp_values.mean()) / pooled_std
                
                # Add effect size to all tests
                for test_name in test_results:
                    if 'error' not in test_results[test_name]:
                        test_results[test_name]['effect_size'] = cohens_d
                        test_results[test_name]['effect_magnitude'] = self._interpret_effect_size(cohens_d)
        except:
            pass
        
        return test_results
    
    def _bin_data_for_chi2(self, ref_values: pd.Series, comp_values: pd.Series, n_bins: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """Bin continuous data for chi-square test"""
        
        # Combine data to get consistent bin edges
        combined_data = pd.concat([ref_values, comp_values])
        
        # Create bins
        try:
            _, bin_edges = np.histogram(combined_data, bins=n_bins)
            
            # Bin each dataset
            ref_binned, _ = np.histogram(ref_values, bins=bin_edges)
            comp_binned, _ = np.histogram(comp_values, bins=bin_edges)
            
            # Remove empty bins
            non_zero_bins = (ref_binned > 0) | (comp_binned > 0)
            ref_binned = ref_binned[non_zero_bins]
            comp_binned = comp_binned[non_zero_bins]
            
            return ref_binned, comp_binned
            
        except Exception:
            # Fallback: use quantile-based binning
            quantiles = np.linspace(0, 1, n_bins + 1)
            bin_edges = combined_data.quantile(quantiles).values
            
            ref_binned, _ = np.histogram(ref_values, bins=bin_edges)
            comp_binned, _ = np.histogram(comp_values, bins=bin_edges)
            
            return ref_binned, comp_binned
    
    def _interpret_effect_size(self, cohens_d: float) -> str:
        """Interpret Cohen's d effect size"""
        
        abs_d = abs(cohens_d)
        
        if abs_d < 0.2:
            return 'negligible'
        elif abs_d < 0.5:
            return 'small'
        elif abs_d < 0.8:
            return 'medium'
        else:
            return 'large'
    
    def _determine_severity(self, test_result: Dict[str, Any]) -> str:
        """Determine severity based on test results"""
        
        p_value = test_result.get('p_value', 1.0)
        effect_size = abs(test_result.get('effect_size', 0))
        
        if p_value < 0.001 and effect_size > 0.8:
            return 'critical'
        elif p_value < 0.01 and effect_size > 0.5:
            return 'high'
        elif p_value < 0.05:
            return 'medium'
        else:
            return 'low'
    
    def _analyze_cross_segment_patterns(self, reference_data: pd.DataFrame, comparison_data: pd.DataFrame,
                                      segments: List[str], metrics: List[str]) -> Dict[str, Any]:
        """Analyze patterns across segments"""
        
        results = {
            'passed': True,
            'anomalies_count': 0,
            'anomalies': []
        }
        
        try:
            # Analyze segment concentration changes
            for segment in segments:
                ref_distribution = reference_data.groupby(segment)['count'].sum() if 'count' in reference_data.columns else reference_data.groupby(segment).size()
                comp_distribution = comparison_data.groupby(segment)['count'].sum() if 'count' in comparison_data.columns else comparison_data.groupby(segment).size()
                
                # Normalize to proportions
                ref_props = ref_distribution / ref_distribution.sum()
                comp_props = comp_distribution / comp_distribution.sum()
                
                # Align segments (handle missing segments)
                all_segments = set(ref_props.index) | set(comp_props.index)
                
                ref_aligned = pd.Series(0.0, index=all_segments)
                comp_aligned = pd.Series(0.0, index=all_segments)
                
                ref_aligned.update(ref_props)
                comp_aligned.update(comp_props)
                
                # Calculate changes in segment concentration
                concentration_changes = abs(comp_aligned - ref_aligned)
                significant_changes = concentration_changes[concentration_changes > 0.1]  # 10% threshold
                
                if len(significant_changes) > 0:
                    results['passed'] = False
                    results['anomalies_count'] += len(significant_changes)
                    
                    for segment_value, change in significant_changes.items():
                        results['anomalies'].append({
                            'type': 'segment_concentration_change',
                            'segment': segment,
                            'segment_value': segment_value,
                            'concentration_change': change,
                            'ref_proportion': ref_aligned[segment_value],
                            'comp_proportion': comp_aligned[segment_value],
                            'severity': 'high' if change > 0.2 else 'medium'
                        })
            
            # Analyze new/disappeared segments
            ref_segments = set()
            comp_segments = set()
            
            for segment in segments:
                ref_segments.update(reference_data[segment].astype(str).unique())
                comp_segments.update(comparison_data[segment].astype(str).unique())
            
            new_segments = comp_segments - ref_segments
            disappeared_segments = ref_segments - comp_segments
            
            if new_segments:
                results['passed'] = False
                results['anomalies_count'] += len(new_segments)
                for new_seg in new_segments:
                    results['anomalies'].append({
                        'type': 'new_segment',
                        'segment_value': new_seg,
                        'description': f'New segment appeared: {new_seg}',
                        'severity': 'medium'
                    })
            
            if disappeared_segments:
                results['passed'] = False
                results['anomalies_count'] += len(disappeared_segments)
                for disappeared_seg in disappeared_segments:
                    results['anomalies'].append({
                        'type': 'disappeared_segment',
                        'segment_value': disappeared_seg,
                        'description': f'Segment disappeared: {disappeared_seg}',
                        'severity': 'high'
                    })
        
        except Exception as e:
            logging.error(f"Cross-segment analysis failed: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def _generate_summary_message(self, results: Dict[str, Any]) -> str:
        """Generate summary message for distribution analysis"""
        
        if results['passed']:
            return "All distribution patterns are normal"
        
        total_anomalies = results['anomalies_count']
        segment_count = len(results['segment_analyses'])
        
        segment_anomalies = sum(1 for r in results['segment_analyses'].values() if not r['passed'])
        cross_segment_anomalies = results.get('cross_segment_analysis', {}).get('anomalies_count', 0)
        
        messages = []
        if segment_anomalies > 0:
            messages.append(f"{segment_anomalies}/{segment_count} segments with anomalies")
        
        if cross_segment_anomalies > 0:
            messages.append(f"{cross_segment_anomalies} cross-segment anomalies")
        
        return f"{total_anomalies} distribution anomalies: " + ", ".join(messages)
    
    def get_segment_summary(self, model_name: str, segments: List[str], 
                          date_column: str = 'created_at', days: int = 30) -> Dict[str, Any]:
        """Get summary statistics for each segment"""
        
        try:
            data = self._get_segmented_data(model_name, segments, ['count'], date_column, days, 'reference')
            
            if data.empty:
                return {'error': 'No data available'}
            
            summary = {}
            
            for segment in segments:
                segment_stats = {
                    'unique_values': data[segment].nunique(),
                    'top_values': data[segment].value_counts().head(10).to_dict(),
                    'total_records': data['count'].sum() if 'count' in data.columns else len(data)
                }
                summary[segment] = segment_stats
            
            return summary
            
        except Exception as e:
            return {'error': f'Failed to get segment summary: {str(e)}'}
    
    def detect_segment_drift(self, model_name: str, segments: List[str], 
                           lookback_days: int = 90, window_size: int = 7) -> Dict[str, Any]:
        """Detect gradual drift in segment distributions over time"""
        
        try:
            schema = self.connection_manager.config.get('schema', 'public')
            
            # Get time-windowed segment data
            query = f"""
                WITH windowed_data AS (
                    SELECT 
                        DATE(created_at) as date,
                        {', '.join(segments)},
                        COUNT(*) as count
                    FROM {schema}.{model_name}
                    WHERE created_at >= CURRENT_DATE - INTERVAL '{lookback_days} days'
                    GROUP BY DATE(created_at), {', '.join(segments)}
                ),
                weekly_data AS (
                    SELECT 
                        DATE_TRUNC('week', date) as week,
                        {', '.join(segments)},
                        SUM(count) as weekly_count
                    FROM windowed_data
                    GROUP BY DATE_TRUNC('week', date), {', '.join(segments)}
                )
                SELECT * FROM weekly_data ORDER BY week, {', '.join(segments)}
            """
            
            # Adapt for different databases
            if self.connection_manager.db_type == 'bigquery':
                query = query.replace('CURRENT_DATE', 'CURRENT_DATE()')
                query = query.replace("INTERVAL '", "INTERVAL ")
                query = query.replace(" days'", " DAY")
            elif self.connection_manager.db_type == 'snowflake':
                query = query.replace('CURRENT_DATE', 'CURRENT_DATE()')
                query = query.replace(" days'", " DAY'")
            
            time_series_data = self.connection_manager.execute_query(query)
            
            if time_series_data.empty or len(time_series_data) < 4:
                return {'error': 'Insufficient time series data for drift detection'}
            
            # Analyze drift for each segment
            drift_results = {}
            
            for segment in segments:
                # Calculate weekly proportions for each segment value
                weekly_proportions = time_series_data.pivot_table(
                    index='week', 
                    columns=segment, 
                    values='weekly_count', 
                    fill_value=0
                )
                
                # Normalize to proportions
                weekly_proportions = weekly_proportions.div(weekly_proportions.sum(axis=1), axis=0)
                
                # Detect significant trends in proportions
                segment_drift = []
                
                for segment_value in weekly_proportions.columns:
                    proportion_series = weekly_proportions[segment_value]
                    
                    # Simple linear trend test
                    x = np.arange(len(proportion_series))
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, proportion_series)
                    
                    # Significant trend if p < 0.05 and substantial change
                    total_change = abs(proportion_series.iloc[-1] - proportion_series.iloc[0])
                    
                    if p_value < 0.05 and total_change > 0.05:  # 5% threshold
                        segment_drift.append({
                            'segment_value': segment_value,
                            'trend_slope': slope,
                            'p_value': p_value,
                            'total_change': total_change,
                            'direction': 'increasing' if slope > 0 else 'decreasing'
                        })
                
                drift_results[segment] = {
                    'drift_detected': len(segment_drift) > 0,
                    'drifting_values': segment_drift
                }
            
            return drift_results
            
        except Exception as e:
            return {'error': f'Drift detection failed: {str(e)}'}
