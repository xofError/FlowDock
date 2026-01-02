#!/usr/bin/env python3
"""
Troubleshooting Guide: JWT Authentication Test Failures

This script helps diagnose JWT authentication issues.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("JWT Authentication Diagnostic Report")
print("=" * 70)

# Check 1: Environment variables
print("\n1. Environment Variables Check:")
print("-" * 70)

required_vars = [
    "JWT_SECRET",
    "JWT_ALGORITHM", 
    "INTERNAL_API_KEY",
    "ACCESS_TOKEN_EXPIRE_MINUTES"
]

for var in required_vars:
    value = os.getenv(var, "NOT SET")
    if value == "NOT SET":
        print(f"  ✗ {var:<30} NOT SET")
    else:
        masked = value[:10] + "..." if len(str(value)) > 10 else value
        print(f"  ✓ {var:<30} {masked}")

# Check 2: Config loading
print("\n2. Configuration Loading Check:")
print("-" * 70)

try:
    from app.core.config import settings
    print(f"  ✓ Settings loaded successfully")
    print(f"    - secret_key set: {'Yes' if settings.secret_key else 'No'}")
    print(f"    - internal_api_key: {settings.internal_api_key[:10] + '...' if len(settings.internal_api_key) > 10 else settings.internal_api_key}")
except Exception as e:
    print(f"  ✗ Failed to load settings: {e}")

# Check 3: JWT functionality
print("\n3. JWT Functionality Check:")
print("-" * 70)

try:
    from app.infrastructure.security.security import JWTTokenGenerator
    from uuid import UUID
    
    gen = JWTTokenGenerator()
    test_uuid = UUID('550e8400-e29b-41d4-a716-446655440000')
    
    # Create a token
    token = gen.create_access_token(test_uuid)
    print(f"  ✓ Token created: {token[:50]}...")
    
    # Decode it
    decoded = gen.decode_access_token(token)
    if decoded:
        print(f"  ✓ Token decoded successfully")
        print(f"    - sub: {decoded.get('sub')}")
        print(f"    - exp: {decoded.get('exp')}")
        print(f"    - type: {decoded.get('type')}")
    else:
        print(f"  ✗ Failed to decode token")
except Exception as e:
    print(f"  ✗ JWT test failed: {e}")
    import traceback
    traceback.print_exc()

# Check 4: Dependencies
print("\n4. Dependency Injection Check:")
print("-" * 70)

try:
    from app.presentation.dependencies import (
        verify_internal_service,
        verify_jwt_token,
        get_current_user_id
    )
    print(f"  ✓ verify_internal_service imported")
    print(f"  ✓ verify_jwt_token imported")
    print(f"  ✓ get_current_user_id imported")
except Exception as e:
    print(f"  ✗ Failed to import dependencies: {e}")

# Check 5: Router registration
print("\n5. Router Registration Check:")
print("-" * 70)

try:
    from app.presentation.api import logs
    routes = logs.router.routes
    print(f"  ✓ Logs router imported")
    print(f"  ✓ Found {len(routes)} routes:")
    for route in routes:
        path = route.path if hasattr(route, 'path') else 'unknown'
        methods = route.methods if hasattr(route, 'methods') else set()
        print(f"    - {path} {methods}")
except Exception as e:
    print(f"  ✗ Failed to check router: {e}")

print("\n" + "=" * 70)
print("Diagnostic Complete")
print("=" * 70)

print("""
Next Steps if Tests Still Fail:

1. Ensure Auth Service is running:
   cd /home/xof/Desktop/FlowDock/backend/auth_service
   python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

2. Run the JWT test:
   cd /home/xof/Desktop/FlowDock
   uv run python backend/auth_service/test_jwt_auth.py

3. If you see 401 errors:
   - Check that the Auth Service is actually running (curl http://localhost:8000/health)
   - Verify JWT_SECRET is set in environment variables
   - Check that the test is using the same JWT_SECRET as the app

4. Debug individual requests:
   # Get a valid token
   python3 -c "
   import sys
   sys.path.insert(0, 'backend/auth_service')
   from app.infrastructure.security.security import JWTTokenGenerator
   from uuid import UUID
   gen = JWTTokenGenerator()
   token = gen.create_access_token(UUID('550e8400-e29b-41d4-a716-446655440000'))
   print('Token:', token)
   "
   
   # Test the endpoint directly
   curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/logs/user/550e8400-e29b-41d4-a716-446655440000
""")
