"""
2QC+ Level 1 SQL Macros
Jinja2 templates for business rule validation tests
"""

# SQL macro templates for different test types
SQL_MACROS = {
    
    'unique': """
        -- Test: Unique constraint on {{ column_name }}
        SELECT 
            '{{ column_name }}' as column_name,
            COUNT(*) as failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) as total_rows,
            'Duplicate values found in {{ column_name }}' as message
        FROM (
            SELECT {{ column_name }}, COUNT(*) as cnt
            FROM {{ schema }}.{{ model_name }}
            WHERE {{ column_name }} IS NOT NULL
            GROUP BY {{ column_name }}
            HAVING COUNT(*) > 1
        ) duplicates
        HAVING COUNT(*) > 0
    """,
    
    'not_null': """
        -- Test: Not null constraint on {{ column_name }}
        SELECT 
            '{{ column_name }}' as column_name,
            COUNT(*) as failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) as total_rows,
            'Null values found in {{ column_name }}' as message
        FROM {{ schema }}.{{ model_name }}
        WHERE {{ column_name }} IS NULL
        HAVING COUNT(*) > 0
    """,
    
    'email_format': """
        -- Test: Email format validation on {{ column_name }}
        SELECT 
            '{{ column_name }}' as column_name,
            COUNT(*) as failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) as total_rows,
            'Invalid email format found in {{ column_name }}' as message
        FROM {{ schema }}.{{ model_name }}
        WHERE {{ column_name }} IS NOT NULL
        AND NOT (
            {{ column_name }} ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'
        )
        GROUP BY 1,4
        HAVING COUNT(*) > 0
    """,
    
    'relationship': """
        -- Test: Foreign key constraint {{ column_name }} -> {{ reference_table }}.{{ reference_column }}
        SELECT 
            '{{ column_name }}' as column_name,
            COUNT(*) as failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) as total_rows,
            'Foreign key violations found in {{ column_name }}' as message
        FROM {{ schema }}.{{ model_name }} main
        LEFT JOIN {{ schema }}.{{ reference_table }} ref 
            ON main.{{ column_name }} = ref.{{ reference_column }}
        WHERE main.{{ column_name }} IS NOT NULL
        AND ref.{{ reference_column }} IS NULL
        HAVING COUNT(*) > 0
    """,
    
    'future_date': """
        -- Test: Future date validation on {{ column_name }}
        SELECT 
            '{{ column_name }}' as column_name,
            COUNT(*) as failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) as total_rows,
            'Future dates found in {{ column_name }}' as message
        FROM {{ schema }}.{{ model_name }}
        WHERE {{ column_name }} IS NOT NULL
        AND {{ column_name }} > CURRENT_DATE
        HAVING COUNT(*) > 0
    """,
    
    'statistical_threshold': """
        -- Test: Statistical threshold for {{ metric }} on {{ column_name or 'table' }}
        WITH current_value AS (
            SELECT 
                {% if column_name %}
                    {% if metric == 'count' %}
                        COUNT({{ column_name }}) as current_metric
                    {% elif metric == 'avg' %}
                        AVG({{ column_name }}) as current_metric
                    {% elif metric == 'sum' %}
                        SUM({{ column_name }}) as current_metric
                    {% elif metric == 'min' %}
                        MIN({{ column_name }}) as current_metric
                    {% elif metric == 'max' %}
                        MAX({{ column_name }}) as current_metric
                    {% else %}
                        COUNT({{ column_name }}) as current_metric
                    {% endif %}
                {% else %}
                    -- Table-level metrics
                    {% if metric == 'count' %}
                        COUNT(*) as current_metric
                    {% else %}
                        COUNT(*) as current_metric
                    {% endif %}
                {% endif %}
            FROM {{ schema }}.{{ model_name }}
            WHERE DATE(created_at) = CURRENT_DATE
        ),
        historical_stats AS (
            SELECT 
                {% if column_name %}
                    {% if metric == 'count' %}
                        AVG(COUNT({{ column_name }})) as avg_metric,
                        STDDEV(COUNT({{ column_name }})) as stddev_metric
                    {% elif metric == 'avg' %}
                        AVG(AVG({{ column_name }})) as avg_metric,
                        STDDEV(AVG({{ column_name }})) as stddev_metric
                    {% elif metric == 'sum' %}
                        AVG(SUM({{ column_name }})) as avg_metric,
                        STDDEV(SUM({{ column_name }})) as stddev_metric
                    {% elif metric == 'min' %}
                        AVG(MIN({{ column_name }})) as avg_metric,
                        STDDEV(MIN({{ column_name }})) as stddev_metric
                    {% elif metric == 'max' %}
                        AVG(MAX({{ column_name }})) as avg_metric,
                        STDDEV(MAX({{ column_name }})) as stddev_metric
                    {% else %}
                        AVG(COUNT({{ column_name }})) as avg_metric,
                        STDDEV(COUNT({{ column_name }})) as stddev_metric
                    {% endif %}
                {% else %}
                    AVG(COUNT(*)) as avg_metric,
                    STDDEV(COUNT(*)) as stddev_metric
                {% endif %}
            FROM {{ schema }}.{{ model_name }}
            WHERE DATE(created_at) BETWEEN 
                CURRENT_DATE - INTERVAL '{{ window_days or 30 }} days' 
                AND CURRENT_DATE - INTERVAL '1 day'
            GROUP BY DATE(created_at)
        ),
        threshold_check AS (
            SELECT 
                c.current_metric,
                h.avg_metric,
                h.stddev_metric,
                {% if threshold_type == 'absolute' %}
                    {{ threshold_value }} as threshold_value,
                    CASE 
                        WHEN c.current_metric > {{ threshold_value }} THEN 1
                        ELSE 0
                    END as threshold_exceeded
                {% else %}
                    h.avg_metric + ({{ threshold_value }} * COALESCE(h.stddev_metric, 0)) as threshold_value,
                    CASE 
                        WHEN c.current_metric > h.avg_metric + ({{ threshold_value }} * COALESCE(h.stddev_metric, 0)) THEN 1
                        WHEN c.current_metric < h.avg_metric - ({{ threshold_value }} * COALESCE(h.stddev_metric, 0)) THEN 1
                        ELSE 0
                    END as threshold_exceeded
                {% endif %}
            FROM current_value c
            CROSS JOIN historical_stats h
        )
        SELECT 
            '{{ column_name or metric }}' as column_name,
            threshold_exceeded as failed_rows,
            1 as total_rows,
            CONCAT(
                'Statistical threshold exceeded: current=', 
                ROUND(current_metric, 2), 
                ', threshold=', 
                ROUND(threshold_value, 2),
                ', historical_avg=',
                ROUND(avg_metric, 2)
            ) as message
        FROM threshold_check
        WHERE threshold_exceeded = 1
    """,
    
    'accepted_values': """
        -- Test: Accepted values constraint on {{ column_name }}
        SELECT 
            '{{ column_name }}' as column_name,
            COUNT(*) as failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) as total_rows,
            'Invalid values found in {{ column_name }}' as message
        FROM {{ schema }}.{{ model_name }}
        WHERE {{ column_name }} IS NOT NULL
        AND {{ column_name }} NOT IN (
            {% for value in accepted_values %}
                '{{ value }}'{% if not loop.last %},{% endif %}
            {% endfor %}
        )
        HAVING COUNT(*) > 0
    """,
    
    'range_check': """
        -- Test: Range check on {{ column_name }}
        SELECT 
            '{{ column_name }}' as column_name,
            COUNT(*) as failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) as total_rows,
            'Values outside allowed range in {{ column_name }}' as message
        FROM {{ schema }}.{{ model_name }}
        WHERE {{ column_name }} IS NOT NULL
        AND (
            {% if min_value is defined %}
                {{ column_name }} < {{ min_value }}
            {% endif %}
            {% if min_value is defined and max_value is defined %}
                OR
            {% endif %}
            {% if max_value is defined %}
                {{ column_name }} > {{ max_value }}
            {% endif %}
        )
        HAVING COUNT(*) > 0
    """,
    
    'custom_sql': """
        -- Test: Custom SQL validation
        {{ custom_sql }}
    """,
    
    'freshness': """
        -- Test: Data freshness check
        SELECT 
            'data_freshness' as column_name,
            CASE 
                WHEN MAX({{ column_name }}) < CURRENT_DATE - INTERVAL '{{ max_age_days }} days' THEN 1
                ELSE 0
            END as failed_rows,
            1 as total_rows,
            CONCAT(
                'Data is stale. Latest record: ', 
                MAX({{ column_name }}),
                ', Expected within: ',
                '{{ max_age_days }} days'
            ) as message
        FROM {{ schema }}.{{ model_name }}
        WHERE {{ column_name }} IS NOT NULL
        HAVING failed_rows = 1
    """,

    'accepted_benchmark_values': """
        -- Test: Benchmark values distribution validation on {{ column_name }}
        WITH actual_distribution AS (
            SELECT 
                {{ column_name }},
                COUNT(*) as actual_count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as actual_percentage
            FROM {{ schema }}.{{ model_name }}
            WHERE {{ column_name }} IS NOT NULL
            GROUP BY {{ column_name }}
        ),
        benchmark_comparison AS (
            SELECT 
                a.{{ column_name }},
                a.actual_percentage,
                CASE 
                    {% for value, expected_pct in benchmark_values.items() %}
                    WHEN a.{{ column_name }} = '{{ value }}' THEN {{ expected_pct }}
                    {% endfor %}
                    ELSE 0
                END as expected_percentage,
                ABS(a.actual_percentage - CASE 
                    {% for value, expected_pct in benchmark_values.items() %}
                    WHEN a.{{ column_name }} = '{{ value }}' THEN {{ expected_pct }}
                    {% endfor %}
                    ELSE 0
                END) as percentage_diff
            FROM actual_distribution a
        ),
        violations AS (
            SELECT 
                {{ column_name }},
                actual_percentage,
                expected_percentage,
                percentage_diff
            FROM benchmark_comparison
            WHERE percentage_diff > {{ threshold }} * 100
        )
        SELECT 
            '{{ column_name }}' as column_name,
            COUNT(*) as failed_rows,
            (SELECT COUNT(DISTINCT {{ column_name }}) FROM {{ schema }}.{{ model_name }}) as total_rows,
            CONCAT(
                'Benchmark violations: ',
                STRING_AGG(
                    CONCAT({{ column_name }}, ' (', ROUND(actual_percentage, 1), '% vs ', expected_percentage, '% expected)'),
                    ', '
                )
            ) as message
        FROM violations
        HAVING COUNT(*) > 0
    """,
}


# Database-specific adaptations for SQL macros
DB_ADAPTATIONS = {
    'postgresql': {
        'regex_operator': '~',
        'date_diff': 'DATE_PART',
        'current_date': 'CURRENT_DATE',
        'interval_syntax': "INTERVAL '{} days'"
    },
    'snowflake': {
        'regex_operator': 'REGEXP',
        'date_diff': 'DATEDIFF',
        'current_date': 'CURRENT_DATE()',
        'interval_syntax': "INTERVAL '{} DAY'"
    },
    'bigquery': {
        'regex_operator': 'REGEXP_CONTAINS',
        'date_diff': 'DATE_DIFF',
        'current_date': 'CURRENT_DATE()',
        'interval_syntax': "INTERVAL {} DAY"
    },
    'redshift': {
        'regex_operator': '~',
        'date_diff': 'DATEDIFF',
        'current_date': 'CURRENT_DATE',
        'interval_syntax': "INTERVAL '{} days'"
    }
}


def adapt_sql_for_database(sql: str, db_type: str) -> str:
    """Adapt SQL template for specific database type"""
    
    if db_type not in DB_ADAPTATIONS:
        return sql
    
    adaptations = DB_ADAPTATIONS[db_type]
    
    # Apply adaptations
    if db_type == 'bigquery':
        # BigQuery specific adaptations
        sql = sql.replace('~', 'REGEXP_CONTAINS')
        sql = sql.replace('DATE_PART', 'DATE_DIFF')
        sql = sql.replace('CURRENT_DATE', 'CURRENT_DATE()')
        sql = sql.replace("INTERVAL '", "INTERVAL ")
        sql = sql.replace(" days'", " DAY")
        
    elif db_type == 'snowflake':
        # Snowflake specific adaptations
        sql = sql.replace('~', 'REGEXP')
        sql = sql.replace('DATE_PART', 'DATEDIFF')
        sql = sql.replace('CURRENT_DATE', 'CURRENT_DATE()')
        sql = sql.replace(" days'", " DAY'")
        
    elif db_type == 'redshift':
        # Redshift specific adaptations
        sql = sql.replace('DATE_PART', 'DATEDIFF')
        
    return sql


def get_macro_help(macro_name: str) -> str:
    """Get help text for a specific macro"""
    
    help_text = {
        'unique': """
        Tests that all values in a column are unique.
        
        Parameters:
        - column_name: Column to test
        - severity: Test severity level
        
        Example:
        unique:
          column_name: customer_id
          severity: critical
        """,
        
        'not_null': """
        Tests that a column contains no null values.
        
        Parameters:
        - column_name: Column to test
        - severity: Test severity level
        
        Example:
        not_null:
          column_name: email
          severity: critical
        """,
        
        'email_format': """
        Tests that email addresses follow valid format.
        
        Parameters:
        - column_name: Email column to validate
        - severity: Test severity level
        
        Example:
        email_format:
          column_name: email_address
          severity: medium
        """,
        
        'statistical_threshold': """
        Tests statistical thresholds based on historical data.
        
        Parameters:
        - column_name: Column to analyze (optional for table-level metrics)
        - metric: Metric to calculate (count, avg, sum, min, max)
        - threshold_type: absolute or relative
        - threshold_value: Threshold value or standard deviation multiplier
        - window_days: Historical window in days (default: 30)
        - severity: Test severity level
        
        Example:
        statistical_threshold:
          metric: count
          threshold_type: relative
          threshold_value: 2.0
          window_days: 30
          severity: medium
        """
    }
    
    return help_text.get(macro_name, "No help available for this macro.")
