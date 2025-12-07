# Prometheus Query Examples for FlowDock

## Quick Start Queries

### 1. HTTP Request Metrics

**Request Rate (per second)**
```promql
rate(http_requests_total[1m])
```

**Request Rate by Status Code**
```promql
rate(http_requests_total[1m]) by (status)
```

**Request Rate by Endpoint**
```promql
rate(http_requests_total[1m]) by (handler)
```

**Total Requests (counter)**
```promql
http_requests_total
```

### 2. Latency Metrics

**Average Response Time**
```promql
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

**95th Percentile Latency**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**99th Percentile Latency**
```promql
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
```

**Latency by Endpoint**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) by (handler)
```

### 3. Error Rate

**Error Rate (5xx responses)**
```promql
rate(http_requests_total{status=~"5.."}[1m])
```

**Error Percentage**
```promql
(rate(http_requests_total{status=~"5.."}[1m]) / rate(http_requests_total[1m])) * 100
```

**Errors by Status Code**
```promql
rate(http_requests_total{status=~"[45].."}[1m]) by (status)
```

### 4. In-Progress Requests

**Active Requests**
```promql
http_requests_in_progress
```

**Active Requests by Endpoint**
```promql
http_requests_in_progress by (handler)
```

### 5. Resource Metrics

**Memory Usage (bytes)**
```promql
process_resident_memory_bytes
```

**Memory Usage (MB)**
```promql
process_resident_memory_bytes / 1024 / 1024
```

**CPU Usage (cores)**
```promql
rate(process_cpu_seconds_total[1m])
```

**File Descriptors Used**
```promql
process_open_fds
```

### 6. Database Metrics

**Database Connection Pool Size**
```promql
sqlalchemy_pool_size
```

**Connections Currently Checked Out**
```promql
sqlalchemy_pool_checked_out
```

**Available Connections**
```promql
sqlalchemy_pool_size - sqlalchemy_pool_checked_out
```

**Connection Pool Overflow**
```promql
sqlalchemy_pool_overflow
```

### 7. Authentication Metrics

**Login Attempts Rate**
```promql
rate(auth_login_attempts_total[5m])
```

**Login Success Rate**
```promql
rate(auth_login_success_total[5m])
```

**Failed Login Rate**
```promql
rate(auth_login_failures_total[5m])
```

### 8. System Metrics

**Uptime (seconds)**
```promql
time() - process_start_time_seconds
```

**Uptime (minutes)**
```promql
(time() - process_start_time_seconds) / 60
```

**System Load**
```promql
node_load1
```

## Advanced Queries

### Top 5 Slowest Endpoints
```promql
topk(5, histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) by (handler))
```

### Top 5 Most Called Endpoints
```promql
topk(5, rate(http_requests_total[1m]) by (handler))
```

### Endpoints with High Error Rate
```promql
(rate(http_requests_total{status=~"[45].."}[5m]) / rate(http_requests_total[5m])) by (handler) > 0.05
```

### Services with High Memory Usage
```promql
process_resident_memory_bytes / 1024 / 1024 by (job) > 100
```

### SLA Compliance (99.9% uptime)
```promql
(count(http_requests_total > 0) / count(time() > 0)) * 100
```

## Visualization Tips

### Gauge Charts (0-100%)
Use error percentage or availability percentage with max: 100

### Single Stat
Use `Last non-null value` for counters and gauges

### Time Series
Use `Average` or `Current` aggregation for rates and latencies

### Table
Use instant queries without `rate()` function

## Common Panel Configurations

### Request Rate Panel
- **Query**: `rate(http_requests_total[1m])`
- **Unit**: `reqps`
- **Visualization**: Time series with legend

### Error Rate Panel
- **Query**: `rate(http_requests_total{status=~"[45].."}[1m]) / rate(http_requests_total[1m]) * 100`
- **Unit**: `percent`
- **Visualization**: Gauge or stat with threshold 5%

### Memory Panel
- **Query**: `process_resident_memory_bytes / 1024 / 1024`
- **Unit**: `decmbytes`
- **Visualization**: Stat or gauge

### Latency Panel
- **Query**: `histogram_quantile(0.95, http_request_duration_seconds_bucket)`
- **Unit**: `s`
- **Visualization**: Time series

## Testing Metrics

To verify metrics are being collected, use the Prometheus expression browser:
1. Go to `http://localhost:9090`
2. Click "Graph"
3. Paste a query and click "Execute"
4. Check if you see data points
