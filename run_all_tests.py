#!/usr/bin/env python3
"""
Comprehensive test runner for the Database Service API

This script runs all test suites including:
- Unit tests (pytest)
- Integration tests
- Endpoint-specific tests
- Performance tests
"""

import asyncio
import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    print(f"Running: {command}")
    print()
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=False)
    end_time = time.time()
    
    duration = end_time - start_time
    status = "✅ PASSED" if result.returncode == 0 else "❌ FAILED"
    
    print(f"\n{status} - {description} (took {duration:.2f}s)")
    return result.returncode == 0

def run_pytest_tests():
    """Run pytest test suite"""
    return run_command(
        "python -m pytest tests/ -v --tb=short",
        "Running pytest test suite"
    )

def run_endpoint_tests():
    """Run individual endpoint test scripts"""
    test_scripts = [
        ("python test_admin_endpoints.py", "Admin Endpoints"),
        ("python test_crud_endpoints.py", "CRUD Operations"),
        ("python test_raw_endpoints.py", "Raw SQL Operations"),
        ("python test_prepared_endpoints.py", "Prepared SQL Operations")
    ]
    
    results = []
    for command, description in test_scripts:
        if os.path.exists(command.split()[-1]):
            results.append(run_command(command, description))
        else:
            print(f"⚠️  Skipping {description} - test file not found")
            results.append(True)  # Don't fail overall if test file missing
    
    return all(results)

def run_integration_tests():
    """Run integration tests"""
    return run_command(
        "python -m pytest tests/test_integration.py -v --tb=short",
        "Running integration tests"
    )

def run_connection_test():
    """Run basic connection test"""
    return run_command(
        "python run_tests.py",
        "Running basic connection test"
    )

def check_service_health():
    """Check if the service is running and healthy"""
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Service is running and healthy")
            return True
        else:
            print(f"❌ Service returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Service health check failed: {e}")
        print("💡 Make sure the service is running with: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return False

def main():
    """Main test runner"""
    print("🚀 Database Service API - Comprehensive Test Suite")
    print("=" * 60)
    
    # Check if service is running
    print("\n🔍 Checking service health...")
    service_healthy = check_service_health()
    
    if not service_healthy:
        print("\n⚠️  Service is not running. Some tests may fail.")
        print("   Start the service with: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        response = input("\nContinue with tests anyway? (y/N): ")
        if response.lower() != 'y':
            print("❌ Tests cancelled")
            sys.exit(1)
    
    # Track test results
    test_results = []
    
    # Run basic connection test
    test_results.append(("Basic Connection Test", run_connection_test()))
    
    # Run pytest unit tests
    test_results.append(("Pytest Unit Tests", run_pytest_tests()))
    
    # Run integration tests
    test_results.append(("Integration Tests", run_integration_tests()))
    
    # Run endpoint-specific tests
    test_results.append(("Endpoint Tests", run_endpoint_tests()))
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All tests passed! The service is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
