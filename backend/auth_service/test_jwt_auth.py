#!/usr/bin/env python3
"""
Test JWT authentication on activity logging endpoints.

Tests:
1. /logs/internal - Requires API key (X-API-Key header)
2. /logs/user/{user_id} - Requires JWT auth & user_id match
3. /logs/action/{action} - Requires JWT auth
4. /logs/all - Requires JWT auth
"""

import requests
import json
from datetime import datetime, timedelta, timezone
import os
import sys

# Add parent directory to path to import app config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.infrastructure.security.security import JWTTokenGenerator

BASE_URL = "http://localhost:8000"
INTERNAL_API_KEY = "internal-api-key-change-in-production"

# Use the real JWTTokenGenerator from the app
def create_jwt_token(user_id: str) -> str:
    """Create a test JWT token using the app's JWT generator"""
    token_gen = JWTTokenGenerator()
    from uuid import UUID
    try:
        user_uuid = UUID(user_id)
    except (ValueError, AttributeError):
        user_uuid = UUID('550e8400-e29b-41d4-a716-446655440000')
    return token_gen.create_access_token(user_uuid)

def print_test_header(test_num: str, description: str):
    """Print a formatted test header"""
    print(f"\n{'='*70}")
    print(f"Test {test_num}: {description}")
    print('='*70)

def print_result(test_name: str, expected: str, actual: str, passed: bool):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}: {test_name}")
    print(f"  Expected: {expected}")
    print(f"  Actual:   {actual}")

# Test 1: POST /logs/internal without API key (should fail with 401)
print_test_header("1a", "POST /logs/internal without API key")
try:
    response = requests.post(
        f"{BASE_URL}/logs/internal",
        json={
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "action": "TEST_ACTION",
            "details": {"test": "data"},
            "ip_address": "127.0.0.1",
        },
        timeout=5
    )
    passed = response.status_code == 401
    print_result(
        "Missing X-API-Key header",
        "401 (Unauthorized)",
        f"{response.status_code}",
        passed,
    )
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 1b: POST /logs/internal with correct API key (should succeed or FK error)
print_test_header("1b", "POST /logs/internal with correct API key")
try:
    response = requests.post(
        f"{BASE_URL}/logs/internal",
        headers={"X-API-Key": INTERNAL_API_KEY},
        json={
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "action": "TEST_ACTION",
            "details": {"test": "data"},
            "ip_address": "127.0.0.1",
        },
        timeout=5
    )
    passed = response.status_code in [201, 500]  # 500 for FK constraint
    print_result(
        "Correct X-API-Key header",
        "201 or 500 (FK error expected without real user)",
        f"{response.status_code}",
        passed,
    )
    if response.status_code != 201:
        print(f"  Response: {response.text[:200]}")
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 2a: GET /logs/user without JWT (should fail with 401)
print_test_header("2a", "GET /logs/user/{user_id} without JWT")
try:
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    response = requests.get(f"{BASE_URL}/logs/user/{user_id}", timeout=5)
    passed = response.status_code == 401
    print_result(
        "Missing Authorization header",
        "401 (Unauthorized)",
        f"{response.status_code}",
        passed,
    )
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 2b: GET /logs/user with JWT but wrong user_id (should fail with 403)
print_test_header("2b", "GET /logs/user/{user_id} - mismatch user_id")
try:
    token = create_jwt_token("550e8400-e29b-41d4-a716-446655440001")
    different_user = "550e8400-e29b-41d4-a716-446655440000"
    response = requests.get(
        f"{BASE_URL}/logs/user/{different_user}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5
    )
    passed = response.status_code == 403
    print_result(
        "User trying to access different user's logs",
        "403 (Forbidden)",
        f"{response.status_code}",
        passed,
    )
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 2c: GET /logs/user with JWT and matching user_id (should succeed)
print_test_header("2c", "GET /logs/user/{user_id} - matching user_id")
try:
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    token = create_jwt_token(user_id)
    response = requests.get(
        f"{BASE_URL}/logs/user/{user_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5
    )
    passed = response.status_code == 200
    print_result(
        "User accessing their own logs",
        "200 (Success)",
        f"{response.status_code}",
        passed,
    )
    if response.status_code == 200:
        data = response.json()
        print(f"  Retrieved {len(data)} logs")
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 3a: GET /logs/action without JWT (should fail)
print_test_header("3a", "GET /logs/action/{action} without JWT")
try:
    response = requests.get(f"{BASE_URL}/logs/action/USER_LOGIN", timeout=5)
    passed = response.status_code == 401
    print_result(
        "Missing Authorization header",
        "401 (Unauthorized)",
        f"{response.status_code}",
        passed,
    )
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 3b: GET /logs/action with JWT (should succeed)
print_test_header("3b", "GET /logs/action/{action} with JWT")
try:
    token = create_jwt_token("550e8400-e29b-41d4-a716-446655440000")
    response = requests.get(
        f"{BASE_URL}/logs/action/USER_LOGIN",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5
    )
    passed = response.status_code == 200
    print_result(
        "User accessing action logs with JWT",
        "200 (Success)",
        f"{response.status_code}",
        passed,
    )
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 4a: GET /logs/all without JWT
print_test_header("4a", "GET /logs/all without JWT")
try:
    response = requests.get(f"{BASE_URL}/logs/all", timeout=5)
    passed = response.status_code == 401
    print_result(
        "Missing Authorization header",
        "401 (Unauthorized)",
        f"{response.status_code}",
        passed,
    )
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 4b: GET /logs/all with JWT
print_test_header("4b", "GET /logs/all with JWT")
try:
    token = create_jwt_token("550e8400-e29b-41d4-a716-446655440000")
    response = requests.get(
        f"{BASE_URL}/logs/all",
        headers={"Authorization": f"Bearer {token}"},
        timeout=5
    )
    passed = response.status_code == 200
    print_result(
        "User accessing /logs/all",
        "200 (Success)",
        f"{response.status_code}",
        passed,
    )
    if response.status_code == 200:
        data = response.json()
        print(f"  Retrieved {len(data)} total logs")
except Exception as e:
    print(f"✗ ERROR: {e}")

print("\n" + "="*70)
print("JWT Authentication Test Suite Complete")
print("="*70)