# Gateway Timeout Fix - Login Endpoint 504 Error

## Problem
The login endpoint was returning a 504 Gateway Timeout error. This was happening because:
1. **Auth service startup takes time** - Database initialization, Prometheus setup, etc.
2. **Traefik timeout too short** - Default timeouts weren't sufficient
3. **Healthcheck too strict** - Retries and timeout values were too aggressive

## Solution Implemented

### 1. Traefik Configuration
Added extended timeout configuration to handle slow service startup:
- Write timeout: 60 seconds (from default 15s)
- Read timeout: 60 seconds
- Idle timeout: 90 seconds

### 2. Auth Service Configuration
- Increased healthcheck start period to 30 seconds
- More lenient retries: 5 instead of 3
- Increased timeout tolerance to 10 seconds
- Added explicit scheme and service timeout to Traefik labels

### 3. All Services Enhanced
- Added/fixed healthchecks for PgAdmin, Prometheus, Grafana
- All have 15-second intervals with 10-second timeouts
- Proper path stripping middleware for sub-path access

## How to Apply the Fix

### Quick Restart
```bash
cd /home/xof/Desktop/FlowDock
docker-compose restart
```

### Or Full Down/Up (Recommended)
```bash
cd /home/xof/Desktop/FlowDock
docker-compose down
docker-compose up -d
```

### Monitor Startup
```bash
docker-compose logs -f auth_service
```

Wait for: `Auth Service startup complete`

## What to Expect

### Startup Time
- Initial startup: 30-60 seconds (auth_service initializes DB, test user, Prometheus)
- Healthcheck passes after 30+ seconds

### Testing
After startup, test these URLs:

**Direct Port** (fastest):
```bash
curl http://localhost:8000/health
```

**Via Traefik** (through path):
```bash
curl http://localhost/auth/health
```

**Login Request**:
```bash
curl -X POST http://localhost/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@pgadmin.com","password":"admin"}'
```

## If Issues Persist

### Check Service Status
```bash
docker-compose ps
```

All services should show `healthy` or `running`:
- ✅ postgres: healthy
- ✅ redis: healthy
- ✅ auth_service: healthy
- ✅ pgadmin: healthy
- ✅ prometheus: healthy
- ✅ grafana: healthy
- ✅ traefik: running

### Check Logs
```bash
# Auth service logs
docker-compose logs auth_service | tail -50

# Traefik logs (routing)
docker-compose logs flowdock_gateway | tail -50

# All logs
docker-compose logs
```

### If Auth Service is Failing
The most common issues:
1. **Database connection** - Check postgres is healthy
2. **Redis connection** - Check redis is healthy
3. **Network issues** - Services not on flowdock_public/flowdock_internal networks

### Force Clean Restart
```bash
# Stop everything
docker-compose down

# Remove old volumes (only if needed)
docker volume prune -f

# Rebuild and start fresh
docker-compose up -d --build
```

## Service Status Indicators

### Healthy Startup Sequence
1. PostgreSQL starts and healthcheck passes (20-30 seconds)
2. Redis starts and healthcheck passes (10-20 seconds)
3. Auth service starts, initializes DB, Prometheus metrics (30-60 seconds)
4. Traefik routes traffic to healthy services
5. Frontend, Prometheus, Grafana, PgAdmin start (10-20 seconds each)

### Total Expected Time
**2-3 minutes** from `docker-compose up` to all services being fully ready

## Accessing Services After Fix

| Service | Port Access | Traefik Path |
|---------|------------|-------------|
| Frontend | http://localhost | http://localhost/ |
| Auth API | http://localhost:8000 | http://localhost/auth |
| Login | POST localhost:8000/auth/login | POST localhost/auth/login |
| Prometheus | http://localhost:9090 | http://localhost/prometheus |
| Grafana | http://localhost:3000 | http://localhost/grafana |
| PgAdmin | http://localhost:5050 | http://localhost/pgadmin |
| Traefik Dashboard | - | http://localhost:8080 |

## Key Configuration Changes in docker-compose.yml

```yaml
# Traefik extended timeouts
traefik:
  command:
    - "--entrypoints.web.transport.respondingTimeouts.writeTimeout=60s"
    - "--entrypoints.web.transport.respondingTimeouts.readTimeout=60s"
    - "--serversTransport.respondingTimeouts.idleTimeout=90s"

# Auth service enhanced configuration
auth_service:
  healthcheck:
    start_period: 30s  # Wait 30s before checking health
    retries: 5        # Allow 5 failed checks
    timeout: 10s      # Give 10s per check
  labels:
    - "traefik.http.routers.auth.timeout=60s"
```

## Next Steps

1. Restart services with the fixed configuration
2. Wait 30-60 seconds for auth_service to fully initialize
3. Test login endpoint
4. If working, all other services should also be functional

## Still Having Issues?

If login still times out after 3+ minutes of waiting:
1. Check `docker-compose logs auth_service` for errors
2. Verify database connectivity: `docker exec flowdock_postgres pg_isready`
3. Verify Redis connectivity: `docker exec flowdock_redis redis-cli ping`
4. Share the last 50 lines of auth_service logs for further debugging
