#!/usr/bin/env python3
"""
Simple script to run database connection tests
"""
import asyncio
import sys
from app.core.database import test_connection, get_pool_stats, close_pool
from app.core.config import settings

async def main():
    """Run connection tests"""
    print("🔍 Testing Database Connection to PgBouncer...")
    print(f"   Host: {settings.PGBOUNCER_HOST}")
    print(f"   Port: {settings.PGBOUNCER_PORT}")
    print(f"   Database: {settings.DATABASE_NAME}")
    print(f"   User: {settings.DATABASE_USER}")
    print()
    
    try:
        # Test connection
        print("📡 Testing connection...")
        result = await test_connection()
        
        print("✅ Connection successful!")
        print(f"   Status: {result['status']}")
        print(f"   Database: {result['database']}")
        print(f"   User: {result['user']}")
        print(f"   Version: {result['version']}")
        print(f"   Write test: {result['write_test']}")
        
        # Get pool stats
        print("\n📊 Connection pool stats:")
        stats = await get_pool_stats()
        print(f"   Pool created: {stats['pool_created']}")
        print(f"   Total connections: {stats['total_connections']}")
        print(f"   Active connections: {stats['active_connections']}")
        print(f"   Idle connections: {stats['idle_connections']}")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    finally:
        await close_pool()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 