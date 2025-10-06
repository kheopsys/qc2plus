"""
2QC+ Level 1 Engine
Business rule validation with SQL templates
"""

import logging
from typing import Dict, List, Any, Optional
from jinja2 import Environment, BaseLoader
import pandas as pd

from qc2plus.level1.macros import SQL_MACROS, DB_FUNCTIONS
from qc2plus.core.connection import ConnectionManager


class Level1Engine:
    """Level 1 quality test engine for business rule validation"""
    
    def __init__(self, connection_manager: Optional[ConnectionManager] = None):
        self.connection_manager = connection_manager
        self.jinja_env = Environment(loader=BaseLoader())
        
        # Register SQL macros
        for macro_name, macro_template in SQL_MACROS.items():
            self.jinja_env.globals[macro_name] = self._create_macro_function(macro_template)
        
        from qc2plus.level1.macros import build_sample_clause
        self.jinja_env.globals['build_sample_clause'] = build_sample_clause
    
    def _create_macro_function(self, template_str: str):
        """Create a Jinja2 macro function from template string"""
        def macro_function(**kwargs):
            template = self.jinja_env.from_string(template_str)
            return template.render(**kwargs)
        return macro_function
    
    def run_tests(self, model_name: str, level1_tests: List[Dict[str, Any]], model_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run all Level 1 tests for a model"""
        results = {}
        
        for test_config in level1_tests:
            for test_type, test_params in test_config.items():
                test_name = f"{test_type}_{test_params.get('column_name', 'test')}"
                
                try:
                    result = self._run_single_test(model_name, test_type, test_params, model_config=model_config)
                    results[test_name] = result
                except Exception as e:
                    logging.error(f"Test {test_name} failed: {str(e)}")
                    results[test_name] = {
                        'passed': False,
                        'error': str(e),
                        'severity': test_params.get('severity', 'medium')
                    }
        
        return results
    
    def _run_single_test(self, model_name: str, test_type: str, test_params: Dict[str, Any], model_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run a single Level 1 test"""

        # Resolve sampling configuration
        sample_config = self._resolve_sample_config(test_params, model_config)
        
        
        # Generate SQL for the test
        sql = self.compile_test(test_type, test_params, model_name, sample_config=sample_config)
        
        # Prepare base result with new fields
        base_result = {
            'query': sql,  # New field for the executed SQL query
            'explanation': self._get_test_explanation(test_type, test_params),  # New field for human-readable explanation
            'examples': [],  # New field for error examples
            'severity': test_params.get('severity', 'medium')
        }
    
        
        if not self.connection_manager:
            # If no connection manager, return compilation result
            return {
                **base_result,
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
                    **base_result,
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
                # New: Extract examples of errors
                examples = self._extract_examples_from_results(df, test_type, test_params)

                return {
                    **base_result,
                    'examples': df.head(5).to_dict(orient='records'), 
                    'passed': False,
                    'failed_rows': int(failed_rows),
                    'total_rows': int(total_rows),
                    'severity': test_params.get('severity', 'medium'),
                    'message': f'Test failed - {failed_rows} violations found'
                }
                
        except Exception as e:
            return {
                **base_result,
                'passed': False,
                'error': str(e),
                'severity': test_params.get('severity', 'medium'),
                'message': f'Test execution failed: {str(e)}'
            }
    
    def compile_test(self, test_type: str, test_params: Dict[str, Any], model_name: str, sample_config: Optional[Dict[str, Any]] = None) -> str:
        """Compile a test to SQL"""

        if test_type not in SQL_MACROS:
            raise ValueError(f"Unknown test type: {test_type}")

        # Déterminer le type de base de données
        db_type = self.connection_manager.db_type if self.connection_manager else 'postgresql'
        
        # Sélectionner uniquement les fonctions de la DB courante
        db_functions = DB_FUNCTIONS.get(db_type, DB_FUNCTIONS['postgresql'])

        # Préparer le contexte pour le rendu Jinja
        context = {
            'model_name': model_name,
            'column_name': test_params.get('column_name'),
            'schema': self.connection_manager.config.get('schema', 'public') if self.connection_manager else 'public',
            'sample_config': sample_config,
            'db': db_functions,
            **test_params
        }

        # Rendu du SQL
        template = self.jinja_env.from_string(SQL_MACROS[test_type])
        sql = template.render(**context)

        return sql

    def get_available_tests(self) -> List[str]:
        """Get list of available test types"""
        return list(SQL_MACROS.keys())
    
    def get_test_documentation(self, test_type: str) -> Dict[str, Any]:
        """Get documentation for a specific test type"""
        
        test_docs = {
            'unique': {
                'description': 'Tests that a column contains only unique values',
                'parameters': {
                    'column_name': 'Column to test for uniqueness',
                    'severity': 'Test severity (critical, high, medium, low)'
                },
                'example': {
                    'unique': {
                        'column_name': 'customer_id',
                        'severity': 'critical'
                    }
                }
            },
            'not_null': {
                'description': 'Tests that a column contains no null values',
                'parameters': {
                    'column_name': 'Column to test for null values',
                    'severity': 'Test severity (critical, high, medium, low)'
                },
                'example': {
                    'not_null': {
                        'column_name': 'email',
                        'severity': 'critical'
                    }
                }
            },
            'email_format': {
                'description': 'Tests that email addresses follow valid format',
                'parameters': {
                    'column_name': 'Email column to validate',
                    'severity': 'Test severity (critical, high, medium, low)'
                },
                'example': {
                    'email_format': {
                        'column_name': 'email',
                        'severity': 'medium'
                    }
                }
            },
            'relationship': {
                'description': 'Tests referential integrity between tables',
                'parameters': {
                    'column_name': 'Foreign key column',
                    'reference_table': 'Referenced table name',
                    'reference_column': 'Referenced column name',
                    'severity': 'Test severity (critical, high, medium, low)'
                },
                'example': {
                    'foreign_key': {
                        'column_name': 'customer_id',
                        'reference_table': 'customers',
                        'reference_column': 'id',
                        'severity': 'critical'
                    }
                }
            },
            'future_date': {
                'description': 'Tests that date values are not in the future',
                'parameters': {
                    'column_name': 'Date column to test',
                    'severity': 'Test severity (critical, high, medium, low)'
                },
                'example': {
                    'future_date': {
                        'column_name': 'created_at',
                        'severity': 'medium'
                    }
                }
            },
            'statistical_threshold': {
                'description': 'Tests statistical thresholds based on historical data',
                'parameters': {
                    'column_name': 'Column to analyze (optional for aggregations)',
                    'metric': 'Metric to calculate (count, avg, sum, etc.)',
                    'threshold_type': 'Type of threshold (absolute, relative)',
                    'threshold_value': 'Threshold value or multiplier',
                    'window_days': 'Historical window in days (default: 30)',
                    'severity': 'Test severity (critical, high, medium, low)'
                },
                'example': {
                    'statistical_threshold': {
                        'metric': 'count',
                        'threshold_type': 'relative',
                        'threshold_value': 2.0,
                        'window_days': 30,
                        'severity': 'medium'
                    }
                }
            },
            'accepted_benchmark_values': {
                'description': 'Tests that column values match benchmark distribution percentages',
                'parameters': {
                    'column_name': 'Column to test distribution',
                    'benchmark_values': 'Dictionary of value: expected_percentage pairs',
                    'threshold': 'Acceptable deviation from benchmark (0.0-1.0)',
                    'severity': 'Test severity (critical, high, medium, low)'
                },
                'example': {
                    'benchmark_values': {
                        'column_name': 'customer_segment',
                        'benchmark_values': {
                            'Mono-buyer': 50,
                            'Regular-buyer': 40,
                            'VIP-buyer': 10
                        },
                        'threshold': 0.2,
                        'severity': 'critical'
                    }
                }
            }
        }
        
        return test_docs.get(test_type, {'description': 'No documentation available'})
    
    def validate_test_config(self, test_type: str, test_params: Dict[str, Any]) -> List[str]:
        """Validate test configuration and return list of issues"""
        issues = []
        
        # Common validations
        if 'severity' in test_params:
            valid_severities = ['critical', 'high', 'medium', 'low']
            if test_params['severity'] not in valid_severities:
                issues.append(f"Invalid severity: {test_params['severity']}. Must be one of {valid_severities}")
        
        # Test-specific validations
        if test_type in ['unique', 'not_null', 'email_format', 'future_date']:
            if 'column_name' not in test_params:
                issues.append(f"Test {test_type} requires 'column_name' parameter")
        
        elif test_type == 'relationship':
            required_params = ['column_name', 'reference_table', 'reference_column']
            for param in required_params:
                if param not in test_params:
                    issues.append(f"Test {test_type} requires '{param}' parameter")
        
        elif test_type == 'statistical_threshold':
            if 'metric' not in test_params:
                issues.append("Test statistical_threshold requires 'metric' parameter")
            
            if 'threshold_type' not in test_params:
                issues.append("Test statistical_threshold requires 'threshold_type' parameter")
            elif test_params['threshold_type'] not in ['absolute', 'relative']:
                issues.append("threshold_type must be 'absolute' or 'relative'")
            
            if 'threshold_value' not in test_params:
                issues.append("Test statistical_threshold requires 'threshold_value' parameter")

        elif test_type == 'accepted_benchmark_values':
            required_params = ['column_name', 'benchmark_values', 'threshold']
            print('start')
            for param in required_params:
                if param not in test_params:
                    issues.append(f"Test {test_type} requires '{param}' parameter")
            
            # Validate benchmark_values format
            if 'accepted_benchmark_values' in test_params:
                benchmark_values = test_params['benchmark_values']
                if not isinstance(benchmark_values, dict):
                    issues.append("benchmark_values must be a dictionary")
                else:
                    # Check that percentages sum to ~100%
                    total_pct = sum(benchmark_values.values())
                    if abs(total_pct - 100) > 5:  # Allow 5% tolerance
                        issues.append(f"benchmark_values percentages should sum to ~100% (got {total_pct}%)")
            
            # Validate threshold
            if 'threshold' in test_params:
                threshold = test_params['threshold']
                if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
                    issues.append("threshold must be a number between 0 and 1")
        
        return issues
    def _get_test_explanation(self, test_type: str, test_params: Dict[str, Any]) -> str:
        """Generate human-readable explanation for a test"""
        
        explanations = {
            'unique': f"Verifies that column '{test_params.get('column_name', 'N/A')}' contains only unique values. Duplicates may indicate data entry errors or process issues.",
            
            'not_null': f"Verifies that column '{test_params.get('column_name', 'N/A')}' contains no empty (NULL) values. Missing values can compromise data integrity.",
            
            'email_format': f"Verifies that column '{test_params.get('column_name', 'N/A')}' contains valid email addresses in name@domain.com format. Values like 'Lyon' or 'Paris' are not valid emails.",
            
            'relationship': f"Verifies referential integrity between column '{test_params.get('column_name', 'N/A')}' and reference table '{test_params.get('reference_table', 'N/A')}'. Each value must exist in the reference table.",
            
            'future_date': f"Verifies that column '{test_params.get('column_name', 'N/A')}' does not contain future dates. Future dates may indicate data entry errors or synchronization issues.",
            
            'accepted_values': f"Verifies that column '{test_params.get('column_name', 'N/A')}' contains only authorized values. Non-compliant values may indicate data entry errors.",
            
            'statistical_threshold': f"Verifies that metric '{test_params.get('metric', 'N/A')}' respects statistical thresholds based on the last {test_params.get('window_days', 30)} days of historical data.",
            
            'accepted_benchmark_values': f"Verifies that the distribution of values in '{test_params.get('column_name', 'N/A')}' matches expected reference percentages with a tolerance of {test_params.get('threshold', 0)*100}%.",
            
            'freshness': f"Verifies that data in column '{test_params.get('column_name', 'N/A')}' is not too old (more than {test_params.get('max_age_days', 'N/A')} days)."
        }
        
        return explanations.get(test_type, f"Test de qualité de type '{test_type}' sur le modèle de données.")
    
    def _extract_examples_from_results(self, df: pd.DataFrame, test_type: str, test_params: Dict[str, Any]) -> List[str]:
        """Extract examples of errors from test results"""
        
        examples = []
        max_examples = 10  
        
        try:
            # Extraction example logic based on test type
            if test_type in ['unique', 'not_null', 'email_format', 'future_date']:
            
                column_name = test_params.get('column_name', '')
                
                if column_name in df.columns:
                    unique_values = df[column_name].dropna().unique()[:max_examples]
                    examples = [str(val) for val in unique_values]
                
                elif 'invalid_value' in df.columns:
                    unique_values = df['invalid_value'].dropna().unique()[:max_examples]
                    examples = [str(val) for val in unique_values]
                
                elif len(df.columns) > 0:
                    first_col = df.columns[0]
                    unique_values = df[first_col].dropna().unique()[:max_examples]
                    examples = [str(val) for val in unique_values]
            
            elif test_type == 'relationship':
                column_name = test_params.get('column_name', '')
                if column_name in df.columns:
                    unique_values = df[column_name].dropna().unique()[:max_examples]
                    examples = [f"ID orphelin: {val}" for val in unique_values]
            
            elif test_type == 'accepted_benchmark_values':
                if 'value' in df.columns and 'actual_pct' in df.columns and 'expected_pct' in df.columns:
                    for _, row in df.head(max_examples).iterrows():
                        examples.append(f"{row['value']}: {row['actual_pct']:.1f}% (attendu: {row['expected_pct']:.1f}%)")
            
            elif test_type == 'statistical_threshold':
                if 'current_value' in df.columns and 'threshold_value' in df.columns:
                    row = df.iloc[0]
                    examples.append(f"Valeur actuelle: {row['current_value']}, Seuil: {row['threshold_value']}")
        
        except Exception as e:
            logging.warning(f"Could not extract examples for test {test_type}: {str(e)}")
            if len(df) > 0 and len(df.columns) > 0:
                first_col = df.columns[0]
                examples = [str(val) for val in df[first_col].head(max_examples).tolist()]
        
        return examples
    

    def _resolve_sample_config(self, test_config: Dict[str, Any], 
                          model_config: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Resolve sampling configuration for a test"""
        
        # 1. Test-specific sample config (highest priority)
        if 'sample' in test_config:
            if test_config['sample'] is None or test_config['sample'] is False:
                return None  # Explicitly disable sampling
            return test_config['sample']
        
        # 2. Model-level sample config
        if model_config and 'sample' in model_config:
            return model_config['sample']
        
        # 3. No sampling
        return None
