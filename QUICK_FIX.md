# Quick Fix for Services Not Working

## The Problem
Multiple services were failing due to:
1. Traefik depending on auth_service being healthy to start
2. Prometheus having complex external URL settings causing issues
3. Missing healthchecks for some services
4. Network dependency issues

## The Solution
All issues have been fixed in docker-compose.yml:
- ✅ Removed problematic dependency constraints
- ✅ Simplified Prometheus configuration
- ✅ Added missing healthchecks
- ✅ Fixed network configurations

## To Apply Fix and Restart

### Option 1: Quick Restart (Recommended)
```bash
cd /home/xof/Desktop/FlowDock
docker-compose restart
```

### Option 2: Full Restart (Cleaner)
```bash
cd /home/xof/Desktop/FlowDock
docker-compose down
docker-compose up -d
```

### Option 3: Full Rebuild (If issues persist)
```bash
cd /home/xof/Desktop/FlowDock
docker-compose down
docker-compose up -d --build
```

## Wait for Services to Start
Services take 30-60 seconds to fully initialize. Monitor with:
```bash
docker-compose logs -f
```

Look for these indicators of success:
- `auth_service: startup complete`
- `prometheus: Server is ready to receive web requests`
- `grafana: HTTP Server Listen` 
- `pgadmin: gunicorn: master`
- `gateway: Traefik is running`

## Test Services

### Direct Port Access (Most Reliable)
```bash
# Auth Service
curl http://localhost:8000/health

# Prometheus
curl http://localhost:9090/-/healthy

# Grafana
curl http://localhost:3000/api/health

# PgAdmin
curl http://localhost:5050

# Traefik
curl http://localhost:8080/dashboard/
```

### Path-Based Access (Via Traefik)
```bash
# Auth
curl http://localhost/auth/health

# Prometheus
curl http://localhost/prometheus

# Grafana
curl http://localhost/grafana

# PgAdmin
curl http://localhost/pgadmin
```

## If Services Still Don't Work

### Check which services are running
```bash
docker-compose ps
```

### View logs for specific service
```bash
docker-compose logs auth_service
docker-compose logs prometheus
docker-compose logs grafana
docker-compose logs pgadmin
docker-compose logs flowdock_gateway
```

### Force stop and clean restart
```bash
docker-compose down -v
docker-compose up -d --build
```

## Accessing Services

| Service | Direct Port | Via Traefik |
|---------|------------|-------------|
| Frontend | http://localhost | http://localhost/ |
| Auth API | http://localhost:8000 | http://localhost/auth |
| Prometheus | http://localhost:9090 | http://localhost/prometheus |
| Grafana | http://localhost:3000 | http://localhost/grafana |
| PgAdmin | http://localhost:5050 | http://localhost/pgadmin |
| Traefik | - | http://localhost:8080 |

## PostgreSQL Connection (For PgAdmin)
- Hostname: `postgres` (internal Docker name)
- Port: 5432
- Database: FlowDock
- User: postgres
- Password: postgres
