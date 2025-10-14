"""
2QC+ Database-Specific SQL Functions
Provides lambda templates for PostgreSQL, BigQuery, Snowflake, and Redshift.
"""

DB_FUNCTIONS = {
    "postgresql": {
        "string_agg": lambda col: f"STRING_AGG({col}::text, ', ')",
        "cast_text": lambda col: f"{col}::text",
        "limit": lambda n: f"LIMIT {n}",
        "limit_offset": lambda limit, offset: f"LIMIT {limit} OFFSET {offset}",
        "current_date": lambda: "CURRENT_DATE",
        "random_func": lambda: "RANDOM()",
        "coalesce": lambda a, b: f"COALESCE({a}, {b})",
        "regex_not_match": lambda col, pattern: f"NOT ({col} ~ '{pattern}')",
        "date_sub": lambda date_col, days: f"{date_col} - INTERVAL '{days} days'",
        "date_cast": lambda col: f"CAST({col} AS DATE)",
    },

    "bigquery": {
        "string_agg": lambda col: f"STRING_AGG(CAST({col} AS STRING), ', ')",
        "cast_text": lambda col: f"CAST({col} AS STRING)",
        "limit": lambda n: f"LIMIT {n}",
        "limit_offset": lambda limit, offset: f"LIMIT {limit} OFFSET {offset}",
        "current_date": lambda: "CURRENT_DATE()",
        "random_func": lambda: "RAND()",
        "coalesce": lambda a, b: f"IFNULL({a}, {b})",
        "regex_not_match": lambda col, pattern: f"NOT REGEXP_CONTAINS({col}, '{pattern}')",
        "date_sub": lambda date_col, days: f"DATE_SUB({date_col}, INTERVAL {days} DAY)",
        "date_cast": lambda col: f"DATE({col})",
    },

    "snowflake": {
        "string_agg": lambda col: f"LISTAGG({col}, ', ')",
        "cast_text": lambda col: f"CAST({col} AS STRING)",
        "limit": lambda n: f"LIMIT {n}",
        "limit_offset": lambda limit, offset: f"LIMIT {limit} OFFSET {offset}",
        "current_date": lambda: "CURRENT_DATE()",
        "random_func": lambda: "RANDOM()",
        "coalesce": lambda a, b: f"COALESCE({a}, {b})",
        "regex_not_match": lambda col, pattern: f"NOT REGEXP_LIKE({col}, '{pattern}')",
        "date_sub": lambda date_col, days: f"DATEADD(day, -{days}, {date_col})",
        "date_cast": lambda col: f"CAST({col} AS DATE)",
    },

    "redshift": {
        "string_agg": lambda col: f"LISTAGG({col}, ', ')",
        "cast_text": lambda col: f"CAST({col} AS VARCHAR)",
        "limit": lambda n: f"LIMIT {n}",
        "limit_offset": lambda limit, offset: f"LIMIT {limit} OFFSET {offset}",
        "current_date": lambda: "CURRENT_DATE",
        "random_func": lambda: "RANDOM()",
        "coalesce": lambda a, b: f"COALESCE({a}, {b})",
        "regex_not_match": lambda col, pattern: f"NOT ({col} ~ '{pattern}')",
        "date_sub": lambda date_col, days: f"{date_col} - INTERVAL '{days} days'",
        "date_cast": lambda col: f"CAST({col} AS DATE)",
    },
}

DB_LEVEL2_FUNCTIONS = {
    'postgresql': {
        'current_date': lambda: "CURRENT_DATE",
        'date_sub': lambda date_col, days: f"{date_col} - INTERVAL '{days} days'",
        'date_trunc_day': lambda col: f"DATE_TRUNC('day', {col})",
        'date_trunc_week': lambda col: f"DATE_TRUNC('week', {col})",
        'date_trunc_month': lambda col: f"DATE_TRUNC('month', {col})",
        'cast_date': lambda col: f"CAST({col} AS DATE)",
    },
    'bigquery': {
        'current_date': lambda: "CURRENT_DATE()",
        'date_sub': lambda date_col, days: f"DATE_SUB({date_col}, INTERVAL {days} DAY)",
        'date_trunc_day': lambda col: f"DATE_TRUNC(CAST({col} AS DATE), DAY)",
        'date_trunc_week': lambda col: f"DATE_TRUNC(CAST({col} AS DATE), WEEK(MONDAY))",
        'date_trunc_month': lambda col: f"DATE_TRUNC(CAST({col} AS DATE), MONTH)",
        'cast_date': lambda col: f"CAST({col} AS DATE)",
    },
    'snowflake': {
        'current_date': lambda: "CURRENT_DATE()",
        'date_sub': lambda date_col, days: f"DATEADD(day, -{days}, {date_col})",
        'date_trunc_day': lambda col: f"DATE_TRUNC('DAY', {col})",
        'date_trunc_week': lambda col: f"DATE_TRUNC('WEEK', {col})",
        'date_trunc_month': lambda col: f"DATE_TRUNC('MONTH', {col})",
        'cast_date': lambda col: f"CAST({col} AS DATE)",
    },
}
