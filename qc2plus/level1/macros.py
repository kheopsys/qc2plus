"""
SQL_MACROS
-----------
Jinja2 SQL templates for automated data quality tests.

Each entry defines a validation rule that can be rendered dynamically
depending on the database type (PostgreSQL, BigQuery, Snowflake, Redshift)
using DB_FUNCTIONS abstractions.
"""

from qc2plus.sql.db_functions import DB_FUNCTIONS
from qc2plus.level1.utils import build_sample_clause

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
        -- {% set regex_pattern = '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$' %}


        
        {% if db_type == 'bigquery' %}
           {% set regex_pattern = '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\\\\\.[A-Za-z]{2,}$' %}
         {% else %}
         {% set regex_pattern = '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' %}
         {% endif %}

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
                {% if db_type == 'bigquery' %}
                    CAST(COUNT(*) AS FLOAT64) * 100.0 / CAST(SUM(COUNT(*)) OVER() AS FLOAT64) AS actual_percentage
                {% else %}
                    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() AS actual_percentage
                {% endif %}
            FROM {{ table_ref }}
            WHERE {{ column_name }} IS NOT NULL
            GROUP BY {{ column_name }}
        ),
        benchmark_comparison AS (
            SELECT 
                a.{{ column_name }},
                a.actual_percentage,
                {% if db_type == 'bigquery' %}
                    CAST(CASE 
                        {% for value, expected_pct in benchmark_values.items() %}
                        WHEN a.{{ column_name }} = '{{ value }}' THEN {{ expected_pct }}
                        {% endfor %}
                        ELSE 0
                    END AS FLOAT64) AS expected_percentage,
                {% else %}
                    CASE 
                        {% for value, expected_pct in benchmark_values.items() %}
                        WHEN a.{{ column_name }} = '{{ value }}' THEN {{ expected_pct }}
                        {% endfor %}
                        ELSE 0
                    END AS expected_percentage,
                {% endif %}
                ABS(
                    {% if db_type == 'bigquery' %}
                        CAST(COALESCE(a.actual_percentage, 0) AS FLOAT64)
                        - CAST(COALESCE(
                            CASE 
                                {% for value, expected_pct in benchmark_values.items() %}
                                WHEN a.{{ column_name }} = '{{ value }}' THEN {{ expected_pct }}
                                {% endfor %}
                                ELSE 0
                            END, 0) AS FLOAT64)
                    {% else %}
                        COALESCE(a.actual_percentage, 0) 
                        - COALESCE(
                            CASE 
                                {% for value, expected_pct in benchmark_values.items() %}
                                WHEN a.{{ column_name }} = '{{ value }}' THEN {{ expected_pct }}
                                {% endfor %}
                                ELSE 0
                            END, 0)
                    {% endif %}
                ) AS percentage_diff
            FROM actual_distribution a
        ),
        violation_count AS (
            SELECT COUNT(*) as total_violations
            FROM benchmark_comparison 
            WHERE percentage_diff > {{ threshold }} * 100
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
                    {% if db_type == 'bigquery' %}
                        CAST(ROUND(actual_percentage, 1) AS STRING), '% vs ',
                        CAST(expected_percentage AS STRING), '% expected)'
                    {% else %}
                        CAST(ROUND(actual_percentage, 1) AS VARCHAR), '% vs ',
                        CAST(expected_percentage AS VARCHAR), '% expected)'
                    {% endif %}
                ) AS violation_detail
            FROM benchmark_comparison
            WHERE percentage_diff > {{ threshold }} * 100
            {{ db_functions.limit(10) }}
        )
        SELECT 
            '{{ column_name }}' AS column_name,
            (SELECT total_violations FROM violation_count) AS failed_rows,
            (SELECT COUNT(DISTINCT {{ column_name }}) FROM {{ schema }}.{{ model_name }}) AS total_rows,
            'Benchmark violations found in distribution' AS message,
            CONCAT('Invalid distributions: ', {{ db_functions.string_agg('violation_detail') }}) AS invalid_examples
        FROM violations
        CROSS JOIN violation_count
        WHERE violation_count.total_violations > 0
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
