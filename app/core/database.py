import asyncpg
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None

async def get_pool() -> asyncpg.Pool:
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
async def get_db_connection():
    """Get a database connection from the pool"""
    pool = await get_pool()
    
    async with pool.acquire() as connection:
        try:
            yield connection
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise

async def test_connection() -> Dict[str, Any]:
    """Test database connection and return connection details"""
    try:
        async with get_db_connection() as conn:
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