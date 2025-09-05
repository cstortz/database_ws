# Router Structure Documentation

## Overview

The database service has been refactored to use a modular router structure, breaking down the monolithic `main.py` into separate, focused router classes. This provides better organization, maintainability, and separation of concerns.

## Architecture

### Router Classes

The application now uses four main router classes:

1. **AdminRouter** (`/admin/*`) - Database service management
2. **RawRouter** (`/raw/*`) - Raw SQL execution
3. **CrudRouter** (`/crud/*`) - Standard CRUD operations
4. **PreparedRouter** (`/crud/prepared/*`) - Advanced prepared SQL operations

### File Structure

```
app/
├── main.py                 # Main application entry point
├── routers/
│   ├── __init__.py        # Router package initialization
│   ├── admin_router.py    # Admin endpoints
│   ├── raw_router.py      # Raw SQL endpoints
│   ├── crud_router.py     # CRUD operations
│   └── prepared_router.py # Prepared SQL operations
└── core/
    ├── database.py        # Database manager with prepared statements
    ├── sql_security.py    # SQL injection protection
    └── config.py          # Configuration settings
```

## Router Details

### 1. AdminRouter (`/admin/*`)

**Purpose**: Database service management and monitoring

**Endpoints**:
- `GET /admin/health` - Health check
- `GET /admin/test-connection` - Test database connection
- `GET /admin/db-info` - Get database information
- `GET /admin/databases` - List all databases
- `GET /admin/schemas` - List all schemas
- `GET /admin/tables` - List all tables
- `GET /admin/tables/{schema_name}` - List tables by schema

**Features**:
- Service health monitoring
- Database metadata exploration
- Connection testing and diagnostics

### 2. RawRouter (`/raw/*`)

**Purpose**: Execute raw SQL queries with parameter support

**Endpoints**:
- `POST /raw/sql` - Execute read queries
- `POST /raw/sql/write` - Execute write queries (INSERT, UPDATE, DELETE)

**Features**:
- Raw SQL execution with parameter binding
- SQL injection protection via `sql_security`
- Support for both read and write operations
- Parameter validation and error handling

### 3. CrudRouter (`/crud/*`)

**Purpose**: Standard CRUD operations using prepared statements

**Endpoints**:
- `GET /crud/{schema_name}/{table_name}` - Read multiple records
- `GET /crud/{schema_name}/{table_name}/{record_id}` - Read single record
- `POST /crud/{schema_name}/{table_name}` - Create record
- `PUT /crud/{schema_name}/{table_name}/{record_id}` - Update record
- `DELETE /crud/{schema_name}/{table_name}/{record_id}` - Delete record
- `PATCH /crud/{schema_name}/{table_name}/{record_id}` - Upsert record

**Features**:
- Automatic prepared statement generation
- Dynamic query building
- Input validation and sanitization
- Pagination and ordering support

### 4. PreparedRouter (`/crud/prepared/*`)

**Purpose**: Advanced prepared SQL operations with enhanced features

**Endpoints**:

#### Execution Endpoints
- `POST /crud/prepared/execute` - Execute any prepared SQL statement
- `POST /crud/prepared/select` - Execute SELECT statements
- `POST /crud/prepared/insert` - Execute INSERT statements
- `POST /crud/prepared/update` - Execute UPDATE statements
- `POST /crud/prepared/delete` - Execute DELETE statements

#### Management Endpoints
- `GET /crud/prepared/statements` - List cached prepared statements
- `DELETE /crud/prepared/statements/{statement_name}` - Clear specific statement
- `DELETE /crud/prepared/statements` - Clear all statements

#### Validation Endpoints
- `POST /crud/prepared/validate` - Validate SQL without execution

**Features**:
- Specialized endpoints for different SQL operations
- Prepared statement caching and management
- SQL validation without execution
- Enhanced error reporting and debugging
- Parameter count validation

## API Usage Examples

### Admin Operations

```bash
# Health check
curl -X GET "http://localhost:8000/admin/health"

# Get database info
curl -X GET "http://localhost:8000/admin/db-info"

# List tables
curl -X GET "http://localhost:8000/admin/tables"
```

### Raw SQL Operations

```bash
# Execute read query
curl -X POST "http://localhost:8000/raw/sql" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM users WHERE age > $1",
    "parameters": {"1": 18}
  }'

# Execute write query
curl -X POST "http://localhost:8000/raw/sql/write" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "UPDATE users SET status = $1 WHERE id = $2",
    "parameters": {"1": "active", "2": 123}
  }'
```

### CRUD Operations

```bash
# Read records
curl -X GET "http://localhost:8000/crud/public/users?limit=10&offset=0"

# Create record
curl -X POST "http://localhost:8000/crud/public/users" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "name": "John Doe",
      "email": "john@example.com",
      "age": 30
    }
  }'

# Update record
curl -X PUT "http://localhost:8000/crud/public/users/123" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "age": 31,
      "status": "updated"
    }
  }'
```

### Prepared SQL Operations

```bash
# Execute prepared SELECT
curl -X POST "http://localhost:8000/crud/prepared/select" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM users WHERE department = $1 AND active = $2",
    "parameters": {"1": "engineering", "2": true},
    "operation_type": "read"
  }'

# Execute prepared INSERT
curl -X POST "http://localhost:8000/crud/prepared/insert" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "INSERT INTO users (name, email, department) VALUES ($1, $2, $3) RETURNING *",
    "parameters": {"1": "Jane Smith", "2": "jane@example.com", "3": "marketing"},
    "operation_type": "write"
  }'

# Validate SQL without execution
curl -X POST "http://localhost:8000/crud/prepared/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM users WHERE id = $1",
    "parameters": {"1": 123},
    "operation_type": "read"
  }'

# List cached prepared statements
curl -X GET "http://localhost:8000/crud/prepared/statements"

# Clear all prepared statements
curl -X DELETE "http://localhost:8000/crud/prepared/statements"
```

## Request/Response Models

### PreparedSQLRequest
```python
{
    "sql": "SELECT * FROM users WHERE id = $1",
    "parameters": {"1": 123},
    "operation_type": "read"  # "read" or "write"
}
```

### PreparedSQLResponse
```python
{
    "success": true,
    "message": "Prepared SQL query executed successfully. Rows returned: 1",
    "data": [{"id": 123, "name": "John Doe"}],
    "row_count": 1,
    "affected_rows": null,
    "sql": "SELECT * FROM users WHERE id = $1",
    "parameters": {"1": 123}
}
```

### Validation Response
```python
{
    "valid": true,
    "message": "Prepared SQL statement is valid",
    "sql": "SELECT * FROM users WHERE id = $1",
    "parameters": {"1": 123},
    "placeholder_count": 1,
    "parameter_count": 1,
    "operation_type": "read"
}
```

## Security Features

### SQL Injection Protection
- All endpoints use prepared statements
- Parameter binding prevents SQL injection
- `sql_security` module provides additional validation
- Input sanitization for schema and table names

### Operation Type Validation
- Read operations only allow SELECT statements
- Write operations only allow INSERT, UPDATE, DELETE
- Dangerous SQL keywords are blocked
- Pattern-based injection detection

## Performance Benefits

### Prepared Statement Caching
- Statements can be cached and reused
- Reduced parsing overhead
- Better connection pool utilization
- Automatic cache management

### Connection Pooling
- Efficient connection reuse
- Configurable pool sizes
- Automatic connection cleanup
- Health monitoring

## Error Handling

### Comprehensive Error Responses
- Detailed error messages
- HTTP status codes
- Logging for debugging
- Parameter validation errors

### Graceful Degradation
- Connection failure handling
- Timeout management
- Resource cleanup
- Fallback mechanisms

## Monitoring and Debugging

### Health Checks
- Database connectivity monitoring
- Service status endpoints
- Performance metrics
- Error rate tracking

### Prepared Statement Management
- Cache size monitoring
- Statement performance tracking
- Memory usage optimization
- Cache cleanup utilities

## Migration Guide

### From Version 1.0
- All existing endpoints remain functional
- No breaking changes to API contracts
- Enhanced security and performance
- Additional prepared SQL capabilities

### New Features
- `/crud/prepared/*` endpoints for advanced operations
- Enhanced validation and error reporting
- Better monitoring and debugging tools
- Improved documentation and examples

## Best Practices

### Using Prepared SQL Endpoints
1. Always validate SQL before execution
2. Use appropriate operation types
3. Monitor prepared statement cache
4. Clear cache when needed

### Security Considerations
1. Validate all inputs
2. Use parameter binding
3. Limit SQL complexity
4. Monitor for suspicious patterns

### Performance Optimization
1. Reuse prepared statements
2. Monitor cache usage
3. Optimize connection pooling
4. Track query performance

This modular router structure provides a clean, maintainable, and extensible architecture for the database service while maintaining backward compatibility and adding powerful new prepared SQL capabilities.
