# 2QC+ Data Quality Automation Framework

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-passing-green.svg)](https://github.com/qc2plus/qc2plus)

A comprehensive, production-ready framework for automated data quality control with machine learning-powered anomaly detection.

## 🎯 Overview

2QC+ is an open-source Python framework that provides two levels of data quality automation:

- **Level 1**: Business rule validation (constraints, formats, statistical thresholds)
- **Level 2**: ML-powered anomaly detection (correlations, temporal patterns, multivariate analysis, distributions)

Inspired by dbt's approach, 2QC+ offers a familiar CLI experience while providing advanced ML capabilities for comprehensive data quality monitoring.

## ✨ Key Features

### 🔧 **Easy to Use**
- **dbt-like CLI**: Familiar commands and workflow
- **YAML Configuration**: Simple model and test definitions
- **Multi-Environment**: Dev, staging, prod support
- **Auto-Discovery**: Automatic model and test discovery

### 🗄️ **Multi-Database Support**
- PostgreSQL
- Snowflake
- BigQuery
- Redshift
- MySQL (experimental)

### 📊 **Comprehensive Testing**
- **Level 1 Tests**: Unique, not-null, email format, foreign keys, statistical thresholds
- **Level 2 ML Analysis**: Correlation analysis, temporal patterns, multivariate outliers, distribution changes

### 🚨 **Smart Alerting**
- **Multi-Channel**: Email, Slack, Microsoft Teams
- **Severity-Based**: Critical alerts for immediate attention
- **Rich Formatting**: HTML emails, Slack cards, Teams notifications

### 📈 **Power BI Integration**
- **Auto-Created Tables**: quality_test_results, quality_run_summary, quality_anomalies
- **Historical Tracking**: Trend analysis and reporting
- **Executive Dashboards**: Ready-to-use Power BI templates

## 🚀 Quick Start

### Installation

```bash
pip install qc2plus
```

### Initialize a Project

```bash
qc2plus init my_data_quality_project
cd my_data_quality_project
```

### Configure Database Connection

Edit `profiles.yml`:

```yaml
my_data_quality_project:
  target: dev
  outputs:
    dev:
      type: postgresql
      host: localhost
      port: 5432
      user: your_username
      password: your_password
      dbname: your_database
      schema: public
    prod:
      type: snowflake
      account: your_account
      user: your_username
      password: your_password
      role: your_role
      database: your_database
      warehouse: your_warehouse
      schema: public
```

### Define Your First Model

Create `models/customers.yml`:

```yaml
models:
  - name: customers
    description: Customer data quality tests
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
            severity: medium
        - statistical_threshold:
            metric: count
            threshold_type: relative
            threshold_value: 2.0
            severity: medium
      
      level2:
        correlation_analysis:
          variables: [daily_registrations, daily_activations]
          expected_correlation: 0.8
          threshold: 0.2
        
        temporal_analysis:
          date_column: created_at
          metrics: [count, avg_revenue]
          seasonality_check: true
        
        distribution_analysis:
          segments: [country, customer_type]
          metrics: [revenue, orders_count]
```

### Run Quality Tests

```bash
# Test database connection
qc2plus test-connection --target dev

# Run all tests
qc2plus run --target dev

# Run specific model
qc2plus run --models customers --target dev

# Run only Level 1 tests
qc2plus run --level 1 --target dev

# Run with parallel execution
qc2plus run --threads 4 --target dev
```

## 📋 Available Test Types

### Level 1 (Business Rules)

| Test Type | Description | Parameters |
|-----------|-------------|------------|
| `unique` | Ensures column values are unique | `column_name`, `severity` |
| `not_null` | Ensures no null values | `column_name`, `severity` |
| `email_format` | Validates email format | `column_name`, `severity` |
| `foreign_key` | Checks referential integrity | `column_name`, `reference_table`, `reference_column`, `severity` |
| `future_date` | Ensures dates are not in the future | `column_name`, `severity` |
| `statistical_threshold` | Statistical anomaly detection | `metric`, `threshold_type`, `threshold_value`, `window_days`, `severity` |
| `accepted_values` | Validates against allowed values | `column_name`, `accepted_values`, `severity` |
| `range_check` | Validates numeric ranges | `column_name`, `min_value`, `max_value`, `severity` |

### Level 2 (ML-Powered)

| Analyzer | Description | Use Cases |
|----------|-------------|-----------|
| **Correlation Analysis** | Detects changes in variable relationships | Revenue vs. marketing spend correlation breaks |
| **Temporal Analysis** | Identifies time series anomalies | Seasonal pattern disruptions, trend breaks |
| **Multivariate Analysis** | Finds outliers in multi-dimensional space | Complex fraud detection, system anomalies |
| **Distribution Analysis** | Compares distributions across segments | Geographic shifts, demographic changes |

## 🔧 Configuration Examples

### Statistical Threshold Test

```yaml
statistical_threshold:
  column_name: daily_registrations
  metric: count
  threshold_type: relative  # or 'absolute'
  threshold_value: 2.0      # 2 standard deviations
  window_days: 30
  severity: medium
```

### Correlation Analysis

```yaml
correlation_analysis:
  variables: [ad_spend, conversions, revenue]
  expected_correlation: 0.7
  threshold: 0.2
  correlation_type: pearson  # or 'spearman'
```

### Multivariate Analysis

```yaml
multivariate_analysis:
  features: [revenue, orders, session_duration, page_views]
  contamination: 0.1
  algorithms: [isolation_forest, lof, pca]
  min_samples: 100
```

## 🚨 Alerting Configuration

Add to your project's `qc2plus_project.yml`:

```yaml
alerting:
  enabled_channels: [email, slack, teams]
  
  thresholds:
    critical_failure_threshold: 1
    failure_rate_threshold: 0.2
    individual_alerts: [critical]
    summary_alerts: [high, medium, low]
  
  email:
    enabled: true
    smtp_server: smtp.gmail.com
    smtp_port: 587
    username: your_email@gmail.com
    password: your_app_password
    to_emails: [team@company.com, alerts@company.com]
  
  slack:
    enabled: true
    webhook_url: https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
  
  teams:
    enabled: true
    webhook_url: https://company.webhook.office.com/webhookb2/YOUR/TEAMS/WEBHOOK
```
## 📊 Power BI Integration

2QC+ automatically creates three tables for Power BI reporting:

### 1. quality_test_results
Individual test results with details about failures and execution times.

### 2. quality_run_summary
High-level summary of each test run including overall success rates and execution duration.

### 3. quality_anomalies
Detailed information about Level 2 ML-detected anomalies with severity scores.

Connect Power BI to your database and use these tables to create:
- Executive quality dashboards
- Trend analysis reports
- Anomaly investigation views
- Model performance tracking

## 🏗️ Architecture

```
qc2plus/
├── qc2plus/
│   ├── cli.py              # Command-line interface
│   ├── core/
│   │   ├── project.py      # Project management
│   │   ├── connection.py   # Multi-database support
│   │   └── runner.py       # Test orchestration
│   ├── level1/
│   │   ├── engine.py       # Business rule engine
│   │   └── macros.py       # SQL templates
│   ├── level2/
│   │   ├── correlation.py  # Correlation analysis
│   │   ├── temporal.py     # Time series analysis
│   │   ├── multivariate.py # Multivariate outlier detection
│   │   └── distribution.py # Distribution comparison
│   ├── alerting/
│   │   └── alerts.py       # Multi-channel alerting
│   └── output/
│       └── persistence.py  # Database persistence
├── setup.py
└── requirements.txt
```

## 🔬 Advanced Usage

### Custom SQL Tests

```yaml
custom_sql:
  sql: |
    SELECT customer_id, COUNT(*) as violation_count
    FROM customers 
    WHERE email IS NULL OR email NOT LIKE '%@%'
    HAVING COUNT(*) > 0
  severity: critical
```

### Parallel Execution

```bash
# Run tests in parallel for faster execution
qc2plus run --threads 8 --target prod
```

### Environment-Specific Configuration

```yaml
# qc2plus_project.yml
vars:
  dev:
    statistical_threshold_sensitivity: 3.0
  prod:
    statistical_threshold_sensitivity: 2.0
```

### Compilation Without Execution

```bash
# Compile tests to SQL for review
qc2plus compile
```

## 🧪 Testing Your Setup

```bash
# Test alert configurations
qc2plus test-alerts

# Validate project configuration
qc2plus validate

# List all available models
qc2plus list-models
```

## 📈 Performance Tips

1. **Use Parallel Execution**: Set `--threads` based on your database capabilities
2. **Optimize Windows**: Adjust `window_days` for statistical tests based on data volume
3. **Segment Wisely**: Choose segments that balance granularity with performance
4. **Index Optimization**: Ensure proper indexing on date and key columns
5. **Batch Scheduling**: Run during low-traffic periods for production systems

## 🐛 Troubleshooting

### Common Issues

**Database Connection Fails**
```bash
qc2plus test-connection --target dev
```

**Tests Not Found**
```bash
qc2plus list-models --output-format table
```

**Memory Issues with Large Datasets**
- Reduce `window_days` for statistical tests
- Increase `min_samples` threshold for ML tests
- Use sampling in your models

**Slow Execution**
- Enable parallel execution with `--threads`
- Optimize database queries and indexes
- Consider pre-aggregated tables for large datasets

### Debug Mode

```bash
# Run with detailed logging
QC2PLUS_LOG_LEVEL=DEBUG qc2plus run --models customers
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/qc2plus/qc2plus.git
cd qc2plus
pip install -e ".[dev]"
pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♀️ Support

- **Documentation**: [https://qc2plus.readthedocs.io/](https://qc2plus.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/qc2plus/qc2plus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/qc2plus/qc2plus/discussions)
- **Email**: support@qc2plus.org

## 🎉 Acknowledgments

- Inspired by [dbt](https://www.getdbt.com/) for the CLI and project structure approach
- Built on top of excellent open-source libraries: SQLAlchemy, scikit-learn, pandas
- Thanks to the data quality community for feedback and contributions

---

**Made with ❤️ by the 2QC+ Team**
