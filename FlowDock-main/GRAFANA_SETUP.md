# Grafana Setup Guide

## Access Grafana

1. Open your browser and navigate to: `http://localhost/grafana`
2. Login with default credentials:
   - **Username**: `admin`
   - **Password**: `admin`

## Step 1: Add Prometheus Data Source

1. Click on **Configuration** (gear icon) in the left sidebar
2. Select **Data Sources**
3. Click **Add data source**
4. Choose **Prometheus**
5. Configure the connection:
   - **Name**: `Prometheus`
   - **URL**: `http://prometheus:9090` (internal Docker network connection)
   - **Access**: `Server (default)`
   - **Scrape interval**: `15s`
6. Click **Save & Test** - you should see "Data source is working"

## Step 2: Create a Dashboard

1. Click on **Create** (plus icon) in the left sidebar
2. Select **Dashboard**
3. Click **Add panel**

## Step 3: Write Prometheus Queries

### Example Queries for Auth Service:

#### 1. **Request Rate** (requests per second)
```promql
rate(http_requests_total[1m])
```

#### 2. **Request Latency** (95th percentile)
```promql
histogram_quantile(0.95, http_request_duration_seconds_bucket)
```

#### 3. **Error Rate**
```promql
rate(http_requests_total{status=~"5.."}[1m])
```

#### 4. **Active Requests**
```promql
http_requests_in_progress
```

#### 5. **Database Connection Pool**
```promql
sqlalchemy_pool_size
sqlalchemy_pool_checked_out
```

#### 6. **Login Attempts**
```promql
rate(auth_login_attempts_total[5m])
```

#### 7. **CPU Usage**
```promql
rate(process_cpu_seconds_total[1m])
```

#### 8. **Memory Usage** (in MB)
```promql
process_resident_memory_bytes / 1024 / 1024
```

## Step 4: Configure Panel Visualization

1. In the panel editor:
   - **Query**: Paste one of the PromQL queries above
   - **Legend**: Set to `{{instance}}` to show which service
   - **Visualization**: Choose appropriate type:
     - **Graph** - for time series data
     - **Stat** - for single values
     - **Gauge** - for percentage/threshold values
     - **Table** - for tabular data

2. Click **Apply** to save the panel

## Step 5: Save Dashboard

1. Click **Save dashboard** (top right)
2. Give it a name (e.g., "FlowDock Metrics")
3. Click **Save**

## Available Metrics from Auth Service

The auth_service exposes metrics on `/metrics` endpoint. Common metrics include:

- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_in_progress` - Currently processing requests
- `process_cpu_seconds_total` - CPU time used
- `process_resident_memory_bytes` - Memory usage
- `sqlalchemy_pool_*` - Database connection pool metrics

## Troubleshooting

### Can't connect to Prometheus?
- Ensure Prometheus is running: `docker ps | grep prometheus`
- Check Prometheus is healthy: `http://localhost:9090`
- Verify the internal Docker hostname `prometheus:9090` is correct
- Check firewall/network settings

### No metrics appearing?
- Verify auth_service is running and exposing `/metrics`
- Check if Prometheus is actually scraping metrics:
  - Go to `http://localhost:9090/targets`
  - Look for "auth_service" job and verify status is "UP"
- Wait a few minutes for metrics to be collected

### Want to use direct port instead of path?
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`
- PgAdmin: `http://localhost:5050`

## Next Steps

1. Create more complex queries combining multiple metrics
2. Set up alerts based on thresholds
3. Create dashboards for different teams (DevOps, Backend, etc.)
4. Export dashboards as JSON for version control
