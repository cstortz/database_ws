from fastapi import APIRouter, HTTPException
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime

from app.core.database import db_manager
from app.core.sql_security import sql_security

logger = logging.getLogger(__name__)

# Pydantic models for CRUD operations
class RecordCreate(BaseModel):
    """Model for creating a new record"""
    data: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "age": 30,
                    "status": "active"
                }
            }
        }

class RecordUpdate(BaseModel):
    """Model for updating an existing record"""
    data: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "age": 31,
                    "status": "updated"
                }
            }
        }

class RecordResponse(BaseModel):
    """Model for record response"""
    id: Optional[Any] = None
    data: Dict[str, Any]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "data": {
                    "id": 123,
                    "name": "John Doe",
                    "email": "john@example.com",
                    "age": 30,
                    "status": "active",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z"
                },
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }

class RecordsResponse(BaseModel):
    """Model for multiple records response"""
    records: List[RecordResponse]
    count: int
    total_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "records": [
                    {
                        "id": 123,
                        "data": {
                            "id": 123,
                            "name": "John Doe",
                            "email": "john@example.com",
                            "age": 30,
                            "status": "active"
                        },
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "count": 1,
                "total_count": 100
            }
        }

class DeleteResponse(BaseModel):
    """Model for delete operation response"""
    message: str
    deleted_record: RecordResponse
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Record deleted successfully",
                "deleted_record": {
                    "id": 123,
                    "data": {
                        "id": 123,
                        "name": "John Doe",
                        "email": "john@example.com",
                        "age": 30,
                        "status": "active"
                    },
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z"
                }
            }
        }

class UpsertResponse(BaseModel):
    """Model for upsert operation response"""
    message: str
    operation: str
    record: RecordResponse
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Record created successfully",
                "operation": "created",
                "record": {
                    "id": 123,
                    "data": {
                        "id": 123,
                        "name": "John Doe",
                        "email": "john@example.com",
                        "age": 30,
                        "status": "active"
                    },
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z"
                }
            }
        }

class CrudRouter:
    """CRUD router for database operations"""
    
    def __init__(self):
        self.router = APIRouter(prefix="/crud", tags=["CRUD Operations"])
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup all CRUD routes"""
        
        @self.router.get("/{schema_name}/{table_name}", response_model=RecordsResponse, summary="Read Records", description="Retrieve records from a table with pagination and optional ordering")
        async def read_records(
            schema_name: str, 
            table_name: str, 
            limit: int = 100, 
            offset: int = 0,
            order_by: Optional[str] = None
        ):
            """
            Read records from a table - Retrieve records with pagination and optional ordering
            
            This endpoint allows you to read multiple records from a specified table with support for
            pagination, ordering, and automatic prepared statement generation for security.
            
            Parameters:
            - **schema_name**: Name of the database schema
            - **table_name**: Name of the table to query
            - **limit**: Maximum number of records to return (default: 100, max: 1000)
            - **offset**: Number of records to skip for pagination (default: 0)
            - **order_by**: Column name to order results by (e.g., "created_at DESC")
            
            Returns:
            - **records**: Array of record objects
            - **count**: Number of records returned in this response
            - **total_count**: Total number of records in the table
            
            Each record contains:
            - **id**: Primary key value
            - **data**: Complete record data
            - **created_at**: Record creation timestamp
            - **updated_at**: Record last update timestamp
            
            Example:
            ```
            GET /crud/public/users?limit=10&offset=0&order_by=created_at DESC
            ```
            """
            try:
                # Validate schema and table names
                schema_name = sql_security.validate_schema_name(schema_name)
                table_name = sql_security.validate_table_name(table_name)
                
                async with db_manager.get_connection() as conn:
                    # Validate table exists using prepared statement
                    table_exists_stmt = db_manager.prepare_table_exists_query(schema_name, table_name)
                    table_exists = await db_manager.execute_prepared_val(table_exists_stmt, conn)
                    
                    if not table_exists:
                        raise HTTPException(status_code=404, detail=f"Table {schema_name}.{table_name} not found")
                    
                    # Prepare SELECT query with parameters
                    select_stmt = db_manager.prepare_select_query(
                        schema_name=schema_name,
                        table_name=table_name,
                        order_by=order_by,
                        limit=limit,
                        offset=offset
                    )
                    
                    # Prepare COUNT query
                    count_stmt = db_manager.prepare_count_query(schema_name, table_name)
                    
                    # Execute queries using prepared statements
                    total_count = await db_manager.execute_prepared_val(count_stmt, conn)
                    rows = await db_manager.execute_prepared(select_stmt, conn)
                    
                    records = []
                    for row in rows:
                        # The database manager now returns a dict with converted datetime strings
                        record_data = row
                        
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

        @self.router.get("/{schema_name}/{table_name}/{record_id}", response_model=RecordResponse, summary="Read Single Record", description="Retrieve a specific record from a table by ID")
        async def read_record(schema_name: str, table_name: str, record_id: str):
            """
            Read a single record by ID - Retrieve a specific record from a table
            
            This endpoint allows you to read a single record by its primary key ID.
            The ID can be either an integer or string, and the endpoint will automatically
            determine the appropriate type for the query.
            
            Parameters:
            - **schema_name**: Name of the database schema
            - **table_name**: Name of the table to query
            - **record_id**: Primary key value of the record to retrieve
            
            Returns:
            - **id**: Primary key value
            - **data**: Complete record data
            - **created_at**: Record creation timestamp
            - **updated_at**: Record last update timestamp
            
            Example:
            ```
            GET /crud/public/users/123
            ```
            """
            try:
                # Validate schema and table names
                schema_name = sql_security.validate_schema_name(schema_name)
                table_name = sql_security.validate_table_name(table_name)
                
                async with db_manager.get_connection() as conn:
                    # Validate table exists using prepared statement
                    table_exists_stmt = db_manager.prepare_table_exists_query(schema_name, table_name)
                    table_exists = await db_manager.execute_prepared_val(table_exists_stmt, conn)
                    
                    if not table_exists:
                        raise HTTPException(status_code=404, detail=f"Table {schema_name}.{table_name} not found")
                    
                    # Try to convert record_id to integer if possible, otherwise use as string
                    try:
                        record_id_int = int(record_id)
                        record_id_final = record_id_int
                    except ValueError:
                        # If not an integer, use as string
                        record_id_final = record_id
                    
                    # Prepare SELECT query with parameters
                    select_stmt = db_manager.prepare_select_query(
                        schema_name=schema_name,
                        table_name=table_name,
                        where_clause="id = $1"
                    )
                    select_stmt.parameters = (record_id_final,)
                    
                    # Execute query using prepared statement
                    row = await db_manager.execute_prepared_row(select_stmt, conn)
                    
                    if not row:
                        raise HTTPException(status_code=404, detail=f"Record with ID {record_id} not found")
                    
                    # The database manager now returns a dict with converted datetime strings
                    record_data = row
                    
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

        @self.router.post("/{schema_name}/{table_name}", response_model=RecordResponse, summary="Create Record", description="Insert a new record into a table")
        async def create_record(schema_name: str, table_name: str, record: RecordCreate):
            """
            Create a new record - Insert a new record into a table
            
            This endpoint allows you to create a new record in the specified table.
            The record data is automatically validated and inserted using prepared statements
            for security. The endpoint returns the complete created record including
            any auto-generated fields like IDs and timestamps.
            
            Parameters:
            - **schema_name**: Name of the database schema
            - **table_name**: Name of the table to insert into
            - **record**: Record data to insert
            
            Request Body:
            - **data**: Dictionary containing the record fields and values
            
            Returns:
            - **id**: Primary key value (auto-generated if not provided)
            - **data**: Complete record data including auto-generated fields
            - **created_at**: Record creation timestamp
            - **updated_at**: Record last update timestamp
            
            Example:
            ```json
            {
                "data": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "age": 30,
                    "status": "active"
                }
            }
            ```
            """
            try:
                # Validate schema and table names
                schema_name = sql_security.validate_schema_name(schema_name)
                table_name = sql_security.validate_table_name(table_name)
                
                async with db_manager.get_connection() as conn:
                    # Validate table exists using prepared statement
                    table_exists_stmt = db_manager.prepare_table_exists_query(schema_name, table_name)
                    table_exists = await db_manager.execute_prepared_val(table_exists_stmt, conn)
                    
                    if not table_exists:
                        raise HTTPException(status_code=404, detail=f"Table {schema_name}.{table_name} not found")
                    
                    # Prepare INSERT query with parameters
                    insert_stmt = db_manager.prepare_insert_query(schema_name, table_name, record.data)
                    
                    # Execute insert using prepared statement
                    row = await db_manager.execute_prepared_row(insert_stmt, conn)
                    
                    if not row:
                        raise HTTPException(status_code=500, detail="Failed to create record")
                    
                    # The database manager now returns a dict with converted datetime strings
                    record_data = row
                    
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

        @self.router.put("/{schema_name}/{table_name}/{record_id}", response_model=RecordResponse, summary="Update Record", description="Modify an existing record in a table")
        async def update_record(schema_name: str, table_name: str, record_id: str, record: RecordUpdate):
            """
            Update an existing record - Modify a record in a table
            
            This endpoint allows you to update an existing record by its primary key ID.
            Only the fields provided in the request will be updated, and the endpoint
            returns the complete updated record.
            
            Parameters:
            - **schema_name**: Name of the database schema
            - **table_name**: Name of the table to update
            - **record_id**: Primary key value of the record to update
            - **record**: Record data to update
            
            Request Body:
            - **data**: Dictionary containing only the fields to update
            
            Returns:
            - **id**: Primary key value
            - **data**: Complete updated record data
            - **created_at**: Record creation timestamp
            - **updated_at**: Record last update timestamp
            
            Example:
            ```json
            {
                "data": {
                    "age": 31,
                    "status": "updated"
                }
            }
            ```
            """
            try:
                # Validate schema and table names
                schema_name = sql_security.validate_schema_name(schema_name)
                table_name = sql_security.validate_table_name(table_name)
                
                async with db_manager.get_connection() as conn:
                    # Validate table exists using prepared statement
                    table_exists_stmt = db_manager.prepare_table_exists_query(schema_name, table_name)
                    table_exists = await db_manager.execute_prepared_val(table_exists_stmt, conn)
                    
                    if not table_exists:
                        raise HTTPException(status_code=404, detail=f"Table {schema_name}.{table_name} not found")
                    
                    # Try to convert record_id to integer if possible, otherwise use as string
                    try:
                        record_id_int = int(record_id)
                        record_id_final = record_id_int
                    except ValueError:
                        # If not an integer, use as string
                        record_id_final = record_id
                    
                    # Check if record exists using prepared statement
                    exists_stmt = db_manager.prepare_exists_query(schema_name, table_name, record_id_final)
                    exists = await db_manager.execute_prepared_val(exists_stmt, conn)
                    
                    if not exists:
                        raise HTTPException(status_code=404, detail=f"Record with ID {record_id} not found")
                    
                    # Prepare UPDATE query with parameters
                    update_stmt = db_manager.prepare_update_query(schema_name, table_name, record_id_final, record.data)
                    
                    # Execute update using prepared statement
                    row = await db_manager.execute_prepared_row(update_stmt, conn)
                    
                    if not row:
                        raise HTTPException(status_code=500, detail="Failed to update record")
                    
                    # The database manager now returns a dict with converted datetime strings
                    record_data = row
                    
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

        @self.router.delete("/{schema_name}/{table_name}/{record_id}", response_model=DeleteResponse, summary="Delete Record", description="Remove a record from a table")
        async def delete_record(schema_name: str, table_name: str, record_id: str):
            """
            Delete a record - Remove a record from a table
            
            This endpoint allows you to delete a record by its primary key ID.
            The endpoint returns the deleted record data for confirmation.
            
            Parameters:
            - **schema_name**: Name of the database schema
            - **table_name**: Name of the table to delete from
            - **record_id**: Primary key value of the record to delete
            
            Returns:
            - **message**: Confirmation message
            - **deleted_record**: Complete record data that was deleted
            
            Example:
            ```
            DELETE /crud/public/users/123
            ```
            """
            try:
                # Validate schema and table names
                schema_name = sql_security.validate_schema_name(schema_name)
                table_name = sql_security.validate_table_name(table_name)
                
                async with db_manager.get_connection() as conn:
                    # Validate table exists using prepared statement
                    table_exists_stmt = db_manager.prepare_table_exists_query(schema_name, table_name)
                    table_exists = await db_manager.execute_prepared_val(table_exists_stmt, conn)
                    
                    if not table_exists:
                        raise HTTPException(status_code=404, detail=f"Table {schema_name}.{table_name} not found")
                    
                    # Try to convert record_id to integer if possible, otherwise use as string
                    try:
                        record_id_int = int(record_id)
                        record_id_final = record_id_int
                    except ValueError:
                        # If not an integer, use as string
                        record_id_final = record_id
                    
                    # Check if record exists using prepared statement
                    exists_stmt = db_manager.prepare_exists_query(schema_name, table_name, record_id_final)
                    exists = await db_manager.execute_prepared_val(exists_stmt, conn)
                    
                    if not exists:
                        raise HTTPException(status_code=404, detail=f"Record with ID {record_id} not found")
                    
                    # Prepare DELETE query with parameters
                    delete_stmt = db_manager.prepare_delete_query(schema_name, table_name, record_id_final)
                    
                    # Execute delete using prepared statement
                    row = await db_manager.execute_prepared_row(delete_stmt, conn)
                    
                    if not row:
                        raise HTTPException(status_code=500, detail="Failed to delete record")
                    
                    # The database manager now returns a dict with converted datetime strings
                    record_data = row
                    
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

        @self.router.patch("/{schema_name}/{table_name}/{record_id}", response_model=UpsertResponse, summary="Upsert Record", description="Insert if not exists, update if exists")
        async def upsert_record(schema_name: str, table_name: str, record_id: str, record: RecordUpdate):
            """
            Upsert a record - Insert if not exists, update if exists
            
            This endpoint allows you to either create a new record or update an existing one
            based on the provided record ID. If a record with the given ID exists, it will
            be updated. If not, a new record will be created with the specified ID.
            
            Parameters:
            - **schema_name**: Name of the database schema
            - **table_name**: Name of the table to upsert into
            - **record_id**: Primary key value for the record
            - **record**: Record data to insert or update
            
            Request Body:
            - **data**: Dictionary containing the record fields and values
            
            Returns:
            - **message**: Operation result message
            - **operation**: Type of operation performed ("created" or "updated")
            - **record**: Complete record data after the operation
            
            Example:
            ```json
            {
                "data": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "age": 30,
                    "status": "active"
                }
            }
            ```
            """
            try:
                # Validate schema and table names
                schema_name = sql_security.validate_schema_name(schema_name)
                table_name = sql_security.validate_table_name(table_name)
                
                async with db_manager.get_connection() as conn:
                    # Validate table exists using prepared statement
                    table_exists_stmt = db_manager.prepare_table_exists_query(schema_name, table_name)
                    table_exists = await db_manager.execute_prepared_val(table_exists_stmt, conn)
                    
                    if not table_exists:
                        raise HTTPException(status_code=404, detail=f"Table {schema_name}.{table_name} not found")
                    
                    # Try to convert record_id to integer if possible, otherwise use as string
                    try:
                        record_id_int = int(record_id)
                        record_id_final = record_id_int
                    except ValueError:
                        # If not an integer, use as string
                        record_id_final = record_id
                    
                    # Check if record exists using prepared statement
                    exists_stmt = db_manager.prepare_exists_query(schema_name, table_name, record_id_final)
                    exists = await db_manager.execute_prepared_val(exists_stmt, conn)
                    
                    if exists:
                        # Update existing record using prepared statement
                        update_stmt = db_manager.prepare_update_query(schema_name, table_name, record_id_final, record.data)
                        row = await db_manager.execute_prepared_row(update_stmt, conn)
                        operation = "updated"
                    else:
                        # Insert new record with the specified ID
                        data_with_id = record.data.copy()
                        data_with_id['id'] = record_id_final
                        insert_stmt = db_manager.prepare_insert_query(schema_name, table_name, data_with_id)
                        row = await db_manager.execute_prepared_row(insert_stmt, conn)
                        operation = "created"
                    
                    if not row:
                        raise HTTPException(status_code=500, detail=f"Failed to {operation} record")
                    
                    # The database manager now returns a dict with converted datetime strings
                    record_data = row
                    
                    return {
                        "message": f"Record {operation} successfully",
                        "operation": operation,
                        "record": RecordResponse(
                            id=record_data.get('id'),
                            data=record_data,
                            created_at=record_data.get('created_at'),
                            updated_at=record_data.get('updated_at')
                        )
                    }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to upsert record {record_id} in {schema_name}.{table_name}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to upsert record: {str(e)}")

# Create router instance
crud_router = CrudRouter().router
