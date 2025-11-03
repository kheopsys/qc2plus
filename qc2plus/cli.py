"""
2QC+ Command Line Interface
Similar to dbt CLI for ease of use
"""

import os
import sys
from pathlib import Path

import click
from qc2plus import __version__  
import yaml

from qc2plus.core.connection import ConnectionManager
from qc2plus.core.project import QC2PlusProject
from qc2plus.core.runner import QC2PlusRunner


@click.group()
@click.version_option(version=__version__, prog_name="qc2plus")
def cli():
    """2QC+ Data Quality Automation Framework"""
    pass


@cli.command()
@click.argument("project_name")
@click.option(
    "--profile-template",
    default="postgresql",
    type=click.Choice(["postgresql", "snowflake", "bigquery", "redshift"]),
    help="Database profile template to use",
)
def init(project_name: str, profile_template: str):
    """Initialize a new 2QC+ project"""
    try:
        project = QC2PlusProject.init_project(project_name, profile_template)
        click.echo(f"✅ Successfully initialized 2QC+ project: {project_name}")
        click.echo(f"📁 Project created at: {os.path.abspath(project_name)}")
        click.echo(
            f"🔧 Edit {project_name}/profiles.yml to configure your database connection"
        )
        click.echo(f"📋 Add your models in {project_name}/models/ directory")
    except Exception as e:
        click.echo(f"❌ Error initializing project: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--models",
    multiple=True,
    help="Specific models to run (default: all)",
)
@click.option(
    "--level",
    type=click.Choice(["1", "2", "all"]),
    default="all",
    help="Quality control level to run",
)
@click.option("--target", default="dev", help="Target environment")
@click.option(
    "--profiles-dir",
    default=".",
    help="Directory containing profiles.yml",
)
@click.option("--project-dir", default=".", help="Project directory")
@click.option("--fail-fast", is_flag=True, help="Stop on first failure")
@click.option(
    "--threads",
    default=1,
    type=int,
    help="Number of parallel threads",
)
def run(
    models: tuple,
    level: str,
    target: str,
    profiles_dir: str,
    project_dir: str,
    fail_fast: bool,
    threads: int,
):
    """Run 2QC+ quality tests"""
    try:
        # Load project
        project = QC2PlusProject.load_project(project_dir)
        click.echo("")
        click.echo(f"🚀 Running 2QC+ for project: {project.name}")

        # Initialize runner
        runner = QC2PlusRunner(project, target, profiles_dir)

        # Run tests
        results = runner.run(
            models=list(models) if models else None,
            level=level,
            fail_fast=fail_fast,
            threads=threads,
        )

        # Display results
        _display_results(results)

        # Exit with appropriate code
        if results["status"] == "success":
            click.echo("✅ All tests passed!")
            sys.exit(0)
        else:
            click.echo("Final result")
            click.echo("❌ Some tests failed!")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error running tests: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--target", default="dev", help="Target environment")
@click.option(
    "--profiles-dir",
    default=".",
    help="Directory containing profiles.yml",
)
def test_connection(target: str, profiles_dir: str):
    """Test database connection"""
    try:
        # Load profiles
        profiles_path = Path(profiles_dir) / "profiles.yml"
        if not profiles_path.exists():
            click.echo(f"❌ profiles.yml not found in {profiles_dir}")
            sys.exit(1)

        with open(profiles_path, "r") as f:
            profiles = yaml.safe_load(f)

        # Test connection
        conn_manager = ConnectionManager(profiles, target)
        success = conn_manager.test_connection()

        if success:
            click.echo("✅ All database connections successful!")
        else:
            click.echo("❌ Some database connections failed!")
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Connection test failed: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--project-dir", default=".", help="Project directory")
def compile(project_dir: str):
    """Compile 2QC+ models and tests"""
    try:
        project = QC2PlusProject.load_project(project_dir)
        click.echo(f"🔧 Compiling 2QC+ project: {project.name}")

        compiled_tests = project.compile_tests()
        click.echo(f"✅ Compiled {len(compiled_tests)} tests")

        # Save compiled tests for inspection
        compiled_dir = Path(project_dir) / "target" / "compiled"
        compiled_dir.mkdir(parents=True, exist_ok=True)

        for model_name, tests in compiled_tests.items():
            model_file = compiled_dir / f"{model_name}.sql"
            with open(model_file, "w") as f:
                f.write(f"-- Compiled tests for {model_name}\n\n")
                for test_name, test_sql in tests.items():
                    f.write(f"-- Test: {test_name}\n{test_sql}\n\n")

        click.echo(f"📁 Compiled tests saved to: {compiled_dir}")

    except Exception as e:
        click.echo(f"❌ Error compiling tests: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--project-dir", default=".", help="Project directory")
@click.option(
    "--output-format",
    default="table",
    type=click.Choice(["table", "json", "yaml"]),
    help="Output format",
)
def list_models(project_dir: str, output_format: str):
    """List all models in the project"""
    try:
        project = QC2PlusProject.load_project(project_dir)
        models = project.get_models()

        if output_format == "table":
            click.echo(f"Models in project '{project.name}':")
            click.echo("-" * 50)
            for model_name, model_config in models.items():
                tests_count = len(
                    model_config.get("qc2plus_tests", {}).get("level1", [])
                ) + (1 if model_config.get("qc2plus_tests", {}).get("level2") else 0)
                click.echo(f"📊 {model_name:<30} ({tests_count} tests)")
        elif output_format == "json":
            import json

            click.echo(json.dumps(models, indent=2))
        elif output_format == "yaml":
            click.echo(yaml.dump(models, default_flow_style=False))

    except Exception as e:
        click.echo(f"❌ Error listing models: {str(e)}", err=True)
        sys.exit(1)


def _display_results(results: dict):
    """Display test results in a formatted way"""
    # click.echo("\n" + "="*40)
    click.echo("2QC+ TEST RESULTS")
    # click.echo("="*40)

    # Summary
    total_tests = results.get("total_tests", 0)
    passed_tests = results.get("passed_tests", 0)
    failed_tests = results.get("failed_tests", 0)

    click.echo(f"📊 Total tests: {total_tests}")
    click.echo(f"✅ Passed: {passed_tests}")
    click.echo(f"❌ Failed: {failed_tests}")
    click.echo(
        f"📈 Success rate: {(passed_tests / total_tests) * 100:.1f}%"
        if total_tests > 0
        else "No tests run"
    )

    # Detailed results by model
    for model_name, model_results in results.get("models", {}).items():
        click.echo(f"\n📋 Model: {model_name}")
        # click.echo("-" * 40)

        # Level 1 results
        if model_results.get("level1"):
            click.echo("  Level 1 (Business Rules):")
            for test_name, test_result in model_results["level1"].items():
                status = "✅" if test_result["passed"] else "❌"
                click.echo(f"    {status} {test_name}")
                if not test_result["passed"] and "message" in test_result:
                    click.echo(f"      └─ {test_result['message']}")

        # Level 2 results
        if model_results.get("level2"):
            click.echo("  Level 2 (ML Anomalies):")
            for analyzer_name, analyzer_result in model_results["level2"].items():
                status = "✅" if analyzer_result["passed"] else "⚠️"
                anomalies = analyzer_result.get("anomalies_count", 0)
                click.echo(f"    {status} {analyzer_name} ({anomalies} anomalies)")


def main():
    """Entry point for the CLI"""
    cli()


if __name__ == "__main__":
    main()
