"""
2QC+ Level 2 Multivariate Analysis
ML-powered multivariate anomaly detection using Isolation Forest and LOF
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA
from sklearn.cluster import DBSCAN
import warnings

from qc2plus.core.connection import ConnectionManager


class MultivariateAnalyzer:
    """Detects multivariate anomalies using ML algorithms"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.scaler = RobustScaler()  # More robust to outliers than StandardScaler
        
    def analyze(self, model_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform multivariate anomaly detection"""
        
        try:
            # Extract configuration
            features = config.get('features', [])
            contamination = config.get('contamination', 0.1)
            algorithms = config.get('algorithms', ['isolation_forest', 'lof'])
            date_column = config.get('date_column', 'created_at')
            window_days = config.get('window_days', 30)
            min_samples = config.get('min_samples', 100)
            
            # Validate configuration
            if len(features) < 2:
                raise ValueError("At least 2 features required for multivariate analysis")
            
            # Get data
            data = self._get_multivariate_data(model_name, features, date_column, window_days)
            
            if data.empty or len(data) < min_samples:
                return {
                    'passed': True,
                    'anomalies_count': 0,
                    'message': f'Insufficient data for multivariate analysis (need {min_samples}, got {len(data)})',
                    'details': {}
                }
            
            # Prepare features
            feature_data = self._prepare_features(data, features)
            
            # Run anomaly detection algorithms
            results = {}
            total_anomalies = 0
            
            if 'isolation_forest' in algorithms:
                iso_results = self._run_isolation_forest(feature_data, contamination)
                results['isolation_forest'] = iso_results
                total_anomalies += iso_results['anomalies_count']
            
            if 'lof' in algorithms:
                lof_results = self._run_local_outlier_factor(feature_data, contamination)
                results['local_outlier_factor'] = lof_results
                total_anomalies += lof_results['anomalies_count']
            
            if 'pca' in algorithms:
                pca_results = self._run_pca_anomaly_detection(feature_data, contamination)
                results['pca_anomaly'] = pca_results
                total_anomalies += pca_results['anomalies_count']
            
            if 'dbscan' in algorithms:
                dbscan_results = self._run_dbscan_anomaly_detection(feature_data)
                results['dbscan'] = dbscan_results
                total_anomalies += dbscan_results['anomalies_count']
            
            # Consensus anomaly detection
            consensus_results = self._get_consensus_anomalies(results, feature_data, data)
            
            # Determine overall status
            passed = consensus_results['anomalies_count'] == 0
            
            return {
                'passed': passed,
                'anomalies_count': consensus_results['anomalies_count'],
                'message': self._generate_summary_message(consensus_results, total_anomalies),
                'details': {
                    'algorithms_used': algorithms,
                    'features_analyzed': features,
                    'data_points': len(data),
                    'individual_results': results,
                    'consensus_anomalies': consensus_results
                }
            }
            
        except Exception as e:
            logging.error(f"Multivariate analysis failed for {model_name}: {str(e)}")
            return {
                'passed': False,
                'error': str(e),
                'anomalies_count': 1,
                'message': f'Multivariate analysis failed: {str(e)}'
            }
    
    def _get_multivariate_data(self, model_name: str, features: List[str], 
                             date_column: str, window_days: int) -> pd.DataFrame:
        """Get data for multivariate analysis"""
        
        schema = self.connection_manager.config.get('schema', 'public')
        
        # Build query to get recent data
        query = f"""
            SELECT 
                {date_column},
                {', '.join(features)}
            FROM {schema}.{model_name}
            WHERE {date_column} >= CURRENT_DATE - INTERVAL '{window_days} days'
            AND {' AND '.join([f'{feature} IS NOT NULL' for feature in features])}
            ORDER BY {date_column} DESC
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
    
    def _prepare_features(self, data: pd.DataFrame, features: List[str]) -> np.ndarray:
        """Prepare and scale features for analysis"""
        
        # Extract feature columns
        feature_data = data[features].copy()
        
        # Handle missing values
        feature_data = feature_data.fillna(feature_data.median())
        
        # Remove infinite values
        feature_data = feature_data.replace([np.inf, -np.inf], np.nan)
        feature_data = feature_data.fillna(feature_data.median())
        
        # Scale features
        scaled_features = self.scaler.fit_transform(feature_data)
        
        return scaled_features
    
    def _run_isolation_forest(self, feature_data: np.ndarray, contamination: float) -> Dict[str, Any]:
        """Run Isolation Forest anomaly detection"""
        
        try:
            # Initialize Isolation Forest
            iso_forest = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100
            )
            
            # Fit and predict
            predictions = iso_forest.fit_predict(feature_data)
            anomaly_scores = iso_forest.decision_function(feature_data)
            
            # Identify anomalies (predictions == -1)
            anomaly_indices = np.where(predictions == -1)[0]
            
            return {
                'anomalies_count': len(anomaly_indices),
                'anomaly_indices': anomaly_indices.tolist(),
                'anomaly_scores': anomaly_scores.tolist(),
                'algorithm': 'isolation_forest',
                'contamination_used': contamination
            }
            
        except Exception as e:
            logging.error(f"Isolation Forest failed: {str(e)}")
            return {
                'anomalies_count': 0,
                'error': str(e),
                'algorithm': 'isolation_forest'
            }
    
    def _run_local_outlier_factor(self, feature_data: np.ndarray, contamination: float) -> Dict[str, Any]:
        """Run Local Outlier Factor anomaly detection"""
        
        try:
            # Initialize LOF
            lof = LocalOutlierFactor(
                contamination=contamination,
                n_neighbors=min(20, len(feature_data) // 5)
            )
            
            # Fit and predict
            predictions = lof.fit_predict(feature_data)
            anomaly_scores = lof.negative_outlier_factor_
            
            # Identify anomalies (predictions == -1)
            anomaly_indices = np.where(predictions == -1)[0]
            
            return {
                'anomalies_count': len(anomaly_indices),
                'anomaly_indices': anomaly_indices.tolist(),
                'anomaly_scores': anomaly_scores.tolist(),
                'algorithm': 'local_outlier_factor',
                'contamination_used': contamination
            }
            
        except Exception as e:
            logging.error(f"Local Outlier Factor failed: {str(e)}")
            return {
                'anomalies_count': 0,
                'error': str(e),
                'algorithm': 'local_outlier_factor'
            }
    
    def _run_pca_anomaly_detection(self, feature_data: np.ndarray, contamination: float) -> Dict[str, Any]:
        """Run PCA-based anomaly detection"""
        
        try:
            # Apply PCA
            pca = PCA(n_components=min(feature_data.shape[1], feature_data.shape[0] // 2))
            pca_features = pca.fit_transform(feature_data)
            
            # Reconstruct data
            reconstructed = pca.inverse_transform(pca_features)
            
            # Calculate reconstruction error
            reconstruction_errors = np.mean((feature_data - reconstructed) ** 2, axis=1)
            
            # Identify anomalies based on reconstruction error threshold
            threshold = np.percentile(reconstruction_errors, (1 - contamination) * 100)
            anomaly_indices = np.where(reconstruction_errors > threshold)[0]
            
            return {
                'anomalies_count': len(anomaly_indices),
                'anomaly_indices': anomaly_indices.tolist(),
                'anomaly_scores': reconstruction_errors.tolist(),
                'algorithm': 'pca_reconstruction',
                'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
                'threshold': threshold
            }
            
        except Exception as e:
            logging.error(f"PCA anomaly detection failed: {str(e)}")
            return {
                'anomalies_count': 0,
                'error': str(e),
                'algorithm': 'pca_reconstruction'
            }
    
    def _run_dbscan_anomaly_detection(self, feature_data: np.ndarray) -> Dict[str, Any]:
        """Run DBSCAN-based anomaly detection"""
        
        try:
            # Auto-determine eps using k-distance plot heuristic
            from sklearn.neighbors import NearestNeighbors
            
            k = min(5, feature_data.shape[1] * 2)  # Rule of thumb: k = 2 * dimensions
            neighbors = NearestNeighbors(n_neighbors=k)
            neighbors.fit(feature_data)
            distances, indices = neighbors.kneighbors(feature_data)
            
            # Use the k-th nearest neighbor distance
            k_distances = distances[:, k-1]
            eps = np.percentile(k_distances, 75)  # Use 75th percentile as eps
            
            # Run DBSCAN
            dbscan = DBSCAN(eps=eps, min_samples=k)
            cluster_labels = dbscan.fit_predict(feature_data)
            
            # Anomalies are points labeled as -1 (noise)
            anomaly_indices = np.where(cluster_labels == -1)[0]
            
            return {
                'anomalies_count': len(anomaly_indices),
                'anomaly_indices': anomaly_indices.tolist(),
                'algorithm': 'dbscan',
                'eps_used': eps,
                'min_samples_used': k,
                'n_clusters': len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
            }
            
        except Exception as e:
            logging.error(f"DBSCAN anomaly detection failed: {str(e)}")
            return {
                'anomalies_count': 0,
                'error': str(e),
                'algorithm': 'dbscan'
            }
    
    def _get_consensus_anomalies(self, results: Dict[str, Any], feature_data: np.ndarray, 
                               original_data: pd.DataFrame) -> Dict[str, Any]:
        """Get consensus anomalies from multiple algorithms"""
        
        # Collect all anomaly indices from different algorithms
        all_anomaly_indices = set()
        algorithm_votes = {}
        
        for algorithm, result in results.items():
            if 'anomaly_indices' in result:
                indices = result['anomaly_indices']
                all_anomaly_indices.update(indices)
                
                for idx in indices:
                    if idx not in algorithm_votes:
                        algorithm_votes[idx] = []
                    algorithm_votes[idx].append(algorithm)
        
        # Determine consensus threshold (at least 2 algorithms must agree)
        consensus_threshold = max(1, len(results) // 2)
        consensus_anomalies = []
        
        for idx in all_anomaly_indices:
            vote_count = len(algorithm_votes.get(idx, []))
            if vote_count >= consensus_threshold:
                
                # Get anomaly details
                anomaly_info = {
                    'index': idx,
                    'vote_count': vote_count,
                    'algorithms': algorithm_votes[idx],
                    'confidence': vote_count / len(results)
                }
                
                # Add feature values for context
                if idx < len(original_data):
                    row_data = original_data.iloc[idx]
                    anomaly_info['feature_values'] = row_data.to_dict()
                
                consensus_anomalies.append(anomaly_info)
        
        # Sort by confidence (highest first)
        consensus_anomalies.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'anomalies_count': len(consensus_anomalies),
            'anomalies': consensus_anomalies,
            'total_candidates': len(all_anomaly_indices),
            'consensus_threshold': consensus_threshold
        }
    
    def _generate_summary_message(self, consensus_results: Dict[str, Any], 
                                total_algorithm_anomalies: int) -> str:
        """Generate summary message for multivariate analysis"""
        
        consensus_count = consensus_results['anomalies_count']
        total_candidates = consensus_results['total_candidates']
        
        if consensus_count == 0:
            return "No consensus multivariate anomalies detected"
        
        return (f"{consensus_count} consensus anomalies detected "
                f"({total_candidates} total candidates from all algorithms)")
    
    def get_feature_importance(self, model_name: str, features: List[str], 
                             method: str = 'isolation_forest') -> Dict[str, float]:
        """Get feature importance for anomaly detection"""
        
        try:
            data = self._get_multivariate_data(model_name, features, 'created_at', 30)
            feature_data = self._prepare_features(data, features)
            
            if method == 'isolation_forest':
                # Use feature permutation importance
                iso_forest = IsolationForest(random_state=42)
                iso_forest.fit(feature_data)
                
                base_scores = iso_forest.decision_function(feature_data)
                base_anomalies = len(np.where(iso_forest.predict(feature_data) == -1)[0])
                
                importance_scores = {}
                
                for i, feature in enumerate(features):
                    # Permute this feature
                    permuted_data = feature_data.copy()
                    np.random.shuffle(permuted_data[:, i])
                    
                    # Calculate impact on anomaly detection
                    permuted_scores = iso_forest.decision_function(permuted_data)
                    permuted_anomalies = len(np.where(iso_forest.predict(permuted_data) == -1)[0])
                    
                    # Importance is the change in anomaly detection performance
                    score_change = np.mean(np.abs(base_scores - permuted_scores))
                    anomaly_change = abs(base_anomalies - permuted_anomalies)
                    
                    importance_scores[feature] = score_change + (anomaly_change / len(feature_data))
                
                # Normalize importance scores
                total_importance = sum(importance_scores.values())
                if total_importance > 0:
                    importance_scores = {k: v / total_importance for k, v in importance_scores.items()}
                
                return importance_scores
                
        except Exception as e:
            logging.error(f"Feature importance calculation failed: {str(e)}")
            return {feature: 1.0 / len(features) for feature in features}  # Equal importance fallback
