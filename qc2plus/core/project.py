"""
2QC+ Project Management
Handles project initialization, configuration, and model discovery
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class ModelConfig:
    """Configuration for a single model"""

    name: str
    qc2plus_tests: Dict[str, Any]
    description: Optional[str] = None
    depends_on: Optional[List[str]] = None


class QC2PlusProject:
    """Main project management class"""

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.name = self.project_dir.name
        self.models_dir = self.project_dir / "models"
        self.target_dir = self.project_dir / "target"

        # Load project configuration
        self.config = self._load_project_config()

    def _load_project_config(self) -> Dict[str, Any]:
        """Load qc2plus_project.yml configuration"""
        config_path = self.project_dir / "qc2plus_project.yml"
        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f) or {}
        return {}

    @classmethod
    def init_project(
        cls, project_name: str, profile_template: str = "postgresql"
    ) -> "QC2PlusProject":
        """Initialize a new 2QC+ project"""
        project_dir = Path(project_name)

        if project_dir.exists():
            raise ValueError(f"Directory {project_name} already exists")

        # Create project structure
        project_dir.mkdir(parents=True)
        (project_dir / "models").mkdir()
        (project_dir / "target").mkdir()
        (project_dir / "logs").mkdir()

        # Create qc2plus_project.yml
        project_config = {
            "name": project_name,
            "version": "1.0.0",
            "profile": project_name,
            "model-paths": ["models"],
            "target-path": "target",
            "log-path": "logs",
            "vars": {},
        }

        with open(project_dir / "qc2plus_project.yml", "w") as f:
            yaml.dump(project_config, f, default_flow_style=False)

        # Create profiles.yml template
        profile_configs = {
            "postgresql": {
                "type": "postgresql",
                "host": "localhost",
                "port": 5432,
                "user": "your_username",
                "password": "your_password",
                "dbname": "your_database",
                "schema": "public",
            },
            "snowflake": {
                "type": "snowflake",
                "account": "your_account",
                "user": "your_username",
                "password": "your_password",
                "role": "your_role",
                "database": "your_database",
                "warehouse": "your_warehouse",
                "schema": "public",
            },
            "bigquery": {
                "type": "bigquery",
                "method": "service-account",
                "project": "your_project",
                "dataset": "your_dataset",
                "keyfile": "path/to/keyfile.json",
                "location": "US",
            },
            "redshift": {
                "type": "redshift",
                "host": "your_cluster.redshift.amazonaws.com",
                "port": 5439,
                "user": "your_username",
                "password": "your_password",
                "dbname": "your_database",
                "schema": "public",
            },
        }

        profiles_config = {
            project_name: {
                "target": "dev",
                "outputs": {
                    "dev": profile_configs[profile_template],
                    "staging": {
                        **profile_configs[profile_template],
                        "schema": "staging",
                    },
                    "prod": {
                        **profile_configs[profile_template],
                        "schema": "prod",
                    },
                },
            }
        }

        with open(project_dir / "profiles.yml", "w") as f:
            yaml.dump(profiles_config, f, default_flow_style=False)

        # Create example model configuration
        example_model = {
            "models": [
                {
                    "name": "customers",
                    "description": "Customer data quality tests",
                    "qc2plus_tests": {
                        "level1": [
                            {
                                "unique": {
                                    "column_name": "customer_id",
                                    "severity": "critical",
                                }
                            },
                            {
                                "not_null": {
                                    "column_name": "email",
                                    "severity": "critical",
                                }
                            },
                            {
                                "email_format": {
                                    "column_name": "email",
                                    "severity": "medium",
                                }
                            },
                            {
                                "statistical_threshold": {
                                    "column_name": "daily_registrations",
                                    "metric": "count",
                                    "threshold_type": "relative",
                                    "threshold_value": 2.0,
                                    "severity": "medium",
                                }
                            },
                        ],
                        "level2": {
                            "correlation_analysis": {
                                "variables": [
                                    "daily_registrations",
                                    "daily_activations",
                                ],
                                "expected_correlation": 0.8,
                                "threshold": 0.2,
                            },
                            "temporal_analysis": {
                                "date_column": "created_at",
                                "metrics": ["count", "avg_revenue"],
                                "seasonality_check": True,
                            },
                            "distribution_analysis": {
                                "segments": [
                                    "country",
                                    "customer_type",
                                ],
                                "metrics": [
                                    "revenue",
                                    "orders_count",
                                ],
                            },
                        },
                    },
                }
            ]
        }

        with open(project_dir / "models" / "customers.yml", "w") as f:
            yaml.dump(example_model, f, default_flow_style=False)

        # Create README
        readme_content = f"""# {project_name}

This is a 2QC+ data quality project.

## Getting Started

1. Configure your database connection in `profiles.yml`
2. Define your models and tests in the `models/` directory
3. Run quality tests:
   ```bash
   qc2plus run --target dev
   ```

## Project Structure

- `models/`: Model configurations with quality tests
- `profiles.yml`: Database connection profiles
- `qc2plus_project.yml`: Project configuration
- `target/`: Compiled tests and results
- `logs/`: Execution logs

## Example Commands

```bash
# Run all tests
qc2plus run

# Run specific model
qc2plus run --models customers

# Run only Level 1 tests
qc2plus run --level 1

# Test connection
qc2plus test-connection --target prod
```

For more information, visit: https://github.com/qc2plus/qc2plus
"""

        with open(project_dir / "README.md", "w") as f:
            f.write(readme_content)

        return cls(str(project_dir))

    @classmethod
    def load_project(cls, project_dir: str = ".") -> "QC2PlusProject":
        """Load an existing 2QC+ project"""
        project_path = Path(project_dir)

        if not (project_path / "qc2plus_project.yml").exists():
            raise ValueError(f"No qc2plus_project.yml found in {project_dir}")

        return cls(str(project_path))

    def get_models(self) -> Dict[str, Dict[str, Any]]:
        """Discover and load all model configurations"""
        models = {}

        for yml_file in self.models_dir.glob("*.yml"):
            try:
                with open(yml_file, "r") as f:
                    config = yaml.safe_load(f)

                if "models" in config:
                    for model_config in config["models"]:
                        model_name = model_config["name"]
                        models[model_name] = model_config
            except Exception as e:
                print(f"Warning: Error loading {yml_file}: {e}")

        return models

    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model"""
        models = self.get_models()
        if model_name in models:
            model_data = models[model_name]
            return ModelConfig(
                name=model_name,
                qc2plus_tests=model_data.get("qc2plus_tests", {}),
                description=model_data.get("description"),
                depends_on=model_data.get("depends_on"),
            )
        return None

    def compile_tests(self) -> Dict[str, Dict[str, str]]:
        """Compile all tests to SQL"""
        from qc2plus.level1.engine import Level1Engine

        compiled_tests = {}
        models = self.get_models()

        # Initialize Level 1 engine (we'll need connection info for proper
        # compilation)
        level1_engine = Level1Engine()

        for model_name, model_config in models.items():
            model_tests = {}

            # Compile Level 1 tests
            level1_tests = model_config.get("qc2plus_tests", {}).get("level1", [])
            for test_config in level1_tests:
                for test_type, test_params in test_config.items():
                    test_name = f"{test_type}_{test_params.get('column_name', 'test')}"
                    try:
                        # This is a simplified compilation - full compilation
                        # needs DB connection
                        sql = level1_engine.compile_test(
                            test_type, test_params, model_name
                        )
                        model_tests[test_name] = sql
                    except Exception as e:
                        model_tests[test_name] = f"-- Compilation error: {str(e)}"

            compiled_tests[model_name] = model_tests

        return compiled_tests

    def validate_config(self) -> List[str]:
        """Validate project configuration and return list of issues"""
        issues = []

        # Check required directories
        if not self.models_dir.exists():
            issues.append("models/ directory not found")

        # Check for model configurations
        models = self.get_models()
        if not models:
            issues.append("No model configurations found in models/")

        # Validate each model config
        for model_name, model_config in models.items():
            if "qc2plus_tests" not in model_config:
                issues.append(f"Model '{model_name}' has no qc2plus_tests defined")
                continue

            tests = model_config["qc2plus_tests"]
            if "level1" not in tests and "level2" not in tests:
                issues.append(f"Model '{model_name}' has no tests defined")

        return issues
