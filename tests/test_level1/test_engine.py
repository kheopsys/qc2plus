# tests/test_level1/test_engine.py
"""
Tests pour qc2plus.level1.engine
"""

import pytest
from qc2plus.level1.engine import Level1Engine


class TestLevel1Engine:
    
    def test_sql_compilation_unique(self):
        """Test compilation SQL pour test unique"""
        engine = Level1Engine()
        
        sql = engine.compile_test(
            'unique',
            {'column_name': 'customer_id', 'severity': 'critical'},
            'customers'
        )
        
        assert 'SELECT' in sql.upper()
        assert 'customer_id' in sql
        assert 'customers' in sql
        assert 'GROUP BY' in sql.upper()
        assert 'HAVING COUNT(*) > 1' in sql
    
    def test_sql_compilation_not_null(self):
        """Test compilation SQL pour test not_null"""
        engine = Level1Engine()
        
        sql = engine.compile_test(
            'not_null',
            {'column_name': 'email', 'severity': 'critical'},
            'customers'
        )
        
        assert 'IS NULL' in sql.upper()
        assert 'email' in sql
        assert 'customers' in sql
    
    def test_available_tests_list(self):
        """Test liste des tests disponibles"""
        engine = Level1Engine()
        available_tests = engine.get_available_tests()
        
        expected_tests = [
            'unique', 'not_null', 'email_format', 
            'relationship', 'future_date', 'statistical_threshold'
        ]
        
        for test in expected_tests:
            assert test in available_tests
    
    def test_run_tests_with_mock_db(self, mock_connection_manager):
        """Test exécution des tests avec DB mockée"""
        engine = Level1Engine(mock_connection_manager)
        
        test_configs = [
            {'unique': {'column_name': 'customer_id', 'severity': 'critical'}},
            {'not_null': {'column_name': 'email', 'severity': 'critical'}}
        ]
        
        results = engine.run_tests('customers', test_configs)
        
        assert 'unique_customer_id' in results
        assert 'not_null_email' in results
        assert results['unique_customer_id']['passed'] == True


