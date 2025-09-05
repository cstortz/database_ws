from fastapi import APIRouter, HTTPException
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.core.database import get_db_connection, test_connection
from app.core.config import settings

logger = logging.getLogger(__name__)

# Response models for admin endpoints
class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    database: str
    pgbouncer_host: str
    pgbouncer_port: int
    
    class Config:
        json_json_schema_extra = {
            "example": {
                "status": "healthy",
                "database": "connected",
                "pgbouncer_host": "localhost",
                "pgbouncer_port": 5432
            }
        }

class ConnectionTestResponse(BaseModel):
    """Database connection test response model"""
    status: str
    message: str
    details: Dict[str, Any]
    
    class Config:
        json_json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Database connection successful",
                "details": {
                    "status": "connected",
                    "version": "PostgreSQL 13.4 on x86_64-pc-linux-gnu",
                    "database": "testdb",
                    "user": "postgres",
                    "host": "localhost",
                    "port": 5432,
                    "write_test": "passed"
                }
            }
        }

class DatabaseInfoResponse(BaseModel):
    """Database information response model"""
    version: str
    database: str
    user: str
    host: str
    port: int
    
    class Config:
        json_json_schema_extra = {
            "example": {
                "version": "PostgreSQL 13.4 on x86_64-pc-linux-gnu",
                "database": "testdb",
                "user": "postgres",
                "host": "localhost",
                "port": 5432
            }
        }

class DatabaseInfo(BaseModel):
    """Database information model"""
    database_name: str
    owner: str
    encoding: str
    collation: str
    ctype: str
    access_privileges: Optional[str] = None
    size: str
    comment: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "database_name": "testdb",
                "owner": "postgres",
                "encoding": "UTF8",
                "collation": "en_US.utf8",
                "ctype": "en_US.utf8",
                "access_privileges": "postgres=CTc/postgres",
                "size": "8.5 MB",
                "comment": "Test database"
            }
        }

class DatabasesResponse(BaseModel):
    """Databases list response model"""
    databases: list[DatabaseInfo]
    count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "databases": [
                    {
                        "database_name": "testdb",
                        "owner": "postgres",
                        "encoding": "UTF8",
                        "collation": "en_US.utf8",
                        "ctype": "en_US.utf8",
                        "access_privileges": "postgres=CTc/postgres",
                        "size": "8.5 MB",
                        "comment": "Test database"
                    }
                ],
                "count": 1
            }
        }

class SchemaInfo(BaseModel):
    """Schema information model"""
    schema_name: str
    owner: str
    access_privileges: Optional[str] = None
    comment: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_name": "public",
                "owner": "postgres",
                "access_privileges": "postgres=UC/postgres",
                "comment": "Standard public schema"
            }
        }

class SchemasResponse(BaseModel):
    """Schemas list response model"""
    schemas: list[SchemaInfo]
    count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "schemas": [
                    {
                        "schema_name": "public",
                        "owner": "postgres",
                        "access_privileges": "postgres=UC/postgres",
                        "comment": "Standard public schema"
                    }
                ],
                "count": 1
            }
        }

class TableInfo(BaseModel):
    """Table information model"""
    schema_name: str
    table_name: str
    table_type: str
    owner: str
    size: str
    estimated_rows: int
    comment: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_name": "public",
                "table_name": "users",
                "table_type": "BASE TABLE",
                "owner": "postgres",
                "size": "16 kB",
                "estimated_rows": 100,
                "comment": "User accounts table"
            }
        }

class TablesResponse(BaseModel):
    """Tables list response model"""
    tables: list[TableInfo]
    count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "tables": [
                    {
                        "schema_name": "public",
                        "table_name": "users",
                        "table_type": "BASE TABLE",
                        "owner": "postgres",
                        "size": "16 kB",
                        "estimated_rows": 100,
                        "comment": "User accounts table"
                    }
                ],
                "count": 1
            }
        }

class TablesBySchemaResponse(BaseModel):
    """Tables by schema response model"""
    schema_name: str
    tables: list[TableInfo]
    count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "schema_name": "public",
                "tables": [
                    {
                        "schema_name": "public",
                        "table_name": "users",
                        "table_type": "BASE TABLE",
                        "owner": "postgres",
                        "size": "16 kB",
                        "estimated_rows": 100,
                        "comment": "User accounts table"
                    }
                ],
                "count": 1
            }
        }

class AdminRouter:
    """Admin router for database service management endpoints"""
    
    def __init__(self):
        self.router = APIRouter(prefix="/admin", tags=["Admin"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup all admin routes"""
        
        @self.router.get("/health", response_model=HealthResponse, summary="Health Check", description="Check if the database service is healthy and connected")
        async def health_check():
            """
            Health check endpoint - Check if the database service is healthy and connected
            
            Returns:
            - **status**: Service status (healthy/unhealthy)
            - **database**: Database connection status
            - **pgbouncer_host**: PgBouncer host address
            - **pgbouncer_port**: PgBouncer port number
            """
            try:
                # Test database connection
                await test_connection()
                return HealthResponse(
                    status="healthy",
                    database="connected",
                    pgbouncer_host=settings.PGBOUNCER_HOST,
                    pgbouncer_port=settings.PGBOUNCER_PORT
                )
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

        @self.router.get("/test-connection", response_model=ConnectionTestResponse, summary="Test Database Connection", description="Verify database connectivity and get connection details")
        async def test_db_connection():
            """
            Test database connection endpoint - Verify database connectivity and get connection details
            
            Returns:
            - **status**: Test status (success/failed)
            - **message**: Human-readable message
            - **details**: Detailed connection information including version, database name, user, etc.
            """
            try:
                result = await test_connection()
                return ConnectionTestResponse(
                    status="success",
                    message="Database connection successful",
                    details=result
                )
            except Exception as e:
                logger.error(f"Connection test failed: {e}")
                raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

        @self.router.get("/db-info", response_model=DatabaseInfoResponse, summary="Get Database Information", description="Retrieve current database version, name, user, and connection details")
        async def get_db_info():
            """
            Get database information - Retrieve current database version, name, user, and connection details
            
            Returns:
            - **version**: PostgreSQL version string
            - **database**: Current database name
            - **user**: Current database user
            - **host**: Database host address
            - **port**: Database port number
            """
            try:
                async with get_db_connection() as conn:
                    # Get database version
                    version = await conn.fetchval("SELECT version()")
                    
                    # Get current database name
                    db_name = await conn.fetchval("SELECT current_database()")
                    
                    # Get current user
                    current_user = await conn.fetchval("SELECT current_user")
                    
                    return DatabaseInfoResponse(
                        version=version,
                        database=db_name,
                        user=current_user,
                        host=settings.PGBOUNCER_HOST,
                        port=settings.PGBOUNCER_PORT
                    )
            except Exception as e:
                logger.error(f"Failed to get database info: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to get database info: {str(e)}")

        @self.router.get("/databases", response_model=DatabasesResponse, summary="Get All Databases", description="Retrieve list of all databases with their descriptions/comments")
        async def get_databases():
            """
            Get all databases - Retrieve list of all databases with their descriptions/comments
            
            Returns:
            - **databases**: List of database information objects
            - **count**: Total number of databases
            
            Each database object contains:
            - **database_name**: Name of the database
            - **owner**: Database owner
            - **encoding**: Character encoding
            - **collation**: Collation settings
            - **ctype**: Character type
            - **access_privileges**: Access control list
            - **size**: Database size in human-readable format
            - **comment**: Database description/comment
            """
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
                        databases.append(DatabaseInfo(
                            database_name=row["database_name"],
                            owner=row["owner"],
                            encoding=row["encoding"],
                            collation=row["collation"],
                            ctype=row["ctype"],
                            access_privileges=row["access_privileges"],
                            size=row["size"],
                            comment=row["comment"]
                        ))
                    
                    return DatabasesResponse(
                        databases=databases,
                        count=len(databases)
                    )
            except Exception as e:
                logger.error(f"Failed to get databases: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to get databases: {str(e)}")

        @self.router.get("/schemas", response_model=SchemasResponse, summary="Get All Schemas", description="Retrieve list of all schemas with their descriptions/comments")
        async def get_schemas():
            """
            Get all schemas - Retrieve list of all schemas with their descriptions/comments
            
            Returns:
            - **schemas**: List of schema information objects
            - **count**: Total number of schemas
            
            Each schema object contains:
            - **schema_name**: Name of the schema
            - **owner**: Schema owner
            - **access_privileges**: Access control list
            - **comment**: Schema description/comment
            """
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
                        schemas.append(SchemaInfo(
                            schema_name=row["schema_name"],
                            owner=row["owner"],
                            access_privileges=row["access_privileges"],
                            comment=row["comment"]
                        ))
                    
                    return SchemasResponse(
                        schemas=schemas,
                        count=len(schemas)
                    )
            except Exception as e:
                logger.error(f"Failed to get schemas: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to get schemas: {str(e)}")

        @self.router.get("/tables", response_model=TablesResponse, summary="Get All Tables", description="Retrieve list of all tables with their descriptions/comments")
        async def get_tables():
            """
            Get all tables - Retrieve list of all tables with their descriptions/comments
            
            Returns:
            - **tables**: List of table information objects
            - **count**: Total number of tables
            
            Each table object contains:
            - **schema**: Schema name
            - **table_name**: Table name
            - **table_type**: Type of table (BASE TABLE, VIEW, etc.)
            - **owner**: Table owner
            - **size**: Table size in human-readable format
            - **estimated_rows**: Estimated number of rows
            - **comment**: Table description/comment
            """
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
                        tables.append(TableInfo(
                            schema_name=row["table_schema"],
                            table_name=row["table_name"],
                            table_type=row["table_type"],
                            owner=row["owner"],
                            size=row["size"],
                            estimated_rows=row["estimated_rows"],
                            comment=row["comment"]
                        ))
                    
                    return TablesResponse(
                        tables=tables,
                        count=len(tables)
                    )
            except Exception as e:
                logger.error(f"Failed to get tables: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to get tables: {str(e)}")

        @self.router.get("/tables/{schema_name}", response_model=TablesBySchemaResponse, summary="Get Tables by Schema", description="Retrieve list of tables in a specific schema with their descriptions/comments")
        async def get_tables_by_schema(schema_name: str):
            """
            Get tables by schema - Retrieve list of tables in a specific schema with their descriptions/comments
            
            Parameters:
            - **schema_name**: Name of the schema to query
            
            Returns:
            - **schema**: Schema name
            - **tables**: List of table information objects
            - **count**: Total number of tables in the schema
            
            Each table object contains:
            - **schema**: Schema name
            - **table_name**: Table name
            - **table_type**: Type of table (BASE TABLE, VIEW, etc.)
            - **owner**: Table owner
            - **size**: Table size in human-readable format
            - **estimated_rows**: Estimated number of rows
            - **comment**: Table description/comment
            """
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
                        tables.append(TableInfo(
                            schema_name=row["table_schema"],
                            table_name=row["table_name"],
                            table_type=row["table_type"],
                            owner=row["owner"],
                            size=row["size"],
                            estimated_rows=row["estimated_rows"],
                            comment=row["comment"]
                        ))
                    
                    return TablesBySchemaResponse(
                        schema_name=schema_name,
                        tables=tables,
                        count=len(tables)
                    )
            except Exception as e:
                logger.error(f"Failed to get tables for schema {schema_name}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to get tables for schema {schema_name}: {str(e)}")

# Create router instance
admin_router = AdminRouter().router
