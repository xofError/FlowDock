# PgAdmin Setup Guide - Connect to PostgreSQL

## Access PgAdmin

1. Open your browser and navigate to: `http://localhost/pgadmin`
2. Login with default credentials:
   - **Username**: `admin@pgadmin.com`
   - **Password**: `admin`

## Connect to PostgreSQL Database

### Step 1: Register a New Server

1. In the left sidebar, right-click on "Servers"
2. Select "Register" → "Server..."
3. A dialog window will open

### Step 2: Configure Connection Details

**General Tab:**
- **Name**: `FlowDock` (or any name you prefer)
- **Comment**: `FlowDock Production Database`

**Connection Tab:**
- **Hostname/address**: `postgres` (this is the Docker service name - internal hostname)
- **Port**: `5432`
- **Maintenance database**: `FlowDock`
- **Username**: `postgres`
- **Password**: `postgres`
- **Save password?**: Check the box for convenience

### Step 3: Advanced Options (Optional)

- **SSL mode**: `Prefer` (default is fine)
- **Connection timeout**: `10` seconds

### Step 4: Click "Save"

The server should connect and appear in your server list on the left sidebar.

## Common PostgreSQL Connection Parameters

| Parameter | Value |
|-----------|-------|
| Host | `postgres` (internal Docker hostname) OR `localhost:5432` (from host machine) |
| Port | `5432` |
| Database | `FlowDock` |
| Username | `postgres` |
| Password | `postgres` |

## Why Use `postgres` as Hostname?

In Docker Compose:
- **`postgres`** - Use this when connecting from other containers (internal Docker network)
- **`localhost:5432`** - Use this when connecting from your host machine

Since PgAdmin runs as a Docker container on the same network as PostgreSQL, use **`postgres`** as the hostname.

## Useful PgAdmin Features

### Browse Database
1. Expand "FlowDock" server in the left panel
2. Click "Databases" → "FlowDock" to see tables
3. Right-click on any table to view, edit, or execute queries

### Run SQL Queries
1. Right-click on "FlowDock" database
2. Select "Query Tool"
3. Write your SQL and click "Execute"

### View Table Data
1. Navigate to: Servers → FlowDock → Databases → FlowDock → Schemas → public → Tables
2. Right-click on any table
3. Select "View/Edit Data" → "All Rows"

### Create Backups
1. Right-click on "FlowDock" database
2. Select "Backup..."
3. Choose location and format

## Troubleshooting

### Connection Refused?
- Ensure PostgreSQL container is running: `docker ps | grep postgres`
- Check hostname is `postgres` (not `localhost`)
- Verify credentials match docker-compose.yml

### "Cannot connect to server"?
- Make sure both PgAdmin and PostgreSQL are on the same Docker network
- Check firewall settings
- Verify PostgreSQL is healthy: `docker exec flowdock_postgres pg_isready`

### Forgot Password?
- Default credentials are in docker-compose.yml:
  - User: `postgres`
  - Password: `postgres`
  - Can be changed there if needed

## Access from Host Machine

If you want to connect directly from your host machine (not through PgAdmin):

```bash
psql -h localhost -U postgres -d FlowDock
```

When prompted, enter password: `postgres`

## Environment Variables Reference

From docker-compose.yml:
```yaml
POSTGRES_USER: postgres
POSTGRES_PASSWORD: postgres
POSTGRES_DB: FlowDock
POSTGRES_HOST: postgres (internal), localhost (external)
POSTGRES_PORT: 5432
```
