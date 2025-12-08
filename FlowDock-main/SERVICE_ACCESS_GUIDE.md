# FlowDock Service Access Guide

## Quick Access URLs

All services are accessible through your localhost without needing to remember port numbers.

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend** | `http://localhost/` | - |
| **PgAdmin** | `http://localhost/pgadmin` | admin@pgadmin.com / admin |
| **Grafana** | `http://localhost/grafana` | admin / admin |
| **Prometheus** | `http://localhost/prometheus` | - |
| **Traefik Dashboard** | `http://localhost:8080` | - |

---

## Detailed Setup Instructions

### 1. Access PgAdmin and Connect to PostgreSQL

**URL**: `http://localhost/pgadmin`

**Login Credentials**:
- Email: `admin@pgadmin.com`
- Password: `admin`

**Connect to PostgreSQL**:
1. Right-click "Servers" in left sidebar
2. Select "Register" → "Server..."
3. **Connection Details**:
   - Hostname: `postgres` (use this - it's the internal Docker name)
   - Port: `5432`
   - Database: `FlowDock`
   - Username: `postgres`
   - Password: `postgres`
4. Click "Save"

**Why use "postgres" as hostname?**
- PgAdmin runs in Docker on the same internal network as PostgreSQL
- It uses the Docker service name `postgres` to connect internally
- If connecting from your host machine, use `localhost:5432` instead

---

### 2. Access Grafana and View Metrics

**URL**: `http://localhost/grafana`

**Login Credentials**:
- Username: `admin`
- Password: `admin`

**Features**:
- ✅ Prometheus datasource automatically configured
- ✅ Sample dashboard pre-loaded with 4 key metrics
- ✅ Ready to create custom dashboards and panels

**What's Available**:
- Request rates and latency
- Error rates
- Memory usage
- CPU usage
- Database connection pools

---

### 3. Access Prometheus

**URL**: `http://localhost/prometheus`

**Features**:
- Query metrics using PromQL
- View scrape targets
- See raw metric values

**Common Queries**:
```promql
rate(http_requests_total[1m])           # Request rate
histogram_quantile(0.95, http_request_duration_seconds_bucket)  # Latency
process_resident_memory_bytes / 1024 / 1024  # Memory in MB
```

---

### 4. Access Traefik Dashboard (for DevOps)

**URL**: `http://localhost:8080`

**Features**:
- View all configured routers
- Monitor services and load balancing
- Check middleware configurations
- View real-time metrics

---

## Docker Service Hostnames (Internal)

These are used within Docker containers to communicate with other services:

| Service | Hostname | Port |
|---------|----------|------|
| PostgreSQL | `postgres` | 5432 |
| Redis | `redis` | 6379 |
| MongoDB | `mongo_meta` | 27017 |
| RabbitMQ | `rabbitmq` | 5672 |
| Auth Service | `auth_service` | 8000 |
| Prometheus | `prometheus` | 9090 |
| Grafana | `grafana` | 3000 |

---

## Environment Variables Reference

**PostgreSQL (for all services)**:
```
POSTGRES_USER: postgres
POSTGRES_PASSWORD: postgres
POSTGRES_DB: FlowDock
POSTGRES_HOST: postgres (Docker internal)
POSTGRES_PORT: 5432
```

**Redis (for caching)**:
```
REDIS_HOST: redis
REDIS_PORT: 6379
```

**Auth Service**:
```
JWT_SECRET: secret
JWT_ALGORITHM: HS256
BACKEND_URL: http://localhost:8000
FRONTEND_URL: http://localhost:5173
```

---

## Troubleshooting

### Can't access services via localhost/path?
- Ensure Traefik container is running: `docker ps | grep traefik`
- Check if port 80 is in use: `lsof -i :80` (Mac/Linux)
- Restart Traefik: `docker restart flowdock_gateway`

### PgAdmin won't connect to PostgreSQL?
- Verify you're using hostname `postgres` (not localhost)
- Check PostgreSQL is healthy: `docker exec flowdock_postgres pg_isready`
- Review PGADMIN_SETUP.md for detailed connection guide

### Grafana not showing data?
- Verify Prometheus datasource is configured (auto-provisioned)
- Check if auth_service is exposing `/metrics` endpoint
- Wait 2-3 minutes for metrics to be collected
- Review GRAFANA_SETUP.md for detailed setup guide

### Services running but page says "Connection refused"?
- Services may be starting up - wait 30 seconds
- Check Docker logs: `docker logs flowdock_[service_name]`
- Verify container is running: `docker ps | grep flowdock`

---

## Direct Port Access (If Needed)

If you prefer direct port access without the path:

| Service | Direct URL |
|---------|-----------|
| PgAdmin | `http://localhost:5050` |
| Grafana | `http://localhost:3000` |
| Prometheus | `http://localhost:9090` |
| Auth Service | `http://localhost:8000` |
| RabbitMQ Management | `http://localhost:15672` |

---

## Next Steps

1. **Configure Grafana dashboards** - Create custom panels for your metrics
2. **Set up alerts** - Configure alerting rules in Prometheus
3. **Monitor logs** - Use PgAdmin to monitor database performance
4. **Optimize queries** - Use Prometheus to identify slow endpoints
