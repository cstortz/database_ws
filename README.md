# Database REST Service

A comprehensive FastAPI service that connects to a PgBouncer instance and provides full database operations with advanced security and performance features.

## Features

- **PgBouncer Connection**: Connects to PgBouncer with configurable host and port
- **Environment-based Configuration**: Uses `.env` files and environment variables
- **Connection Pooling**: Uses asyncpg connection pool for efficient database connections
- **Prepared Statements**: All database operations use prepared statements for security and performance
- **SQL Injection Protection**: Comprehensive SQL security validation and parameter binding
- **CRUD Operations**: Full Create, Read, Update, Delete operations with pagination and ordering
- **Raw SQL Execution**: Execute custom SQL queries with parameter binding
- **Advanced Prepared SQL**: Specialized endpoints for complex prepared statement operations
- **Health Checks**: Comprehensive endpoints to validate database connectivity and service status
- **Comprehensive Tests**: Full test suite covering all endpoints and functionality

## Quick Start

### Prerequisites
- Python 3.8+
- PgBouncer running (configurable host and port)
- PostgreSQL database accessible via PgBouncer

### Installation

#### Option 1: Local Development

```bash
# Clone and setup
git clone <repository-url>
cd database_ws

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your database settings

# Run connection test
python run_tests.py

# Start the service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Option 2: Docker (Recommended for Production)

```bash
# Clone and setup
git clone <repository-url>
cd database_ws

# Setup environment variables
cp .env.example .env
# Edit .env with your database settings

# Build and run with Docker
./build.sh

# Or manually:
docker build -t database-service:latest .
docker-compose up -d
```

### Configuration

The service uses environment variables for configuration. Copy `.env.example` to `.env` and update the values:

```bash
# Database Configuration
PGBOUNCER_HOST=localhost
PGBOUNCER_PORT=5432
DATABASE_NAME=postgres
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password_here

# Connection Pool Settings
MIN_CONNECTIONS=1
MAX_CONNECTIONS=10

# Application Settings
DEBUG=true
```

You can also override these settings using environment variables:

```bash
export PGBOUNCER_HOST="your-pgbouncer-host"
export PGBOUNCER_PORT="5432"
export DATABASE_NAME="your-database"
export DATABASE_USER="your-user"
export DATABASE_PASSWORD="your-password"
```

## API Endpoints

### Root
```bash
GET /
```
Returns basic service information and available endpoint groups.

### Admin Endpoints (`/admin/*`)

All admin endpoints are grouped under `/admin` and provide database service management and monitoring.

#### Health Check
```bash
GET /admin/health
```
Returns comprehensive service health status including database connection status.

#### Connection Test
```bash
GET /admin/test-connection
```
Tests database connection and returns detailed connection information.

#### Database Info
```bash
GET /admin/db-info
```
Returns database version, name, user, and connection details.

#### Get All Databases
```bash
GET /admin/databases
```
Returns list of all databases with their descriptions, owners, sizes, and comments.

#### Get All Schemas
```bash
GET /admin/schemas
```
Returns list of all schemas with their descriptions, owners, and comments.

#### Get All Tables
```bash
GET /admin/tables
```
Returns list of all tables with their descriptions, owners, sizes, estimated rows, and comments.

#### Get Tables by Schema
```bash
GET /admin/tables/{schema_name}
```
Returns list of tables in a specific schema with their descriptions, owners, sizes, and comments.

### CRUD Operations (`/crud/*`)

Standard CRUD operations with prepared statements, pagination, and ordering support.

#### Read Operations
```bash
GET /crud/{schema_name}/{table_name}
GET /crud/{schema_name}/{table_name}/{record_id}
```
Read multiple records with pagination and ordering, or read a single record by ID.

#### Write Operations
```bash
POST /crud/{schema_name}/{table_name}
PUT /crud/{schema_name}/{table_name}/{record_id}
DELETE /crud/{schema_name}/{table_name}/{record_id}
PATCH /crud/{schema_name}/{table_name}/{record_id}
```
Create, update, delete, or upsert records with automatic prepared statement generation.

### Raw SQL Operations (`/raw/*`)

Execute custom SQL queries with parameter binding and security validation.

#### Read Queries
```bash
POST /raw/sql
```
Execute SELECT queries with parameter binding.

#### Write Queries
```bash
POST /raw/sql/write
```
Execute INSERT, UPDATE, DELETE queries with parameter binding.

### Advanced Prepared SQL Operations (`/crud/prepared/*`)

Specialized endpoints for complex prepared statement operations with caching and validation.

#### Execution Endpoints
```bash
POST /crud/prepared/execute
POST /crud/prepared/select
POST /crud/prepared/insert
POST /crud/prepared/update
POST /crud/prepared/delete
```
Execute prepared SQL statements with specialized operation types.

#### Management Endpoints
```bash
GET /crud/prepared/statements
DELETE /crud/prepared/statements
DELETE /crud/prepared/statements/{statement_name}
```
Manage cached prepared statements.

#### Validation Endpoints
```bash
POST /crud/prepared/validate
```
Validate SQL statements without execution.

## API Usage Examples

### Admin Operations

```bash
# Health check
curl -X GET "http://localhost:8000/admin/health"

# Get database info
curl -X GET "http://localhost:8000/admin/db-info"

# List all tables
curl -X GET "http://localhost:8000/admin/tables"

# List tables in specific schema
curl -X GET "http://localhost:8000/admin/tables/public"
```

### CRUD Operations

```bash
# Read multiple records with pagination
curl -X GET "http://localhost:8000/crud/public/documents?limit=10&offset=0&order_by=id DESC"

# Read single record
curl -X GET "http://localhost:8000/crud/public/documents/1"

# Create new record
curl -X POST "http://localhost:8000/crud/public/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "content": "New document content"
    }
  }'

# Update record
curl -X PUT "http://localhost:8000/crud/public/documents/1" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "content": "Updated document content"
    }
  }'

# Delete record
curl -X DELETE "http://localhost:8000/crud/public/documents/1"

# Upsert record (create or update)
curl -X PATCH "http://localhost:8000/crud/public/documents/999" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "content": "Upserted document content"
    }
  }'
```

### Raw SQL Operations

```bash
# Execute read query
curl -X POST "http://localhost:8000/raw/sql" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM documents WHERE id > $1 LIMIT $2",
    "parameters": {"1": "0", "2": "5"}
  }'

# Execute write query
curl -X POST "http://localhost:8000/raw/sql/write" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "INSERT INTO documents (content) VALUES ($1) RETURNING *",
    "parameters": {"1": "New document from raw SQL"}
  }'
```

### Advanced Prepared SQL Operations

```bash
# Execute prepared SELECT
curl -X POST "http://localhost:8000/crud/prepared/select" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM documents WHERE content ILIKE $1",
    "parameters": {"1": "%test%"},
    "operation_type": "read"
  }'

# Execute prepared INSERT
curl -X POST "http://localhost:8000/crud/prepared/insert" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "INSERT INTO documents (content) VALUES ($1) RETURNING *",
    "parameters": {"1": "Document from prepared statement"},
    "operation_type": "write"
  }'

# Validate SQL without execution
curl -X POST "http://localhost:8000/crud/prepared/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM documents WHERE id = $1",
    "parameters": {"1": "1"},
    "operation_type": "read"
  }'

# List cached prepared statements
curl -X GET "http://localhost:8000/crud/prepared/statements"

# Clear all prepared statements
curl -X DELETE "http://localhost:8000/crud/prepared/statements"
```

## Docker

### Quick Start with Docker

```bash
# Build and run
./build.sh

# Or step by step:
docker build -t database-service:latest .
docker-compose up -d
```

### Docker Commands

```bash
# View logs
docker-compose logs -f

# Stop service
docker-compose down

# Restart service
docker-compose restart

# Rebuild and restart
docker-compose up -d --build

# Run tests in container
docker-compose exec database-service python run_tests.py
```

### Environment Variables in Docker

The Docker setup supports environment variables through:
- `.env` file (mounted into container)
- Environment variables in `docker-compose.yml`
- Direct environment variable overrides

## Testing

### Comprehensive Test Suite

The service includes a comprehensive test suite covering all endpoints and functionality:

#### Quick Connection Test
```bash
# Basic connection test
python run_tests.py
```

#### Full Endpoint Testing
```bash
# Test all admin endpoints
python test_admin_endpoints.py

# Test all CRUD endpoints
python test_crud_endpoints.py

# Test all raw SQL endpoints
python test_raw_endpoints.py

# Test all prepared SQL endpoints
python test_prepared_endpoints.py
```

#### Pytest Suite
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_database.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# In Docker container
docker-compose exec database-service python run_tests.py
```

### Test Coverage

The test suite covers:

- **Admin Endpoints**: All 8 admin endpoints with health checks, database info, and metadata
- **CRUD Operations**: All 6 CRUD endpoints with create, read, update, delete, and upsert operations
- **Raw SQL Operations**: Both read and write SQL execution with parameter binding
- **Prepared SQL Operations**: All 8 prepared SQL endpoints with validation and caching
- **Error Handling**: Comprehensive error scenarios and edge cases
- **Security**: SQL injection protection and parameter validation
- **Performance**: Connection pooling and prepared statement caching

### Test Output Example
```
🔍 Testing Database Connection to PgBouncer...
   Host: db01.int.stortz.tech
   Port: 6432
   Database: postgres
   User: postgres

📡 Testing connection...
✅ Connection successful!
   Status: connected
   Database: postgres
   User: postgres
   Version: PostgreSQL 15.1 on x86_64-pc-linux-gnu
   Write test: passed

📊 Connection pool stats:
   Pool created: True
   Total connections: 1
   Active connections: 0
   Idle connections: 1

🎉 All tests passed!
```

## Project Structure

```
database_ws/
├── app/
│   ├── main.py                    # FastAPI application with router configuration
│   ├── core/
│   │   ├── config.py             # Configuration settings
│   │   ├── database.py           # Database manager with prepared statements
│   │   └── sql_security.py       # SQL injection protection
│   └── routers/
│       ├── __init__.py           # Router package initialization
│       ├── admin_router.py       # Admin endpoints (/admin/*)
│       ├── crud_router.py        # CRUD operations (/crud/*)
│       ├── raw_router.py         # Raw SQL endpoints (/raw/*)
│       └── prepared_router.py    # Prepared SQL operations (/crud/prepared/*)
├── tests/
│   ├── __init__.py               # Test package initialization
│   └── test_database.py          # Core database and API tests
├── test_*.py                     # Comprehensive endpoint test scripts
├── requirements.txt              # Python dependencies
├── run_tests.py                  # Quick connection test script
├── docker-compose.yml            # Docker configuration
├── Dockerfile                    # Docker image definition
├── build.sh                      # Build script
├── README.md                     # This documentation
├── ROUTER_STRUCTURE.md           # Router architecture documentation
├── PREPARED_STATEMENTS.md        # Prepared statements documentation
└── CHANGELOG.md                  # Version history and changes
```

## Development

### Running the Service
```bash
# Development mode with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_database.py::TestDatabaseConnection::test_database_connection -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### API Documentation
Once the service is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

The API documentation includes:
- Complete endpoint descriptions with examples
- Request/response schemas
- Parameter validation rules
- Error response formats
- Interactive testing interface

## Troubleshooting

### Connection Issues
1. **Verify PgBouncer is running**: Check if PgBouncer is accessible at `192.168.68.129:6432`
2. **Check credentials**: Verify database user and password
3. **Network connectivity**: Ensure the service can reach the PgBouncer host
4. **Database permissions**: Ensure the user has proper permissions

### Common Error Messages
- `connection failed`: PgBouncer is not accessible
- `authentication failed`: Invalid username/password
- `database does not exist`: Database name is incorrect

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PGBOUNCER_HOST` | `db01.int.stortz.tech` | PgBouncer host address |
| `PGBOUNCER_PORT` | `6432` | PgBouncer port |
| `DATABASE_NAME` | `postgres` | Database name |
| `DATABASE_USER` | `postgres` | Database username |
| `DATABASE_PASSWORD` | `postgres` | Database password |
| `MIN_CONNECTIONS` | `1` | Minimum connections in pool |
| `MAX_CONNECTIONS` | `10` | Maximum connections in pool |
| `DEBUG` | `True` | Enable debug mode |

### Security Features

- **Prepared Statements**: All database operations use prepared statements to prevent SQL injection
- **Parameter Binding**: All user inputs are properly parameterized using PostgreSQL placeholders
- **Parameter Ordering Security**: Parameters are automatically sorted numerically to ensure correct binding order, preventing injection vulnerabilities from parameter misordering
- **RETURNING Clause Handling**: Write operations automatically detect RETURNING clauses and use appropriate parameterized execution methods
- **SQL Security Validation**: Additional validation layer for dangerous SQL keywords and patterns
- **Input Sanitization**: Schema and table names are validated and sanitized
- **Operation Type Validation**: Read/write operations are strictly separated and validated

## License

MIT License
