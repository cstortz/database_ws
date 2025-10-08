import asyncpg
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List, Tuple, Union
from dataclasses import dataclass
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None

def convert_datetime_to_string(obj: Any) -> Any:
    """Convert datetime objects to ISO format strings recursively"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: convert_datetime_to_string(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_datetime_to_string(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_datetime_to_string(item) for item in obj)
    else:
        return obj

@dataclass
class PreparedStatement:
    """Represents a prepared statement with its SQL and parameters"""
    sql: str
    parameters: Tuple[Any, ...]
    name: Optional[str] = None

class DatabaseManager:
    """Database manager with prepared statement support"""
    
    def __init__(self):
        self.prepared_statements: Dict[str, PreparedStatement] = {}
    
    async def get_pool(self) -> asyncpg.Pool:
        """Get or create the connection pool"""
        global _pool
        
        if _pool is None:
            try:
                _pool = await asyncpg.create_pool(
                    settings.DATABASE_URL,
                    min_size=settings.MIN_CONNECTIONS,
                    max_size=settings.MAX_CONNECTIONS,
                    command_timeout=30,
                    server_settings={
                        "application_name": "database_service"
                    }
                )
                logger.info(f"Created connection pool to {settings.PGBOUNCER_HOST}:{settings.PGBOUNCER_PORT}")
            except Exception as e:
                logger.error(f"Failed to create connection pool: {e}")
                raise
        
        return _pool
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection from the pool"""
        pool = await self.get_pool()
        
        async with pool.acquire() as connection:
            try:
                yield connection
            except Exception as e:
                logger.error(f"Database operation failed: {e}")
                raise
    
    def prepare_select_query(self, schema_name: str, table_name: str, 
                           columns: Optional[List[str]] = None,
                           where_clause: Optional[str] = None,
                           order_by: Optional[str] = None,
                           limit: Optional[int] = None,
                           offset: Optional[int] = None) -> PreparedStatement:
        """Prepare a SELECT query with parameters"""
        # Build column list
        if columns:
            column_list = ", ".join(columns)
        else:
            column_list = "*"
        
        # Build the base query
        sql_parts = [f"SELECT {column_list} FROM {schema_name}.{table_name}"]
        parameters = []
        param_count = 0
        
        # Add WHERE clause if provided
        if where_clause:
            sql_parts.append(f"WHERE {where_clause}")
        
        # Add ORDER BY if provided
        if order_by:
            sql_parts.append(f"ORDER BY {order_by}")
        
        # Add LIMIT and OFFSET
        if limit is not None:
            param_count += 1
            sql_parts.append(f"LIMIT ${param_count}")
            parameters.append(limit)
        
        if offset is not None:
            param_count += 1
            sql_parts.append(f"OFFSET ${param_count}")
            parameters.append(offset)
        
        sql = " ".join(sql_parts)
        return PreparedStatement(sql, tuple(parameters))
    
    def prepare_count_query(self, schema_name: str, table_name: str,
                          where_clause: Optional[str] = None) -> PreparedStatement:
        """Prepare a COUNT query with parameters"""
        sql_parts = [f"SELECT COUNT(*) FROM {schema_name}.{table_name}"]
        parameters = []
        
        if where_clause:
            sql_parts.append(f"WHERE {where_clause}")
        
        sql = " ".join(sql_parts)
        return PreparedStatement(sql, tuple(parameters))
    
    def prepare_insert_query(self, schema_name: str, table_name: str,
                           data: Dict[str, Any]) -> PreparedStatement:
        """Prepare an INSERT query with parameters"""
        columns = list(data.keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]
        values = list(data.values())
        
        sql = f"""
            INSERT INTO {schema_name}.{table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """
        
        return PreparedStatement(sql, tuple(values))
    
    def prepare_update_query(self, schema_name: str, table_name: str,
                           record_id: Union[int, str], data: Dict[str, Any]) -> PreparedStatement:
        """Prepare an UPDATE query with parameters"""
        columns = list(data.keys())
        set_clause = ", ".join([f"{col} = ${i+2}" for i, col in enumerate(columns)])
        values = list(data.values())
        
        # Add record_id as the first parameter
        all_values = [record_id] + values
        
        sql = f"""
            UPDATE {schema_name}.{table_name}
            SET {set_clause}
            WHERE id = $1
            RETURNING *
        """
        
        return PreparedStatement(sql, tuple(all_values))
    
    def prepare_delete_query(self, schema_name: str, table_name: str,
                           record_id: Union[int, str]) -> PreparedStatement:
        """Prepare a DELETE query with parameters"""
        sql = f"DELETE FROM {schema_name}.{table_name} WHERE id = $1 RETURNING *"
        return PreparedStatement(sql, (record_id,))
    
    def prepare_exists_query(self, schema_name: str, table_name: str,
                           record_id: Union[int, str]) -> PreparedStatement:
        """Prepare an EXISTS query with parameters"""
        sql = f"SELECT EXISTS(SELECT 1 FROM {schema_name}.{table_name} WHERE id = $1)"
        return PreparedStatement(sql, (record_id,))
    
    def prepare_table_exists_query(self, schema_name: str, table_name: str) -> PreparedStatement:
        """Prepare a table existence check query"""
        sql = "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = $1 AND table_name = $2)"
        return PreparedStatement(sql, (schema_name, table_name))
    
    async def execute_prepared(self, stmt: PreparedStatement, connection: asyncpg.Connection) -> Any:
        """Execute a prepared statement"""
        try:
            if stmt.name:
                # Use named prepared statement
                if stmt.name not in self.prepared_statements:
                    await connection.prepare(stmt.name, stmt.sql)
                    self.prepared_statements[stmt.name] = stmt
                
                stmt_obj = connection.get_prepared_statement(stmt.name)
                result = await stmt_obj.fetch(*stmt.parameters)
            else:
                # Execute directly with parameters
                result = await connection.fetch(stmt.sql, *stmt.parameters)
            
            # Convert asyncpg Records to dicts and then convert datetime objects to strings
            if result:
                result_list = [dict(row) for row in result]
                return convert_datetime_to_string(result_list)
            return result
        except Exception as e:
            logger.error(f"Failed to execute prepared statement: {e}")
            raise
    
    async def execute_prepared_val(self, stmt: PreparedStatement, connection: asyncpg.Connection) -> Any:
        """Execute a prepared statement and return a single value"""
        try:
            if stmt.name:
                # Use named prepared statement
                if stmt.name not in self.prepared_statements:
                    await connection.prepare(stmt.name, stmt.sql)
                    self.prepared_statements[stmt.name] = stmt
                
                stmt_obj = connection.get_prepared_statement(stmt.name)
                return await stmt_obj.fetchval(*stmt.parameters)
            else:
                # Execute directly with parameters
                return await connection.fetchval(stmt.sql, *stmt.parameters)
        except Exception as e:
            logger.error(f"Failed to execute prepared statement: {e}")
            raise
    
    async def execute_prepared_row(self, stmt: PreparedStatement, connection: asyncpg.Connection) -> Any:
        """Execute a prepared statement and return a single row"""
        try:
            if stmt.name:
                # Use named prepared statement
                if stmt.name not in self.prepared_statements:
                    await connection.prepare(stmt.name, stmt.sql)
                    self.prepared_statements[stmt.name] = stmt
                
                stmt_obj = connection.get_prepared_statement(stmt.name)
                result = await stmt_obj.fetchrow(*stmt.parameters)
            else:
                # Execute directly with parameters
                result = await connection.fetchrow(stmt.sql, *stmt.parameters)
            
            # Convert asyncpg Record to dict and then convert datetime objects to strings
            if result:
                result_dict = dict(result)
                return convert_datetime_to_string(result_dict)
            return result
        except Exception as e:
            logger.error(f"Failed to execute prepared statement: {e}")
            raise

# Global database manager instance
db_manager = DatabaseManager()

# Legacy functions for backward compatibility
async def get_pool() -> asyncpg.Pool:
    """Get or create the connection pool"""
    return await db_manager.get_pool()

@asynccontextmanager
async def get_db_connection():
    """Get a database connection from the pool"""
    async with db_manager.get_connection() as connection:
        yield connection

async def test_connection() -> Dict[str, Any]:
    """Test database connection and return connection details"""
    try:
        async with db_manager.get_connection() as conn:
            # Test basic query
            version = await conn.fetchval("SELECT version()")
            db_name = await conn.fetchval("SELECT current_database()")
            current_user = await conn.fetchval("SELECT current_user")
            
            # Test if we can write (optional)
            test_table = "connection_test_temp"
            await conn.execute(f"CREATE TEMP TABLE {test_table} (id int)")
            await conn.execute(f"INSERT INTO {test_table} VALUES (1)")
            result = await conn.fetchval(f"SELECT id FROM {test_table}")
            await conn.execute(f"DROP TABLE {test_table}")
            
            return {
                "status": "connected",
                "version": version,
                "database": db_name,
                "user": current_user,
                "host": settings.PGBOUNCER_HOST,
                "port": settings.PGBOUNCER_PORT,
                "write_test": "passed" if result == 1 else "failed"
            }
            
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise Exception(f"Database connection failed: {str(e)}")

async def close_pool():
    """Close the connection pool"""
    global _pool
    
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Connection pool closed")

async def get_pool_stats() -> Dict[str, Any]:
    """Get connection pool statistics"""
    if _pool is None:
        return {
            "pool_created": False,
            "total_connections": 0,
            "active_connections": 0,
            "idle_connections": 0
        }
    
    # Get basic pool info
    total_size = _pool.get_size()
    
    return {
        "pool_created": True,
        "total_connections": total_size,
        "active_connections": total_size,  # Simplified for now
        "idle_connections": total_size,    # Simplified for now
        "free_connections": total_size     # Simplified for now
    } 