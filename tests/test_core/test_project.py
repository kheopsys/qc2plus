# tests/test_core/test_project.py
"""
Tests pour qc2plus.core.project
"""

import pytest
import yaml
from qc2plus.core.project import QC2PlusProject


class TestQC2PlusProject:
    
    def test_init_project_creates_structure(self, temp_project_dir):
        """Test que init_project crée la bonne structure"""
        project_name = "test_project"
        project_path = temp_project_dir / project_name
        
        project = QC2PlusProject.init_project(str(project_path))
        
        # Vérifier que tous les dossiers sont créés
        assert project_path.exists()
        assert (project_path / "models").exists()
        assert (project_path / "target").exists()
        assert (project_path / "logs").exists()
        
        # Vérifier que les fichiers de config sont créés
        assert (project_path / "qc2plus_project.yml").exists()
        assert (project_path / "profiles.yml").exists()
        assert (project_path / "README.md").exists()
    
    def test_load_existing_project(self, temp_project_dir):
        """Test le chargement d'un projet existant"""
        project_name = "test_project"
        project_path = temp_project_dir / project_name
        
        # Créer le projet
        QC2PlusProject.init_project(str(project_path))
        
        # Le recharger
        loaded_project = QC2PlusProject.load_project(str(project_path))
        
        assert loaded_project.name == project_name
        assert loaded_project.project_dir == project_path
    
    def test_get_models_discovery(self, temp_project_dir, sample_model_config):
        """Test la découverte des modèles"""
        project_path = temp_project_dir / "test_project"
        project = QC2PlusProject.init_project(str(project_path))
        
        # Ajouter un fichier de modèle
        with open(project_path / "models" / "test_model.yml", "w") as f:
            yaml.dump(sample_model_config, f)
        
        models = project.get_models()
        
        assert "customers" in models
        assert models["customers"]["qc2plus_tests"]["level1"] is not None



