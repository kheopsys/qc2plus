# QC2Plus Documentation

Complete reference documentation for all QC2Plus classes, methods, and parameters.

---

## Table of Contents

1. [Core Classes](#core-classes)
2. [Level 1 Tests](#level-1-tests)
3. [Level 2 Analyzers](#level-2-analyzers)
4. [Connection Management](#connection-management)
5. [Alerting](#alerting)
6. [CLI Reference](#cli-reference)

---

## Core Classes

### QC2PlusProject

Main project management class for initializing and loading QC2Plus projects.

**Class**: `qc2plus.core.project.QC2PlusProject`

#### Methods

##### `__init__(project_dir)`

Initialize a QC2Plus project.

**Parameters:**
- `project_dir` : str
  - Path to the project directory
  - Must contain `qc2plus_project.yml`

**Example:**
```python
from qc2plus.core.project import QC2PlusProject

project = QC2PlusProject('/path/to/project')
```

---

##### `init_project(project_name, profile_template='postgresql')`

Class method to initialize a new project.

**Parameters:**
- `project_name` : str
  - Name of the project to create
- `profile_template` : str, default='postgresql'
  - Database type template
  - Options: 'postgresql', 'snowflake', 'bigquery', 'redshift'

**Returns:**
- `QC2PlusProject` instance

**Example:**
```python
project = QC2PlusProject.init_project(
    'my_quality_project',
    profile_template='snowflake'
)
```

---

##### `get_models()`

Get all model configurations from the project.

**Returns:**
- `dict` : Dictionary of model configurations
  - Keys: model names
  - Values: model configuration dicts

**Example:**
```python
models = project.get_models()
for name, config in models.items():
    print(f"Model: {name}")
    print(f"Tests: {config.get('qc2plus_tests', {})}")
```

---

##### `validate_config()`

Validate project configuration.

**Returns:**
- `list` : List of validation issues (empty if valid)

**Example:**
```python
issues = project.validate_config()
if issues:
    print("Configuration issues found:")
    for issue in issues:
        print(f"  - {issue}")
```

---

### QC2PlusRunner

Main test runner for executing quality tests.

**Class**: `qc2plus.core.runner.QC2PlusRunner`

#### Methods

##### `__init__(project, target, profiles_dir='.')`

Initialize the test runner.

**Parameters:**
- `project` : QC2PlusProject
  - Project instance
- `target` : str
  - Target environment ('dev', 'staging', 'prod')
- `profiles_dir` : str, default='.'
  - Directory containing profiles.yml

**Example:**
```python
from qc2plus.core.runner import QC2PlusRunner

runner = QC2PlusRunner(
    project=project,
    target='dev',
    profiles_dir='/path/to/profiles'
)
```

---

##### `run(models=None, level='all', fail_fast=False, threads=1)`

Run quality tests.

**Parameters:**
- `models` : list of str, optional
  - List of model names to test
  - If None, tests all models
- `level` : str, default='all'
  - Test level to run
  - Options: '1', '2', 'all'
- `fail_fast` : bool, default=False
  - Stop execution on first critical failure
- `threads` : int, default=1
  - Number of parallel threads for execution
  - Range: 1-16 (recommended: 1-8)

**Returns:**
- `dict` : Test results dictionary
  ```python
  {
      'run_id': str,           # Unique run identifier
      'status': str,           # 'success', 'failure', 'critical_failure'
      'total_tests': int,      # Total number of tests run
      'passed_tests': int,     # Number of passed tests
      'failed_tests': int,     # Number of failed tests
      'critical_failures': int,# Number of critical failures
      'models': dict,          # Results by model
      'execution_time': float, # Start timestamp
      'execution_duration': int,# Duration in seconds
      'target': str            # Target environment
  }
  ```

**Example:**
```python
# Run all tests
results = runner.run()

# Run specific models with parallel execution
results = runner.run(
    models=['customers', 'orders'],
    level='all',
    threads=4
)

# Run only Level 1 tests with fail-fast
results = runner.run(
    level='1',
    fail_fast=True
)
```

---

## Level 1 Tests

### Test Configuration Format

All Level 1 tests are defined in YAML with this structure:

```yaml
models:
  - name: model_name
    qc2plus_tests:
      level1:
        - test_type:
            parameter1: value1
            parameter2: value2
            severity: critical  # or 'high', 'medium', 'low'
```

### Common Parameters

All Level 1 tests support these parameters:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `severity` | str | No | 'medium' | Test severity: 'critical', 'high', 'medium', 'low' |

---

### unique

Ensures column values are unique.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `column_name` | str | Yes | - | Column to check for uniqueness |
| `severity` | str | No | 'medium' | Severity level |

**Example:**
```yaml
- unique:
    column_name: customer_id
    severity: critical
```

**SQL Generated:**
```sql
SELECT column_name, COUNT(*) as duplicate_count
FROM schema.model_name
WHERE column_name IS NOT NULL
GROUP BY column_name
HAVING COUNT(*) > 1
```

---

### not_null

Ensures column has no null values.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `column_name` | str | Yes | - | Column to check for nulls |
| `severity` | str | No | 'medium' | Severity level |

**Example:**
```yaml
- not_null:
    column_name: email
    severity: critical
```

**SQL Generated:**
```sql
SELECT COUNT(*) as null_count
FROM schema.model_name
WHERE column_name IS NULL
```

---

### email_format

Validates email format using regex.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `column_name` | str | Yes | - | Email column to validate |
| `severity` | str | No | 'medium' | Severity level |

**Example:**
```yaml
- email_format:
    column_name: email
    severity: high
```

**SQL Generated:**
```sql
SELECT COUNT(*) as invalid_count
FROM schema.model_name
WHERE column_name IS NOT NULL
  AND column_name !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
```

---

### relationship

Checks referential integrity between tables.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `column_name` | str | Yes | - | Foreign key column |
| `reference_table` | str | Yes | - | Referenced table name |
| `reference_column` | str | Yes | - | Referenced column name |
| `severity` | str | No | 'medium' | Severity level |

**Example:**
```yaml
- relationship:
    column_name: customer_id
    reference_table: customers
    reference_column: id
    severity: critical
```

**SQL Generated:**
```sql
SELECT COUNT(*) as orphan_count
FROM schema.model_name m
LEFT JOIN schema.reference_table r ON m.column_name = r.reference_column
WHERE r.reference_column IS NULL AND m.column_name IS NOT NULL
```

---

### accepted_values

Validates values against a whitelist.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `column_name` | str | Yes | - | Column to validate |
| `accepted_values` | list | Yes | - | List of allowed values |
| `severity` | str | No | 'medium' | Severity level |

**Example:**
```yaml
- accepted_values:
    column_name: status
    accepted_values: ['active', 'inactive', 'pending']
    severity: high
```

**SQL Generated:**
```sql
SELECT COUNT(*) as invalid_count
FROM schema.model_name
WHERE column_name NOT IN ('active', 'inactive', 'pending')
  AND column_name IS NOT NULL
```

---

### range_check

Validates numeric values are within a range.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `column_name` | str | Yes | - | Numeric column to check |
| `min_value` | float | No | None | Minimum allowed value (inclusive) |
| `max_value` | float | No | None | Maximum allowed value (inclusive) |
| `severity` | str | No | 'medium' | Severity level |

**Example:**
```yaml
- range_check:
    column_name: age
    min_value: 0
    max_value: 120
    severity: medium
```

**SQL Generated:**
```sql
SELECT COUNT(*) as out_of_range_count
FROM schema.model_name
WHERE (column_name < 0 OR column_name > 120)
  AND column_name IS NOT NULL
```

---

### future_date

Ensures dates are not in the future.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `column_name` | str | Yes | - | Date column to check |
| `severity` | str | No | 'medium' | Severity level |

**Example:**
```yaml
- future_date:
    column_name: birth_date
    severity: high
```

**SQL Generated:**
```sql
SELECT COUNT(*) as future_date_count
FROM schema.model_name
WHERE column_name > CURRENT_DATE
```

---

### statistical_threshold

Detects statistical anomalies in aggregated metrics.

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `column_name` | str | Yes | - | Column to aggregate (optional for count) |
| `metric` | str | Yes | - | Aggregation: 'count', 'sum', 'avg', 'min', 'max' |
| `threshold_type` | str | Yes | - | 'relative' (std dev) or 'absolute' (fixed) |
| `threshold_value` | float | Yes | - | Threshold value (std devs or absolute) |
| `window_days` | int | No | 30 | Historical window in days |
| `severity` | str | No | 'medium' | Severity level |

**Example:**
```yaml
- statistical_threshold:
    column_name: daily_registrations
    metric: count
    threshold_type: relative
    threshold_value: 2.0
    window_days: 30
    severity: high
```

**Logic:**
- `relative`: Current value > (mean + threshold_value * std_dev)
- `absolute`: Current value > threshold_value

**SQL Generated:**
```sql
WITH historical_data AS (
  SELECT DATE(created_at) as date, COUNT(*) as metric_value
  FROM schema.model_name
  WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
  GROUP BY DATE(created_at)
),
stats AS (
  SELECT 
    AVG(metric_value) as mean_value,
    STDDEV(metric_value) as std_value
  FROM historical_data
),
current_value AS (
  SELECT COUNT(*) as current_metric
  FROM schema.model_name
  WHERE DATE(created_at) = CURRENT_DATE
)
SELECT 
  CASE 
    WHEN current_metric > (mean_value + 2.0 * std_value) THEN 1
    ELSE 0
  END as is_anomaly
FROM current_value, stats
```

---

## Level 2 Analyzers

### CorrelationAnalyzer

Detects changes in variable relationships over time.

**Class**: `qc2plus.level2.correlation.CorrelationAnalyzer`

#### Configuration

```yaml
correlation_analysis:
  variables: list              # Required: List of 2+ numeric columns
  expected_correlation: float  # Required: Expected correlation (-1 to 1)
  threshold: float            # Required: Acceptable deviation (0 to 1)
  correlation_type: str       # Optional: 'pearson' or 'spearman', default='pearson'
  window_days: int           # Optional: Analysis window, default=90
  min_samples: int           # Optional: Minimum rows required, default=30
```

#### Parameters

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `variables` | list[str] | Yes | - | 2+ columns | Numeric columns to analyze |
| `expected_correlation` | float | Yes | - | -1.0 to 1.0 | Expected correlation coefficient |
| `threshold` | float | Yes | - | 0.0 to 1.0 | Acceptable deviation from expected |
| `correlation_type` | str | No | 'pearson' | 'pearson', 'spearman' | Type of correlation |
| `window_days` | int | No | 90 | 7-365 | Days of historical data to analyze |
| `min_samples` | int | No | 30 | 10-1000 | Minimum rows for valid analysis |

#### Example

```yaml
level2:
  correlation_analysis:
    variables: [marketing_spend, revenue, conversions]
    expected_correlation: 0.8
    threshold: 0.2
    correlation_type: pearson
    window_days: 60
    min_samples: 50
```

#### Result Format

```python
{
    'passed': bool,              # True if all correlations within threshold
    'anomalies_count': int,      # Number of anomalies detected
    'message': str,              # Human-readable summary
    'details': {
        'static_correlation': {
            'correlations': {
                ('var1', 'var2'): float,  # Correlation coefficient
                ...
            },
            'anomalies': [
                {
                    'variable_pair': str,
                    'correlation': float,
                    'expected_correlation': float,
                    'deviation': float,
                    'severity': str,
                    'reason': str
                },
                ...
            ]
        },
        'temporal_correlation': {
            'correlations_over_time': {
                ('var1', 'var2'): [float, ...],  # Time series
                ...
            },
            'anomalies': [
                {
                    'variable_pair': str,
                    'anomaly_type': str,  # 'sudden_change', 'high_volatility', 'degradation'
                    'correlation_std': float,
                    'recent_change': float,
                    'severity': str
                },
                ...
            ]
        }
    }
}
```

---

### TemporalAnalyzer

Identifies time series anomalies and pattern changes.

**Class**: `qc2plus.level2.temporal.TemporalAnalyzer`

#### Configuration

```yaml
temporal_analysis:
  date_column: str            # Required: Date/timestamp column
  metrics: list               # Required: Metrics to analyze
  seasonality_check: bool     # Optional: Check for seasonal patterns, default=True
  window_days: int           # Optional: Analysis window, default=90
  min_samples: int           # Optional: Minimum rows, default=30
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `date_column` | str | Yes | - | Date or timestamp column name |
| `metrics` | list[str] | Yes | - | Numeric columns or aggregations: 'count', 'avg_column', 'sum_column' |
| `seasonality_check` | bool | No | True | Detect seasonal patterns (weekly, monthly) |
| `window_days` | int | No | 90 | Days of historical data |
| `min_samples` | int | No | 30 | Minimum data points required |

#### Example

```yaml
level2:
  temporal_analysis:
    date_column: order_date
    metrics: [count , avg_revenue, sum_quantity]
    seasonality_check: true
    window_days: 180
    min_samples: 60
```

#### Result Format

```python
{
    'passed': bool,
    'anomalies_count': int,
    'message': str,
    'details': {
        'individual_analyses': {
            'metric_name': {
                'trend': str,          # 'increasing', 'decreasing', 'stable'
                'seasonality': {
                    'detected': bool,
                    'period': int,     # Days
                    'strength': float  # 0-1
                },
                'anomalies': [
                    {
                        'date': str,
                        'value': float,
                        'expected': float,
                        'z_score': float,
                        'type': str,   # 'spike', 'drop', 'level_shift'
                        'severity': str
                    },
                    ...
                ]
            },
            ...
        }
    }
}
```

---

### DistributionAnalyzer

Compares distributions across segments and time.

**Class**: `qc2plus.level2.distribution.DistributionAnalyzer`

#### Configuration

```yaml
distribution_analysis:
  segments: list              # Required: Categorical columns for segmentation
  metrics: list               # Required: Numeric metrics to compare
  comparison_window: int      # Optional: Days to compare, default=30
  reference_window: int       # Optional: Reference period days, default=90 
  date_column: str            # Rquired : Date Column used for comparison
  min_samples_per_segment: int # Optional: Min samples, default=30
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `segments` | list[str] | Yes | - | Categorical columns (country, type, etc.) |
| `metrics` | list[str] | Yes | - | Numeric metrics to compare across segments |
| `comparison_window` | int | No | 30 | Recent period to compare (days) |
| `reference_window` | int | No | 90 | Historical reference period (days) |
| `min_samples_per_segment` | int | No | 30 | Minimum samples per segment |

#### Example

```yaml
level2:
  distribution_analysis:
    segments: [country, customer_type, subscription_tier]
    metrics: [revenue, lifetime_value, churn_rate]
    comparison_window: 30
    reference_window: 90
    min_samples_per_segment: 50
    date_column: order_date
```

#### Result Format

```python
{
    'passed': bool,
    'anomalies_count': int,
    'message': str,
    'details': {
        'individual_analyses': {
            'segment_column': {
                'segment_values': list,
                'metric_distributions': {
                    'metric_name': {
                        'segment_value': {
                            'mean': float,
                            'median': float,
                            'std': float
                        },
                        ...
                    }
                },
                'anomalies': [
                    {
                        'segment_value': str,
                        'metric': str,
                        'shift_magnitude': float,
                        'p_value': float,
                        'severity': str
                    },
                    ...
                ]
            }
        },
        'cross_segment_analysis': {
            'concentration_changes': [...],
            'anomalies': [...]
        }
    }
}
```

---

## Connection Management

### ConnectionManager

Manages database connections with support for multiple database types.

**Class**: `qc2plus.core.connection.ConnectionManager`

#### Methods

##### `__init__(profiles, target)`

**Parameters:**
- `profiles` : dict
  - Loaded profiles configuration
- `target` : str
  - Target environment name

**Example:**
```python
import yaml
from qc2plus.core.connection import ConnectionManager

with open('profiles.yml') as f:
    profiles = yaml.safe_load(f)

conn_manager = ConnectionManager(profiles, 'dev')
```

---

##### `execute_query(query, params=None, use_data_source=True)`

Execute a query and return results as DataFrame.

**Parameters:**
- `query` : str
  - SQL query to execute
- `params` : dict, optional
  - Query parameters for prepared statements
- `use_data_source` : bool, default=True
  - If True, use data source; if False, use quality database

**Returns:**
- `pandas.DataFrame` : Query results

**Example:**
```python
# Simple query
df = conn_manager.execute_query("SELECT * FROM customers LIMIT 10")

# Parameterized query
df = conn_manager.execute_query(
    "SELECT * FROM customers WHERE country = :country",
    params={'country': 'US'}
)

# Query quality database
df = conn_manager.execute_query(
    "SELECT * FROM quality_test_results",
    use_data_source=False
)
```

---

##### `test_connection()`

Test database connection.

**Returns:**
- `bool` : True if connection successful

**Example:**
```python
if conn_manager.test_connection():
    print("Connection successful!")
else:
    print("Connection failed!")
```

---

##### `create_quality_tables()`

Create quality monitoring tables.

Creates three tables:
- `quality_test_results`
- `quality_run_summary`
- `quality_anomalies`

**Example:**
```python
conn_manager.create_quality_tables()
```

---

## Alerting

### AlertManager

Manages multi-channel alerting for test results.

**Class**: `qc2plus.alerting.alerts.AlertManager`

#### Configuration

```yaml
alerting:
  enabled_channels: [email, slack, teams]
  
  thresholds:
    critical_failure_threshold: int    # Min critical failures to alert
    failure_rate_threshold: float      # Min failure rate (0-1) to alert
    individual_alerts: list            # Severities for individual alerts
    summary_alerts: list               # Severities for summary alerts
  
  email:
    enabled: bool
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    from_email: str
    to_emails: list
  
  slack:
    enabled: bool
    webhook_url: str
  
  teams:
    enabled: bool
    webhook_url: str
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `critical_failure_threshold` | int | 1 | Minimum critical failures to trigger alert |
| `failure_rate_threshold` | float | 0.2 | Minimum failure rate to trigger alert |
| `individual_alerts` | list | ['critical'] | Severity levels for individual alerts |
| `summary_alerts` | list | ['high', 'medium', 'low'] | Severity levels for summary alerts |

#### Example

```yaml
alerting:
  enabled_channels: [email, slack]
  
  thresholds:
    critical_failure_threshold: 1
    failure_rate_threshold: 0.15
    individual_alerts: [critical, high]
    summary_alerts: [medium, low]
  
  email:
    enabled: true
    smtp_server: smtp.gmail.com
    smtp_port: 587
    username: alerts@company.com
    password: ${EMAIL_PASSWORD}
    from_email: qc2plus@company.com
    to_emails:
      - team@company.com
      - manager@company.com
  
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK_URL}
```

---

## CLI Reference

### qc2plus init

Initialize a new QC2Plus project.

**Usage:**
```bash
qc2plus init PROJECT_NAME 
```

**Arguments:**
- `PROJECT_NAME` : str, required
  - Name of the project to create

**Options:**
- `--profile` : str, default='postgresql'
  - Database profile template
  - Choices: postgresql, snowflake, bigquery, redshift

**Example:**
```bash
qc2plus init my_quality_project
qc2plus init analytics_quality --profile snowflake
```

---

### qc2plus run

Run quality tests.

**Usage:**
```bash
qc2plus run 
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--target` | str | 'dev' | Target environment |
| `--models` | str | None | Comma-separated model names |
| `--level` | str | 'all' | Test level: '1', '2', or 'all' |
| `--threads` | int | 1 | Number of parallel threads (1-16) |
| `--fail-fast` | flag | False | Stop on first critical failure |

**Examples:**
```bash
# Run all tests on dev
qc2plus run --target dev

# Run specific models
qc2plus run --models customers,orders --target prod

# Run only Level 1 tests
qc2plus run --level 1

# Parallel execution
qc2plus run --threads 4

# Fail fast mode
qc2plus run --fail-fast --target prod
```

---

### qc2plus test-connection

Test database connection.

**Usage:**
```bash
qc2plus test-connection 
```

**Options:**
- `--target` : str, default='dev'
  - Target environment to test

**Example:**
```bash
qc2plus test-connection --target prod
```

---

### qc2plus list-models

List all models in the project.

**Options:**
- `--output-format` : str, default='table'
  - Output format: 'table', 'json', 'yaml'

**Example:**
```bash
qc2plus list-models
qc2plus list-models --output-format json
```


---

### qc2plus compile

Compile tests to SQL without executing.

**Example:**
```bash
qc2plus compile

```

---

## Complete Example

Here's a complete example using all features:

**Project Structure:**
```
my_quality_project/
├── qc2plus_project.yml
├── profiles.yml
└── models/
    ├── customers.yml
    └── orders.yml
```

**qc2plus_project.yml:**
```yaml
name: my_quality_project
version: 1.0.0
profile: my_quality_project
model-paths: ["models"]
target-path: "target"
log-path: "logs"

alerting:
  enabled_channels: [slack, email]
  thresholds:
    critical_failure_threshold: 1
    failure_rate_threshold: 0.2
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK_URL}
  email:
    enabled: true
    smtp_server: smtp.gmail.com
    smtp_port: 587
    username: ${EMAIL_USERNAME}
    password: ${EMAIL_PASSWORD}
    to_emails: [team@company.com]
```

**profiles.yml:**
```yaml
my_quality_project:
  target: dev
  outputs:
    dev:
      data_source:
        type: postgresql
        host: localhost
        port: 5432
        user: ${DB_USER}
        password: ${DB_PASSWORD}
        dbname: analytics
        schema: public
      quality_output:
        type: postgresql
        host: localhost
        port: 5432
        dbname: quality_results
        schema: qc2plus
```

**models/customers.yml:**
```yaml
models:
  - name: customers
    description: Customer data quality
    qc2plus_tests:
      level1:
        - unique:
            column_name: customer_id
            severity: critical
        - not_null:
            column_name: email
            severity: critical
        - email_format:
            column_name: email
            severity: high
        - accepted_values:
            column_name: status
            accepted_values: ['active', 'inactive', 'churned']
            severity: medium
        - range_check:
            column_name: lifetime_value
            min_value: 0
            max_value: 1000000
            severity: medium
        - statistical_threshold:
            metric: count
            threshold_type: relative
            threshold_value: 2.5
            window_days: 30
            severity: high
      
      level2:
        correlation_analysis:
          variables: [lifetime_value, orders_count, avg_order_value]
          expected_correlation: 0.75
          threshold: 0.2
          window_days: 90
        
        temporal_analysis:
          date_column: created_at
          metrics: [count, avg_lifetime_value]
          seasonality_check: true
          window_days: 180
        
        distribution_analysis:
          segments: [country, customer_tier]
          metrics: [lifetime_value, orders_count]
          comparison_window: 30
          reference_window: 90
```

**Run the tests:**
```bash
# Test connection
qc2plus test-connection --target dev

# Run all tests
qc2plus run --target dev

# Run with parallelization
qc2plus run --target prod --threads 4 --fail-fast
```

---

## Best Practices

### 1. Severity Levels

- **critical**: Data corruption, business-critical violations
- **high**: Important but not immediately critical
- **medium**: Quality issues that should be addressed
- **low**: Nice-to-have improvements

### 2. Threshold Configuration

**Statistical Thresholds:**
- `threshold_value: 2.0` = 95% confidence
- `threshold_value: 3.0` = 99.7% confidence
- Use lower values (1.5-2.0) for sensitive metrics
- Use higher values (2.5-3.0) to reduce false positives

### 3. Window Sizing

- **Short windows (7-30 days)**: Fast-changing metrics
- **Medium windows (30-90 days)**: Standard metrics
- **Long windows (90-180 days)**: Seasonal patterns

### 4. Performance Optimization

- Use appropriate `min_samples` to avoid unnecessary processing
- Leverage parallel execution for large test suites
- Index date columns for temporal analysis
- Pre-aggregate data for heavy Level 2 analyses

---

This documentation is comprehensive. All parameters are documented with types, defaults, ranges, and examples.