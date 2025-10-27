# QC2Plus - Advanced Data Quality Framework

<div align="center">

[![PyPI version](https://badge.fury.io/py/qc2plus.svg)](https://badge.fury.io/py/qc2plus)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Documentation](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://qc2plus.readthedocs.io)

**Production-ready data quality framework with ML-powered anomaly detection**

[Features](#-features) •
[Installation](#-installation) •
[Quick Start](#-quick-start) •
[Documentation](#-documentation) •
[Examples](#-examples)

</div>

---

## 🎯 What is QC2Plus?

QC2Plus is an open-source Python framework for **automated data quality testing**, combining traditional SQL-based validation with advanced machine learning anomaly detection.

### Two-Level Quality Approach

**Level 1: SQL-Based Validation** 🔍
- Business rules (unique, not_null, foreign keys)
- Format validation (email, phone, dates)
- Statistical thresholds (detect metric anomalies)
- Custom SQL tests

**Level 2: ML-Based Anomaly Detection** 🤖
- Correlation shifts between variables
- Temporal pattern changes
- Distribution drift across segments
- Smart contextual filtering

### Why QC2Plus?

| Feature | Traditional Tools | QC2Plus |
|---------|------------------|---------|
| **Setup Time** | Hours to days | Minutes |
| **Anomaly Detection** | Rule-based only | ML-powered |
| **Alerting** | Basic notifications | Multi-channel with context |
| **Monitoring** | Standalone | Power BI integration |
| **Learning Curve** | Steep | dbt-like CLI |

---

## ✨ Features

### 🚀 Easy to Use
- **dbt-inspired CLI**: Familiar `qc2plus run`, `qc2plus test` commands
- **YAML Configuration**: Simple model and test definitions
- **Auto-Discovery**: Automatically finds models in your project
- **Multi-Environment**: Separate configs for dev, staging, prod

### 🗄️ Database Support
| Database | Support Level | Installation |
|----------|--------------|--------------|
| PostgreSQL | ✅ Stable | Included |
| Snowflake | ✅ Stable | `pip install qc2plus[snowflake]` |
| BigQuery | ✅ Stable | `pip install qc2plus[bigquery]` |
| Redshift | ⚠️ Beta | `pip install qc2plus[redshift]` |

### 📊 Comprehensive Testing

**Level 1 Tests** (8 built-in types):
- `unique`, `not_null`, `accepted_values`
- `foreign_key`, `range_check`
- `email_format`, `future_date`
- `statistical_threshold` (ML-powered)

**Level 2 Analyzers** (3 ML algorithms):
- **Correlation Analyzer**: Detect relationship changes
- **Temporal Analyzer**: Find time series anomalies
- **Distribution Analyzer**: Monitor segment shifts

### 🔔 Smart Alerting
- **Channels**: Email (SMTP), Slack, Microsoft Teams
- **Severity Levels**: Critical, High, Medium, Low
- **Smart Routing**: Individual alerts for critical, summaries for others
- **Rich Formatting**: HTML emails, Slack cards, Teams adaptive cards

### 📈 Power BI Ready
Three auto-created tables for instant dashboards:
- `quality_test_results` - Individual test outcomes
- `quality_run_summary` - Run-level metrics
- `quality_anomalies` - ML-detected anomalies with details

---

## 📦 Installation

###  Installation

```bash
pip install qc2plus
```


## 🏁 Quick Start

### 1. Initialize Project

```bash
qc2plus init my_quality_project
cd my_quality_project
```

This creates:
```
my_quality_project/
├── qc2plus_project.yml    # Project config
├── profiles.yml            # Database connections
├── models/                 # Test definitions
│   └── customers.yml       # Example model
└── README.md               # Getting started guide
```

### 2. Configure Database

Edit `profiles.yml`:

```yaml
my_quality_project:
  target: dev
  outputs:
    dev:
      data_source:              # Where your data lives
        type: postgresql
        host: localhost
        port: 5432
        user: ${DB_USER}        # Use env variables!
        password: ${DB_PASSWORD}
        dbname: analytics
        schema: public
      
      quality_output:            # Where results are stored
        type: postgresql
        host: localhost
        port: 5432
        dbname: quality_db
        schema: qc2plus
```

**Security Best Practice**: Use environment variables for credentials!

### 3. Define Tests

Edit `models/customers.yml`:

```yaml
models:
  - name: customers
    description: Customer data quality tests
    
    qc2plus_tests:
      # Level 1: Business Rules
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
        
        - statistical_threshold:
            metric: count
            threshold_type: relative
            threshold_value: 2.0     # 2 std deviations
            window_days: 30
            severity: high
      
      # Level 2: ML Anomaly Detection
      level2:
        correlation_analysis:
          variables: [lifetime_value, order_count, avg_order_value]
          expected_correlation: 0.8
          threshold: 0.2
        
        temporal_analysis:
          date_column: created_at
          metrics: [count, avg_lifetime_value]
          seasonality_check: true
        
        distribution_analysis:
          segments: [country, customer_type]
          metrics: [lifetime_value, order_count]
          date_colum: date_order
```

### 4. Run Tests

```bash
# Test connection
qc2plus test-connection

# Run all tests
qc2plus run --target dev

# Run specific model
qc2plus run --models customers --target dev

# Run only Level 1
qc2plus run --level 1

# Parallel execution (4 threads)
qc2plus run --threads 4

# Production run with fail-fast
qc2plus run --target prod --fail-fast
```

---

## 📚 Documentation

### 📖 Complete Guides

- **[API Documentation](API_DOCUMENTATION.md)** - Complete parameter reference (scikit-learn style)
- **[User Guide](https://qc2plus.readthedocs.io/user-guide)** - Comprehensive tutorials
- **[Examples](https://github.com/qc2plus/examples)** - Real-world use cases
- **[Contributing](CONTRIBUTING.md)** - Development guide

### 🎓 Tutorials

- [Getting Started (5 min)](https://qc2plus.readthedocs.io/quickstart)
- [Level 1 Tests Deep Dive](https://qc2plus.readthedocs.io/level1-guide)
- [Level 2 ML Analyzers](https://qc2plus.readthedocs.io/level2-guide)
- [Setting Up Alerts](https://qc2plus.readthedocs.io/alerting)
- [Power BI Integration](https://qc2plus.readthedocs.io/powerbi)

---

## 📋 Test Reference

### Level 1 Tests

| Test | Use Case | Example |
|------|----------|---------|
| `unique` | Primary keys, unique identifiers | `customer_id`, `email` |
| `not_null` | Required fields | `email`, `created_at` |
| `email_format` | Email validation | Email addresses |
| `foreign_key` | Referential integrity | `customer_id` → `customers.id` |
| `accepted_values` | Enum/status fields | `status` in ['active', 'inactive'] |
| `range_check` | Numeric boundaries | `age` between 0 and 120 |
| `future_date` | Date validation | Birth dates, creation dates |
| `statistical_threshold` | Metric anomalies | Daily registrations, revenue |

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete parameter reference.

### Level 2 Analyzers

| Analyzer | Detects | Example Scenario |
|----------|---------|------------------|
| **Correlation** | Relationship changes | Marketing spend vs revenue decoupling |
| **Temporal** | Time series anomalies | Unexpected spike in daily signups |
| **Distribution** | Segment shifts | Geographic distribution change |

---

## 🔔 Alerting Example

Configure in `qc2plus_project.yml`:

```yaml
alerting:
  enabled_channels: [slack, email]
  
  thresholds:
    critical_failure_threshold: 1    # Alert on 1+ critical failure
    failure_rate_threshold: 0.15     # Alert if >15% tests fail
  
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK_URL}
  
  email:
    enabled: true
    smtp_server: smtp.gmail.com
    smtp_port: 587
    username: ${EMAIL_USERNAME}
    password: ${EMAIL_APP_PASSWORD}
    from_email: qc2plus@company.com
    to_emails:
      - data-team@company.com
      - alerts@company.com
```

**Alert Example:**

<img src="https://raw.githubusercontent.com/qc2plus/assets/main/slack-alert-example.png" alt="Slack Alert" width="500"/>

---

## 📊 Power BI Integration

QC2Plus automatically creates three tables in your quality database:

### 1. quality_test_results
Individual test results with full details.

```sql
SELECT 
  model_name,
  test_name,
  test_type,
  level,
  severity,
  status,
  failed_rows,
  total_rows,
  execution_time
FROM qc2plus.quality_test_results
WHERE execution_time >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY execution_time DESC;
```

### 2. quality_run_summary
High-level run metrics for trend analysis.

```sql
SELECT 
  run_id,
  execution_time,
  target_environment,
  total_tests,
  passed_tests,
  failed_tests,
  critical_failures,
  execution_duration_seconds
FROM qc2plus.quality_run_summary
ORDER BY execution_time DESC;
```

### 3. quality_anomalies
ML-detected anomalies with severity scores.

```sql
SELECT 
  model_name,
  analyzer_type,
  anomaly_type,
  anomaly_score,
  affected_columns,
  detection_time,
  severity
FROM qc2plus.quality_anomalies
WHERE detection_time >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY anomaly_score DESC;
```

**Power BI Templates**: Download ready-to-use dashboards from [qc2plus/powerbi-templates](https://github.com/qc2plus/powerbi-templates)

---

## 🎯 Examples

### E-commerce Data Quality

```yaml
models:
  - name: orders
    qc2plus_tests:
      level1:
        - not_null:
            column_name: order_id
            severity: critical
        - foreign_key:
            column_name: customer_id
            reference_table: customers
            reference_column: id
            severity: critical
        - range_check:
            column_name: order_total
            min_value: 0
            severity: high
        - statistical_threshold:
            metric: sum
            column_name: order_total
            threshold_type: relative
            threshold_value: 3.0
            severity: high
      
      level2:
        correlation_analysis:
          variables: [order_total, item_count, shipping_cost]
          expected_correlation: 0.7
          threshold: 0.25
        
        temporal_analysis:
          date_column: order_date
          metrics: [count, sum_order_total, avg_order_total]
          seasonality_check: true
```

### SaaS Metrics Monitoring

```yaml
models:
  - name: daily_metrics
    qc2plus_tests:
      level1:
        - statistical_threshold:
            metric: count
            column_name: new_signups
            threshold_type: relative
            threshold_value: 2.0
            window_days: 30
            severity: high
        
        - statistical_threshold:
            metric: sum
            column_name: mrr
            threshold_type: absolute
            threshold_value: 100000
            severity: critical
      
      level2:
        correlation_analysis:
          variables: [new_signups, trial_starts, paid_conversions]
          expected_correlation: 0.85
          threshold: 0.15
        
        temporal_analysis:
          date_column: metric_date
          metrics: [new_signups, churn_count, mrr]
          seasonality_check: true
          window_days: 180
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         QC2Plus Architecture                │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐     ┌──────────────┐     │
│  │   Level 1    │     │   Level 2    │     │
│  │  SQL Tests   │────▶│  ML Anomaly  │     │
│  │              │     │  Detection   │     │
│  └──────────────┘     └──────────────┘     │
│         │                     │             │
│         ▼                     ▼             │
│  ┌────────────────────────────────────┐    │
│  │      Results Persistence           │    │
│  │  (PostgreSQL/BigQuery/Snowflake)   │    │
│  └────────────────────────────────────┘    │
│         │                                   │
│         ├──▶ Power BI Dashboards            │
│         └──▶ Multi-Channel Alerts           │
│              (Slack/Email/Teams)            │
└─────────────────────────────────────────────┘
```

---

## 🚀 Performance Tips

1. **Parallel Execution**: Use `--threads` based on DB capacity
   ```bash
   qc2plus run --threads 4  # Good for most setups
   ```

2. **Optimize Windows**: Adjust based on data volume
   ```yaml
   window_days: 30  # Fast, less history
   window_days: 90  # Balanced
   window_days: 180  # Comprehensive, slower
   ```

3. **Index Critical Columns**: Especially date columns
   ```sql
   CREATE INDEX idx_created_at ON customers(created_at);
   ```

4. **Use Sampling**: For exploratory analysis
   ```yaml
   min_samples: 1000  # ML tests skip if < 1000 rows
   ```

5. **Schedule Wisely**: Run during low-traffic periods
   ```bash
   # Crontab example: Daily at 2 AM
   0 2 * * * cd /path/to/project && qc2plus run --target prod
   ```

---

## 🐛 Troubleshooting

### Connection Issues

```bash
# Test database connection
qc2plus test-connection --target dev

# Enable debug logging
export QC2PLUS_LOG_LEVEL=DEBUG
qc2plus run
```

### Tests Not Found

```bash
# List all models
qc2plus list-models

# Validate configuration
qc2plus validate
```

### Performance Issues

```yaml
# Reduce window for testing
statistical_threshold:
  window_days: 7  # Instead of 30

# Increase minimum samples
level2:
  temporal_analysis:
    min_samples: 100  # Skip analysis if < 100 rows
```

### Memory Errors

```bash
# Reduce parallel threads
qc2plus run --threads 1

# Or increase Docker memory (if using Docker)
docker run --memory=4g qc2plus
```

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick Start:**
```bash
git clone https://github.com/qc2plus/qc2plus.git
cd qc2plus
pip install -e ".[dev]"
pytest tests/
```

**Areas We Need Help:**
- 📝 Documentation improvements
- 🧪 Additional test types
- 🗄️ New database adapters
- 🎨 Power BI templates
- 🌐 Translations

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Inspired by [dbt](https://www.getdbt.com/) for the CLI approach
- Built with [SQLAlchemy](https://www.sqlalchemy.org/), [scikit-learn](https://scikit-learn.org/), [pandas](https://pandas.pydata.org/)
- Thanks to our [contributors](https://github.com/qc2plus/qc2plus/graphs/contributors)

---

## 📧 Support & Community

- 📖 **Documentation**: https://qc2plus.readthedocs.io
- 🐛 **Issues**: [GitHub Issues](https://github.com/qc2plus/qc2plus/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/qc2plus/qc2plus/discussions)
- 🐦 **Twitter**: [@qc2plus](https://twitter.com/qc2plus)
- 💼 **LinkedIn**: [QC2Plus](https://linkedin.com/company/qc2plus)

---

<div align="center">

**⭐ Star us on GitHub if QC2Plus helps your data quality! ⭐**

Made with ❤️ by the QC2Plus Team

[⬆ Back to top](#qc2plus---advanced-data-quality-framework)

</div>