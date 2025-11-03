# project

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
