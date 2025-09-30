"""
2QC+ Level 1 SQL Macros
Jinja2 templates for business rule validation tests
"""

## Remplacez vos templates dans macros.py par ces versions corrigées :

from typing import Any, Dict


SQL_MACROS = {
    'unique': """
        -- Test: Unique constraint on {{ column_name }}
        {% set table_ref = build_sample_clause(sample_config, schema, model_name) %}
        WITH duplicates AS (
            SELECT {{ column_name }}, COUNT(*) as cnt
            FROM {{ table_ref }}                               --FROM {{ schema }}.{{ model_name }}
            WHERE {{ column_name }} IS NOT NULL
            GROUP BY {{ column_name }}
            HAVING COUNT(*) > 1
        ),
        limited_duplicates AS (
            SELECT {{ column_name }}
            FROM duplicates
            ORDER BY cnt DESC
            LIMIT 10
        )
        SELECT 
            '{{ column_name }}' as column_name,
            (SELECT COUNT(*) FROM duplicates) as failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) as total_rows,
            'Duplicate values found in {{ column_name }}' as message,
            -- NOUVEAU : Exemples de valeurs dupliquées
            STRING_AGG({{ column_name }}::text, ', ') as invalid_examples
        FROM limited_duplicates
        HAVING (SELECT COUNT(*) FROM duplicates) > 0
    """,
    
    'not_null': """
        -- Test: Not null constraint on {{ column_name }}
        {% set table_ref = build_sample_clause(sample_config, schema, model_name) if sample_config else schema + '.' + model_name %}

        WITH null_positions AS (
            SELECT ROW_NUMBER() OVER() as row_pos
            FROM {{ table_ref }}                    -- before sampling FROM {{ schema }}.{{ model_name }}
            WHERE {{ column_name }} IS NULL
            LIMIT 10
        )
        SELECT 
            '{{ column_name }}' as column_name,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }} WHERE {{ column_name }} IS NULL) as failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) as total_rows,
            'Null values found in {{ column_name }}' as message,
            -- NOUVEAU : Pour not_null, on donne les positions des lignes concernées
            'Row positions: ' || STRING_AGG(row_pos::text, ', ') as invalid_examples
        FROM null_positions
        HAVING (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }} WHERE {{ column_name }} IS NULL) > 0
    """,
    
    'email_format': """
        -- Test: Email format validation on {{ column_name }}
        {% set table_ref = build_sample_clause(sample_config, schema, model_name) if sample_config else schema + '.' + model_name %}
        WITH invalid_emails AS (
            SELECT {{ column_name }}
            FROM {{ table_ref }}                       -- before sampling FROM {{ schema }}.{{ model_name }}
            WHERE {{ column_name }} IS NOT NULL
            AND NOT ({{ column_name }} ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')
            LIMIT 10
        )
        SELECT 
            '{{ column_name }}' as column_name,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }} 
             WHERE {{ column_name }} IS NOT NULL
             AND NOT ({{ column_name }} ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')) as failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) as total_rows,
            'Invalid email format found in {{ column_name }}' as message,
            -- NOUVEAU : Exemples d'emails invalides (Lyon, Paris, etc.)
            STRING_AGG({{ column_name }}, ', ') as invalid_examples
        FROM invalid_emails
        HAVING (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }} 
                WHERE {{ column_name }} IS NOT NULL
                AND NOT ({{ column_name }} ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$')) > 0
    """,
    
    'relationship': """
        -- Test: Foreign key constraint {{ column_name }} -> {{ reference_table }}.{{ reference_column }}

        {% set table_ref = build_sample_clause(sample_config, schema, model_name) if sample_config else schema + '.' + model_name %}
        WITH orphan_keys AS (
            SELECT main.{{ column_name }}
            FROM {{ table_ref }} main
            LEFT JOIN {{ schema }}.{{ reference_table }} ref 
                ON main.{{ column_name }} = ref.{{ reference_column }}
            WHERE main.{{ column_name }} IS NOT NULL
            AND ref.{{ reference_column }} IS NULL
            LIMIT 10
        )
        SELECT 
            '{{ column_name }}' as column_name,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }} main
             LEFT JOIN {{ schema }}.{{ reference_table }} ref 
                ON main.{{ column_name }} = ref.{{ reference_column }}
             WHERE main.{{ column_name }} IS NOT NULL
             AND ref.{{ reference_column }} IS NULL) as failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) as total_rows,
            'Foreign key violations found in {{ column_name }}' as message,
            -- NOUVEAU : Exemples de clés orphelines
            STRING_AGG({{ column_name }}::text, ', ') as invalid_examples
        FROM orphan_keys
        HAVING (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }} main
                LEFT JOIN {{ schema }}.{{ reference_table }} ref 
                   ON main.{{ column_name }} = ref.{{ reference_column }}
                WHERE main.{{ column_name }} IS NOT NULL
                AND ref.{{ reference_column }} IS NULL) > 0
    """,
    
    'future_date': """
        -- Test: Future date validation on {{ column_name }}

        {% set table_ref = build_sample_clause(sample_config, schema, model_name) if sample_config else schema + '.' + model_name %}
        WITH future_dates AS (
            SELECT {{ column_name }}
            FROM {{ table_ref }}                 -- before sampling FROM {{ schema }}.{{ model_name }}
            WHERE {{ column_name }} IS NOT NULL
            AND {{ column_name }} > CURRENT_DATE
            LIMIT 10
        )
        SELECT 
            '{{ column_name }}' as column_name,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}
             WHERE {{ column_name }} IS NOT NULL
             AND {{ column_name }} > CURRENT_DATE) as failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) as total_rows,
            'Future dates found in {{ column_name }}' as message,
            -- NOUVEAU : Exemples de dates futures
            STRING_AGG({{ column_name }}::text, ', ') as invalid_examples
        FROM future_dates
        HAVING (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}
                WHERE {{ column_name }} IS NOT NULL
                AND {{ column_name }} > CURRENT_DATE) > 0
    """,
    
    'accepted_values': """
        -- Test: Accepted values constraint on {{ column_name }}
        
        {% set table_ref = build_sample_clause(sample_config, schema, model_name) if sample_config else schema + '.' + model_name %}
        WITH invalid_values AS (
            SELECT {{ column_name }}
            FROM {{ table_ref }}                  -- before sampling FROM {{ schema }}.{{ model_name }}
            WHERE {{ column_name }} IS NOT NULL
            AND {{ column_name }} NOT IN (
                {% for value in accepted_values %}
                    '{{ value }}'{% if not loop.last %},{% endif %}
                {% endfor %}
            )
            LIMIT 10
        )
        SELECT 
            '{{ column_name }}' as column_name,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}
             WHERE {{ column_name }} IS NOT NULL
             AND {{ column_name }} NOT IN (
                {% for value in accepted_values %}
                    '{{ value }}'{% if not loop.last %},{% endif %}
                {% endfor %}
             )) as failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) as total_rows,
            'Invalid values found in {{ column_name }}' as message,
            -- NOUVEAU : Exemples de valeurs invalides
            STRING_AGG({{ column_name }}::text, ', ') as invalid_examples
        FROM invalid_values
        HAVING (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}
                WHERE {{ column_name }} IS NOT NULL
                AND {{ column_name }} NOT IN (
                    {% for value in accepted_values %}
                        '{{ value }}'{% if not loop.last %},{% endif %}
                    {% endfor %}
                )) > 0
    """,
    


    'range_check': """
        -- Test: Range check on {{ column_name }}
        {% set table_ref = build_sample_clause(sample_config, schema, model_name) if sample_config else schema + '.' + model_name %}

        WITH out_of_range AS (
            SELECT {{ column_name }}
            FROM {{ table_ref }}                    -- before sampling FROM {{ schema }}.{{ model_name }}
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
            LIMIT 10
        )
        SELECT 
            '{{ column_name }}' as column_name,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}
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
            )) as failed_rows,
            (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}) as total_rows,
            'Values outside allowed range in {{ column_name }}' as message,
            -- NOUVEAU : Exemples de valeurs hors limites
            STRING_AGG({{ column_name }}::text, ', ') as invalid_examples
        FROM out_of_range
        HAVING (SELECT COUNT(*) FROM {{ schema }}.{{ model_name }}
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
                )) > 0
    """,

    'freshness': """
        -- Test: Data freshness check
        {% set table_ref = build_sample_clause(sample_config, schema, model_name) if sample_config else schema + '.' + model_name %}
        WITH freshness_check AS (
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
                ) as message,
                -- NOUVEAU : Exemple de la date la plus récente trouvée
                'Latest date found: ' || MAX({{ column_name }})::text as invalid_examples
            FROM {{ table_ref }}
            WHERE {{ column_name }} IS NOT NULL
        ) 
        SELECT * FROM freshness_check
        WHERE failed_rows = 1
    """,

    'accepted_benchmark_values': """
        -- Test: Benchmark values distribution validation on {{ column_name }}
       {% set table_ref = build_sample_clause(sample_config, schema, model_name) if sample_config else schema + '.' + model_name %}
        WITH actual_distribution AS (
            SELECT 
                {{ column_name }},
                COUNT(*) as actual_count,
                COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as actual_percentage
            FROM {{ table_ref }}               -- before sampling FROM {{ schema }}.{{ model_name }}
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
                percentage_diff,
                CONCAT({{ column_name }}, ' (', ROUND(actual_percentage, 1), '% vs ', expected_percentage, '% expected)') as violation_detail
            FROM benchmark_comparison
            WHERE percentage_diff > {{ threshold }} * 100
            LIMIT 10
        )
        SELECT 
            '{{ column_name }}' as column_name,
            (SELECT COUNT(*) FROM benchmark_comparison WHERE percentage_diff > {{ threshold }} * 100) as failed_rows,
            (SELECT COUNT(DISTINCT {{ column_name }}) FROM {{ schema }}.{{ model_name }}) as total_rows,
            'Benchmark violations found in distribution' as message,
            -- NOUVEAU : Exemples de violations de distribution
            STRING_AGG(violation_detail, ', ') as invalid_examples
        FROM violations
        HAVING (SELECT COUNT(*) FROM benchmark_comparison WHERE percentage_diff > {{ threshold }} * 100) > 0
    """,

    'statistical_threshold': """
        -- Test: Statistical threshold for {{ metric }} on {{ column_name or 'table' }}
        {% set table_ref = build_sample_clause(sample_config, schema, model_name) if sample_config else schema + '.' + model_name %}
        WITH daily_metrics AS (
            SELECT 
                DATE(created_at) as metric_date,
                {% if column_name %}
                    {% if metric == 'count' %}
                        COUNT({{ column_name }}) as daily_value
                    {% elif metric == 'avg' %}
                        AVG({{ column_name }}) as daily_value
                    {% elif metric == 'sum' %}
                        SUM({{ column_name }}) as daily_value
                    {% elif metric == 'min' %}
                        MIN({{ column_name }}) as daily_value
                    {% elif metric == 'max' %}
                        MAX({{ column_name }}) as daily_value
                    {% else %}
                        COUNT({{ column_name }}) as daily_value
                    {% endif %}
                {% else %}
                    {% if metric == 'count' %}
                        COUNT(*) as daily_value
                    {% else %}
                        COUNT(*) as daily_value
                    {% endif %}
                {% endif %}
            FROM {{ table_ref }}                    -- before sampling FROM {{ schema }}.{{ model_name }}
            WHERE DATE(created_at) BETWEEN 
                CURRENT_DATE - INTERVAL '{{ window_days or 30 }} days' 
                AND CURRENT_DATE - INTERVAL '1 day'
            GROUP BY DATE(created_at)
        ),
        current_value AS (
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
                AVG(daily_value) as avg_metric,
                STDDEV(daily_value) as stddev_metric
            FROM daily_metrics
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
                ROUND(COALESCE(avg_metric, 0), 2)
            ) as message,
            -- NOUVEAU : Exemples avec valeurs statistiques
            CONCAT('Current: ', ROUND(current_metric, 2), ', Historical avg: ', ROUND(COALESCE(avg_metric, 0), 2), ', Threshold: ', ROUND(threshold_value, 2)) as invalid_examples
        FROM threshold_check
        WHERE threshold_exceeded = 1
    """,
    'custom_sql': """
        -- Test: Custom SQL validation
        {{ custom_sql }}
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

# Sampling first step 1 : Utility function to build sampling clause
def build_sample_clause(sample_config: Dict[str, Any], schema: str, model_name: str) -> str:
        """Build SQL sampling clause based on configuration"""
        
        if not sample_config:
            return f"{schema}.{model_name}"
        
        base_table = f"{schema}.{model_name}"
        
        if 'partitioned_by' in sample_config:
            partition_column = sample_config['partitioned_by']
            strategy = sample_config.get('partition_strategy', 'latest')
            
            if strategy == 'latest':
                count = sample_config.get('partition_count', 1)
                base_table = f"""(
                    SELECT * FROM {base_table}
                    WHERE {partition_column} >= (
                        SELECT DISTINCT {partition_column}
                        FROM {base_table}
                        ORDER BY {partition_column} DESC
                        LIMIT 1 OFFSET {count - 1}
                    ) AS partitioned_data
                )"""
            
            elif strategy == 'range':
                start_date = sample_config.get('partition_start')
                end_date = sample_config.get('partition_end')
                if start_date and end_date:
                    base_table = f"""(
                        SELECT * FROM {base_table}
                        WHERE {partition_column} BETWEEN '{start_date}' AND '{end_date}'
                    ) AS partitioned_data """
            
            elif strategy == 'list':
                partition_list = sample_config.get('partition_list', [])
                if partition_list:
                    partitions_str = "', '".join(str(p) for p in partition_list)
                    base_table = f"""(
                        SELECT * FROM {base_table}
                        WHERE {partition_column} IN ('{partitions_str}')
                    ) AS partitioned_data """
                    
        method = sample_config.get('method')

        if method == 'random':
            if 'percentage' in sample_config:
                pct = sample_config['percentage']
                # Si base_table a déjà un alias (partition), on garde
                # Sinon on ajoute un alias pour la table de base
                if 'AS partitioned_data' in base_table:
                    return f"(SELECT * FROM {base_table} ORDER BY RANDOM() LIMIT (SELECT CAST(COUNT(*) * {pct} AS INTEGER) FROM {base_table})) AS sampled_data"
                else:
                    return f"(SELECT * FROM {base_table} AS base_tbl ORDER BY RANDOM() LIMIT (SELECT CAST(COUNT(*) * {pct} AS INTEGER) FROM {base_table})) AS sampled_data"
            
            elif 'size' in sample_config:
                size = sample_config['size']
                if 'AS partitioned_data' in base_table:
                    return f"(SELECT * FROM {base_table} ORDER BY RANDOM() LIMIT {size}) AS sampled_data"
                else:
                    return f"(SELECT * FROM {base_table} ORDER BY RANDOM() LIMIT {size}) AS sampled_data"
        
        elif method == 'systematic':
            interval = sample_config.get('interval', 10)
            return f"(SELECT * FROM (SELECT *, ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) as rn FROM {base_table}) t WHERE rn % {interval} = 0) AS sampled_data"
        
        return base_table


from typing import Any, Dict, Optional


def build_sample_clause(sample_config: Optional[Dict[str, Any]], 
                       schema: str, 
                       model_name: str) -> str:
    """Build SQL sampling clause with integrated partition support"""
    
    if not sample_config:
        return f"{schema}.{model_name}"
    
    base_table = f"{schema}.{model_name}"
    
    # ÉTAPE 1 : Construire le filtre de partition si présent
    partition_filter = None
    if 'partitioned_by' in sample_config:
        partition_column = sample_config['partitioned_by']
        strategy = sample_config.get('partition_strategy', 'latest')
        
        if strategy == 'latest':
            count = sample_config.get('partition_count', 1)
            offset = count - 1
            partition_filter = f"""
                {partition_column} >= (
                    SELECT DISTINCT {partition_column}
                    FROM {base_table}
                    ORDER BY {partition_column} DESC
                    LIMIT 1 OFFSET {offset}
                )
            """
        
        elif strategy == 'range':
            start_date = sample_config.get('partition_start')
            end_date = sample_config.get('partition_end')
            if start_date and end_date:
                partition_filter = f"{partition_column} BETWEEN '{start_date}' AND '{end_date}'"
        
        elif strategy == 'list':
            partition_list = sample_config.get('partition_list', [])
            if partition_list:
                partitions_str = "', '".join(str(p) for p in partition_list)
                partition_filter = f"{partition_column} IN ('{partitions_str}')"
    
    # ÉTAPE 2 : Appliquer partition + sampling
    method = sample_config.get('method')
    
    # Cas 1 : Partition + Random sampling
    if partition_filter and method == 'random':
        if 'percentage' in sample_config:
            pct = sample_config['percentage']
            return f"""(
                SELECT * FROM {base_table}
                WHERE {partition_filter}
                ORDER BY RANDOM()
                LIMIT (SELECT CAST(COUNT(*) * {pct} AS INTEGER) FROM {base_table} WHERE {partition_filter})
            ) AS sampled_data"""
        elif 'size' in sample_config:
            size = sample_config['size']
            return f"""(
                SELECT * FROM {base_table}
                WHERE {partition_filter}
                ORDER BY RANDOM()
                LIMIT {size}
            ) AS sampled_data"""
    
    # Cas 2 : Random sampling sans partition
    elif method == 'random':
        if 'percentage' in sample_config:
            pct = sample_config['percentage']
            return f"""(
                SELECT * FROM {base_table}
                ORDER BY RANDOM()
                LIMIT (SELECT CAST(COUNT(*) * {pct} AS INTEGER) FROM {base_table})
            ) AS sampled_data"""
        elif 'size' in sample_config:
            size = sample_config['size']
            return f"""(
                SELECT * FROM {base_table}
                ORDER BY RANDOM()
                LIMIT {size}
            ) AS sampled_data"""
    
    
    # Cas 3 : Partition uniquement (pas de sampling)
    elif partition_filter:
        return f"""(
            SELECT * FROM {base_table}
            WHERE {partition_filter}
        ) AS partitioned_data"""
    
    # Cas 5 : Aucun sampling ni partition
    return base_table