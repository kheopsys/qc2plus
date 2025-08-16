"""
2QC+ Database Connection Manager
Supports PostgreSQL, Snowflake, BigQuery, Redshift
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import pandas as pd


class ConnectionManager:
    """Manages database connections for multiple database types"""
    
    def __init__(self, profiles: Dict[str, Any], target: str):
        self.profiles = profiles
        self.target = target
        self.engine: Optional[Engine] = None
        self.db_type: Optional[str] = None
        
        # Get target configuration
        profile_name = list(profiles.keys())[0]  # Assume first profile for now
        profile = profiles[profile_name]
        
        if target not in profile['outputs']:
            raise ValueError(f"Target '{target}' not found in profiles")
            
        self.config = profile['outputs'][target]
        self.db_type = self.config['type']
        
        # Initialize connection
        self._create_engine()
    
    def _create_engine(self) -> None:
        """Create SQLAlchemy engine based on database type"""
        try:
            if self.db_type == 'postgresql':
                self.engine = self._create_postgresql_engine()
            elif self.db_type == 'snowflake':
                self.engine = self._create_snowflake_engine()
            elif self.db_type == 'bigquery':
                self.engine = self._create_bigquery_engine()
            elif self.db_type == 'redshift':
                self.engine = self._create_redshift_engine()
            else:
                raise ValueError(f"Unsupported database type: {self.db_type}")
                
        except Exception as e:
            logging.error(f"Failed to create database engine: {str(e)}")
            raise
    
    def _create_postgresql_engine(self) -> Engine:
        """Create PostgreSQL engine"""
        connection_string = (
            f"postgresql://{self.config['user']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}"
            f"/{self.config['dbname']}"
        )
        return create_engine(connection_string)
    
    def _create_snowflake_engine(self) -> Engine:
        """Create Snowflake engine"""
        try:
            from snowflake.sqlalchemy import URL
        except ImportError:
            raise ImportError("snowflake-sqlalchemy package required for Snowflake connections")
            
        connection_string = URL(
            account=self.config['account'],
            user=self.config['user'],
            password=self.config['password'],
            database=self.config['database'],
            schema=self.config['schema'],
            warehouse=self.config['warehouse'],
            role=self.config.get('role')
        )
        return create_engine(connection_string)
    
    def _create_bigquery_engine(self) -> Engine:
        """Create BigQuery engine"""
        try:
            from sqlalchemy_bigquery import BigQueryDialect
        except ImportError:
            raise ImportError("sqlalchemy-bigquery package required for BigQuery connections")
            
        if self.config.get('method') == 'service-account':
            connection_string = (
                f"bigquery://{self.config['project']}/{self.config['dataset']}"
                f"?credentials_path={self.config['keyfile']}"
            )
        else:
            # OAuth method
            connection_string = f"bigquery://{self.config['project']}/{self.config['dataset']}"
            
        return create_engine(connection_string)
    
    def _create_redshift_engine(self) -> Engine:
        """Create Redshift engine"""
        connection_string = (
            f"redshift+psycopg2://{self.config['user']}:{self.config['password']}"
            f"@{self.config['host']}:{self.config['port']}"
            f"/{self.config['dbname']}"
        )
        return create_engine(connection_string)
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                # Simple query to test connection
                if self.db_type == 'bigquery':
                    result = conn.execute(text("SELECT 1 as test"))
                else:
                    result = conn.execute(text("SELECT 1"))
                
                # Fetch result to ensure query executes
                result.fetchone()
                return True
                
        except Exception as e:
            logging.error(f"Connection test failed: {str(e)}")
            return False
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute a query and return results as DataFrame"""
        try:
            with self.engine.connect() as conn:
                return pd.read_sql(text(query), conn)
        except Exception as e:
            logging.error(f"Query execution failed: {str(e)}")
            raise
    
    def execute_sql(self, sql: str, params: dict = None) -> Any:
        """Execute SQL statement (for non-SELECT queries)"""
        try:
            with self.engine.connect() as conn:
                if params:
                    result = conn.execute(text(sql), params)
                else:
                    result = conn.execute(text(sql))
                conn.commit()
                return result
        except Exception as e:
            logging.error(f"SQL execution failed: {str(e)}")
            raise
    
    def get_table_info(self, table_name: str, schema: str = None) -> Dict[str, Any]:
        """Get table information (columns, types, etc.)"""
        schema = schema or self.config.get('schema', 'public')
        
        if self.db_type == 'postgresql':
            query = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = %(table_name)s
                AND table_schema = %(schema)s
                ORDER BY ordinal_position
            """
        elif self.db_type == 'snowflake':
            query = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = %(table_name)s
                AND table_schema = %(schema)s
                ORDER BY ordinal_position
            """
        elif self.db_type == 'bigquery':
            query = f"""
                SELECT column_name, data_type, is_nullable
                FROM `{self.config['project']}.{schema}.INFORMATION_SCHEMA.COLUMNS`
                WHERE table_name = @table_name
                ORDER BY ordinal_position
            """
        elif self.db_type == 'redshift':
            query = """
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = %(table_name)s
                AND table_schema = %(schema)s
                ORDER BY ordinal_position
            """
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
        
        try:
            if self.db_type == 'bigquery':
                # BigQuery uses named parameters differently
                df = self.execute_query(query.replace('@table_name', f"'{table_name}'"))
            else:
                df = self.execute_query(query % {'table_name': table_name, 'schema': schema})
            
            return {
                'columns': df.to_dict('records'),
                'column_count': len(df),
                'table_name': table_name,
                'schema': schema
            }
        except Exception as e:
            logging.error(f"Failed to get table info for {schema}.{table_name}: {str(e)}")
            return {'columns': [], 'column_count': 0, 'table_name': table_name, 'schema': schema}
    
    def create_quality_tables(self) -> None:
        """Create quality monitoring tables for Power BI integration"""
        schema = self.config.get('schema', 'public')
        
        # Table 1: quality_test_results
        quality_test_results_sql = f"""
            CREATE TABLE IF NOT EXISTS {schema}.quality_test_results (
                test_id VARCHAR(255) PRIMARY KEY,
                model_name VARCHAR(255) NOT NULL,
                test_name VARCHAR(255) NOT NULL,
                test_type VARCHAR(50) NOT NULL,
                level VARCHAR(10) NOT NULL,
                severity VARCHAR(20) NOT NULL,
                status VARCHAR(20) NOT NULL,
                message TEXT,
                failed_rows INTEGER,
                total_rows INTEGER,
                execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                target_environment VARCHAR(50)
            )
        """
        
        # Table 2: quality_run_summary
        quality_run_summary_sql = f"""
            CREATE TABLE IF NOT EXISTS {schema}.quality_run_summary (
                run_id VARCHAR(255) PRIMARY KEY,
                project_name VARCHAR(255) NOT NULL,
                execution_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                target_environment VARCHAR(50),
                total_models INTEGER,
                total_tests INTEGER,
                passed_tests INTEGER,
                failed_tests INTEGER,
                critical_failures INTEGER,
                execution_duration_seconds INTEGER,
                status VARCHAR(20)
            )
        """
        
        # Table 3: quality_anomalies
        quality_anomalies_sql = f"""
            CREATE TABLE IF NOT EXISTS {schema}.quality_anomalies (
                anomaly_id VARCHAR(255) PRIMARY KEY,
                model_name VARCHAR(255) NOT NULL,
                analyzer_type VARCHAR(50) NOT NULL,
                anomaly_type VARCHAR(100) NOT NULL,
                anomaly_score DECIMAL(10,4),
                affected_columns TEXT,
                anomaly_details TEXT,
                detection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                severity VARCHAR(20),
                target_environment VARCHAR(50)
            )
        """
        
        # Adapt SQL for different databases
        if self.db_type == 'bigquery':
            quality_test_results_sql = quality_test_results_sql.replace('VARCHAR(255)', 'STRING')
            quality_test_results_sql = quality_test_results_sql.replace('VARCHAR(50)', 'STRING')
            quality_test_results_sql = quality_test_results_sql.replace('VARCHAR(20)', 'STRING')
            quality_test_results_sql = quality_test_results_sql.replace('VARCHAR(10)', 'STRING')
            quality_test_results_sql = quality_test_results_sql.replace('TEXT', 'STRING')
            quality_test_results_sql = quality_test_results_sql.replace('INTEGER', 'INT64')
            quality_test_results_sql = quality_test_results_sql.replace('CURRENT_TIMESTAMP', 'CURRENT_TIMESTAMP()')
            
            quality_run_summary_sql = quality_run_summary_sql.replace('VARCHAR(255)', 'STRING')
            quality_run_summary_sql = quality_run_summary_sql.replace('VARCHAR(50)', 'STRING')
            quality_run_summary_sql = quality_run_summary_sql.replace('VARCHAR(20)', 'STRING')
            quality_run_summary_sql = quality_run_summary_sql.replace('INTEGER', 'INT64')
            quality_run_summary_sql = quality_run_summary_sql.replace('CURRENT_TIMESTAMP', 'CURRENT_TIMESTAMP()')
            
            quality_anomalies_sql = quality_anomalies_sql.replace('VARCHAR(255)', 'STRING')
            quality_anomalies_sql = quality_anomalies_sql.replace('VARCHAR(50)', 'STRING')
            quality_anomalies_sql = quality_anomalies_sql.replace('VARCHAR(100)', 'STRING')
            quality_anomalies_sql = quality_anomalies_sql.replace('VARCHAR(20)', 'STRING')
            quality_anomalies_sql = quality_anomalies_sql.replace('TEXT', 'STRING')
            quality_anomalies_sql = quality_anomalies_sql.replace('DECIMAL(10,4)', 'FLOAT64')
            quality_anomalies_sql = quality_anomalies_sql.replace('CURRENT_TIMESTAMP', 'CURRENT_TIMESTAMP()')
        
        try:
            self.execute_sql(quality_test_results_sql)
            self.execute_sql(quality_run_summary_sql)
            self.execute_sql(quality_anomalies_sql)
            logging.info("Quality monitoring tables created successfully")
        except Exception as e:
            logging.error(f"Failed to create quality tables: {str(e)}")
            raise
    
    def get_db_adapter(self) -> 'DatabaseAdapter':
        """Get database-specific adapter for SQL generation"""
        if self.db_type == 'postgresql':
            return PostgreSQLAdapter()
        elif self.db_type == 'snowflake':
            return SnowflakeAdapter()
        elif self.db_type == 'bigquery':
            return BigQueryAdapter()
        elif self.db_type == 'redshift':
            return RedshiftAdapter()
        else:
            raise ValueError(f"No adapter available for {self.db_type}")


class DatabaseAdapter:
    """Base class for database-specific SQL adaptations"""
    
    def adapt_regex(self, pattern: str) -> str:
        """Adapt regex pattern for database"""
        return pattern
    
    def adapt_date_functions(self, sql: str) -> str:
        """Adapt date functions for database"""
        return sql
    
    def adapt_statistical_functions(self, sql: str) -> str:
        """Adapt statistical functions for database"""
        return sql


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL-specific SQL adaptations"""
    
    def adapt_regex(self, pattern: str) -> str:
        return f"{pattern}"
    
    def adapt_date_functions(self, sql: str) -> str:
        sql = sql.replace('DATE_DIFF', 'DATE_PART')
        sql = sql.replace('CURRENT_DATE()', 'CURRENT_DATE')
        return sql


class SnowflakeAdapter(DatabaseAdapter):
    """Snowflake-specific SQL adaptations"""
    
    def adapt_regex(self, pattern: str) -> str:
        return f"REGEXP '{pattern}'"
    
    def adapt_date_functions(self, sql: str) -> str:
        sql = sql.replace('DATE_DIFF', 'DATEDIFF')
        return sql


class BigQueryAdapter(DatabaseAdapter):
    """BigQuery-specific SQL adaptations"""
    
    def adapt_regex(self, pattern: str) -> str:
        return f"REGEXP_CONTAINS(column, r'{pattern}')"
    
    def adapt_date_functions(self, sql: str) -> str:
        sql = sql.replace('DATE_DIFF', 'DATE_DIFF')
        sql = sql.replace('CURRENT_DATE', 'CURRENT_DATE()')
        return sql


class RedshiftAdapter(DatabaseAdapter):
    """Redshift-specific SQL adaptations"""
    
    def adapt_regex(self, pattern: str) -> str:
        return f"~ '{pattern}'"
    
    def adapt_date_functions(self, sql: str) -> str:
        sql = sql.replace('DATE_DIFF', 'DATEDIFF')
        sql = sql.replace('CURRENT_DATE()', 'CURRENT_DATE')
        return sql
