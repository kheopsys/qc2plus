"""
2QC+ Database Connection Manager (CORRIGÉ FINAL)
Supports PostgreSQL, Snowflake, BigQuery, Redshift
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import pandas as pd
import json


class ConnectionManager:
    """Manages database connections for multiple database types"""
    
    def __init__(self, profiles: Dict[str, Any], target: str):
        self.profiles = profiles
        self.target = target
        self.data_engine: Optional[Engine] = None
        self.quality_engine: Optional[Engine] = None
        self.db_type: Optional[str] = None
        self.quality_db_type: Optional[str] = None
        
        # Get target configuration
        profile_name = list(profiles.keys())[0]
        profile = profiles[profile_name]
        
        if target not in profile['outputs']:
            raise ValueError(f"Target '{target}' not found in profiles")
            
        self.target_config = profile['outputs'][target]
        
        # Support both old format (single DB) and new format (separated DBs)
        if 'data_source' in self.target_config:
            # New format: separated databases
            self.data_config = self.target_config['data_source']
            self.quality_config = self.target_config['quality_output']
            self.db_type = self.data_config['type']
            self.quality_db_type = self.quality_config['type']
        else:
            # Old format: single database for both data and quality
            self.data_config = self.target_config
            self.quality_config = self.target_config
            self.db_type = self.target_config['type']
            self.quality_db_type = self.target_config['type']
        
        # Initialize connections
        self._create_engines()
    
    def _create_engines(self) -> None:
        """Create SQLAlchemy engines for both data and quality databases"""
        try:
            # Create data source engine
            self.data_engine = self._create_engine(self.data_config, self.db_type)
            
            # Create quality output engine
            if self.data_config == self.quality_config:
                # Same database, reuse connection
                self.quality_engine = self.data_engine
            else:
                # Different database, create separate connection
                self.quality_engine = self._create_engine(self.quality_config, self.quality_db_type)
                
        except Exception as e:
            logging.error(f"Failed to create database engines: {str(e)}")
            raise
    
    def _create_engine(self, config: Dict[str, Any], db_type: str) -> Engine:
        """Create SQLAlchemy engine based on database type and config"""
        if db_type == 'postgresql':
            return self._create_postgresql_engine(config)
        elif db_type == 'snowflake':
            return self._create_snowflake_engine(config)
        elif db_type == 'bigquery':
            return self._create_bigquery_engine(config)
        elif db_type == 'redshift':
            return self._create_redshift_engine(config)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
    
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None, use_data_source: bool = True) -> pd.DataFrame:
        """Execute a query and return results as DataFrame"""
        try:
            engine = self.data_engine if use_data_source else self.quality_engine
            with engine.connect() as conn:
                if params:
                    clean_params = json.loads(json.dumps(params, default=str))
                    return pd.read_sql(text(query), conn, params=clean_params)
                else:
    
                    return pd.read_sql(text(query), conn)
        except Exception as e:
            logging.error(f"Query execution failed: {str(e)}")
            raise
    

    def execute_sql(self, sql: str, params: Optional[Dict[str, Any]] = None, use_data_source: bool = False) -> Any:
        """Execute SQL statement (for non-SELECT queries)"""
        try:
            from datetime import datetime, timezone

            engine = self.data_engine if use_data_source else self.quality_engine

            # 🔹 Convert Python datetime to BigQuery-compatible TIMESTAMP string
            if params:
                clean_params = dict(params)
                if self.quality_db_type == "bigquery":
                    for key, value in clean_params.items():
                        if isinstance(value, datetime):
                            # Si datetime sans timezone → ajouter UTC
                            if value.tzinfo is None:
                                value = value.replace(tzinfo=timezone.utc)
                            # Convertir en ISO 8601 compatible TIMESTAMP BigQuery
                            clean_params[key] = value.isoformat()
            else:
                clean_params = {}

            with engine.begin() as conn:
                result = conn.execute(text(sql), clean_params)
                return result

        except Exception as e:
            logging.error(f"SQL execution failed: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """Test both database connections"""
        try:
            # Test data source connection
            with self.data_engine.connect() as conn:
                if self.db_type == 'bigquery':
                    result = conn.execute(text("SELECT 1 as test"))
                else:
                    result = conn.execute(text("SELECT 1"))
                result.fetchone()
            logging.info("✅ DATA source: OK")
            
            # Test quality database connection (if different)
            if self.data_engine != self.quality_engine:
                with self.quality_engine.connect() as conn:
                    if self.quality_db_type == 'bigquery':
                        result = conn.execute(text("SELECT 1 as test"))
                    else:
                        result = conn.execute(text("SELECT 1"))
                    result.fetchone()
                logging.info("✅ QUALITY output: OK")
                    
            return True
                
        except Exception as e:
            logging.error(f"Connection test failed: {str(e)}")
            return False
    
    def create_quality_tables(self) -> None:
        """Create quality monitoring tables in the quality database"""
        
        schema = self.quality_config.get('schema', 'public')
        create_schema_sql = f"CREATE SCHEMA IF NOT EXISTS {schema}"
        
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
                target_environment VARCHAR(50),
                explanation TEXT,
                examples TEXT,
                query TEXT
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
        
        # Adapt SQL for BigQuery
        if self.quality_db_type == 'bigquery':
            quality_test_results_sql = self._adapt_sql_for_bigquery(quality_test_results_sql)
            quality_run_summary_sql = self._adapt_sql_for_bigquery(quality_run_summary_sql)
            quality_anomalies_sql = self._adapt_sql_for_bigquery(quality_anomalies_sql)
        
        try:
            with self.quality_engine.begin() as conn:
                if self.quality_db_type != 'bigquery':
                    logging.info(f"Creating schema if not exists: {schema}")
                    conn.execute(text(create_schema_sql))
                conn.execute(text(quality_test_results_sql))
                conn.execute(text(quality_run_summary_sql))
                conn.execute(text(quality_anomalies_sql))
            logging.info(f"Quality monitoring tables created successfully in schema: {schema}")
        except Exception as e:
            logging.error(f"Failed to create quality tables: {str(e)}")
            raise
    
    def _adapt_sql_for_bigquery(self, sql: str) -> str:
        """Adapt SQL for BigQuery"""
        sql = sql.replace('VARCHAR(255)', 'STRING')
        sql = sql.replace('VARCHAR(50)', 'STRING')
        sql = sql.replace('VARCHAR(20)', 'STRING')
        sql = sql.replace('VARCHAR(10)', 'STRING')
        sql = sql.replace('VARCHAR(100)', 'STRING')
        sql = sql.replace('TEXT', 'STRING')
        sql = sql.replace('INTEGER', 'INT64')
        sql = sql.replace('DECIMAL(10,4)', 'FLOAT64')
        sql = sql.replace('CURRENT_TIMESTAMP', 'CURRENT_TIMESTAMP()')

        sql = sql.replace('PRIMARY KEY', '')
        sql = sql.replace('NOT NULL', '') 

        return sql
    
    @property 
    def config(self):
        """Return data source config for backward compatibility"""
        return self.data_config
    
    def _create_postgresql_engine(self, config: Dict[str, Any]) -> Engine:
        """Create PostgreSQL engine"""
        # CORRECTION : Utiliser le paramètre config au lieu de self.config
        connection_string = (
            f"postgresql://{config['user']}:{config['password']}"
            f"@{config['host']}:{config['port']}"
            f"/{config['dbname']}"
        )
        return create_engine(connection_string)
    
    def _create_snowflake_engine(self, config: Dict[str, Any]) -> Engine:
        """Create Snowflake engine"""
        try:
            from snowflake.sqlalchemy import URL
        except ImportError:
            raise ImportError("snowflake-sqlalchemy package required for Snowflake connections")
            
        connection_string = URL(
            account=config['account'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            schema=config['schema'],
            warehouse=config['warehouse'],
            role=config.get('role')
        )
        return create_engine(connection_string)
    
    def _create_bigquery_engine(self, config: Dict[str, Any]) -> Engine:
        """Create BigQuery engine"""
        try:
            from sqlalchemy_bigquery import BigQueryDialect
        except ImportError:
            raise ImportError("sqlalchemy-bigquery package required for BigQuery connections")
            
        if config.get('method') == 'service-account':
            connection_string = (
                f"bigquery://{config['project']}/{config['dataset']}"
                f"?credentials_path={config['keyfile']}"
            )
        else:
            connection_string = f"bigquery://{config['project']}/{config['dataset']}"
            
        return create_engine(connection_string)
    
    def _create_redshift_engine(self, config: Dict[str, Any]) -> Engine:
        """Create Redshift engine"""
        connection_string = (
            f"redshift+psycopg2://{config['user']}:{config['password']}"
            f"@{config['host']}:{config['port']}"
            f"/{config['dbname']}"
        )
        return create_engine(connection_string)
    
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
            params = {'table_name': table_name, 'schema': schema}
        elif self.db_type == 'bigquery':
            query = f"""
                SELECT column_name, data_type, is_nullable
                FROM `{self.config['project']}.{schema}.INFORMATION_SCHEMA.COLUMNS`
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """
            params = None
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
        
        try:
            df = self.execute_query(query, params, use_data_source=True)
            return {
                'columns': df.to_dict('records'),
                'column_count': len(df),
                'table_name': table_name,
                'schema': schema
            }
        except Exception as e:
            logging.error(f"Failed to get table info for {schema}.{table_name}: {str(e)}")
            return {'columns': [], 'column_count': 0, 'table_name': table_name, 'schema': schema}
    
