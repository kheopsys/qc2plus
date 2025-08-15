# tests/conftest.py
"""
Configuration pytest pour 2QC+ tests
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock
import pandas as pd


@pytest.fixture
def temp_project_dir():
    """Crée un répertoire temporaire pour les tests"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_connection_manager():
    """Mock du gestionnaire de connexion DB"""
    mock = Mock()
    mock.execute_query.return_value = pd.DataFrame()
    mock.execute_sql.return_value = Mock()
    mock.test_connection.return_value = True
    mock.config = {'schema': 'public'}
    mock.db_type = 'postgresql'
    return mock


@pytest.fixture
def sample_model_config():
    """Configuration d'exemple pour les tests"""
    return {
        'models': [{
            'name': 'customers',
            'qc2plus_tests': {
                'level1': [
                    {'unique': {'column_name': 'customer_id', 'severity': 'critical'}},
                    {'not_null': {'column_name': 'email', 'severity': 'critical'}}
                ],
                'level2': {
                    'correlation_analysis': {
                        'variables': ['registrations', 'activations'],
                        'expected_correlation': 0.8
                    }
                }
            }
        }]
    }



