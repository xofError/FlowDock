# FlowDock - Docker Setup Guide

## Overview

FlowDock is a microservices-based file management platform with authentication and media services. This guide explains how to set up and run the application using Docker Compose.

## Project Structure

```
FlowDock/
├── backend/
│   ├── auth_service/          # Authentication & User Management
│   │   ├── app/               # FastAPI application
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   ├── requirements.txt
│   │   └── .dockerignore
│   └── media_service/         # File Management & Sharing
│       ├── app/               # FastAPI application
│       ├── Dockerfile
│       ├── docker-compose.yml
│       ├── requirements.txt
│       └── .dockerignore
├── frontend/                  # React/Vite Frontend
│   ├── src/
│   │   ├── pages/
│   │   │   └── auth/         # Authentication pages
│   │   ├── components/
│   │   ├── layout/
│   │   └── resources/
│   ├── Dockerfile
│   ├── .dockerignore
│   └── package.json
├── docker-compose.yml         # Main orchestration file
├── .env.example               # Environment variables template
└── UML/                       # Architecture diagrams
```

## Services

### Infrastructure
- **PostgreSQL** (16-alpine): Primary database for relational data
- **Redis** (7-alpine): Caching and session management
- **MongoDB** (7-alpine): Document storage for media metadata
- **RabbitMQ** (3.13-management): Message broker for async tasks
- **PgAdmin**: PostgreSQL administration tool (dev only)

### Applications
- **Auth Service** (port 8000): User authentication, token management, 2FA
- **Media Service** (port 8001): File upload, download, sharing, virus scanning
- **Frontend** (port 5173): React/Vite application

## Quick Start

### 1. Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available for Docker
- 10GB disk space for volumes

### 2. Environment Setup

```bash
# Copy example environment file
cp .env.example .env

# Edit .env if needed (optional, defaults are configured)
nano .env
```

### 3. Start All Services

```bash
# Navigate to project root
cd /home/xof/Desktop/Flow

# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f auth_service
docker-compose logs -f media_service
```

### 4. Verify Services Are Running

```bash
# Check service status
docker-compose ps

# Test auth service
curl http://localhost:8000/health

# Test media service
curl http://localhost:8001/health

# Access frontend
open http://localhost:5173

# Access PgAdmin (dev)
open http://localhost:5050

# Access RabbitMQ Dashboard (dev)
open http://localhost:15672
```

## Individual Service Startup

Each service has its own `docker-compose.yml` for standalone development:

### Auth Service Only
```bash
cd backend/auth_service
docker-compose up -d
```

### Media Service Only
```bash
cd backend/media_service
docker-compose up -d
```

## Service Details

### Auth Service
- **Port**: 8000
- **Database**: PostgreSQL (FlowDock database)
- **Cache**: Redis (DB 0)
- **Features**: Login, signup, 2FA, password recovery, token management
- **Dependencies**: PostgreSQL, Redis, RabbitMQ

### Media Service
- **Port**: 8001
- **Databases**: PostgreSQL, MongoDB
- **Cache**: Redis (DB 1)
- **Features**: File upload/download, sharing, permissions, virus scanning
- **Dependencies**: PostgreSQL, MongoDB, Redis, RabbitMQ

### Frontend
- **Port**: 5173 (dev) / 80 (prod)
- **Build**: React 18 + Vite
- **Features**: User authentication flows, file management UI

## Environment Variables

Key configuration variables (see `.env.example`):

```env
# Database
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=FlowDock

# Redis
REDIS_DB=0

# MongoDB
MONGO_USER=root
MONGO_PASSWORD=mongopass

# Security
JWT_SECRET=your-super-secret-key-change-this-in-production
JWT_EXPIRATION=3600

# Media Service
MAX_FILE_SIZE=104857600  # 100MB
ALLOWED_EXTENSIONS=pdf,doc,docx,xls,xlsx,ppt,pptx,jpg,jpeg,png,gif,txt,zip,rar

# API URLs
VITE_API_URL=http://localhost:8000
VITE_MEDIA_API_URL=http://localhost:8001
```

## Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs (follow mode)
docker-compose logs -f

# Restart specific service
docker-compose restart auth_service

# Remove volumes (⚠️ deletes data)
docker-compose down -v

# Rebuild images
docker-compose build --no-cache

# Execute command in container
docker-compose exec auth_service bash

# Run migrations
docker-compose exec auth_service alembic upgrade head

# Scale services (not recommended with stateful DBs)
docker-compose up -d --scale media_service=2
```

## Networking

All services communicate through the `flowdock_network` bridge network:

- **auth_service** ↔ postgres, redis, rabbitmq
- **media_service** ↔ postgres, mongodb, redis, rabbitmq
- **frontend** ↔ auth_service, media_service

Service DNS names within containers:
- `postgres:5432`
- `redis:6379`
- `rabbitmq:5672`
- `mongodb:27017`
- `auth_service:8000`
- `media_service:8000`

## Volume Management

Persistent volumes for data storage:

```
postgres_data/      → PostgreSQL databases
redis_data/         → Redis persistence
mongodb_data/       → MongoDB collections
rabbitmq_data/      → RabbitMQ messages
```

View volumes:
```bash
docker volume ls
docker volume inspect flowdock_postgres_data
```

## Health Checks

All services include health checks. View status:

```bash
docker-compose ps
# HEALTHCHECK column shows: ✓, ✗, or (health: starting)
```

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs auth_service

# Verify ports aren't in use
lsof -i :8000
lsof -i :5432

# Clean up and restart
docker-compose down -v
docker-compose up -d
```

### Database connection errors
```bash
# Check if PostgreSQL is healthy
docker-compose exec postgres pg_isready

# Check Redis connectivity
docker-compose exec redis redis-cli ping

# Check MongoDB connectivity
docker-compose exec mongodb mongosh --eval "db.adminCommand('ping')"
```

### Performance issues
```bash
# Increase Docker memory
# Edit Docker Desktop settings → Resources → Memory: 8GB+

# Clear logs
docker-compose logs --tail 0

# Monitor resource usage
docker stats
```

## Production Deployment

For production, consider:

1. Use `.env` with production values (strong JWT_SECRET, DB_PASSWORD)
2. Change `restart: unless-stopped` to `restart: always`
3. Enable logging rotation (already configured)
4. Use external database services (AWS RDS, MongoDB Atlas)
5. Implement Traefik/nginx reverse proxy
6. Enable SSL/TLS certificates
7. Use Docker Swarm or Kubernetes
8. Set up CI/CD pipelines

## Development Workflow

### Local Development with Hot Reload

Auth Service:
```bash
cd backend/auth_service
docker-compose up -d
# Code changes in app/ will auto-reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
# Vite will hot-reload on save
```

### Debugging

```bash
# Enter service container
docker-compose exec auth_service bash

# Check Python imports
docker-compose exec auth_service python -c "import app; print(app.__file__)"

# Run pytest
docker-compose exec auth_service pytest -v app/tests/
```

## Monitoring & Logging

```bash
# View all logs with timestamps
docker-compose logs --timestamps

# View last 100 lines
docker-compose logs --tail 100

# Stream specific service
docker-compose logs -f media_service

# Export logs
docker-compose logs > logs.txt
```

## Additional Resources

- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
- [React Documentation](https://react.dev/)

## Support

For issues or questions:
1. Check service logs: `docker-compose logs service_name`
2. Verify .env configuration
3. Ensure all ports are available
4. Check Docker daemon is running
5. Review health check status: `docker-compose ps`
