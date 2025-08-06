from fastapi import FastAPI, HTTPException, APIRouter
from contextlib import asynccontextmanager
import logging
import asyncpg
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from app.core.database import get_db_connection, test_connection
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for CRUD operations
class RecordCreate(BaseModel):
    """Model for creating a new record"""
    data: Dict[str, Any]

class RecordUpdate(BaseModel):
    """Model for updating an existing record"""
    data: Dict[str, Any]

class RecordResponse(BaseModel):
    """Model for record response"""
    id: Optional[Any] = None
    data: Dict[str, Any]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class RecordsResponse(BaseModel):
    """Model for multiple records response"""
    records: List[RecordResponse]
    count: int
    total_count: int

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

# Create router for CRUD endpoints
crud_router = APIRouter(prefix="/crud", tags=["CRUD Operations"])

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

# CRUD Operations
@crud_router.get("/{schema_name}/{table_name}")
async def read_records(
    schema_name: str, 
    table_name: str, 
    limit: int = 100, 
    offset: int = 0,
    order_by: Optional[str] = None
):
    """Read records from a table - Retrieve records with pagination and optional ordering"""
    try:
        async with get_db_connection() as conn:
            # Validate table exists
            table_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = $1 AND table_name = $2)",
                schema_name, table_name
            )
            if not table_exists:
                raise HTTPException(status_code=404, detail=f"Table {schema_name}.{table_name} not found")
            
            # Build query with optional ordering
            order_clause = f"ORDER BY {order_by}" if order_by else ""
            query = f"""
                SELECT * FROM {schema_name}.{table_name}
                {order_clause}
                LIMIT $1 OFFSET $2
            """
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM {schema_name}.{table_name}"
            total_count = await conn.fetchval(count_query)
            
            # Get records
            rows = await conn.fetch(query, limit, offset)
            
            records = []
            for row in rows:
                record_data = dict(row)
                records.append(RecordResponse(
                    id=record_data.get('id'),  # Assuming 'id' is the primary key
                    data=record_data,
                    created_at=record_data.get('created_at'),
                    updated_at=record_data.get('updated_at')
                ))
            
            return RecordsResponse(
                records=records,
                count=len(records),
                total_count=total_count
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to read records from {schema_name}.{table_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read records: {str(e)}")

@crud_router.get("/{schema_name}/{table_name}/{record_id}")
async def read_record(schema_name: str, table_name: str, record_id: str):
    """Read a single record by ID - Retrieve a specific record from a table"""
    try:
        async with get_db_connection() as conn:
            # Validate table exists
            table_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = $1 AND table_name = $2)",
                schema_name, table_name
            )
            if not table_exists:
                raise HTTPException(status_code=404, detail=f"Table {schema_name}.{table_name} not found")
            
            # Try to convert record_id to integer if possible, otherwise use as string
            try:
                record_id_int = int(record_id)
                query = f"SELECT * FROM {schema_name}.{table_name} WHERE id = $1"
                row = await conn.fetchrow(query, record_id_int)
            except ValueError:
                # If not an integer, use as string
                query = f"SELECT * FROM {schema_name}.{table_name} WHERE id = $1"
                row = await conn.fetchrow(query, record_id)
            
            if not row:
                raise HTTPException(status_code=404, detail=f"Record with ID {record_id} not found")
            
            record_data = dict(row)
            return RecordResponse(
                id=record_data.get('id'),
                data=record_data,
                created_at=record_data.get('created_at'),
                updated_at=record_data.get('updated_at')
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to read record {record_id} from {schema_name}.{table_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read record: {str(e)}")

@crud_router.post("/{schema_name}/{table_name}")
async def create_record(schema_name: str, table_name: str, record: RecordCreate):
    """Create a new record - Insert a new record into a table"""
    try:
        async with get_db_connection() as conn:
            # Validate table exists
            table_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = $1 AND table_name = $2)",
                schema_name, table_name
            )
            if not table_exists:
                raise HTTPException(status_code=404, detail=f"Table {schema_name}.{table_name} not found")
            
            # Build dynamic INSERT query
            columns = list(record.data.keys())
            placeholders = [f"${i+1}" for i in range(len(columns))]
            values = list(record.data.values())
            
            query = f"""
                INSERT INTO {schema_name}.{table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING *
            """
            
            # Execute insert
            row = await conn.fetchrow(query, *values)
            
            if not row:
                raise HTTPException(status_code=500, detail="Failed to create record")
            
            record_data = dict(row)
            return RecordResponse(
                id=record_data.get('id'),
                data=record_data,
                created_at=record_data.get('created_at'),
                updated_at=record_data.get('updated_at')
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create record in {schema_name}.{table_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create record: {str(e)}")

@crud_router.put("/{schema_name}/{table_name}/{record_id}")
async def update_record(schema_name: str, table_name: str, record_id: str, record: RecordUpdate):
    """Update an existing record - Modify a record in a table"""
    try:
        async with get_db_connection() as conn:
            # Validate table exists
            table_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = $1 AND table_name = $2)",
                schema_name, table_name
            )
            if not table_exists:
                raise HTTPException(status_code=404, detail=f"Table {schema_name}.{table_name} not found")
            
            # Try to convert record_id to integer if possible, otherwise use as string
            try:
                record_id_int = int(record_id)
                exists_query = f"SELECT EXISTS(SELECT 1 FROM {schema_name}.{table_name} WHERE id = $1)"
                exists = await conn.fetchval(exists_query, record_id_int)
            except ValueError:
                # If not an integer, use as string
                exists_query = f"SELECT EXISTS(SELECT 1 FROM {schema_name}.{table_name} WHERE id = $1)"
                exists = await conn.fetchval(exists_query, record_id)
            
            if not exists:
                raise HTTPException(status_code=404, detail=f"Record with ID {record_id} not found")
            
            # Build dynamic UPDATE query
            columns = list(record.data.keys())
            set_clause = ", ".join([f"{col} = ${i+2}" for i, col in enumerate(columns)])
            values = list(record.data.values())
            
            # Use appropriate record_id type
            if isinstance(record_id_int, int):
                query = f"""
                    UPDATE {schema_name}.{table_name}
                    SET {set_clause}
                    WHERE id = $1
                    RETURNING *
                """
                row = await conn.fetchrow(query, record_id_int, *values)
            else:
                query = f"""
                    UPDATE {schema_name}.{table_name}
                    SET {set_clause}
                    WHERE id = $1
                    RETURNING *
                """
                row = await conn.fetchrow(query, record_id, *values)
            
            if not row:
                raise HTTPException(status_code=500, detail="Failed to update record")
            
            record_data = dict(row)
            return RecordResponse(
                id=record_data.get('id'),
                data=record_data,
                created_at=record_data.get('created_at'),
                updated_at=record_data.get('updated_at')
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update record {record_id} in {schema_name}.{table_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update record: {str(e)}")

@crud_router.delete("/{schema_name}/{table_name}/{record_id}")
async def delete_record(schema_name: str, table_name: str, record_id: str):
    """Delete a record - Remove a record from a table"""
    try:
        async with get_db_connection() as conn:
            # Validate table exists
            table_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = $1 AND table_name = $2)",
                schema_name, table_name
            )
            if not table_exists:
                raise HTTPException(status_code=404, detail=f"Table {schema_name}.{table_name} not found")
            
            # Try to convert record_id to integer if possible, otherwise use as string
            try:
                record_id_int = int(record_id)
                exists_query = f"SELECT EXISTS(SELECT 1 FROM {schema_name}.{table_name} WHERE id = $1)"
                exists = await conn.fetchval(exists_query, record_id_int)
            except ValueError:
                # If not an integer, use as string
                exists_query = f"SELECT EXISTS(SELECT 1 FROM {schema_name}.{table_name} WHERE id = $1)"
                exists = await conn.fetchval(exists_query, record_id)
            
            if not exists:
                raise HTTPException(status_code=404, detail=f"Record with ID {record_id} not found")
            
            # Delete record with appropriate type
            if isinstance(record_id_int, int):
                query = f"DELETE FROM {schema_name}.{table_name} WHERE id = $1 RETURNING *"
                row = await conn.fetchrow(query, record_id_int)
            else:
                query = f"DELETE FROM {schema_name}.{table_name} WHERE id = $1 RETURNING *"
                row = await conn.fetchrow(query, record_id)
            
            if not row:
                raise HTTPException(status_code=500, detail="Failed to delete record")
            
            record_data = dict(row)
            return {
                "message": "Record deleted successfully",
                "deleted_record": RecordResponse(
                    id=record_data.get('id'),
                    data=record_data,
                    created_at=record_data.get('created_at'),
                    updated_at=record_data.get('updated_at')
                )
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete record {record_id} from {schema_name}.{table_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete record: {str(e)}")

# Include the routers
app.include_router(admin_router)
app.include_router(crud_router) 