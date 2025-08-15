# tests/test_level2/test_correlation.py
"""
Tests pour qc2plus.level2.correlation
"""

import pytest
import pandas as pd
from qc2plus.level2.correlation import CorrelationAnalyzer


class TestCorrelationAnalyzer:
    
    def test_analyze_insufficient_variables(self, mock_connection_manager):
        """Test erreur avec variables insuffisantes"""
        analyzer = CorrelationAnalyzer(mock_connection_manager)
        
        config = {'variables': ['only_one_var']}
        
        result = analyzer.analyze('test_model', config)
        
        assert result['passed'] == False
        assert 'error' in result
        assert 'At least 2 variables required' in result['error']
    
    def test_analyze_with_valid_data(self, mock_connection_manager):
        """Test analyse avec données valides"""
        # Mock data avec corrélation
        sample_data = pd.DataFrame({
            'analysis_date': pd.date_range('2024-01-01', periods=30),
            'var1': range(30),
            'var2': [x * 0.8 + 5 for x in range(30)]  # Corrélation ~0.8
        })
        
        mock_connection_manager.execute_query.return_value = sample_data
        
        analyzer = CorrelationAnalyzer(mock_connection_manager)
        
        config = {
            'variables': ['var1', 'var2'],
            'expected_correlation': 0.8,
            'threshold': 0.2
        }
        
        result = analyzer.analyze('test_model', config)
        
        assert 'passed' in result
        assert 'anomalies_count' in result
        assert 'details' in result

