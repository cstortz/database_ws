from fastapi import APIRouter, HTTPException
import logging
import re
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.core.database import db_manager, PreparedStatement
from app.core.sql_security import sql_security

logger = logging.getLogger(__name__)

# Pydantic models for raw SQL requests
class RawSQLRequest(BaseModel):
    """Model for raw SQL requests"""
    sql: str
    parameters: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "sql": "SELECT * FROM users WHERE age > $1 AND status = $2",
                "parameters": {
                    "1": 18,
                    "2": "active"
                }
            }
        }

class RawSQLReadRequest(BaseModel):
    """Model for raw SQL read requests"""
    sql: str
    parameters: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "sql": "SELECT * FROM users WHERE age > $1 AND status = $2 ORDER BY created_at DESC",
                "parameters": {
                    "1": 18,
                    "2": "active"
                }
            }
        }

class RawSQLWriteRequest(BaseModel):
    """Model for raw SQL write requests"""
    sql: str
    parameters: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "sql": "UPDATE users SET status = $1 WHERE id = $2 RETURNING *",
                "parameters": {
                    "1": "inactive",
                    "2": 123
                }
            }
        }

class RawSQLResponse(BaseModel):
    """Model for raw SQL responses"""
    success: bool
    message: str
    data: Optional[list] = None
    row_count: Optional[int] = None
    affected_rows: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Raw SQL query executed successfully. Rows returned: 5",
                "data": [
                    {"id": 1, "name": "John Doe", "age": 25, "status": "active"},
                    {"id": 2, "name": "Jane Smith", "age": 30, "status": "active"}
                ],
                "row_count": 2,
                "affected_rows": None
            }
        }

class RawRouter:
    """Raw SQL router for executing raw SQL queries"""
    
    def __init__(self):
        self.router = APIRouter(prefix="/raw", tags=["Raw SQL Operations"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup all raw SQL routes"""
        
        @self.router.post("/sql", response_model=RawSQLResponse, summary="Execute Raw SQL Query", description="Execute a raw SQL query with optional parameters")
        async def execute_raw_sql(request: RawSQLReadRequest):
            """
            Execute a raw SQL query with optional parameters.
            
            This endpoint allows you to execute any SQL query with parameter binding for security.
            The SQL is validated for injection attempts and only read operations are allowed.
            
            Parameters:
            - **sql**: The SQL query to execute (must start with SELECT)
            - **parameters**: Optional dictionary of parameters to bind (using $1, $2, etc. placeholders)
            
            Returns:
            - **success**: Whether the query executed successfully
            - **message**: Human-readable message about the execution
            - **data**: Array of result rows (for SELECT queries)
            - **row_count**: Number of rows returned
            - **affected_rows**: Number of rows affected (for write operations)
            
            Example:
            ```json
            {
                "sql": "SELECT * FROM users WHERE age > $1 AND status = $2",
                "parameters": {
                    "1": 18,
                    "2": "active"
                }
            }
            ```
            """
            try:
                # Validate SQL using sql_security
                sql_security.validate_sql_statement(request.sql, "read")
                logger.info(f"Executing raw SQL: {request.sql}")

                async with db_manager.get_connection() as conn:
                    # Count the number of parameter placeholders in the SQL
                    param_count = len(re.findall(r'\$\d+', request.sql))
                    
                    if request.parameters and param_count > 0:
                        # SQL has placeholders and parameters are provided
                        if param_count != len(request.parameters):
                            raise HTTPException(
                                status_code=400,
                                detail=f"Parameter count mismatch: SQL expects {param_count} parameters, but {len(request.parameters)} were provided"
                            )
                        
                        # Use parameterized query with prepared statement
                        # Convert all parameters to strings for PostgreSQL compatibility
                        param_list = [str(value) for value in request.parameters.values()]
                        stmt = PreparedStatement(request.sql, tuple(param_list))
                        rows = await db_manager.execute_prepared(stmt, conn)
                    elif request.parameters and param_count == 0:
                        # SQL has no placeholders but parameters are provided - ignore parameters
                        logger.warning(f"SQL has no parameter placeholders but parameters were provided: {request.parameters}")
                        stmt = PreparedStatement(request.sql, ())
                        rows = await db_manager.execute_prepared(stmt, conn)
                    else:
                        # No parameters or no placeholders - execute raw SQL
                        stmt = PreparedStatement(request.sql, ())
                        rows = await db_manager.execute_prepared(stmt, conn)
                    
                    # Convert rows to list of dicts
                    data = [dict(row) for row in rows]
                    
                    return RawSQLResponse(
                        success=True,
                        message=f"Raw SQL query executed successfully. Rows returned: {len(data)}",
                        data=data,
                        row_count=len(data)
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to execute raw SQL: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to execute raw SQL: {str(e)}")

        @self.router.post("/sql/write", response_model=RawSQLResponse, summary="Execute Raw SQL Write Query", description="Execute a raw SQL write query (INSERT, UPDATE, DELETE) with optional parameters")
        async def execute_raw_write_sql(request: RawSQLWriteRequest):
            """
            Execute a raw SQL write query (INSERT, UPDATE, DELETE) with optional parameters.
            
            This endpoint allows you to execute write operations with parameter binding for security.
            The SQL is validated for injection attempts and only write operations are allowed.
            
            Parameters:
            - **sql**: The SQL query to execute (must start with INSERT, UPDATE, or DELETE)
            - **parameters**: Optional dictionary of parameters to bind (using $1, $2, etc. placeholders)
            
            Returns:
            - **success**: Whether the query executed successfully
            - **message**: Human-readable message about the execution
            - **data**: Array of result rows (if RETURNING clause is used)
            - **row_count**: Number of rows returned (if RETURNING clause is used)
            - **affected_rows**: Number of rows affected by the write operation
            
            Example:
            ```json
            {
                "sql": "UPDATE users SET status = $1 WHERE id = $2 RETURNING *",
                "parameters": {
                    "1": "inactive",
                    "2": 123
                }
            }
            ```
            """
            try:
                # Validate SQL using sql_security for write operations
                sql_security.validate_sql_statement(request.sql, "write")
                logger.info(f"Executing raw write SQL: {request.sql}")

                async with db_manager.get_connection() as conn:
                    # Count the number of parameter placeholders in the SQL
                    param_count = len(re.findall(r'\$\d+', request.sql))
                    
                    if request.parameters and param_count > 0:
                        # SQL has placeholders and parameters are provided
                        if param_count != len(request.parameters):
                            raise HTTPException(
                                status_code=400,
                                detail=f"Parameter count mismatch: SQL expects {param_count} parameters, but {len(request.parameters)} were provided"
                            )
                        
                        # Use parameterized query with prepared statement
                        # Convert all parameters to strings for PostgreSQL compatibility
                        param_list = [str(value) for value in request.parameters.values()]
                        stmt = PreparedStatement(request.sql, tuple(param_list))
                        result = await conn.execute(stmt.sql, *stmt.parameters)
                    elif request.parameters and param_count == 0:
                        # SQL has no placeholders but parameters are provided - ignore parameters
                        logger.warning(f"SQL has no parameter placeholders but parameters were provided: {request.parameters}")
                        stmt = PreparedStatement(request.sql, ())
                        result = await conn.execute(stmt.sql, *stmt.parameters)
                    else:
                        # No parameters or no placeholders - execute raw SQL
                        stmt = PreparedStatement(request.sql, ())
                        result = await conn.execute(stmt.sql, *stmt.parameters)
                    
                    # Parse the result to extract the number of affected rows
                    affected_rows = 0
                    if result:
                        try:
                            # Result format is like "UPDATE 1" or "INSERT 0 1"
                            parts = result.split()
                            if len(parts) >= 2:
                                affected_rows = int(parts[-1])  # Last part is usually the count
                            else:
                                affected_rows = int(result)
                        except (ValueError, IndexError):
                            affected_rows = 0
                    
                    return RawSQLResponse(
                        success=True,
                        message=f"Raw SQL write query executed successfully. Affected rows: {affected_rows}",
                        affected_rows=affected_rows
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to execute raw write SQL: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to execute raw write SQL: {str(e)}")

# Create router instance
raw_router = RawRouter().router
