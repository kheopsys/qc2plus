"""
2QC+ Level 2 Distribution Analysis
Simplified analysis focusing on 2 key anomaly detections
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional

from qc2plus.core.connection import ConnectionManager

from qc2plus.sql.db_functions import DB_LEVEL2_FUNCTIONS

class DistributionAnalyzer:
    """Analyzes data distributions - Focus on segment shifts and behavior anomalies"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        
    def analyze(self, model_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform simplified distribution analysis - Focus on 2 key anomalies"""
        
        try:
            # Extract configuration
            segments = config.get('segments', [])
            metrics = config.get('metrics', ['count'])
            reference_period = config.get('reference_period', 30)
            comparison_period = config.get('comparison_period', 7)
            date_column = config.get('date_column', None)
            min_data_threshold = config.get('min_data_threshold', 10)
            if date_column is None:
                logging.info(f"No date_column specified for {model_name}, skipping distribution analysis")
                return {
                'passed': False,
                'anomalies_count': 1,
                'message': 'Distribution analysis skipped (no date column specified)',
                'details': {
                    'skipped': True,
                    'reason': 'No date_column configured',
                    'anomalies': [{
                        'type': 'missing_date_column',
                        'segment': 'N/A',
                        'segment_value': 'N/A',
                        'metric': 'configuration',
                        'reference_avg': 0,
                        'comparison_avg': 0,
                        'percent_change': 0,
                        'severity': 'critical',
                        'description': 'No date column configured for distribution analysis - cannot compare time periods without a date column'
                    }]
                    
                    }
                }   
            
            # Validate configuration
            if not segments:
                raise ValueError("At least one segment required for distribution analysis")
            
            # Get segmented data
            reference_data = self._get_segmented_data(
                model_name, segments, metrics, date_column, reference_period, comparison_period, 'reference'
            )
            
            comparison_data = self._get_segmented_data(
                model_name, segments, metrics, date_column, comparison_period, comparison_period, 'comparison'
            )
            
            if reference_data.empty or comparison_data.empty:
                return {
                    'passed': False,
                    'anomalies_count': 1,
                    'message': 'Insufficient data for distribution analysis',
                    'details': {
                        'reason': 'No data in one or both periods',
                        'reference_rows': len(reference_data),
                        'comparison_rows': len(comparison_data),
                        'severity': 'critical',
                        'anomalies': [{
                            'type': 'insufficient_data',
                            'segment': 'N/A',
                            'segment_value': 'N/A',
                            'metric': 'data_availability',
                            'reference_avg': len(reference_data),
                            'comparison_avg': len(comparison_data),
                            'percent_change': 0,
                            'severity': 'critical',
                            'description': f'No data available in one or both periods (reference: {len(reference_data)} rows, comparison: {len(comparison_data)} rows)'
                        }]
                    }
                }
            if min_data_threshold > 0:
                reference_total = self._count_rows(
                    model_name, segments, date_column, reference_period, comparison_period, 'reference'
                )
                comparison_total = self._count_rows(
                    model_name, segments, date_column, comparison_period, comparison_period, 'comparison'
                )
                
                if reference_total < min_data_threshold or comparison_total < min_data_threshold:
                    logging.error(f"Insufficient data for {model_name}: ref={reference_total}, comp={comparison_total}, threshold={min_data_threshold}")
                    return {
                        'passed': False,
                        'anomalies_count': 1,
                        'message': f'Insufficient data - only {reference_total} reference rows and {comparison_total} comparison rows (minimum {min_data_threshold} required)',
                        'details': {
                            'reason': f'Not enough data (minimum {min_data_threshold} rows required per period)',
                            'reference_rows': reference_total,
                            'comparison_rows': comparison_total,
                            'min_threshold': min_data_threshold,
                            'severity': 'critical',
                            'anomalies': [{
                                'type': 'insufficient_data',
                                'segment': 'N/A',
                                'segment_value': 'N/A',
                                'metric': 'data_volume',
                                'reference_avg': reference_total,
                                'comparison_avg': comparison_total,
                                'percent_change': 0,
                                'severity': 'critical',
                                'description': f'Insufficient data volume: {reference_total} reference rows, {comparison_total} comparison rows (minimum {min_data_threshold} required per period)'
                            }]
                        }
                    }
            # Perform ONLY the 2 key analyses
            anomalies = self._detect_segment_anomalies(reference_data, comparison_data, segments, metrics)

            if anomalies:
                logging.info(f"Distribution anomalies detected for {model_name}: {anomalies}")
                        
            results =  {
                'passed': len(anomalies) == 0,
                'anomalies_count': len(anomalies),
                'message': self._generate_summary_message(anomalies),
                'details': {
                    'segments_analyzed': segments,
                    'metrics_analyzed': metrics,
                    'reference_period_days': reference_period,
                    'comparison_period_days': comparison_period,
                    'anomalies': anomalies
                }
            }


            return results
            
        except Exception as e:
            logging.error(f"Distribution analysis failed for {model_name}: {str(e)}")
            return {
                'passed': False,
                'error': str(e),
                'anomalies_count': 1,
                'message': f'Distribution analysis failed: {str(e)}'
            }
    
    def _get_segmented_data(self, model_name: str, segments: List[str], metrics: List[str],
                           date_column: str, reference_period: int, comparison_period:int, period_type: str) -> pd.DataFrame:
        """Get segmented data for specified period"""
        
        schema = self.connection_manager.config.get('schema', 'public')
        db_type = self.connection_manager.db_type

        if db_type in DB_LEVEL2_FUNCTIONS:
            funcs = DB_LEVEL2_FUNCTIONS[db_type]
        else:
            logging.warning(f"Unknown db_type '{db_type}', defaulting to PostgreSQL syntax")
            funcs = DB_LEVEL2_FUNCTIONS['postgresql']

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
            else:
                # Assume it's a column name for sum
                metric_clauses.append(f'SUM({metric}) as {metric}')
        
        
        current_date_expr = funcs['current_date']()
        cast_date_col = funcs['cast_date'](date_column)
                                           
        if period_type == 'comparison':
            date_condition = f"{cast_date_col} >= {funcs['date_sub'](current_date_expr, reference_period)}"
        else:  # reference
            total_days = comparison_period + reference_period
            date_condition = f"""
                {cast_date_col} >= {funcs['date_sub'](current_date_expr, total_days)} 
                AND {cast_date_col} < {funcs['date_sub'](current_date_expr, comparison_period)}
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
        


        data = self.connection_manager.execute_query(query)

        return self.connection_manager.execute_query(query)
    
    def _detect_segment_anomalies(self, reference_data: pd.DataFrame, comparison_data: pd.DataFrame,
                                 segments: List[str], metrics: List[str]) -> List[Dict[str, Any]]:
        """Detect the 2 key segment anomalies"""
        
        anomalies = []
        
        for segment in segments:
            for metric in metrics:
                # 1. SEGMENT SHARE SHIFTS - Detect distribution changes between segments
                share_anomalies = self._detect_share_shifts(
                    reference_data, comparison_data, segment, metric
                )
                anomalies.extend(share_anomalies)
                
                # 2. SEGMENT BEHAVIOR ANOMALIES - Detect unusual metric changes within segments
                behavior_anomalies = self._detect_behavior_anomalies(
                    reference_data, comparison_data, segment, metric
                )
                anomalies.extend(behavior_anomalies)
        
        return anomalies
    
    def _detect_share_shifts(self, reference_data: pd.DataFrame, comparison_data: pd.DataFrame,
                           segment: str, metric: str) -> List[Dict[str, Any]]:
        """Detect segment share shifts"""
        
        anomalies = []
        
        try:
            # Calculate segment shares for reference period
            ref_totals = reference_data.groupby(segment)[metric].sum()
            ref_total = ref_totals.sum()
            ref_shares = (ref_totals / ref_total * 100) if ref_total > 0 else pd.Series()
            
            # Calculate segment shares for comparison period  
            comp_totals = comparison_data.groupby(segment)[metric].sum()
            comp_total = comp_totals.sum()
            comp_shares = (comp_totals / comp_total * 100) if comp_total > 0 else pd.Series()
            
            # Check all segments
            all_segments = set(ref_shares.index) | set(comp_shares.index)
            
            for segment_value in all_segments:
                ref_share = ref_shares.get(segment_value, 0)
                comp_share = comp_shares.get(segment_value, 0)
                
                # Detect significant share shifts (>10 percentage points)
                share_change = comp_share - ref_share
                
                if abs(share_change) > 10:  # 10 percentage points threshold
                    anomalies.append({
                        'type': 'segment_share_shift',
                        'segment': segment,
                        'segment_value': segment_value,
                        'metric': metric,
                        'reference_share': round(ref_share, 1),
                        'comparison_share': round(comp_share, 1), 
                        'share_change': round(share_change, 1),
                        'severity': 'critical' if abs(share_change) > 20 else 'high',
                        'description': f'{segment_value} share changed from {ref_share:.1f}% to {comp_share:.1f}% ({share_change:+.1f} points)'
                    })
        
        except Exception as e:
            logging.warning(f"Share shift detection failed for {segment}/{metric}: {str(e)}")
        
        return anomalies
    
    def _detect_behavior_anomalies(self, reference_data: pd.DataFrame, comparison_data: pd.DataFrame,
                                 segment: str, metric: str) -> List[Dict[str, Any]]:
        """Detect segment behavior anomalies"""
        
        anomalies = []
        
        try:
            # Get average metric per segment for both periods
            ref_segment_avg = reference_data.groupby(segment)[metric].mean()
            comp_segment_avg = comparison_data.groupby(segment)[metric].mean()

            
            # Check all segments
            all_segments = set(ref_segment_avg.index) | set(comp_segment_avg.index)
            
            for segment_value in all_segments:
                ref_avg = ref_segment_avg.get(segment_value, 0)
                
                comp_avg = comp_segment_avg.get(segment_value, 0)
                
                if ref_avg > 0:  # Avoid division by zero
                    # Calculate percentage change
                    pct_change = ((comp_avg - ref_avg) / ref_avg) * 100
                    
                    # Detect significant behavioral changes (>25%)
                    if abs(pct_change) > 25:
                        anomalies.append({
                            'type': 'segment_behavior_anomaly',
                            'segment': segment,
                            'segment_value': segment_value,
                            'metric': metric,
                            'reference_avg': round(ref_avg, 2),
                            'comparison_avg': round(comp_avg, 2),
                            'percent_change': round(pct_change, 1),
                            'severity': 'critical' if abs(pct_change) > 50 else 'high',
                            'description': f'{segment_value} {metric} changed from {ref_avg:.0f} to {comp_avg:.0f} ({pct_change:+.1f}%)'
                        })
        
        except Exception as e:
            logging.warning(f"Behavior anomaly detection failed for {segment}/{metric}: {str(e)}")
        
        return anomalies
    
    def _generate_summary_message(self, anomalies: List[Dict[str, Any]]) -> str:
        """Generate summary message for distribution analysis"""
        
        if not anomalies:
            return "No significant distribution changes detected"
        
        # Count by type
        share_shifts = len([a for a in anomalies if a['type'] == 'segment_share_shift'])
        behavior_anomalies = len([a for a in anomalies if a['type'] == 'segment_behavior_anomaly'])
        
        messages = []
        if share_shifts > 0:
            messages.append(f"{share_shifts} segment share shifts")
        if behavior_anomalies > 0:
            messages.append(f"{behavior_anomalies} segment behavior anomalies")
        
        return f"{len(anomalies)} distribution anomalies: " + ", ".join(messages)
    
    def get_segment_summary(self, model_name: str, segments: List[str], 
                          date_column: str = 'created_at', days: int = 30) -> Dict[str, Any]:
        """Get summary statistics for each segment"""
        
        try:
            data = self._get_segmented_data(model_name, segments, ['count'], date_column, days, 'comparison')
            
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
        
    def _count_rows(self, model_name: str, segments: List[str], date_column: str, 
                reference_period: int, comparison_period: int, period_type: str) -> int:
    
            
        schema = self.connection_manager.config.get('schema', 'public')
        db_type = self.connection_manager.db_type

        if db_type in DB_LEVEL2_FUNCTIONS:
            funcs = DB_LEVEL2_FUNCTIONS[db_type]
        else:
            funcs = DB_LEVEL2_FUNCTIONS['postgresql']

        current_date_expr = funcs['current_date']()
        cast_date_col = funcs['cast_date'](date_column)
                                        
        if period_type == 'comparison':
            date_condition = f"{cast_date_col} >= {funcs['date_sub'](current_date_expr, reference_period)}"
        else:  # reference
            total_days = comparison_period + reference_period
            date_condition = f"""
                {cast_date_col} >= {funcs['date_sub'](current_date_expr, total_days)} 
                AND {cast_date_col} < {funcs['date_sub'](current_date_expr, comparison_period)}
            """
        
        # Query simple COUNT(*)
        count_query = f"""
            SELECT COUNT(*) as total_rows
            FROM {schema}.{model_name}
            WHERE {date_condition}
            AND {' AND '.join([f'{segment} IS NOT NULL' for segment in segments])}
        """
        
        try:
            count_result = self.connection_manager.execute_query(count_query)
            return int(count_result.iloc[0]['total_rows']) if not count_result.empty else 0
        except Exception as e:
            logging.warning(f"Failed to count rows for {model_name}: {str(e)}")
            return 0