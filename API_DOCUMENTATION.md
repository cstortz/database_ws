# Database Service API Documentation

## Overview

The Database Service API provides comprehensive database operations through a secure, high-performance FastAPI service. All operations use prepared statements to prevent SQL injection and ensure optimal performance.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, no authentication is required. All endpoints are publicly accessible.

## Response Format

All API responses follow a consistent JSON format:

### Success Response
```json
{
  "success": true,
  "data": [...],
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "error": "Error type",
  "detail": "Detailed error message"
}
```

## Endpoints

### Root Endpoint

#### GET /
Get service information and available endpoint groups.

**Response:**
```json
{
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
```

### Health Check

#### GET /health
Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "message": "Database Service is running",
  "version": "2.1.0",
  "detailed_health": "/admin/health"
}
```

## Admin Endpoints (`/admin/*`)

### GET /admin/health
Comprehensive health check including database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "pgbouncer_host": "db01.int.stortz.tech",
  "pgbouncer_port": 6432,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### GET /admin/test-connection
Test database connection and return detailed connection information.

**Response:**
```json
{
  "status": "success",
  "details": {
    "status": "connected",
    "host": "db01.int.stortz.tech",
    "port": 6432,
    "database": "postgres",
    "user": "postgres",
    "version": "PostgreSQL 15.1",
    "write_test": "passed"
  }
}
```

### GET /admin/db-info
Get database information including version and connection details.

**Response:**
```json
{
  "version": "PostgreSQL 15.1",
  "database": "postgres",
  "user": "postgres",
  "host": "db01.int.stortz.tech",
  "port": 6432
}
```

### GET /admin/databases
List all databases with their metadata.

**Response:**
```json
{
  "databases": [
    {
      "name": "postgres",
      "owner": "postgres",
      "encoding": "UTF8",
      "collate": "en_US.UTF-8",
      "ctype": "en_US.UTF-8",
      "access_privileges": null,
      "size": "8.1 MB",
      "comment": null
    }
  ]
}
```

### GET /admin/schemas
List all schemas with their metadata.

**Response:**
```json
{
  "schemas": [
    {
      "name": "public",
      "owner": "postgres",
      "access_privileges": null,
      "comment": null
    }
  ]
}
```

### GET /admin/tables
List all tables with their metadata.

**Response:**
```json
{
  "tables": [
    {
      "table_name": "documents",
      "table_schema": "public",
      "table_owner": "postgres",
      "table_size": "8192 bytes",
      "estimated_rows": 4,
      "comment": null
    }
  ]
}
```

### GET /admin/tables/{schema_name}
List tables in a specific schema.

**Parameters:**
- `schema_name` (path): Name of the schema

**Response:**
```json
{
  "tables": [
    {
      "table_name": "documents",
      "table_schema": "public",
      "table_owner": "postgres",
      "table_size": "8192 bytes",
      "estimated_rows": 4,
      "comment": null
    }
  ]
}
```

## CRUD Operations (`/crud/*`)

### GET /crud/{schema_name}/{table_name}
Read multiple records with pagination and ordering.

**Parameters:**
- `schema_name` (path): Name of the schema
- `table_name` (path): Name of the table
- `limit` (query, optional): Maximum number of records to return (default: 100)
- `offset` (query, optional): Number of records to skip (default: 0)
- `order_by` (query, optional): Column to order by (e.g., "id DESC")

**Response:**
```json
{
  "records": [
    {
      "id": 1,
      "data": {
        "id": 1,
        "content": "Document content",
        "embedding": null
      },
      "created_at": null,
      "updated_at": null
    }
  ],
  "count": 1,
  "total_count": 1
}
```

### GET /crud/{schema_name}/{table_name}/{record_id}
Read a single record by ID.

**Parameters:**
- `schema_name` (path): Name of the schema
- `table_name` (path): Name of the table
- `record_id` (path): ID of the record

**Response:**
```json
{
  "id": 1,
  "data": {
    "id": 1,
    "content": "Document content",
    "embedding": null
  },
  "created_at": null,
  "updated_at": null
}
```

### POST /crud/{schema_name}/{table_name}
Create a new record.

**Parameters:**
- `schema_name` (path): Name of the schema
- `table_name` (path): Name of the table

**Request Body:**
```json
{
  "data": {
    "content": "New document content"
  }
}
```

**Response:**
```json
{
  "id": 5,
  "data": {
    "id": 5,
    "content": "New document content",
    "embedding": null
  },
  "created_at": null,
  "updated_at": null
}
```

### PUT /crud/{schema_name}/{table_name}/{record_id}
Update an existing record.

**Parameters:**
- `schema_name` (path): Name of the schema
- `table_name` (path): Name of the table
- `record_id` (path): ID of the record

**Request Body:**
```json
{
  "data": {
    "content": "Updated document content"
  }
}
```

**Response:**
```json
{
  "id": 1,
  "data": {
    "id": 1,
    "content": "Updated document content",
    "embedding": null
  },
  "created_at": null,
  "updated_at": null
}
```

### DELETE /crud/{schema_name}/{table_name}/{record_id}
Delete a record.

**Parameters:**
- `schema_name` (path): Name of the schema
- `table_name` (path): Name of the table
- `record_id` (path): ID of the record

**Response:**
```json
{
  "message": "Record deleted successfully",
  "deleted_record": {
    "id": 1,
    "data": {
      "id": 1,
      "content": "Document content",
      "embedding": null
    },
    "created_at": null,
    "updated_at": null
  }
}
```

### PATCH /crud/{schema_name}/{table_name}/{record_id}
Upsert a record (create if not exists, update if exists).

**Parameters:**
- `schema_name` (path): Name of the schema
- `table_name` (path): Name of the table
- `record_id` (path): ID of the record

**Request Body:**
```json
{
  "data": {
    "content": "Upserted document content"
  }
}
```

**Response:**
```json
{
  "message": "Record created successfully",
  "operation": "created",
  "record": {
    "id": 999,
    "data": {
      "id": 999,
      "content": "Upserted document content",
      "embedding": null
    },
    "created_at": null,
    "updated_at": null
  }
}
```

## Raw SQL Operations (`/raw/*`)

### POST /raw/sql
Execute read-only SQL queries with parameter binding.

**Request Body:**
```json
{
  "sql": "SELECT * FROM documents WHERE id > $1 LIMIT $2",
  "parameters": {
    "1": "0",
    "2": "5"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "content": "Document content",
      "embedding": null
    }
  ],
  "row_count": 1,
  "sql": "SELECT * FROM documents WHERE id > $1 LIMIT $2",
  "parameters": {
    "1": "0",
    "2": "5"
  }
}
```

### POST /raw/sql/write
Execute write SQL queries (INSERT, UPDATE, DELETE) with parameter binding.

**Request Body:**
```json
{
  "sql": "INSERT INTO documents (content) VALUES ($1) RETURNING *",
  "parameters": {
    "1": "New document from raw SQL"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 6,
      "content": "New document from raw SQL",
      "embedding": null
    }
  ],
  "affected_rows": 1,
  "sql": "INSERT INTO documents (content) VALUES ($1) RETURNING *",
  "parameters": {
    "1": "New document from raw SQL"
  }
}
```

## Prepared SQL Operations (`/crud/prepared/*`)

### POST /crud/prepared/execute
Execute any prepared SQL statement.

**Request Body:**
```json
{
  "sql": "SELECT * FROM documents WHERE content ILIKE $1",
  "parameters": {
    "1": "%test%"
  },
  "operation_type": "read"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Prepared SQL query executed successfully. Rows returned: 1",
  "data": [
    {
      "id": 1,
      "content": "Test document",
      "embedding": null
    }
  ],
  "row_count": 1,
  "affected_rows": null,
  "sql": "SELECT * FROM documents WHERE content ILIKE $1",
  "parameters": {
    "1": "%test%"
  }
}
```

### POST /crud/prepared/select
Execute SELECT statements with prepared statement optimization.

**Request Body:**
```json
{
  "sql": "SELECT COUNT(*) as total FROM documents",
  "parameters": {},
  "operation_type": "read"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Prepared SQL query executed successfully. Rows returned: 1",
  "data": [
    {
      "total": 4
    }
  ],
  "row_count": 1,
  "affected_rows": null,
  "sql": "SELECT COUNT(*) as total FROM documents",
  "parameters": {}
}
```

### POST /crud/prepared/insert
Execute INSERT statements with prepared statement optimization.

**Request Body:**
```json
{
  "sql": "INSERT INTO documents (content) VALUES ($1) RETURNING *",
  "parameters": {
    "1": "Document from prepared statement"
  },
  "operation_type": "write"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Prepared SQL query executed successfully. Rows affected: 1",
  "data": [
    {
      "id": 7,
      "content": "Document from prepared statement",
      "embedding": null
    }
  ],
  "row_count": 1,
  "affected_rows": 1,
  "sql": "INSERT INTO documents (content) VALUES ($1) RETURNING *",
  "parameters": {
    "1": "Document from prepared statement"
  }
}
```

### POST /crud/prepared/update
Execute UPDATE statements with prepared statement optimization.

**Request Body:**
```json
{
  "sql": "UPDATE documents SET content = $1 WHERE id = $2 RETURNING *",
  "parameters": {
    "1": "Updated content",
    "2": "1"
  },
  "operation_type": "write"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Prepared SQL query executed successfully. Rows affected: 1",
  "data": [
    {
      "id": 1,
      "content": "Updated content",
      "embedding": null
    }
  ],
  "row_count": 1,
  "affected_rows": 1,
  "sql": "UPDATE documents SET content = $1 WHERE id = $2 RETURNING *",
  "parameters": {
    "1": "Updated content",
    "2": "1"
  }
}
```

### POST /crud/prepared/delete
Execute DELETE statements with prepared statement optimization.

**Request Body:**
```json
{
  "sql": "DELETE FROM documents WHERE id = $1 RETURNING *",
  "parameters": {
    "1": "1"
  },
  "operation_type": "write"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Prepared SQL query executed successfully. Rows affected: 1",
  "data": [
    {
      "id": 1,
      "content": "Document content",
      "embedding": null
    }
  ],
  "row_count": 1,
  "affected_rows": 1,
  "sql": "DELETE FROM documents WHERE id = $1 RETURNING *",
  "parameters": {
    "1": "1"
  }
}
```

### GET /crud/prepared/statements
List all cached prepared statements.

**Response:**
```json
{
  "statements": [
    {
      "name": "select_documents",
      "sql": "SELECT * FROM documents WHERE id = $1",
      "parameter_count": 1,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### DELETE /crud/prepared/statements
Clear all cached prepared statements.

**Response:**
```json
{
  "message": "All prepared statements cleared successfully",
  "cleared_count": 5
}
```

### DELETE /crud/prepared/statements/{statement_name}
Clear a specific cached prepared statement.

**Parameters:**
- `statement_name` (path): Name of the prepared statement

**Response:**
```json
{
  "message": "Prepared statement 'select_documents' cleared successfully"
}
```

### POST /crud/prepared/validate
Validate SQL statements without execution.

**Request Body:**
```json
{
  "sql": "SELECT * FROM documents WHERE id = $1",
  "parameters": {
    "1": "1"
  },
  "operation_type": "read"
}
```

**Response:**
```json
{
  "valid": true,
  "message": "Prepared SQL statement is valid",
  "sql": "SELECT * FROM documents WHERE id = $1",
  "parameters": {
    "1": "1"
  },
  "placeholder_count": 1,
  "parameter_count": 1,
  "operation_type": "read"
}
```

## Error Codes

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid request data or SQL
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

### Common Error Responses

#### Validation Error
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "data"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

#### SQL Error
```json
{
  "error": "SQL execution failed",
  "detail": "relation \"non_existent_table\" does not exist"
}
```

#### Security Error
```json
{
  "error": "SQL injection attempt detected",
  "detail": "SQL injection attempt detected: dangerous keyword 'DROP'"
}
```

## Security Features

### SQL Injection Protection
- All database operations use prepared statements
- Parameter binding prevents SQL injection
- SQL security validation blocks dangerous keywords
- Input sanitization for schema and table names

### Operation Type Validation
- Read operations only allow SELECT statements
- Write operations only allow INSERT, UPDATE, DELETE
- Dangerous SQL keywords are blocked
- Pattern-based injection detection

## Performance Features

### Connection Pooling
- Efficient connection reuse
- Configurable pool sizes
- Automatic connection cleanup
- Health monitoring

### Prepared Statement Caching
- Statements can be cached and reused
- Reduced parsing overhead
- Better connection pool utilization
- Automatic cache management

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production use.

## Examples

### Complete CRUD Workflow

```bash
# 1. Create a record
curl -X POST "http://localhost:8000/crud/public/documents" \
  -H "Content-Type: application/json" \
  -d '{"data": {"content": "New document"}}'

# 2. Read the record
curl -X GET "http://localhost:8000/crud/public/documents/1"

# 3. Update the record
curl -X PUT "http://localhost:8000/crud/public/documents/1" \
  -H "Content-Type: application/json" \
  -d '{"data": {"content": "Updated document"}}'

# 4. Delete the record
curl -X DELETE "http://localhost:8000/crud/public/documents/1"
```

### Raw SQL with Parameters

```bash
# Execute parameterized query
curl -X POST "http://localhost:8000/raw/sql" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM documents WHERE id > $1 LIMIT $2",
    "parameters": {"1": "0", "2": "5"}
  }'
```

### Prepared SQL Operations

```bash
# Validate SQL without execution
curl -X POST "http://localhost:8000/crud/prepared/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM documents WHERE id = $1",
    "parameters": {"1": "1"},
    "operation_type": "read"
  }'

# Execute prepared SELECT
curl -X POST "http://localhost:8000/crud/prepared/select" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT COUNT(*) as total FROM documents",
    "parameters": {},
    "operation_type": "read"
  }'
```

## Interactive Documentation

Visit the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

The interactive documentation provides:
- Complete endpoint descriptions
- Request/response schemas
- Parameter validation rules
- Error response formats
- Interactive testing interface
