"""
2QC+ Level 1 Engine
Business rule validation with SQL templates
"""

import logging
from typing import Dict, List, Any, Optional
from jinja2 import Environment, BaseLoader
import pandas as pd

from qc2plus.level1.macros import SQL_MACROS
from qc2plus.core.connection import ConnectionManager


class Level1Engine:
    """Level 1 quality test engine for business rule validation"""
    
    def __init__(self, connection_manager: Optional[ConnectionManager] = None):
        self.connection_manager = connection_manager
        self.jinja_env = Environment(loader=BaseLoader())
        
        # Register SQL macros
        for macro_name, macro_template in SQL_MACROS.items():
            self.jinja_env.globals[macro_name] = self._create_macro_function(macro_template)
    
    def _create_macro_function(self, template_str: str):
        """Create a Jinja2 macro function from template string"""
        def macro_function(**kwargs):
            template = self.jinja_env.from_string(template_str)
            return template.render(**kwargs)
        return macro_function
    
    def run_tests(self, model_name: str, level1_tests: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run all Level 1 tests for a model"""
        results = {}
        
        for test_config in level1_tests:
            for test_type, test_params in test_config.items():
                test_name = f"{test_type}_{test_params.get('column_name', 'test')}"
                
                try:
                    result = self._run_single_test(model_name, test_type, test_params)
                    results[test_name] = result
                except Exception as e:
                    logging.error(f"Test {test_name} failed: {str(e)}")
                    results[test_name] = {
                        'passed': False,
                        'error': str(e),
                        'severity': test_params.get('severity', 'medium')
                    }
        
        return results
    
    def _run_single_test(self, model_name: str, test_type: str, test_params: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single Level 1 test"""
        
        # Generate SQL for the test
        sql = self.compile_test(test_type, test_params, model_name)
        
        if not self.connection_manager:
            # If no connection manager, return compilation result
            return {
                'passed': True,
                'sql': sql,
                'severity': test_params.get('severity', 'medium'),
                'message': 'Test compiled successfully (not executed)'
            }
        
        # Execute the test
        try:
            df = self.connection_manager.execute_query(sql)
            
            # Analyze results
            if len(df) == 0:
                # No results means test passed (no violations found)
                return {
                    'passed': True,
                    'failed_rows': 0,
                    'total_rows': 0,
                    'severity': test_params.get('severity', 'medium'),
                    'message': 'Test passed - no violations found'
                }
            else:
                # Results found means test failed (violations detected)
                failed_rows = df.iloc[0].get('failed_rows', len(df))
                total_rows = df.iloc[0].get('total_rows', failed_rows)
                
                return {
                    'passed': False,
                    'failed_rows': int(failed_rows),
                    'total_rows': int(total_rows),
                    'severity': test_params.get('severity', 'medium'),
                    'message': f'Test failed - {failed_rows} violations found'
                }
                
        except Exception as e:
            return {
                'passed': False,
                'error': str(e),
                'severity': test_params.get('severity', 'medium'),
                'message': f'Test execution failed: {str(e)}'
            }
    
    def compile_test(self, test_type: str, test_params: Dict[str, Any], model_name: str) -> str:
        """Compile a test to SQL"""
        
        if test_type not in SQL_MACROS:
            raise ValueError(f"Unknown test type: {test_type}")
        
        # Get database adapter for SQL dialect adaptation
        db
