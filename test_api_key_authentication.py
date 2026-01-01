#!/usr/bin/env python
"""
Test script for API Key authentication on /logs/internal endpoint.

This script validates that:
1. Requests without API key are rejected (401)
2. Requests with wrong API key are rejected (401)
3. Requests with correct API key are accepted (201 or 500 for FK violation)
"""

import httpx
import json
import sys

# Configuration
AUTH_SERVICE_URL = "http://localhost:8000"
INTERNAL_API_KEY = "internal-api-key-change-in-production"
TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"


def test_without_api_key():
    """Test that request without API key is rejected"""
    print("\n[Test 1] Request WITHOUT API key...")
    
    payload = {
        "user_id": TEST_USER_ID,
        "action": "TEST_ACTION",
        "details": {},
        "ip_address": "127.0.0.1"
    }
    
    try:
        response = httpx.post(
            f"{AUTH_SERVICE_URL}/logs/internal",
            json=payload,
            timeout=5
        )
        
        if response.status_code == 422:
            print("✅ PASS: Got 422 (header required)")
            return True
        else:
            print(f"❌ FAIL: Got {response.status_code}, expected 422")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_with_wrong_api_key():
    """Test that request with wrong API key is rejected"""
    print("\n[Test 2] Request WITH WRONG API key...")
    
    payload = {
        "user_id": TEST_USER_ID,
        "action": "TEST_ACTION",
        "details": {},
        "ip_address": "127.0.0.1"
    }
    
    try:
        response = httpx.post(
            f"{AUTH_SERVICE_URL}/logs/internal",
            json=payload,
            headers={"X-API-Key": "wrong-api-key"},
            timeout=5
        )
        
        if response.status_code == 401:
            print("✅ PASS: Got 401 (invalid API key)")
            return True
        else:
            print(f"❌ FAIL: Got {response.status_code}, expected 401")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def test_with_correct_api_key():
    """Test that request with correct API key is accepted"""
    print("\n[Test 3] Request WITH CORRECT API key...")
    
    payload = {
        "user_id": TEST_USER_ID,
        "action": "TEST_ACTION",
        "details": {"test": "data"},
        "ip_address": "127.0.0.1"
    }
    
    try:
        response = httpx.post(
            f"{AUTH_SERVICE_URL}/logs/internal",
            json=payload,
            headers={"X-API-Key": INTERNAL_API_KEY},
            timeout=5
        )
        
        if response.status_code == 201:
            print("✅ PASS: Got 201 (API key accepted, user exists)")
            print(f"   Response: {response.json()}")
            return True
        elif response.status_code == 500:
            # Expected if user doesn't exist in database (ForeignKeyViolation)
            if "ForeignKeyViolation" in response.text or "foreign key" in response.text:
                print("✅ PASS: Got 500 (API key accepted, but user doesn't exist in DB)")
                print("   This is expected - the endpoint was reached successfully!")
                return True
            else:
                print(f"❌ FAIL: Got 500 with unexpected error")
                print(f"   Response: {response.text[:200]}")
                return False
        else:
            print(f"❌ FAIL: Got {response.status_code}, expected 201 or 500")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ FAIL: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("API Key Authentication Test Suite")
    print("=" * 70)
    print(f"Auth Service URL: {AUTH_SERVICE_URL}")
    print(f"Expected API Key: {INTERNAL_API_KEY}")
    
    results = []
    
    try:
        # Run all tests
        results.append(("Without API Key", test_without_api_key()))
        results.append(("With Wrong API Key", test_with_wrong_api_key()))
        results.append(("With Correct API Key", test_with_correct_api_key()))
        
        # Summary
        print("\n" + "=" * 70)
        print("Test Summary")
        print("=" * 70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nResult: {passed}/{total} tests passed")
        print("=" * 70 + "\n")
        
        return passed == total
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
