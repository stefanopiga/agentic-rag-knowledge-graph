# FisioRAG Scalability Testing Suite

Comprehensive load testing, performance monitoring, and scalability validation for the FisioRAG system.

## Overview

This testing suite provides enterprise-grade scalability testing with:

- **API Load Testing** using Locust with realistic user behavior patterns
- **Real-time Performance Monitoring** of system resources and application metrics
- **Database Stress Testing** for PostgreSQL, Neo4j, and Redis
- **Automated Report Generation** with actionable insights and recommendations
- **Production Readiness Validation** through comprehensive test scenarios

## Quick Start

### 1. Install Dependencies

```bash
# Install load testing dependencies with UV (10-100x faster than pip)
uv pip install --extra load_testing -e .

# Or install specific load testing tools
uv pip install locust psutil plotly faker pytest-benchmark

# For global Locust installation (optional)
uv tool install locust
```

### 2. Configure Environment

Create a `.env` file or set environment variables:

```bash
export LOAD_TEST_API_URL="http://localhost:8000"
export DATABASE_URL="postgresql://user:password@localhost/fisiorag"
export NEO4J_URI="neo4j://localhost:7687"
export REDIS_URL="redis://localhost:6379/0"
```

### 3. Run Tests

```bash
# Quick baseline test (5 minutes) - using UV
uv run python load_testing/run_scalability_tests.py --quick

# Peak hours simulation (15 minutes)
uv run python load_testing/run_scalability_tests.py --peak

# Comprehensive stress test (30 minutes)
uv run python load_testing/run_scalability_tests.py --stress

# Full production readiness suite (2-3 hours)
uv run python load_testing/run_scalability_tests.py --full-suite
```

## Test Scenarios

### 1. Baseline Test

- **Duration**: 5 minutes
- **Users**: 10 concurrent
- **Purpose**: Establish performance baseline
- **Use Case**: Development and CI/CD validation

### 2. Peak Hours Simulation

- **Duration**: 15 minutes
- **Users**: 50 concurrent (gradual ramp)
- **Purpose**: Simulate university exam periods
- **Use Case**: Capacity planning for peak usage

### 3. Stress Test

- **Duration**: 30 minutes
- **Users**: 200 concurrent
- **Purpose**: Find system breaking points
- **Use Case**: Reliability and failure mode analysis

### 4. Spike Test

- **Duration**: 10 minutes
- **Users**: 100 concurrent (rapid spike)
- **Purpose**: Test sudden traffic increases
- **Use Case**: Social media traffic or viral content

### 5. Endurance Test

- **Duration**: 60+ minutes
- **Users**: 30 concurrent
- **Purpose**: Long-term stability testing
- **Use Case**: Memory leaks and degradation detection

## Test Components

### Load Testing (Locust)

Realistic user behavior simulation with:

```python
# Student users (60% - educational queries)
# Professional users (30% - clinical questions)
# Researcher users (10% - evidence-based queries)
```

**Test Patterns:**

- Clinical question asking (30% of actions)
- Follow-up questions (15% of actions)
- Streaming conversations (10% of actions)
- Health monitoring (8% of actions)

### Performance Monitoring

Real-time metrics collection:

- **System Metrics**: CPU, memory, disk I/O, network
- **Application Metrics**: Response times, throughput, error rates
- **Database Metrics**: Connection counts, query performance
- **Custom Metrics**: RAG query latency, embedding search times

### Database Stress Testing

Concurrent testing of all databases:

**PostgreSQL:**

- Vector similarity searches
- Complex joins and aggregations
- Write-heavy operations
- Connection pool stress

**Neo4j:**

- Graph traversal queries
- Relationship creation/updates
- Complex Cypher patterns
- Memory-intensive operations

**Redis:**

- Cache read/write patterns
- Session management simulation
- Queue operations
- Memory usage under load

## Advanced Usage

### Custom Test Configuration

```python
from config import LoadTestConfig, TestScenario
from test_orchestrator import TestOrchestrator, TestPlan

# Custom test plan
test_plan = TestPlan(
    name="Custom API Test",
    scenario=TestScenario.BASELINE,
    duration_minutes=10,
    concurrent_users=25,
    spawn_rate=2.5,
    include_database_stress=True,
    include_performance_monitoring=True
)

# Run custom test
orchestrator = TestOrchestrator(LoadTestConfig())
await orchestrator.initialize()
results = await orchestrator.run_test_plan(test_plan)
```

### Standalone Components

Run individual test components:

```bash
# Performance monitoring only
uv run python load_testing/performance_monitor.py

# Database stress testing only
uv run python load_testing/database_stress_test.py

# Locust load testing only (with UV environment)
uv run locust -f load_testing/locustfile.py --host http://localhost:8000
```

### CI/CD Integration

```yaml
# GitHub Actions example with UV
- name: Setup UV
  uses: astral-sh/setup-uv@v6
  
- name: Install dependencies
  run: uv pip install --extra load_testing -e .
  
- name: Run Scalability Tests
  run: uv run python load_testing/run_scalability_tests.py --quick
  env:
    LOAD_TEST_API_URL: ${{ secrets.API_URL }}
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

## Performance Thresholds

### Default Thresholds

```python
response_time_p95_threshold: 2.0    # seconds
response_time_p99_threshold: 5.0    # seconds
error_rate_threshold: 0.01          # 1%
throughput_threshold: 100.0         # requests/second
```

### Custom Thresholds

Override in configuration:

```python
config = LoadTestConfig(
    response_time_p95_threshold=1.5,  # Stricter for production
    error_rate_threshold=0.005,       # 0.5% for critical systems
    throughput_threshold=200.0        # Higher expectations
)
```

## Report Generation

### Automated Reports

All tests generate comprehensive reports:

- **HTML Reports**: Visual Locust reports with charts
- **JSON Reports**: Machine-readable detailed results
- **Summary Reports**: Executive-level insights
- **Performance Metrics**: Time-series data for analysis

### Report Locations

```
load_testing/results/
├── baseline_test_report.html          # Locust HTML report
├── baseline_test_stats.csv            # Raw statistics
├── performance_metrics_20250119.json  # Performance data
├── database_stress_test_20250119.json # Database results
└── scalability_suite_report_20250119.json # Complete suite
```

### Key Report Sections

1. **Executive Summary**: Pass/fail status and key metrics
2. **Performance Analysis**: Response times, throughput, error rates
3. **System Resource Usage**: CPU, memory, I/O utilization
4. **Database Performance**: Per-database stress test results
5. **Scalability Assessment**: Breaking points and capacity limits
6. **Recommendations**: Actionable optimization suggestions

## Monitoring Integration

### Prometheus/Grafana

The suite integrates with existing monitoring:

```python
# Collect metrics from Prometheus
prometheus_url = "http://localhost:9090"
grafana_url = "http://localhost:3001"

# Automated dashboard generation
# Real-time monitoring during tests
# Historical performance comparison
```

### Custom Metrics

Export test results to monitoring systems:

```python
# Prometheus metrics
test_duration_seconds.set(test_duration)
max_response_time_seconds.set(max_response_time)
total_requests.inc(request_count)
```

## Troubleshooting

### Common Issues

**High Error Rates:**

```bash
# Check API logs
docker logs fisiorag-api

# Verify database connections
python -c "from config import LoadTestConfig; import asyncio; asyncio.run(LoadTestConfig().test_connections())"
```

**Resource Exhaustion:**

```bash
# Monitor system resources
top -p $(pgrep -f "python.*locust")

# Check database connections
docker exec fisiorag-postgres psql -c "SELECT count(*) FROM pg_stat_activity;"
```

**Test Failures:**

```bash
# Enable verbose logging
python run_scalability_tests.py --quick --verbose

# Check individual components
python performance_monitor.py
python database_stress_test.py
```

### Performance Optimization

**Database Tuning:**

- Increase connection pool sizes
- Optimize query indexes
- Tune database configuration

**Application Tuning:**

- Enable response caching
- Optimize AI model inference
- Implement request rate limiting

**Infrastructure Scaling:**

- Horizontal API scaling
- Database read replicas
- CDN for static content

## Best Practices

### Test Environment

1. **Isolated Environment**: Test against dedicated staging environment
2. **Representative Data**: Use production-like data volumes
3. **Network Conditions**: Test with realistic network latency
4. **Resource Constraints**: Match production hardware specifications

### Test Execution

1. **Baseline First**: Always establish baseline before optimization
2. **Gradual Ramp**: Use realistic user ramp-up patterns
3. **Cool-down Periods**: Allow system recovery between tests
4. **Monitoring**: Monitor all system components during tests

### Result Analysis

1. **Trend Analysis**: Compare results over time
2. **Bottleneck Identification**: Focus on limiting factors
3. **Actionable Insights**: Generate specific optimization recommendations
4. **Capacity Planning**: Project future scaling needs

## Production Deployment

### Pre-deployment Checklist

- [ ] All test scenarios pass
- [ ] Performance thresholds met
- [ ] Error rates below 1%
- [ ] Database performance acceptable
- [ ] System recovery validated
- [ ] Monitoring alerts configured

### Continuous Testing

```bash
# Daily baseline tests
0 2 * * * cd /app/load_testing && python run_scalability_tests.py --quick

# Weekly comprehensive tests
0 1 * * 0 cd /app/load_testing && python run_scalability_tests.py --stress
```

### Production Monitoring

- Real-time performance dashboards
- Automated alerting on threshold violations
- Capacity planning based on usage trends
- Regular stress testing to validate scaling

---

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review log files in `load_testing/logs/`
3. Examine detailed reports in `load_testing/results/`
4. Create an issue with test configuration and error details
