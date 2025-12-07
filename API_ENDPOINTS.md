# FlowDock API Endpoints Reference

## Overview

FlowDock uses a Clean Architecture with separate services behind a Traefik reverse proxy. All API endpoints are routed through the Traefik gateway at `http://localhost` (or your domain in production).

---

## Architecture

### URL Routing (via Traefik)

| Service | Path | Internal Port | External URL |
|---------|------|---------------|--------------|
| Frontend (React) | `/` | 5173 | `http://localhost/` |
| Auth Service | `/auth` | 8000 | `http://localhost/auth/...` |
| Media Service | `/media` | 8000 | `http://localhost/media/...` |
| Prometheus | `/prometheus` | 9090 | `http://localhost:9090` |

### Internal Direct Access (for development without Traefik)

- Auth Service: `http://localhost:8000/auth/...`
- Media Service: `http://localhost:8001/...` (different port)

---

## Authentication Endpoints

### Base URL
```
http://localhost/auth
```

### 1. User Registration
```
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "full_name": "John Doe",
  "password": "SecurePassword123!"
}

Response (201 Created):
{
  "detail": "verification code sent"
}
```

### 2. Verify Email with OTP
```
POST /auth/verify-email
Content-Type: application/json

{
  "email": "user@example.com",
  "token": "123456"  # 6-digit code sent to email
}

Response (200 OK):
{
  "detail": "email verified"
}
```

### 3. User Login
```
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "totp_code": null  # Optional: 6-digit 2FA code if enabled
}

Response (200 OK):
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": "uuid-here",
  "totp_required": false
}

Response if 2FA required (200 OK):
{
  "access_token": "",
  "token_type": "bearer",
  "user_id": "uuid-here",
  "totp_required": true
}
```

### 4. Token Refresh
```
POST /auth/refresh
Cookie: refresh_token=<HttpOnly cookie>
Content-Type: application/json

{}  # No body needed, refresh token is in HttpOnly cookie

Response (200 OK):
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_id": "uuid-here",
  "totp_required": false
}
```

### 5. User Logout
```
POST /auth/logout
Content-Type: application/json

{}

Response (200 OK):
{
  "detail": "logged out"
}
```

---

## Two-Factor Authentication (2FA) Endpoints

### 1. Setup TOTP (QR Code Generation)
```
POST /auth/totp/setup
Content-Type: application/json

{
  "email": "user@example.com"
}

Response (200 OK):
{
  "totp_secret": "JBSWY3DPEBLW64TMMQ======",  # Shared secret for authenticator app
  "totp_uri": "otpauth://totp/FlowDock:user@example.com?secret=JBSWY3..."  # QR code URI
}
```

**Usage in Frontend:**
```javascript
// Generate QR code from totp_uri
<QRCodeSVG value={response.totp_uri} />

// Show manual entry option
// User scans with Google Authenticator, Authy, etc.
```

### 2. Verify TOTP Code (Enable 2FA)
```
POST /auth/totp/verify
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456",  # 6-digit code from authenticator app
  "totp_secret": "JBSWY3DPEBLW64TMMQ======"  # From setup (required for initial setup)
}

Response (200 OK):
{
  "detail": "2FA enabled successfully",
  "recovery_codes": [
    "REC-001",
    "REC-002",
    ...
  ]
}
```

**Alternative: Login with 2FA (no totp_secret)**
```
POST /auth/totp/verify
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456"  # No totp_secret = use stored secret from DB
}

Response (200 OK):
{
  "detail": "TOTP verified successfully"
}
```

---

## Password Recovery Endpoints

### 1. Request Password Reset
```
POST /auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}

Response (200 OK):
{
  "detail": "If email exists, recovery instructions sent"
}
```

### 2. Verify Reset Token
```
POST /auth/verify-reset-token
Content-Type: application/json

{
  "email": "user@example.com",
  "token": "reset-token-from-email"
}

Response (200 OK):
{
  "detail": "Token is valid"
}
```

### 3. Reset Password
```
POST /auth/reset-password
Content-Type: application/json

{
  "email": "user@example.com",
  "token": "reset-token-from-email",
  "new_password": "NewSecurePassword456!"
}

Response (200 OK):
{
  "detail": "Password reset successful"
}
```

---

## OAuth/Social Login Endpoints

### 1. Initiate Google OAuth Login
```
GET /auth/oauth/google/login

Redirects to Google login page
```

### 2. Google OAuth Callback (Handled Internally)
```
GET /auth/oauth/google/callback?code=...&state=...

Processes OAuth callback and redirects to:
http://localhost/#/dashboard (on success)
http://localhost/#/login?error=... (on failure)
```

---

## User Profile Endpoints

### 1. Get Current User Info
```
GET /api/users/{user_id}
Authorization: Bearer <access_token>

Response (200 OK):
{
  "id": "uuid-here",
  "email": "user@example.com",
  "full_name": "John Doe",
  "verified": true,
  "twofa_enabled": true,
  "storage_used": 1048576,
  "storage_limit": 10737418240,
  "created_at": "2025-12-07T12:00:00Z"
}
```

### 2. Get User by Email
```
GET /api/users/by-email/{email}
Authorization: Bearer <access_token>

Response (200 OK):
{
  "id": "uuid-here",
  "email": "user@example.com",
  "full_name": "John Doe",
  "verified": true,
  "twofa_enabled": true,
  "storage_used": 1048576,
  "storage_limit": 10737418240,
  "created_at": "2025-12-07T12:00:00Z"
}
```

### 3. Update User Profile
```
PATCH /api/users/{user_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "full_name": "Jane Doe",
  "phone_number": "+1234567890"
}

Response (200 OK):
{
  "id": "uuid-here",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "verified": true,
  "twofa_enabled": true
}
```

---

## Health & Status Endpoints

### 1. Service Health Check
```
GET /auth/health

Response (200 OK):
{
  "status": "ok"
}
```

### 2. Root Endpoint
```
GET /auth/

Response (200 OK):
{
  "message": "Auth service is running"
}
```

### 3. Prometheus Metrics (for monitoring)
```
GET /metrics

Returns Prometheus format metrics:
# HELP fastapi_requests_total Total requests
# TYPE fastapi_requests_total counter
fastapi_requests_total{method="POST",path_template="/auth/login",status="200"} 42.0
...
```

---

## Error Responses

### Standard Error Format
```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Login successful |
| 201 | Created | Account registered |
| 400 | Bad Request | Invalid email format |
| 401 | Unauthorized | Invalid password |
| 403 | Forbidden | Email not verified |
| 404 | Not Found | User not found |
| 422 | Unprocessable | Missing required fields |
| 500 | Server Error | Database connection failed |

---

## Authentication Headers

### Access Token Usage
```javascript
const headers = {
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
};

fetch('http://localhost/api/users/123', {
  method: 'GET',
  headers: headers
});
```

### Refresh Token (HttpOnly Cookie)
- Automatically sent with `credentials: 'include'`
- Frontend **cannot** access it directly (security feature)
- Browser automatically includes it in requests

```javascript
fetch('http://localhost/auth/refresh', {
  method: 'POST',
  credentials: 'include',  // Include HttpOnly cookies
  headers: { 'Content-Type': 'application/json' }
});
```

---

## Frontend Usage Examples

### Using the API Client (Recommended)
```javascript
import api from '@/services/api.js';

// Register
const response = await api.register('user@example.com', 'John', 'password');

// Login
const response = await api.login('user@example.com', 'password', '123456');
if (response.totp_required) {
  // Show 2FA prompt
}

// Setup 2FA
const qr = await api.setupTOTP('user@example.com');
// Display QR code to user

// Verify 2FA
const recovery = await api.verifyTOTP('user@example.com', '123456', secret);
// Show recovery codes to user
```

### Direct Fetch Calls
```javascript
// Login directly
const response = await fetch('http://localhost/auth/login', {
  method: 'POST',
  credentials: 'include',  // Important for refresh token cookie
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password'
  })
});

const data = await response.json();
localStorage.setItem('access_token', data.access_token);
```

---

## Environment Variables

### Frontend (.env)
```bash
VITE_AUTH_API_URL=/auth          # Via Traefik (Docker)
VITE_MEDIA_API_URL=/media        # Via Traefik (Docker)
```

### Auth Service (.env)
```bash
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=FlowDock
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
REDIS_HOST=redis
REDIS_PORT=6379
ALLOWED_ORIGINS=http://localhost:5173,http://localhost
LOG_LEVEL=INFO
```

---

## Rate Limiting & Throttling

- Email verification: 3 attempts per email per day
- Login attempts: 5 failed attempts = 15 min lockout
- Password reset: 1 per email per hour
- TOTP setup: No limit (but requires verified email)

---

## Monitoring & Observability

### Prometheus Metrics
- `fastapi_requests_total` - Total requests by endpoint
- `fastapi_request_duration_seconds` - Request latency
- `fastapi_requests_in_progress` - Concurrent requests

### Access Prometheus Dashboard
```
http://localhost:9090
```

### Sample Queries
```
# Requests per second to login endpoint
rate(fastapi_requests_total{path_template="/auth/login"}[1m])

# 99th percentile latency
histogram_quantile(0.99, fastapi_request_duration_seconds)

# Error rate
rate(fastapi_requests_total{status=~"5.."}[1m])
```

---

## Important Security Notes

1. **Never send passwords in URLs** - Always use POST with JSON body
2. **Refresh tokens are HttpOnly** - Cannot be accessed by JavaScript
3. **Access tokens expire** - Use refresh endpoint to get new one
4. **CORS is configured** - Only allowed origins can make requests
5. **Passwords hashed with Argon2** - Industry standard
6. **2FA recovery codes** - Save immediately, cannot be recovered later
7. **Sessions table tracks** - Force logout, device management, suspicious activity

