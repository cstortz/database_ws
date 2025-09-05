import pytest
import asyncio
import json
from httpx import AsyncClient
from app.main import app
from app.core.database import test_connection, get_pool_stats, close_pool
from app.core.config import settings

@pytest.fixture
async def client():
    """Async client for testing"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(autouse=True)
async def cleanup():
    """Cleanup after tests"""
    yield
    await close_pool()

class TestDatabaseConnection:
    """Test database connection functionality"""
    
    @pytest.mark.asyncio
    async def test_database_connection(self):
        """Test that we can connect to the database"""
        try:
            result = await test_connection()
            
            # Verify connection details
            assert result["status"] == "connected"
            assert result["host"] == settings.PGBOUNCER_HOST
            assert result["port"] == settings.PGBOUNCER_PORT
            assert result["database"] is not None
            assert result["user"] is not None
            assert result["version"] is not None
            assert result["write_test"] == "passed"
            
            print(f"✅ Database connection successful")
            print(f"   Host: {result['host']}:{result['port']}")
            print(f"   Database: {result['database']}")
            print(f"   User: {result['user']}")
            print(f"   Version: {result['version']}")
            
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")
    
    @pytest.mark.asyncio
    async def test_pool_stats(self):
        """Test connection pool statistics"""
        # First, establish a connection
        await test_connection()
        
        # Get pool stats
        stats = await get_pool_stats()
        
        # Verify pool is created
        assert stats["pool_created"] == True
        assert stats["total_connections"] > 0
        assert stats["total_connections"] <= settings.MAX_CONNECTIONS
        
        print(f"✅ Connection pool stats:")
        print(f"   Total connections: {stats['total_connections']}")
        print(f"   Active connections: {stats['active_connections']}")
        print(f"   Idle connections: {stats['idle_connections']}")

class TestAPIEndpoints:
    """Test API endpoints"""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = await client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Database Service API"
        assert data["version"] == "2.0.0"
        assert "features" in data
        assert "admin" in data["features"]
        assert "crud" in data["features"]
        assert "raw_sql" in data["features"]
        assert "prepared_sql" in data["features"]
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "2.0.0"
        assert "detailed_health" in data
    
    @pytest.mark.asyncio
    async def test_admin_health_endpoint(self, client):
        """Test admin health check endpoint"""
        response = await client.get("/admin/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["pgbouncer_host"] == settings.PGBOUNCER_HOST
        assert data["pgbouncer_port"] == settings.PGBOUNCER_PORT
    
    @pytest.mark.asyncio
    async def test_admin_connection_test_endpoint(self, client):
        """Test admin connection test endpoint"""
        response = await client.get("/admin/test-connection")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "details" in data
        
        details = data["details"]
        assert details["status"] == "connected"
        assert details["write_test"] == "passed"
    
    @pytest.mark.asyncio
    async def test_admin_db_info_endpoint(self, client):
        """Test admin database info endpoint"""
        response = await client.get("/admin/db-info")
        assert response.status_code == 200
        
        data = response.json()
        assert "version" in data
        assert "database" in data
        assert "user" in data
        assert data["host"] == settings.PGBOUNCER_HOST
        assert data["port"] == settings.PGBOUNCER_PORT
    
    @pytest.mark.asyncio
    async def test_admin_databases_endpoint(self, client):
        """Test admin databases endpoint"""
        response = await client.get("/admin/databases")
        assert response.status_code == 200
        
        data = response.json()
        assert "databases" in data
        assert isinstance(data["databases"], list)
    
    @pytest.mark.asyncio
    async def test_admin_schemas_endpoint(self, client):
        """Test admin schemas endpoint"""
        response = await client.get("/admin/schemas")
        assert response.status_code == 200
        
        data = response.json()
        assert "schemas" in data
        assert isinstance(data["schemas"], list)
    
    @pytest.mark.asyncio
    async def test_admin_tables_endpoint(self, client):
        """Test admin tables endpoint"""
        response = await client.get("/admin/tables")
        assert response.status_code == 200
        
        data = response.json()
        assert "tables" in data
        assert isinstance(data["tables"], list)
    
    @pytest.mark.asyncio
    async def test_admin_tables_by_schema_endpoint(self, client):
        """Test admin tables by schema endpoint"""
        response = await client.get("/admin/tables/public")
        assert response.status_code == 200
        
        data = response.json()
        assert "tables" in data
        assert isinstance(data["tables"], list)

class TestCRUDOperations:
    """Test CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_crud_read_multiple_records(self, client):
        """Test reading multiple records"""
        response = await client.get("/crud/public/documents?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "records" in data
        assert "count" in data
        assert "total_count" in data
        assert isinstance(data["records"], list)
    
    @pytest.mark.asyncio
    async def test_crud_read_single_record(self, client):
        """Test reading single record"""
        # First get a record ID
        response = await client.get("/crud/public/documents?limit=1")
        assert response.status_code == 200
        
        data = response.json()
        if data["records"]:
            record_id = data["records"][0]["id"]
            
            # Now read the single record
            response = await client.get(f"/crud/public/documents/{record_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert "id" in data
            assert "data" in data
    
    @pytest.mark.asyncio
    async def test_crud_create_record(self, client):
        """Test creating a record"""
        create_data = {
            "data": {
                "content": "Test document from pytest"
            }
        }
        
        response = await client.post("/crud/public/documents", json=create_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "data" in data
        assert data["data"]["content"] == "Test document from pytest"
    
    @pytest.mark.asyncio
    async def test_crud_update_record(self, client):
        """Test updating a record"""
        # First create a record
        create_data = {
            "data": {
                "content": "Original content"
            }
        }
        
        response = await client.post("/crud/public/documents", json=create_data)
        assert response.status_code == 200
        
        record_id = response.json()["id"]
        
        # Now update it
        update_data = {
            "data": {
                "content": "Updated content from pytest"
            }
        }
        
        response = await client.put(f"/crud/public/documents/{record_id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["data"]["content"] == "Updated content from pytest"
    
    @pytest.mark.asyncio
    async def test_crud_delete_record(self, client):
        """Test deleting a record"""
        # First create a record
        create_data = {
            "data": {
                "content": "Record to be deleted"
            }
        }
        
        response = await client.post("/crud/public/documents", json=create_data)
        assert response.status_code == 200
        
        record_id = response.json()["id"]
        
        # Now delete it
        response = await client.delete(f"/crud/public/documents/{record_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "deleted_record" in data
    
    @pytest.mark.asyncio
    async def test_crud_upsert_record(self, client):
        """Test upserting a record"""
        upsert_data = {
            "data": {
                "content": "Upserted record from pytest"
            }
        }
        
        response = await client.patch("/crud/public/documents/9999", json=upsert_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "operation" in data
        assert "record" in data

class TestRawSQLOperations:
    """Test raw SQL operations"""
    
    @pytest.mark.asyncio
    async def test_raw_sql_read(self, client):
        """Test raw SQL read operation"""
        sql_data = {
            "sql": "SELECT COUNT(*) as total FROM documents",
            "parameters": {}
        }
        
        response = await client.post("/raw/sql", json=sql_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert isinstance(data["data"], list)
    
    @pytest.mark.asyncio
    async def test_raw_sql_write(self, client):
        """Test raw SQL write operation"""
        sql_data = {
            "sql": "CREATE TEMP TABLE IF NOT EXISTS test_table (id TEXT, name TEXT)",
            "parameters": {}
        }
        
        response = await client.post("/raw/sql/write", json=sql_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data

class TestPreparedSQLOperations:
    """Test prepared SQL operations"""
    
    @pytest.mark.asyncio
    async def test_prepared_sql_select(self, client):
        """Test prepared SQL select operation"""
        sql_data = {
            "sql": "SELECT COUNT(*) as total FROM documents",
            "parameters": {},
            "operation_type": "read"
        }
        
        response = await client.post("/crud/prepared/select", json=sql_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "data" in data
    
    @pytest.mark.asyncio
    async def test_prepared_sql_validate(self, client):
        """Test prepared SQL validation"""
        sql_data = {
            "sql": "SELECT * FROM documents WHERE id = $1",
            "parameters": {"1": "1"},
            "operation_type": "read"
        }
        
        response = await client.post("/crud/prepared/validate", json=sql_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "valid" in data
        assert data["valid"] == True
    
    @pytest.mark.asyncio
    async def test_prepared_sql_statements_list(self, client):
        """Test listing prepared statements"""
        response = await client.get("/crud/prepared/statements")
        assert response.status_code == 200
        
        data = response.json()
        assert "statements" in data
        assert isinstance(data["statements"], list)

class TestConfiguration:
    """Test configuration settings"""
    
    def test_pgbouncer_config(self):
        """Test PgBouncer configuration"""
        # Test that environment variables are loaded correctly
        assert settings.PGBOUNCER_HOST == "db01.int.stortz.tech"
        assert settings.PGBOUNCER_PORT == 6432
        assert settings.DATABASE_NAME == "postgres"
        assert settings.DATABASE_USER == "postgres"
        assert settings.DATABASE_PASSWORD == "postgres"
        
        # Test database URL construction
        expected_url = f"postgresql://postgres:postgres@db01.int.stortz.tech:6432/postgres"
        assert settings.DATABASE_URL == expected_url
        
        print(f"✅ Configuration validated:")
        print(f"   PgBouncer: {settings.PGBOUNCER_HOST}:{settings.PGBOUNCER_PORT}")
        print(f"   Database: {settings.DATABASE_NAME}")
        print(f"   User: {settings.DATABASE_USER}")

if __name__ == "__main__":
    # Run tests manually
    pytest.main([__file__, "-v"]) 