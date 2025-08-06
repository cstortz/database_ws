from fastapi import FastAPI, HTTPException, APIRouter
from contextlib import asynccontextmanager
import logging
import asyncpg
from typing import Optional, List, Dict, Any

from app.core.database import get_db_connection, test_connection
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Database Service...")
    try:
        # Test database connection on startup
        await test_connection()
        logger.info("Database connection successful")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    logger.info("Database Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Database Service...")

app = FastAPI(
    title="Database Service",
    description="Simple FastAPI service connecting to PgBouncer",
    version="1.0.0",
    lifespan=lifespan
)

# Create router for admin endpoints
admin_router = APIRouter(prefix="/admin", tags=["Admin"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Database Service API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@admin_router.get("/health")
async def health_check():
    """Health check endpoint - Check if the database service is healthy and connected"""
    try:
        # Test database connection
        await test_connection()
        return {
            "status": "healthy",
            "database": "connected",
            "pgbouncer_host": settings.PGBOUNCER_HOST,
            "pgbouncer_port": settings.PGBOUNCER_PORT
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

@admin_router.get("/test-connection")
async def test_db_connection():
    """Test database connection endpoint - Verify database connectivity and get connection details"""
    try:
        result = await test_connection()
        return {
            "status": "success",
            "message": "Database connection successful",
            "details": result
        }
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@admin_router.get("/db-info")
async def get_db_info():
    """Get database information - Retrieve current database version, name, user, and connection details"""
    try:
        async with get_db_connection() as conn:
            # Get database version
            version = await conn.fetchval("SELECT version()")
            
            # Get current database name
            db_name = await conn.fetchval("SELECT current_database()")
            
            # Get current user
            current_user = await conn.fetchval("SELECT current_user")
            
            return {
                "version": version,
                "database": db_name,
                "user": current_user,
                "host": settings.PGBOUNCER_HOST,
                "port": settings.PGBOUNCER_PORT
            }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get database info: {str(e)}")

@admin_router.get("/databases")
async def get_databases():
    """Get all databases - Retrieve list of all databases with their descriptions/comments"""
    try:
        async with get_db_connection() as conn:
            query = """
                SELECT 
                    d.datname as database_name,
                    pg_catalog.pg_get_userbyid(d.datdba) as owner,
                    pg_catalog.pg_encoding_to_char(d.encoding) as encoding,
                    d.datcollate as collation,
                    d.datctype as ctype,
                    pg_catalog.array_to_string(d.datacl, E'\n') AS access_privileges,
                    CASE 
                        WHEN pg_catalog.has_database_privilege(d.datname, 'CONNECT')
                            THEN pg_catalog.pg_size_pretty(pg_catalog.pg_database_size(d.datname))
                        ELSE 'No Access'
                    END as size,
                    pg_catalog.shobj_description(d.oid, 'pg_database') as comment
                FROM pg_catalog.pg_database d
                ORDER BY 1;
            """
            rows = await conn.fetch(query)
            
            databases = []
            for row in rows:
                databases.append({
                    "database_name": row["database_name"],
                    "owner": row["owner"],
                    "encoding": row["encoding"],
                    "collation": row["collation"],
                    "ctype": row["ctype"],
                    "access_privileges": row["access_privileges"],
                    "size": row["size"],
                    "comment": row["comment"]
                })
            
            return {
                "databases": databases,
                "count": len(databases)
            }
    except Exception as e:
        logger.error(f"Failed to get databases: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get databases: {str(e)}")

@admin_router.get("/schemas")
async def get_schemas():
    """Get all schemas - Retrieve list of all schemas with their descriptions/comments"""
    try:
        async with get_db_connection() as conn:
            query = """
                SELECT 
                    n.nspname as schema_name,
                    pg_catalog.pg_get_userbyid(n.nspowner) as owner,
                    pg_catalog.array_to_string(n.nspacl, E'\n') AS access_privileges,
                    pg_catalog.obj_description(n.oid, 'pg_namespace') as comment
                FROM pg_catalog.pg_namespace n
                WHERE n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
                ORDER BY 1;
            """
            rows = await conn.fetch(query)
            
            schemas = []
            for row in rows:
                schemas.append({
                    "schema_name": row["schema_name"],
                    "owner": row["owner"],
                    "access_privileges": row["access_privileges"],
                    "comment": row["comment"]
                })
            
            return {
                "schemas": schemas,
                "count": len(schemas)
            }
    except Exception as e:
        logger.error(f"Failed to get schemas: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get schemas: {str(e)}")

@admin_router.get("/tables")
async def get_tables():
    """Get all tables - Retrieve list of all tables with their descriptions/comments"""
    try:
        async with get_db_connection() as conn:
            query = """
                SELECT 
                    t.table_schema,
                    t.table_name,
                    t.table_type,
                    pg_catalog.pg_get_userbyid(c.relowner) as owner,
                    pg_catalog.pg_size_pretty(pg_catalog.pg_total_relation_size(c.oid)) as size,
                    pg_catalog.obj_description(c.oid, 'pg_class') as comment,
                    c.reltuples as estimated_rows
                FROM information_schema.tables t
                JOIN pg_catalog.pg_class c ON c.relname = t.table_name
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace AND n.nspname = t.table_schema
                WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY t.table_schema, t.table_name;
            """
            rows = await conn.fetch(query)
            
            tables = []
            for row in rows:
                tables.append({
                    "schema": row["table_schema"],
                    "table_name": row["table_name"],
                    "table_type": row["table_type"],
                    "owner": row["owner"],
                    "size": row["size"],
                    "estimated_rows": row["estimated_rows"],
                    "comment": row["comment"]
                })
            
            return {
                "tables": tables,
                "count": len(tables)
            }
    except Exception as e:
        logger.error(f"Failed to get tables: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tables: {str(e)}")

@admin_router.get("/tables/{schema_name}")
async def get_tables_by_schema(schema_name: str):
    """Get tables by schema - Retrieve list of tables in a specific schema with their descriptions/comments"""
    try:
        async with get_db_connection() as conn:
            query = """
                SELECT 
                    t.table_schema,
                    t.table_name,
                    t.table_type,
                    pg_catalog.pg_get_userbyid(c.relowner) as owner,
                    pg_catalog.pg_size_pretty(pg_catalog.pg_total_relation_size(c.oid)) as size,
                    pg_catalog.obj_description(c.oid, 'pg_class') as comment,
                    c.reltuples as estimated_rows
                FROM information_schema.tables t
                JOIN pg_catalog.pg_class c ON c.relname = t.table_name
                JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace AND n.nspname = t.table_schema
                WHERE t.table_schema = $1
                ORDER BY t.table_name;
            """
            rows = await conn.fetch(query, schema_name)
            
            tables = []
            for row in rows:
                tables.append({
                    "schema": row["table_schema"],
                    "table_name": row["table_name"],
                    "table_type": row["table_type"],
                    "owner": row["owner"],
                    "size": row["size"],
                    "estimated_rows": row["estimated_rows"],
                    "comment": row["comment"]
                })
            
            return {
                "schema": schema_name,
                "tables": tables,
                "count": len(tables)
            }
    except Exception as e:
        logger.error(f"Failed to get tables for schema {schema_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tables for schema {schema_name}: {str(e)}")

# Include the admin router
app.include_router(admin_router) 