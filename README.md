# Database REST Service

A simple FastAPI service that connects to a PgBouncer instance and provides connection validation endpoints.

## Features

- **PgBouncer Connection**: Connects to PgBouncer with configurable host and port
- **Environment-based Configuration**: Uses `.env` files and environment variables
- **Connection Pooling**: Uses asyncpg connection pool for efficient database connections
- **Health Checks**: Endpoints to validate database connectivity
- **Comprehensive Tests**: Tests that validate the connection and API endpoints

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
Returns basic service information.

### Admin Endpoints

All admin endpoints are grouped under `/admin` and include detailed descriptions and comments.

#### Health Check
```bash
GET /admin/health
```
Returns service health status including database connection status.

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

### Run Connection Tests
```bash
# Quick connection test
python run_tests.py

# Full pytest suite
pytest tests/ -v

# In Docker container
docker-compose exec database-service python run_tests.py
```

### Test Output Example
```
🔍 Testing Database Connection to PgBouncer...
   Host: 192.168.68.129
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
│   ├── main.py              # FastAPI application
│   └── core/
│       ├── config.py        # Configuration settings
│       └── database.py      # Database connection utilities
├── tests/
│   └── test_database.py     # Connection and API tests
├── requirements.txt          # Python dependencies
├── run_tests.py             # Quick connection test script
└── README.md               # This file
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
| `PGBOUNCER_HOST` | `192.168.68.129` | PgBouncer host address |
| `PGBOUNCER_PORT` | `6432` | PgBouncer port |
| `DATABASE_NAME` | `postgres` | Database name |
| `DATABASE_USER` | `postgres` | Database username |
| `DATABASE_PASSWORD` | `postgres` | Database password |
| `MIN_CONNECTIONS` | `1` | Minimum connections in pool |
| `MAX_CONNECTIONS` | `10` | Maximum connections in pool |
| `DEBUG` | `True` | Enable debug mode |

## License

MIT License
