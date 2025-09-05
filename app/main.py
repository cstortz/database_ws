from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.core.database import test_connection
from app.routers import admin_router, raw_router, crud_router, prepared_router

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
    title="Database Service API",
    description="""
    A comprehensive FastAPI service that provides secure database operations through PgBouncer.
    
    ## Features
    
    * **Admin Operations**: Database service management and monitoring
    * **CRUD Operations**: Full Create, Read, Update, Delete operations with pagination
    * **Raw SQL Execution**: Execute custom SQL queries with parameter binding
    * **Prepared SQL Operations**: Advanced prepared statement operations with caching
    * **Security**: All operations use prepared statements to prevent SQL injection
    * **Performance**: Connection pooling and prepared statement caching
    
    ## Security
    
    All database operations use prepared statements with parameter binding to prevent SQL injection attacks.
    The service includes comprehensive input validation and SQL security checks.
    
    ## Endpoints
    
    * **Admin** (`/admin/*`): Service health, database info, and metadata
    * **CRUD** (`/crud/*`): Standard database operations
    * **Raw SQL** (`/raw/*`): Custom SQL execution
    * **Prepared SQL** (`/crud/prepared/*`): Advanced prepared statement operations
    """,
    version="2.1.0",
    lifespan=lifespan,
    contact={
        "name": "Database Service API",
        "url": "http://localhost:8000/docs",
    },
    license_info={
        "name": "MIT License",
    },
)

@app.get("/", 
         summary="Service Information",
         description="Get basic service information and available endpoint groups",
         response_description="Service information and available endpoints")
async def root():
    """
    Root endpoint providing service information and available endpoint groups.
    
    Returns basic service information including version, documentation links,
    and available endpoint groups for the database service.
    """
    return {
        "message": "Database Service API",
        "version": "2.1.0",
        "docs": "/docs",
        "health": "/admin/health",
        "features": {
            "admin": "/admin/*",
            "crud": "/crud/*", 
            "raw_sql": "/raw/*",
            "prepared_sql": "/crud/prepared/*"
        }
    }

@app.get("/health",
         summary="Basic Health Check",
         description="Simple health check endpoint that indicates service is running",
         response_description="Basic health status")
async def health_check():
    """
    Simple health check endpoint that indicates the service is running.
    
    For detailed health information including database connectivity,
    use the admin health endpoint at `/admin/health`.
    """
    return {
        "status": "healthy",
        "message": "Database Service is running",
        "version": "2.1.0",
        "detailed_health": "/admin/health"
    }

# Include all routers (order matters - more specific routes first)
app.include_router(admin_router)
app.include_router(raw_router)
app.include_router(prepared_router)  # More specific /crud/prepared routes first
app.include_router(crud_router)      # General /crud routes last 