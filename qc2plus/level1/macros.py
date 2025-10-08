"""
2QC+ Level 1 SQL Macros
Jinja2 templates for business rule validation tests
"""

from typing import Any, Dict, Optional

DB_FUNCTIONS = {
    'postgresql': {
        'string_agg': lambda col: f"STRING_AGG({col}::text, ', ')",
        'cast_text': lambda col: f"{col}::text",
        'limit': lambda n: f"LIMIT {n}",
        'limit_offset': lambda limit, offset: f"LIMIT {limit} OFFSET {offset}",
        'current_date': lambda: "CURRENT_DATE",
        'random_func': lambda: "RANDOM()",
        'coalesce': lambda a, b: f"COALESCE({a}, {b})",
        'regex_not_match': lambda col, pattern: f"NOT ({col} ~ '{pattern}')",
        'date_sub': lambda date_col, days: f"{date_col} - INTERVAL '{days} days'",
        'date_cast': lambda col: f"CAST({col} AS DATE)"
    },

    'bigquery': {
        'string_agg': lambda col: f"STRING_AGG(CAST({col} AS STRING), ', ')",
        'cast_text': lambda col: f"CAST({col} AS STRING)",
        'limit': lambda n: f"LIMIT {n}",
        'limit_offset': lambda limit, offset: f"LIMIT {limit} OFFSET {offset}",
        'current_date': lambda: "CURRENT_DATE()",
        'random_func': lambda: "RAND()",
        'coalesce': lambda a, b: f"IFNULL({a}, {b})",
        'regex_not_match': lambda col, pattern: f"NOT REGEXP_CONTAINS({col}, '{pattern}')",
        'date_sub': lambda date_col, days: f"DATE_SUB({date_col}, INTERVAL {days} DAY)",
        'date_cast': lambda col: f"DATE({col})"
    },

    'snowflake': {
        'string_agg': lambda col: f"LISTAGG({col}, ', ')",
        'cast_text': lambda col: f"CAST({col} AS STRING)",
        'limit': lambda n: f"LIMIT {n}",
        'limit_offset': lambda limit, offset: f"LIMIT {limit} OFFSET {offset}",
        'current_date': lambda: "CURRENT_DATE()",
        'random_func': lambda: "RANDOM()",
        'coalesce': lambda a, b: f"COALESCE({a}, {b})",
        'regex_not_match': lambda col, pattern: f"NOT REGEXP_LIKE({col}, '{pattern}')",
        'date_sub': lambda date_col, days: f"DATEADD(day, -{days}, {date_col})",
        'date_cast': lambda col: f"CAST({col} AS DATE)"
    },

    'redshift': {
        'string_agg': lambda col: f"LISTAGG({col}, ', ')",
        'cast_text': lambda col: f"CAST({col} AS VARCHAR)",
        'limit': lambda n: f"LIMIT {n}",
        'limit_offset': lambda limit, offset: f"LIMIT {limit} OFFSET {offset}",
        'current_date': lambda: "CURRENT_DATE",
        'random_func': lambda: "RANDOM()",
        'coalesce': lambda a, b: f"COALESCE({a}, {b})",
        'regex_not_match': lambda col, pattern: f"NOT ({col} ~ '{pattern}')",
        'date_sub': lambda date_col, days: f"{date_col} - INTERVAL '{days} days'",
        'date_cast': lambda col: f"CAST({col} AS DATE)"
    }
}

SQL_MACROS = {
    'unique': """
        -- Test: Unique constraint on {{ column_name }}
        
        {% set table_ref = build_sample_clause(sample_config, schema, model_name, db_type) %}
        
        WITH duplicates AS (
            SELECT {{ column_name }}, COUNT(*) AS cnt
            FROM {{ table_ref }}
            WHERE {{ column_name }} IS NOT NULL
            GROUP BY {{ column_name }}
            HAVING COUNT(*) > 1
        ),
        limited_duplicates AS (
            SELECT {{ column_name }}
            FROM duplicates
            ORDER BY cnt DESC
            {{ db_functions.limit(10) }}
        )
        SELECT 
            '{{ column_name }}' AS column_name,
            (SELECT COUNT(*) FROM duplicates) AS failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) AS total_rows,
            'Duplicate values found in {{ column_name }}' AS message,
            {{ db_functions.string_agg(column_name) }} AS invalid_examples
        FROM limited_duplicates
        HAVING (SELECT COUNT(*) FROM duplicates) > 0
    """,

    'not_null': """
        -- Test: Not null constraint on {{ column_name }}
        
        {% set table_ref = build_sample_clause(sample_config, schema, model_name, db_type) %}

        WITH null_positions AS (
            SELECT ROW_NUMBER() OVER() AS row_pos
            FROM {{ table_ref }}
            WHERE {{ column_name }} IS NULL
            {{ db_functions.limit(10) }}
        )
        SELECT 
            '{{ column_name }}' AS column_name,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }} WHERE {{ column_name }} IS NULL) AS failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) AS total_rows,
            'Null values found in {{ column_name }}' AS message,
            CONCAT('Row positions: ', {{ db_functions.string_agg('row_pos') }}) AS invalid_examples
        FROM null_positions
        HAVING (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }} WHERE {{ column_name }} IS NULL) > 0
    """,

    'email_format': """
        -- Test: Email format validation on {{ column_name }}
        
        {% set table_ref = build_sample_clause(sample_config, schema, model_name, db_type) %}

        {# 🔹 Doubler les backslashes pour BigQuery et éviter le préfixe r'' #}
        {% set regex_pattern = '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\\\\\.[A-Za-z]{2,}$' %}


        WITH invalid_emails AS (
            SELECT {{ column_name }}
            FROM {{ table_ref }}
            WHERE {{ column_name }} IS NOT NULL
            AND {{ db_functions.regex_not_match(column_name, regex_pattern) }}
            {{ db_functions.limit(10) }}
        )
        SELECT 
            '{{ column_name }}' AS column_name,
            (SELECT COUNT(*) 
            FROM {{ schema }}.{{ model_name }}
            WHERE {{ column_name }} IS NOT NULL
            AND {{ db_functions.regex_not_match(column_name, regex_pattern) }}) AS failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) AS total_rows,
            'Invalid email format found in {{ column_name }}' AS message,
            CONCAT('Invalid examples: ', {{ db_functions.string_agg(column_name) }}) AS invalid_examples
        FROM invalid_emails
        HAVING (SELECT COUNT(*) 
                FROM {{ schema }}.{{ model_name }}
                WHERE {{ column_name }} IS NOT NULL
                AND {{ db_functions.regex_not_match(column_name, regex_pattern) }}) > 0
    """,


    'relationship': """
        -- Test: Foreign key constraint {{ column_name }} -> {{ reference_table }}.{{ reference_column }}
        
        {% set table_ref = build_sample_clause(sample_config, schema, model_name, db_type) %}

        WITH orphan_keys AS (
            SELECT sampled_data.{{ column_name }}
            FROM {{ table_ref }}
            LEFT JOIN {{ schema }}.{{ reference_table }} ref 
                ON sampled_data.{{ column_name }} = ref.{{ reference_column }}
            WHERE sampled_data.{{ column_name }} IS NOT NULL
            AND ref.{{ reference_column }} IS NULL
            {{ db_functions.limit(10) }}
        )
        SELECT 
            '{{ column_name }}' AS column_name,
            (SELECT COUNT(*) 
            FROM {{ schema }}.{{ model_name }} m
            LEFT JOIN {{ schema }}.{{ reference_table }} r 
                ON m.{{ column_name }} = r.{{ reference_column }}
            WHERE m.{{ column_name }} IS NOT NULL
            AND r.{{ reference_column }} IS NULL) AS failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) AS total_rows,
            'Foreign key violations found in {{ column_name }}' AS message,
            CONCAT('Orphan keys: ', {{ db_functions.string_agg('orphan_keys.' + column_name) }}) AS invalid_examples
        FROM orphan_keys
        HAVING (
            SELECT COUNT(*) 
            FROM {{ schema }}.{{ model_name }} m
            LEFT JOIN {{ schema }}.{{ reference_table }} r 
                ON m.{{ column_name }} = r.{{ reference_column }}
            WHERE m.{{ column_name }} IS NOT NULL
            AND r.{{ reference_column }} IS NULL
        ) > 0
    """,


    'future_date': """
        -- Test: Future date validation on {{ column_name }}
        
        {% set table_ref = build_sample_clause(sample_config, schema, model_name, db_type) %}

        WITH future_dates AS (
            SELECT {{ column_name }}
            FROM {{ table_ref }}
            WHERE {{ column_name }} IS NOT NULL
            AND (
                {% if db_type == 'bigquery' %}
                    DATE({{ column_name }}) > {{ db_functions.current_date() }}
                {% else %}
                    {{ column_name }} > {{ db_functions.current_date() }}
                {% endif %}
            )
            {{ db_functions.limit(10) }}
        )
        SELECT 
            '{{ column_name }}' AS column_name,
            (SELECT COUNT(*) 
            FROM {{ schema }}.{{ model_name }}
            WHERE {{ column_name }} IS NOT NULL
            AND (
                {% if db_type == 'bigquery' %}
                    DATE({{ column_name }}) > {{ db_functions.current_date() }}
                {% else %}
                    {{ column_name }} > {{ db_functions.current_date() }}
                {% endif %}
            )) AS failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) AS total_rows,
            'Future dates found in {{ column_name }}' AS message,
            CONCAT('Invalid future values: ', {{ db_functions.string_agg(column_name) }}) AS invalid_examples
        FROM future_dates
        HAVING (SELECT COUNT(*) 
                FROM {{ schema }}.{{ model_name }}
                WHERE {{ column_name }} IS NOT NULL
                AND (
                    {% if db_type == 'bigquery' %}
                        DATE({{ column_name }}) > {{ db_functions.current_date() }}
                    {% else %}
                        {{ column_name }} > {{ db_functions.current_date() }}
                    {% endif %}
                )) > 0
    """,


    'accepted_values': """
        -- Test: Accepted values constraint on {{ column_name }}
        
        {% set table_ref = build_sample_clause(sample_config, schema, model_name, db_type) %}

        WITH invalid_values AS (
            SELECT {{ column_name }}
            FROM {{ table_ref }}
            WHERE {{ column_name }} IS NOT NULL
            AND {{ column_name }} NOT IN (
                {% for value in accepted_values %}
                    '{{ value }}'{% if not loop.last %},{% endif %}
                {% endfor %}
            )
            {{ db_functions.limit(10) }}
        )
        SELECT 
            '{{ column_name }}' AS column_name,
            (SELECT COUNT(*) 
            FROM {{ schema }}.{{ model_name }}
            WHERE {{ column_name }} IS NOT NULL
            AND {{ column_name }} NOT IN (
                {% for value in accepted_values %}
                    '{{ value }}'{% if not loop.last %},{% endif %}
                {% endfor %}
            )) AS failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) AS total_rows,
            'Invalid values found in {{ column_name }}' AS message,
            CONCAT('Invalid examples: ', {{ db_functions.string_agg(column_name) }}) AS invalid_examples
        FROM invalid_values
        HAVING (SELECT COUNT(*) 
                FROM {{ schema }}.{{ model_name }}
                WHERE {{ column_name }} IS NOT NULL
                AND {{ column_name }} NOT IN (
                    {% for value in accepted_values %}
                        '{{ value }}'{% if not loop.last %},{% endif %}
                    {% endfor %}
                )) > 0
    """,

    'range_check': """
        -- Test: Range check on {{ column_name }}
        
        {% set table_ref = build_sample_clause(sample_config, schema, model_name, db_type) %}

        {# Helper : ajoute des quotes si min/max sont des dates ou strings #}
        {% macro safe_val(val) -%}
            {% if val is string and not val.isdigit() %}
                '{{ val }}'
            {% else %}
                {{ val }}
            {% endif %}
        {%- endmacro %}

        WITH out_of_range AS (
            SELECT {{ column_name }}
            FROM {{ table_ref }}
            WHERE {{ column_name }} IS NOT NULL
            AND (
                {% if min_value is defined %}
                    {{ column_name }} < {{ safe_val(min_value) }}
                {% endif %}
                {% if min_value is defined and max_value is defined %}
                    OR
                {% endif %}
                {% if max_value is defined %}
                    {{ column_name }} > {{ safe_val(max_value) }}
                {% endif %}
            )
            {{ db_functions.limit(10) }}
        )
        SELECT 
            '{{ column_name }}' AS column_name,
            (SELECT COUNT(*)
            FROM {{ schema }}.{{ model_name }}
            WHERE {{ column_name }} IS NOT NULL
            AND (
                {% if min_value is defined %}
                    {{ column_name }} < {{ safe_val(min_value) }}
                {% endif %}
                {% if min_value is defined and max_value is defined %}
                    OR
                {% endif %}
                {% if max_value is defined %}
                    {{ column_name }} > {{ safe_val(max_value) }}
                {% endif %}
            )) AS failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) AS total_rows,
            'Values outside allowed range in {{ column_name }}' AS message,
            CONCAT('Out-of-range examples: ', {{ db_functions.string_agg(column_name) }}) AS invalid_examples
        FROM out_of_range
        HAVING (SELECT COUNT(*)
                FROM {{ schema }}.{{ model_name }}
                WHERE {{ column_name }} IS NOT NULL
                AND (
                    {% if min_value is defined %}
                        {{ column_name }} < {{ safe_val(min_value) }}
                    {% endif %}
                    {% if min_value is defined and max_value is defined %}
                        OR
                    {% endif %}
                    {% if max_value is defined %}
                        {{ column_name }} > {{ safe_val(max_value) }}
                    {% endif %}
                )) > 0
    """,

    'freshness': """
        -- Test: Data freshness check
        
        {% set table_ref = build_sample_clause(sample_config, schema, model_name, db_type) %}

        WITH freshness_check AS (
            SELECT 
                'data_freshness' AS column_name,
                CASE 
                    WHEN {{ db_functions.date_cast('MAX(' ~ column_name ~ ')') }} < {{ db_functions.date_sub(db_functions.current_date(), max_age_days) }} THEN 1
                    ELSE 0
                END AS failed_rows,
                1 AS total_rows,
                CONCAT(
                    'Data is stale. Latest record: ',
                    {{ db_functions.cast_text('MAX(' ~ column_name ~ ')') }},
                    ', Expected within: ',
                    '{{ max_age_days }} days'
                ) AS message,
                CONCAT('Latest date found: ', {{ db_functions.cast_text('MAX(' ~ column_name ~ ')') }}) AS invalid_examples
            FROM {{ table_ref }}
            WHERE {{ column_name }} IS NOT NULL
        )
        SELECT * FROM freshness_check
        WHERE failed_rows = 1
    """,

    'accepted_benchmark_values': """
        -- Test: Benchmark values distribution validation on {{ column_name }}

        {% set table_ref = build_sample_clause(sample_config, schema, model_name, db_type) %}

        WITH actual_distribution AS (
            SELECT 
                {{ column_name }},
                COUNT(*) AS actual_count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() AS actual_percentage
            FROM {{ table_ref }}
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
                END AS expected_percentage,
                ABS(
                    a.actual_percentage - 
                    CASE 
                        {% for value, expected_pct in benchmark_values.items() %}
                        WHEN a.{{ column_name }} = '{{ value }}' THEN {{ expected_pct }}
                        {% endfor %}
                        ELSE 0
                    END
                ) AS percentage_diff
            FROM actual_distribution a
        ),
        violations AS (
            SELECT 
                {{ column_name }},
                actual_percentage,
                expected_percentage,
                percentage_diff,
                CONCAT(
                    {{ db_functions.cast_text(column_name) }},
                    ' (',
                    ROUND(actual_percentage, 1), '% vs ',
                    expected_percentage, '% expected)'
                ) AS violation_detail
            FROM benchmark_comparison
            WHERE percentage_diff > {{ threshold }} * 100
            {{ db_functions.limit(10) }}
        )
        SELECT 
            '{{ column_name }}' AS column_name,
            (SELECT COUNT(*) FROM benchmark_comparison WHERE percentage_diff > {{ threshold }} * 100) AS failed_rows,
            (SELECT COUNT(DISTINCT {{ column_name }}) FROM {{ schema }}.{{ model_name }}) AS total_rows,
            'Benchmark violations found in distribution' AS message,
            CONCAT('Invalid distributions: ', {{ db_functions.string_agg('violation_detail') }}) AS invalid_examples
        FROM violations
        HAVING (SELECT COUNT(*) FROM benchmark_comparison WHERE percentage_diff > {{ threshold }} * 100) > 0
    """,

    'statistical_threshold': """
        -- Test: Statistical threshold for {{ metric }} on {{ column_name or 'table' }}

        {% set table_ref = build_sample_clause(sample_config, schema, model_name, db_type) %}

        WITH daily_metrics AS (
            SELECT 
                {{ db_functions.date_cast('created_at') }} AS metric_date,
                {% if column_name %}
                    {% if metric == 'count' %}
                        COUNT({{ column_name }}) AS daily_value
                    {% elif metric == 'avg' %}
                        AVG({{ column_name }}) AS daily_value
                    {% elif metric == 'sum' %}
                        SUM({{ column_name }}) AS daily_value
                    {% elif metric == 'min' %}
                        MIN({{ column_name }}) AS daily_value
                    {% elif metric == 'max' %}
                        MAX({{ column_name }}) AS daily_value
                    {% else %}
                        COUNT({{ column_name }}) AS daily_value
                    {% endif %}
                {% else %}
                    COUNT(*) AS daily_value
                {% endif %}
            FROM {{ table_ref }}
            WHERE {{ db_functions.date_cast('created_at') }} BETWEEN 
                {{ db_functions.date_sub(db_functions.current_date(), window_days or 30) }}
                AND {{ db_functions.date_sub(db_functions.current_date(), 1) }}
            GROUP BY {{ db_functions.date_cast('created_at') }}
        ),
        current_value AS (
            SELECT 
                {% if column_name %}
                    {% if metric == 'count' %}
                        COUNT({{ column_name }}) AS current_metric
                    {% elif metric == 'avg' %}
                        AVG({{ column_name }}) AS current_metric
                    {% elif metric == 'sum' %}
                        SUM({{ column_name }}) AS current_metric
                    {% elif metric == 'min' %}
                        MIN({{ column_name }}) AS current_metric
                    {% elif metric == 'max' %}
                        MAX({{ column_name }}) AS current_metric
                    {% else %}
                        COUNT({{ column_name }}) AS current_metric
                    {% endif %}
                {% else %}
                    COUNT(*) AS current_metric
                {% endif %}
            FROM {{ schema }}.{{ model_name }}
            WHERE {{ db_functions.date_cast('created_at') }} = {{ db_functions.current_date() }}
        ),
        historical_stats AS (
            SELECT 
                AVG(daily_value) AS avg_metric,
                STDDEV(daily_value) AS stddev_metric
            FROM daily_metrics
        ),
        threshold_check AS (
            SELECT 
                c.current_metric,
                h.avg_metric,
                h.stddev_metric,
                {% if threshold_type == 'absolute' %}
                    {{ threshold_value }} AS threshold_value,
                    CASE 
                        WHEN c.current_metric > {{ threshold_value }} THEN 1
                        ELSE 0
                    END AS threshold_exceeded
                {% else %}
                    h.avg_metric + ({{ threshold_value }} * {{ db_functions.coalesce('h.stddev_metric', '0') }}) AS threshold_value,
                    CASE 
                        WHEN c.current_metric > h.avg_metric + ({{ threshold_value }} * {{ db_functions.coalesce('h.stddev_metric', '0') }}) THEN 1
                        WHEN c.current_metric < h.avg_metric - ({{ threshold_value }} * {{ db_functions.coalesce('h.stddev_metric', '0') }}) THEN 1
                        ELSE 0
                    END AS threshold_exceeded
                {% endif %}
            FROM current_value c
            CROSS JOIN historical_stats h
        )
        SELECT 
            '{{ column_name or metric }}' AS column_name,
            threshold_exceeded AS failed_rows,
            1 AS total_rows,
            CONCAT(
                'Statistical threshold exceeded: current=',
                ROUND(current_metric, 2),
                ', threshold=',
                ROUND(threshold_value, 2),
                ', historical_avg=',
                ROUND({{ db_functions.coalesce('avg_metric', '0') }}, 2)
            ) AS message,
            CONCAT(
                'Current: ', ROUND(current_metric, 2),
                ', Historical avg: ', ROUND({{ db_functions.coalesce('avg_metric', '0') }}, 2),
                ', Threshold: ', ROUND(threshold_value, 2)
            ) AS invalid_examples
        FROM threshold_check
        WHERE threshold_exceeded = 1
    """,


    'custom_sql': """
        -- Test: Custom SQL validation
        {{ custom_sql }}
    """,
}

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

# Sampling with partition support (multi-database compatible)
def build_sample_clause(
    sample_config: Optional[Dict[str, Any]],
    schema: str,
    model_name: str,
    db_type: str = "postgresql"
) -> str:
    """
    Build SQL sampling clause with integrated partition support.
    Compatible with PostgreSQL, BigQuery, Snowflake, and Redshift.
    """
    if not sample_config:
        return f"{schema}.{model_name}"

    base_table = f"{schema}.{model_name}"
    db_funcs = DB_FUNCTIONS.get(db_type, DB_FUNCTIONS["postgresql"])
    random_func = db_funcs["random_func"]()

    partition_filter = None
    if "partitioned_by" in sample_config:
        partition_column = sample_config["partitioned_by"]
        strategy = sample_config.get("partition_strategy", "latest")

        if strategy == "latest":
            count = sample_config.get("partition_count", 1)
            offset = count - 1
            limit_offset_clause = db_funcs["limit_offset"](1, offset)
            partition_filter = f"""
                {partition_column} >= (
                    SELECT DISTINCT {partition_column}
                    FROM {base_table}
                    ORDER BY {partition_column} DESC
                    {limit_offset_clause}
                )
            """

        elif strategy == "range":
            start_date = sample_config.get("partition_start")
            end_date = sample_config.get("partition_end")
            if start_date and end_date:
                partition_filter = f"{partition_column} BETWEEN '{start_date}' AND '{end_date}'"

        elif strategy == "list":
            partition_list = sample_config.get("partition_list", [])
            if partition_list:
                partitions_str = "', '".join(str(p) for p in partition_list)
                partition_filter = f"{partition_column} IN ('{partitions_str}')"

    method = sample_config.get("method")

    # Random sampling + partition
    if partition_filter and method == "random":
        if "percentage" in sample_config:
            pct = sample_config["percentage"]

            # ✅ BigQuery : use RAND() < pct instead of TABLESAMPLE
            if db_type == "bigquery":
                return f"""(
                    SELECT * 
                    FROM {base_table}
                    WHERE {partition_filter}
                    AND RAND() < {pct}
                ) AS sampled_data"""

            # Default for other DBs
            return f"""(
                SELECT * FROM {base_table}
                WHERE {partition_filter}
                ORDER BY {random_func}
                {db_funcs["limit"](f"(SELECT CAST(COUNT(*) * {pct} AS INT) FROM {base_table} WHERE {partition_filter})")}
            ) AS sampled_data"""

        elif "size" in sample_config:
            size = sample_config["size"]
            return f"""(
                SELECT * FROM {base_table}
                WHERE {partition_filter}
                ORDER BY {random_func}
                {db_funcs["limit"](size)}
            ) AS sampled_data"""

    # Random sampling without partition
    elif method == "random":
        if "percentage" in sample_config:
            pct = sample_config["percentage"]

            if db_type == "bigquery":
                return f"""(
                    SELECT * 
                    FROM {base_table}
                    WHERE RAND() < {pct}
                ) AS sampled_data"""

            return f"""(
                SELECT * FROM {base_table}
                ORDER BY {random_func}
                {db_funcs["limit"](f"(SELECT CAST(COUNT(*) * {pct} AS INT) FROM {base_table})")}
            ) AS sampled_data"""

        elif "size" in sample_config:
            size = sample_config["size"]
            return f"""(
                SELECT * FROM {base_table}
                ORDER BY {random_func}
                {db_funcs["limit"](size)}
            ) AS sampled_data"""

    # Partition only
    elif partition_filter:
        return f"""(
            SELECT * FROM {base_table}
            WHERE {partition_filter}
        ) AS partitioned_data"""

    # Default: full table
    return base_table
