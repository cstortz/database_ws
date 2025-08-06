import pytest
import asyncio
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
        assert data["version"] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = await client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["pgbouncer_host"] == settings.PGBOUNCER_HOST
        assert data["pgbouncer_port"] == settings.PGBOUNCER_PORT
    
    @pytest.mark.asyncio
    async def test_connection_test_endpoint(self, client):
        """Test connection test endpoint"""
        response = await client.get("/test-connection")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        assert "details" in data
        
        details = data["details"]
        assert details["status"] == "connected"
        assert details["write_test"] == "passed"
    
    @pytest.mark.asyncio
    async def test_db_info_endpoint(self, client):
        """Test database info endpoint"""
        response = await client.get("/db-info")
        assert response.status_code == 200
        
        data = response.json()
        assert "version" in data
        assert "database" in data
        assert "user" in data
        assert data["host"] == settings.PGBOUNCER_HOST
        assert data["port"] == settings.PGBOUNCER_PORT

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