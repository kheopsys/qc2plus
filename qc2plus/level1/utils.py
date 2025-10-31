"""
2QC+ Level 1 SQL Macros
Jinja2 templates for business rule validation tests
"""

from typing import Any, Dict, Optional

from qc2plus.sql.db_functions import DB_FUNCTIONS


def get_macro_help(macro_name: str) -> str:
    """Get help text for a specific macro"""

    help_text = {
        "unique": """
        Tests that all values in a column are unique.

        Parameters:
        - column_name: Column to test
        - severity: Test severity level

        Example:
        unique:
          column_name: customer_id
          severity: critical
        """,
        "not_null": """
        Tests that a column contains no null values.

        Parameters:
        - column_name: Column to test
        - severity: Test severity level

        Example:
        not_null:
          column_name: email
          severity: critical
        """,
        "email_format": """
        Tests that email addresses follow valid format.

        Parameters:
        - column_name: Email column to validate
        - severity: Test severity level

        Example:
        email_format:
          column_name: email_address
          severity: medium
        """,
        "statistical_threshold": """
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
        """,
    }

    return help_text.get(macro_name, "No help available for this macro.")


# Sampling with partition support (multi-database compatible)
def build_sample_clause(
    sample_config: Optional[Dict[str, Any]],
    schema: str,
    model_name: str,
    db_type: str = "postgresql",
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
                partition_filter = (
                    f"{partition_column} BETWEEN '{start_date}' AND '{end_date}'"
                )

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
