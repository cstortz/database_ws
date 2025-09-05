from fastapi import APIRouter, HTTPException
import logging
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel

from app.core.database import db_manager, PreparedStatement
from app.core.sql_security import sql_security

logger = logging.getLogger(__name__)

# Pydantic models for prepared SQL operations
class PreparedSQLRequest(BaseModel):
    """Model for prepared SQL requests"""
    sql: str
    parameters: Optional[Dict[str, Any]] = None
    operation_type: str = "read"  # "read" or "write"
    
    class Config:
        json_schema_extra = {
            "example": {
                "sql": "SELECT * FROM users WHERE department = $1 AND active = $2",
                "parameters": {
                    "1": "engineering",
                    "2": True
                },
                "operation_type": "read"
            }
        }

class PreparedSelectRequest(BaseModel):
    """Model for prepared SELECT requests"""
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

class PreparedInsertRequest(BaseModel):
    """Model for prepared INSERT requests"""
    sql: str
    parameters: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "sql": "INSERT INTO users (name, email, department) VALUES ($1, $2, $3) RETURNING *",
                "parameters": {
                    "1": "Jane Smith",
                    "2": "jane@example.com",
                    "3": "marketing"
                }
            }
        }

class PreparedUpdateRequest(BaseModel):
    """Model for prepared UPDATE requests"""
    sql: str
    parameters: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "sql": "UPDATE users SET status = $1, updated_at = NOW() WHERE id = $2 RETURNING *",
                "parameters": {
                    "1": "inactive",
                    "2": 123
                }
            }
        }

class PreparedDeleteRequest(BaseModel):
    """Model for prepared DELETE requests"""
    sql: str
    parameters: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "sql": "DELETE FROM users WHERE id = $1 RETURNING *",
                "parameters": {
                    "1": 123
                }
            }
        }

class PreparedSQLResponse(BaseModel):
    """Model for prepared SQL responses"""
    success: bool
    message: str
    data: Optional[List[Dict[str, Any]]] = None
    row_count: Optional[int] = None
    affected_rows: Optional[int] = None
    sql: str
    parameters: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Prepared SQL query executed successfully. Rows returned: 2",
                "data": [
                    {"id": 1, "name": "John Doe", "department": "engineering", "active": True},
                    {"id": 2, "name": "Jane Smith", "department": "engineering", "active": True}
                ],
                "row_count": 2,
                "affected_rows": None,
                "sql": "SELECT * FROM users WHERE department = $1 AND active = $2",
                "parameters": {
                    "1": "engineering",
                    "2": True
                }
            }
        }

class PreparedStatementInfo(BaseModel):
    """Model for prepared statement information"""
    name: str
    sql: str
    parameter_count: int
    created_at: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "user_query_1",
                "sql": "SELECT * FROM users WHERE id = $1",
                "parameter_count": 1,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

class StatementsResponse(BaseModel):
    """Model for prepared statements list response"""
    statements: List[PreparedStatementInfo]
    count: int
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "statements": [
                    {
                        "name": "user_query_1",
                        "sql": "SELECT * FROM users WHERE id = $1",
                        "parameter_count": 1,
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "count": 1,
                "message": "Found 1 cached prepared statements"
            }
        }

class ValidationResponse(BaseModel):
    """Model for SQL validation response"""
    valid: bool
    message: str
    sql: str
    parameters: Optional[Dict[str, Any]] = None
    placeholder_count: Optional[int] = None
    parameter_count: Optional[int] = None
    operation_type: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "valid": True,
                "message": "Prepared SQL statement is valid",
                "sql": "SELECT * FROM users WHERE id = $1",
                "parameters": {"1": 123},
                "placeholder_count": 1,
                "parameter_count": 1,
                "operation_type": "read"
            }
        }

class PreparedRouter:
    """Prepared SQL router for advanced prepared statement operations"""
    
    def __init__(self):
        self.router = APIRouter(prefix="/crud/prepared", tags=["Prepared SQL Operations"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup all prepared SQL routes"""
        
        @self.router.post("/execute", response_model=PreparedSQLResponse, summary="Execute Prepared SQL", description="Execute a prepared SQL statement with parameters")
        async def execute_prepared_sql(request: PreparedSQLRequest):
            """
            Execute a prepared SQL statement with parameters
            
            This endpoint allows you to execute any SQL statement with parameter binding for security.
            The SQL is validated for injection attempts and the operation type determines whether
            read or write operations are allowed.
            
            Parameters:
            - **sql**: The SQL query to execute
            - **parameters**: Optional dictionary of parameters to bind (using $1, $2, etc. placeholders)
            - **operation_type**: Type of operation ("read" or "write")
            
            Returns:
            - **success**: Whether the query executed successfully
            - **message**: Human-readable message about the execution
            - **data**: Array of result rows (for read operations)
            - **row_count**: Number of rows returned
            - **affected_rows**: Number of rows affected (for write operations)
            - **sql**: The SQL query that was executed
            - **parameters**: The parameters that were bound
            
            Example:
            ```json
            {
                "sql": "SELECT * FROM users WHERE department = $1 AND active = $2",
                "parameters": {
                    "1": "engineering",
                    "2": true
                },
                "operation_type": "read"
            }
            ```
            """
            try:
                # Validate SQL using sql_security
                sql_security.validate_sql_statement(request.sql, request.operation_type)
                logger.info(f"Executing prepared SQL: {request.sql}")

                async with db_manager.get_connection() as conn:
                    # Convert parameters to tuple if provided
                    parameters = tuple(request.parameters.values()) if request.parameters else ()
                    
                    # Create prepared statement
                    stmt = PreparedStatement(request.sql, parameters)
                    
                    if request.operation_type == "read":
                        # Execute read operation
                        rows = await db_manager.execute_prepared(stmt, conn)
                        data = [dict(row) for row in rows]
                        
                        return PreparedSQLResponse(
                            success=True,
                            message=f"Prepared SQL query executed successfully. Rows returned: {len(data)}",
                            data=data,
                            row_count=len(data),
                            sql=request.sql,
                            parameters=request.parameters
                        )
                    else:
                        # Execute write operation
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
                        
                        return PreparedSQLResponse(
                            success=True,
                            message=f"Prepared SQL write query executed successfully. Affected rows: {affected_rows}",
                            affected_rows=affected_rows,
                            sql=request.sql,
                            parameters=request.parameters
                        )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to execute prepared SQL: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to execute prepared SQL: {str(e)}")

        @self.router.post("/select", response_model=PreparedSQLResponse, summary="Execute Prepared SELECT", description="Execute a prepared SELECT statement with parameters")
        async def execute_prepared_select(request: PreparedSelectRequest):
            """
            Execute a prepared SELECT statement with parameters
            
            This endpoint is specifically designed for SELECT operations with parameter binding.
            The SQL is validated to ensure it starts with SELECT and only read operations are allowed.
            
            Parameters:
            - **sql**: The SELECT query to execute (must start with SELECT)
            - **parameters**: Optional dictionary of parameters to bind (using $1, $2, etc. placeholders)
            - **operation_type**: Should be "read" for SELECT operations
            
            Returns:
            - **success**: Whether the query executed successfully
            - **message**: Human-readable message about the execution
            - **data**: Array of result rows
            - **row_count**: Number of rows returned
            - **sql**: The SQL query that was executed
            - **parameters**: The parameters that were bound
            
            Example:
            ```json
            {
                "sql": "SELECT * FROM users WHERE age > $1 AND status = $2 ORDER BY created_at DESC",
                "parameters": {
                    "1": 18,
                    "2": "active"
                },
                "operation_type": "read"
            }
            ```
            """
            try:
                # Validate SQL using sql_security for read operations
                sql_security.validate_sql_statement(request.sql, "read")
                logger.info(f"Executing prepared SELECT: {request.sql}")

                async with db_manager.get_connection() as conn:
                    # Convert parameters to tuple if provided
                    parameters = tuple(request.parameters.values()) if request.parameters else ()
                    
                    # Create prepared statement
                    stmt = PreparedStatement(request.sql, parameters)
                    
                    # Execute select operation
                    rows = await db_manager.execute_prepared(stmt, conn)
                    data = [dict(row) for row in rows]
                    
                    return PreparedSQLResponse(
                        success=True,
                        message=f"Prepared SELECT query executed successfully. Rows returned: {len(data)}",
                        data=data,
                        row_count=len(data),
                        sql=request.sql,
                        parameters=request.parameters
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to execute prepared SELECT: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to execute prepared SELECT: {str(e)}")

        @self.router.post("/insert", response_model=PreparedSQLResponse, summary="Execute Prepared INSERT", description="Execute a prepared INSERT statement with parameters")
        async def execute_prepared_insert(request: PreparedInsertRequest):
            """
            Execute a prepared INSERT statement with parameters
            
            This endpoint is specifically designed for INSERT operations with parameter binding.
            The SQL is validated to ensure it starts with INSERT and only write operations are allowed.
            
            Parameters:
            - **sql**: The INSERT query to execute (must start with INSERT)
            - **parameters**: Optional dictionary of parameters to bind (using $1, $2, etc. placeholders)
            - **operation_type**: Should be "write" for INSERT operations
            
            Returns:
            - **success**: Whether the query executed successfully
            - **message**: Human-readable message about the execution
            - **affected_rows**: Number of rows affected by the INSERT
            - **sql**: The SQL query that was executed
            - **parameters**: The parameters that were bound
            
            Example:
            ```json
            {
                "sql": "INSERT INTO users (name, email, department) VALUES ($1, $2, $3) RETURNING *",
                "parameters": {
                    "1": "Jane Smith",
                    "2": "jane@example.com",
                    "3": "marketing"
                },
                "operation_type": "write"
            }
            ```
            """
            try:
                # Validate SQL using sql_security for write operations
                sql_security.validate_sql_statement(request.sql, "write")
                logger.info(f"Executing prepared INSERT: {request.sql}")

                async with db_manager.get_connection() as conn:
                    # Convert parameters to tuple if provided
                    parameters = tuple(request.parameters.values()) if request.parameters else ()
                    
                    # Create prepared statement
                    stmt = PreparedStatement(request.sql, parameters)
                    
                    # Execute insert operation
                    result = await conn.execute(stmt.sql, *stmt.parameters)
                    
                    # Parse the result to extract the number of affected rows
                    affected_rows = 0
                    if result:
                        try:
                            # Result format is like "INSERT 0 1"
                            parts = result.split()
                            if len(parts) >= 3:
                                affected_rows = int(parts[2])  # Third part is the count
                            else:
                                affected_rows = int(result)
                        except (ValueError, IndexError):
                            affected_rows = 0
                    
                    return PreparedSQLResponse(
                        success=True,
                        message=f"Prepared INSERT query executed successfully. Affected rows: {affected_rows}",
                        affected_rows=affected_rows,
                        sql=request.sql,
                        parameters=request.parameters
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to execute prepared INSERT: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to execute prepared INSERT: {str(e)}")

        @self.router.post("/update", response_model=PreparedSQLResponse, summary="Execute Prepared UPDATE", description="Execute a prepared UPDATE statement with parameters")
        async def execute_prepared_update(request: PreparedUpdateRequest):
            """
            Execute a prepared UPDATE statement with parameters
            
            This endpoint is specifically designed for UPDATE operations with parameter binding.
            The SQL is validated to ensure it starts with UPDATE and only write operations are allowed.
            
            Parameters:
            - **sql**: The UPDATE query to execute (must start with UPDATE)
            - **parameters**: Optional dictionary of parameters to bind (using $1, $2, etc. placeholders)
            - **operation_type**: Should be "write" for UPDATE operations
            
            Returns:
            - **success**: Whether the query executed successfully
            - **message**: Human-readable message about the execution
            - **affected_rows**: Number of rows affected by the UPDATE
            - **sql**: The SQL query that was executed
            - **parameters**: The parameters that were bound
            
            Example:
            ```json
            {
                "sql": "UPDATE users SET status = $1, updated_at = NOW() WHERE id = $2 RETURNING *",
                "parameters": {
                    "1": "inactive",
                    "2": 123
                },
                "operation_type": "write"
            }
            ```
            """
            try:
                # Validate SQL using sql_security for write operations
                sql_security.validate_sql_statement(request.sql, "write")
                logger.info(f"Executing prepared UPDATE: {request.sql}")

                async with db_manager.get_connection() as conn:
                    # Convert parameters to tuple if provided
                    parameters = tuple(request.parameters.values()) if request.parameters else ()
                    
                    # Create prepared statement
                    stmt = PreparedStatement(request.sql, parameters)
                    
                    # Execute update operation
                    result = await conn.execute(stmt.sql, *stmt.parameters)
                    
                    # Parse the result to extract the number of affected rows
                    affected_rows = 0
                    if result:
                        try:
                            # Result format is like "UPDATE 1"
                            parts = result.split()
                            if len(parts) >= 2:
                                affected_rows = int(parts[1])  # Second part is the count
                            else:
                                affected_rows = int(result)
                        except (ValueError, IndexError):
                            affected_rows = 0
                    
                    return PreparedSQLResponse(
                        success=True,
                        message=f"Prepared UPDATE query executed successfully. Affected rows: {affected_rows}",
                        affected_rows=affected_rows,
                        sql=request.sql,
                        parameters=request.parameters
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to execute prepared UPDATE: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to execute prepared UPDATE: {str(e)}")

        @self.router.post("/delete", response_model=PreparedSQLResponse, summary="Execute Prepared DELETE", description="Execute a prepared DELETE statement with parameters")
        async def execute_prepared_delete(request: PreparedDeleteRequest):
            """
            Execute a prepared DELETE statement with parameters
            
            This endpoint is specifically designed for DELETE operations with parameter binding.
            The SQL is validated to ensure it starts with DELETE and only write operations are allowed.
            
            Parameters:
            - **sql**: The DELETE query to execute (must start with DELETE)
            - **parameters**: Optional dictionary of parameters to bind (using $1, $2, etc. placeholders)
            - **operation_type**: Should be "write" for DELETE operations
            
            Returns:
            - **success**: Whether the query executed successfully
            - **message**: Human-readable message about the execution
            - **affected_rows**: Number of rows affected by the DELETE
            - **sql**: The SQL query that was executed
            - **parameters**: The parameters that were bound
            
            Example:
            ```json
            {
                "sql": "DELETE FROM users WHERE id = $1 RETURNING *",
                "parameters": {
                    "1": 123
                },
                "operation_type": "write"
            }
            ```
            """
            try:
                # Validate SQL using sql_security for write operations
                sql_security.validate_sql_statement(request.sql, "write")
                logger.info(f"Executing prepared DELETE: {request.sql}")

                async with db_manager.get_connection() as conn:
                    # Convert parameters to tuple if provided
                    parameters = tuple(request.parameters.values()) if request.parameters else ()
                    
                    # Create prepared statement
                    stmt = PreparedStatement(request.sql, parameters)
                    
                    # Execute delete operation
                    result = await conn.execute(stmt.sql, *stmt.parameters)
                    
                    # Parse the result to extract the number of affected rows
                    affected_rows = 0
                    if result:
                        try:
                            # Result format is like "DELETE 1"
                            parts = result.split()
                            if len(parts) >= 2:
                                affected_rows = int(parts[1])  # Second part is the count
                            else:
                                affected_rows = int(result)
                        except (ValueError, IndexError):
                            affected_rows = 0
                    
                    return PreparedSQLResponse(
                        success=True,
                        message=f"Prepared DELETE query executed successfully. Affected rows: {affected_rows}",
                        affected_rows=affected_rows,
                        sql=request.sql,
                        parameters=request.parameters
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to execute prepared DELETE: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to execute prepared DELETE: {str(e)}")

        @self.router.get("/statements", response_model=StatementsResponse, summary="Get Prepared Statements", description="Get information about cached prepared statements")
        async def get_prepared_statements():
            """
            Get information about cached prepared statements
            
            This endpoint returns information about all currently cached prepared statements,
            including their SQL, parameter counts, and creation times.
            
            Returns:
            - **statements**: Array of prepared statement information objects
            - **count**: Total number of cached statements
            - **message**: Human-readable message about the results
            
            Each statement object contains:
            - **name**: Statement name/identifier
            - **sql**: The SQL query
            - **parameter_count**: Number of parameters
            - **created_at**: Creation timestamp
            
            Example:
            ```
            GET /crud/prepared/statements
            ```
            """
            try:
                # Get prepared statements from the database manager
                statements = db_manager.prepared_statements
                
                statement_info = []
                for name, stmt in statements.items():
                    statement_info.append(PreparedStatementInfo(
                        name=name,
                        sql=stmt.sql,
                        parameter_count=len(stmt.parameters),
                        created_at="N/A"  # We don't track creation time currently
                    ))
                
                return {
                    "statements": statement_info,
                    "count": len(statement_info),
                    "message": f"Found {len(statement_info)} cached prepared statements"
                }
            except Exception as e:
                logger.error(f"Failed to get prepared statements: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to get prepared statements: {str(e)}")

        @self.router.delete("/statements/{statement_name}", summary="Clear Specific Prepared Statement", description="Clear a specific prepared statement from cache")
        async def clear_prepared_statement(statement_name: str):
            """
            Clear a specific prepared statement from cache
            
            This endpoint allows you to remove a specific prepared statement from the cache
            by its name/identifier.
            
            Parameters:
            - **statement_name**: Name/identifier of the prepared statement to clear
            
            Returns:
            - **success**: Whether the operation was successful
            - **message**: Confirmation message
            
            Example:
            ```
            DELETE /crud/prepared/statements/user_query_1
            ```
            """
            try:
                if statement_name in db_manager.prepared_statements:
                    del db_manager.prepared_statements[statement_name]
                    return {
                        "success": True,
                        "message": f"Prepared statement '{statement_name}' cleared from cache"
                    }
                else:
                    raise HTTPException(status_code=404, detail=f"Prepared statement '{statement_name}' not found in cache")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to clear prepared statement: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to clear prepared statement: {str(e)}")

        @self.router.delete("/statements", summary="Clear All Prepared Statements", description="Clear all prepared statements from cache")
        async def clear_all_prepared_statements():
            """
            Clear all prepared statements from cache
            
            This endpoint allows you to remove all cached prepared statements at once.
            This can be useful for freeing up memory or forcing fresh statement preparation.
            
            Returns:
            - **success**: Whether the operation was successful
            - **message**: Confirmation message with count of cleared statements
            
            Example:
            ```
            DELETE /crud/prepared/statements
            ```
            """
            try:
                count = len(db_manager.prepared_statements)
                db_manager.prepared_statements.clear()
                return {
                    "success": True,
                    "message": f"Cleared {count} prepared statements from cache"
                }
            except Exception as e:
                logger.error(f"Failed to clear all prepared statements: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to clear all prepared statements: {str(e)}")

        @self.router.post("/validate", response_model=ValidationResponse, summary="Validate Prepared SQL", description="Validate a prepared SQL statement without executing it")
        async def validate_prepared_sql(request: PreparedSQLRequest):
            """
            Validate a prepared SQL statement without executing it
            
            This endpoint allows you to validate SQL syntax and parameter binding without
            actually executing the query. This is useful for testing and debugging.
            
            Parameters:
            - **sql**: The SQL query to validate
            - **parameters**: Optional dictionary of parameters to validate
            - **operation_type**: Type of operation ("read" or "write")
            
            Returns:
            - **valid**: Whether the SQL is valid
            - **message**: Validation result message
            - **sql**: The SQL query that was validated
            - **parameters**: The parameters that were validated
            - **placeholder_count**: Number of parameter placeholders in SQL
            - **parameter_count**: Number of provided parameters
            - **operation_type**: Type of operation
            - **error**: Error details if validation failed
            
            Example:
            ```json
            {
                "sql": "SELECT * FROM users WHERE id = $1 AND active = $2",
                "parameters": {
                    "1": 123,
                    "2": true
                },
                "operation_type": "read"
            }
            ```
            """
            try:
                # Validate SQL using sql_security
                sql_security.validate_sql_statement(request.sql, request.operation_type)
                
                # Count parameters
                param_count = len(request.parameters) if request.parameters else 0
                
                # Count placeholders in SQL
                import re
                placeholder_count = len(re.findall(r'\$\d+', request.sql))
                
                # Check for parameter mismatch
                if param_count != placeholder_count:
                    return {
                        "valid": False,
                        "message": f"Parameter count mismatch: SQL expects {placeholder_count} parameters, but {param_count} were provided",
                        "sql": request.sql,
                        "parameters": request.parameters,
                        "placeholder_count": placeholder_count,
                        "parameter_count": param_count
                    }
                
                return {
                    "valid": True,
                    "message": "Prepared SQL statement is valid",
                    "sql": request.sql,
                    "parameters": request.parameters,
                    "placeholder_count": placeholder_count,
                    "parameter_count": param_count,
                    "operation_type": request.operation_type
                }
            except HTTPException as e:
                return {
                    "valid": False,
                    "message": str(e.detail),
                    "sql": request.sql,
                    "parameters": request.parameters,
                    "error": str(e.detail)
                }
            except Exception as e:
                logger.error(f"Failed to validate prepared SQL: {e}")
                return {
                    "valid": False,
                    "message": f"Validation failed: {str(e)}",
                    "sql": request.sql,
                    "parameters": request.parameters,
                    "error": str(e)
                }

# Create router instance
prepared_router = PreparedRouter().router
