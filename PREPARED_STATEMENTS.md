# Prepared Statements Implementation

This document describes the prepared statements implementation in the database service, which provides enhanced security and performance for all CRUD operations.

## Overview

The database service has been updated to use prepared statements consistently across all database operations. This provides several benefits:

1. **Security**: Prevents SQL injection attacks by properly parameterizing all queries
2. **Performance**: Prepared statements can be cached and reused by the database
3. **Consistency**: All database operations now follow the same pattern
4. **Maintainability**: Centralized query preparation logic

## Architecture

### DatabaseManager Class

The core of the prepared statements implementation is the `DatabaseManager` class located in `app/core/database.py`. This class provides:

- Connection pool management
- Prepared statement creation and execution
- Query parameter handling
- Error handling and logging

### PreparedStatement Dataclass

```python
@dataclass
class PreparedStatement:
    sql: str                    # The SQL query with placeholders
    parameters: Tuple[Any, ...] # The parameters to bind
    name: Optional[str] = None  # Optional name for named prepared statements
```

## Key Features

### 1. Automatic Query Preparation

The `DatabaseManager` provides methods to automatically prepare common query types:

- `prepare_select_query()` - SELECT queries with optional WHERE, ORDER BY, LIMIT, OFFSET
- `prepare_insert_query()` - INSERT queries with dynamic column handling
- `prepare_update_query()` - UPDATE queries with dynamic SET clause
- `prepare_delete_query()` - DELETE queries
- `prepare_count_query()` - COUNT queries
- `prepare_exists_query()` - EXISTS queries for record validation
- `prepare_table_exists_query()` - Table existence validation

### 2. Parameter Binding

All queries use PostgreSQL-style parameter placeholders (`$1`, `$2`, etc.) and proper parameter binding:

```python
# Example: SELECT query with parameters
stmt = db_manager.prepare_select_query(
    schema_name="public",
    table_name="users",
    where_clause="age > $1 AND status = $2",
    order_by="created_at DESC",
    limit=10,
    offset=0
)
stmt.parameters = (18, "active")
```

### 3. Execution Methods

The `DatabaseManager` provides three execution methods:

- `execute_prepared()` - Returns multiple rows
- `execute_prepared_row()` - Returns a single row
- `execute_prepared_val()` - Returns a single value

## CRUD Operations

All CRUD endpoints now use prepared statements:

### Read Operations

```python
# Get multiple records
@crud_router.get("/{schema_name}/{table_name}")
async def read_records(schema_name: str, table_name: str, limit: int = 100, offset: int = 0):
    select_stmt = db_manager.prepare_select_query(
        schema_name=schema_name,
        table_name=table_name,
        limit=limit,
        offset=offset
    )
    rows = await db_manager.execute_prepared(select_stmt, conn)
```

### Create Operations

```python
# Create a new record
@crud_router.post("/{schema_name}/{table_name}")
async def create_record(schema_name: str, table_name: str, record: RecordCreate):
    insert_stmt = db_manager.prepare_insert_query(schema_name, table_name, record.data)
    row = await db_manager.execute_prepared_row(insert_stmt, conn)
```

### Update Operations

```python
# Update an existing record
@crud_router.put("/{schema_name}/{table_name}/{record_id}")
async def update_record(schema_name: str, table_name: str, record_id: str, record: RecordUpdate):
    update_stmt = db_manager.prepare_update_query(schema_name, table_name, record_id_final, record.data)
    row = await db_manager.execute_prepared_row(update_stmt, conn)
```

### Delete Operations

```python
# Delete a record
@crud_router.delete("/{schema_name}/{table_name}/{record_id}")
async def delete_record(schema_name: str, table_name: str, record_id: str):
    delete_stmt = db_manager.prepare_delete_query(schema_name, table_name, record_id_final)
    row = await db_manager.execute_prepared_row(delete_stmt, conn)
```

## Raw SQL Endpoints

The raw SQL endpoints also use prepared statements for enhanced security:

```python
@crud_router.post("/raw-sql")
async def execute_raw_sql(request: RawSQLRequest):
    stmt = PreparedStatement(request.sql, tuple(param_list))
    rows = await db_manager.execute_prepared(stmt, conn)
```

## Security Benefits

### SQL Injection Prevention

All user input is properly parameterized, preventing SQL injection attacks:

```python
# Before (vulnerable to SQL injection)
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# After (secure with prepared statements)
stmt = db_manager.prepare_select_query("public", "users", where_clause="name = $1")
stmt.parameters = (user_input,)
```

### Input Validation

The existing `sql_security` module continues to provide additional validation:

- SQL keyword validation
- Dangerous pattern detection
- Operation type validation (read vs write)

## Performance Benefits

### Query Caching

Prepared statements can be cached by the database server, reducing parsing overhead for repeated queries.

### Connection Pooling

The existing connection pool works seamlessly with prepared statements, maintaining efficient resource usage.

## Testing

A test script `test_prepared_statements.py` is provided to verify the implementation:

```bash
python test_prepared_statements.py
```

This script tests:
- Basic prepared statement functionality
- CRUD operations with prepared statements
- Parameter binding
- Error handling

## Migration Notes

### Backward Compatibility

The existing API endpoints remain unchanged. The prepared statements are an internal implementation detail.

### Legacy Functions

Legacy functions are maintained for backward compatibility:
- `get_pool()`
- `get_db_connection()`
- `test_connection()`

### Configuration

No additional configuration is required. The prepared statements work with the existing database configuration.

## Best Practices

### 1. Always Use Prepared Statements

Never construct SQL queries using string formatting. Always use the `DatabaseManager` methods.

### 2. Validate Input

Continue using the `sql_security` module for input validation and sanitization.

### 3. Handle Errors Gracefully

The `DatabaseManager` provides comprehensive error handling and logging.

### 4. Monitor Performance

Use the existing monitoring endpoints to track database performance and connection pool statistics.

## Example Usage

```python
from app.core.database import db_manager

async def example_crud_operations():
    async with db_manager.get_connection() as conn:
        # Create a record
        data = {"name": "John Doe", "email": "john@example.com"}
        insert_stmt = db_manager.prepare_insert_query("public", "users", data)
        new_user = await db_manager.execute_prepared_row(insert_stmt, conn)
        
        # Read records
        select_stmt = db_manager.prepare_select_query(
            "public", "users", 
            where_clause="email ILIKE $1",
            limit=10
        )
        select_stmt.parameters = ("%example.com",)
        users = await db_manager.execute_prepared(select_stmt, conn)
        
        # Update a record
        update_data = {"email": "john.updated@example.com"}
        update_stmt = db_manager.prepare_update_query("public", "users", 1, update_data)
        updated_user = await db_manager.execute_prepared_row(update_stmt, conn)
        
        # Delete a record
        delete_stmt = db_manager.prepare_delete_query("public", "users", 1)
        deleted_user = await db_manager.execute_prepared_row(delete_stmt, conn)
```

This implementation ensures that all database operations are secure, efficient, and maintainable.
