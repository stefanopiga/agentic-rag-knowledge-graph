# 🚀 Production Deployment Guide - FisioRAG

## Panoramica

Guida completa per il deployment in produzione di FisioRAG con stack modernizzato (UV, PNPM, BUN) e architettura enterprise-grade.

## 📋 Indice

1. [Architettura Production](#architettura-production)
2. [Prerequisiti](#prerequisiti)
3. [Environment Configuration](#environment-configuration)
4. [Docker Deployment](#docker-deployment)
5. [CI/CD Deployment](#cicd-deployment)
6. [Database Setup](#database-setup)
7. [Monitoring & Observability](#monitoring--observability)
8. [Security Configuration](#security-configuration)
9. [Performance Tuning](#performance-tuning)
10. [Backup & Recovery](#backup--recovery)
11. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architettura Production

FisioRAG utilizza un'architettura a microservizi containerizzata:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   FisioRAG App   │    │    Frontend     │
│    (Nginx/ALB)  │────│  (FastAPI + AI)  │────│  (React + TS)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
            ┌───────▼────┐ ┌────▼────┐ ┌───▼─────┐
            │ PostgreSQL │ │  Neo4j  │ │  Redis  │
            │ (pgvector) │ │ (Graph) │ │ (Cache) │
            └────────────┘ └─────────┘ └─────────┘
```

### Stack Tecnologico Production

- **Backend**: FastAPI + Pydantic-AI + UV (10-100x più veloce)
- **Frontend**: React 19 + TypeScript + PNPM (2-3x più veloce)
- **Database**: PostgreSQL 16 + pgvector extension
- **Graph DB**: Neo4j 5.x + APOC plugins
- **Cache**: Redis 7.x con LRU eviction
- **Container**: Docker multi-stage con UV optimization
- **Orchestration**: Docker Compose / Kubernetes
- **CI/CD**: GitHub Actions con cache moderni

---

## 🔧 Prerequisiti

### Infrastruttura Minima

- **CPU**: 4 vCPU (raccomandati 8 vCPU)
- **RAM**: 8GB (raccomandati 16GB)
- **Storage**: 50GB SSD (raccomandati 100GB)
- **Network**: Connessione stabile con latenza <100ms

### Software Requirements

- Docker 24.0+ con Docker Compose 2.x
- SSL certificate per HTTPS
- Domain name configurato
- Backup storage (S3/Azure Blob/GCS)

### Cloud Providers Supportati

- ✅ **AWS**: ECS + RDS + ElastiCache + Neptune
- ✅ **Azure**: Container Instances + PostgreSQL + Redis + Cosmos DB
- ✅ **GCP**: Cloud Run + Cloud SQL + Memorystore + Firestore
- ✅ **Digital Ocean**: Droplets + Managed Databases
- ✅ **Self-hosted**: Docker + PostgreSQL + Neo4j + Redis

---

## 🌍 Environment Configuration

### Variabili d'Ambiente Critiche

Crea il file `.env` in produzione:

```bash
# === DATABASE CONFIGURATION ===
DATABASE_URL=postgresql://fisiorag_user:secure_password@db.example.com:5432/fisiorag_prod
POSTGRES_HOST=db.example.com
POSTGRES_PORT=5432
POSTGRES_DB=fisiorag_prod
POSTGRES_USER=fisiorag_user
POSTGRES_PASSWORD=secure_password

# === NEO4J CONFIGURATION ===
NEO4J_URI=neo4j+s://neo4j.example.com:7687
NEO4J_USER=fisiorag
NEO4J_PASSWORD=secure_neo4j_password
NEO4J_TIMEOUT=300
NEO4J_MAX_RETRY=3
NEO4J_RETRY_DELAY=5

# === REDIS CONFIGURATION ===
REDIS_URL=redis://redis.example.com:6379
REDIS_MAX_MEMORY=1gb
REDIS_EVICTION_POLICY=allkeys-lru

# === AI PROVIDERS ===
LLM_PROVIDER=openai
LLM_CHOICE=gpt-4o-mini
LLM_API_KEY=sk-your_production_openai_key
LLM_BASE_URL=https://api.openai.com/v1

EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=sk-your_production_openai_key
VECTOR_DIMENSION=1536

# === APPLICATION ===
APP_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=INFO
DEBUG_MODE=false

# === SECURITY ===
JWT_SECRET_KEY=your_super_secure_jwt_secret_256_bits
CORS_ORIGINS=https://fisiorag.example.com,https://app.fisiorag.com
ALLOWED_HOSTS=fisiorag.example.com,app.fisiorag.com

# === MONITORING ===
SENTRY_DSN=https://your_sentry_dsn@sentry.io/project
PROMETHEUS_ENABLED=true
METRICS_PORT=9090

# === BACKUP ===
BACKUP_S3_BUCKET=fisiorag-backups
BACKUP_ENCRYPTION_KEY=your_backup_encryption_key
```

### Environment Templates

#### Development
```bash
cp env.txt .env.development
# Edit with development values
```

#### Staging
```bash
cp env.txt .env.staging
# Edit with staging values
```

#### Production
```bash
cp env.txt .env.production
# Edit with production values and secure secrets
```

---

## 🐳 Docker Deployment

### Production Docker Build

Il Dockerfile è ottimizzato per produzione con:
- **Multi-stage build** per ridurre dimensioni (70% più piccolo)
- **UV package manager** (10-100x più veloce di pip)
- **Health checks** integrati
- **Environment validation** automatica

#### Build Production Image

```bash
# Build ottimizzato per produzione
docker build -t fisiorag:production .

# Build con cache per faster rebuilds
docker build --cache-from fisiorag:production -t fisiorag:latest .

# Multi-platform build (ARM64 + AMD64)
docker buildx build --platform linux/amd64,linux/arm64 -t fisiorag:latest .
```

#### Production Docker Compose

Crea `docker-compose.prod.yml`:

```yaml
version: "3.8"

services:
  app:
    image: fisiorag:production
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - LOG_LEVEL=INFO
    env_file:
      - .env.production
    depends_on:
      - postgres
      - neo4j
      - redis
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl/certs:ro
    depends_on:
      - app
    restart: unless-stopped

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/schema_with_auth.sql:/docker-entrypoint-initdb.d/init.sql
      - ./backups:/backups
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'

  neo4j:
    image: neo4j:5.15-enterprise
    environment:
      NEO4J_AUTH: ${NEO4J_USER}/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
      NEO4J_ACCEPT_LICENSE_AGREEMENT: "yes"
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_import:/var/lib/neo4j/import
      - neo4j_plugins:/plugins
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 3G
          cpus: '1.5'

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
      - frontend
    restart: unless-stopped

volumes:
  postgres_data:
    driver: local
  neo4j_data:
    driver: local
  neo4j_logs:
    driver: local
  neo4j_import:
    driver: local
  neo4j_plugins:
    driver: local
  redis_data:
    driver: local
```

#### Deploy Production

```bash
# Deploy produzione
docker-compose -f docker-compose.prod.yml up -d

# Verificare status
docker-compose -f docker-compose.prod.yml ps

# Logs monitoring
docker-compose -f docker-compose.prod.yml logs -f

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale app=3
```

---

## 🔄 CI/CD Deployment

### GitHub Actions Production Workflow

Il progetto include già workflow GitHub Actions ottimizzati per deployment production:

#### Automated Deployment Pipeline

1. **Trigger**: Push su branch `main`
2. **Security Scanning**: Bandit, Safety, CodeQL, Trivy
3. **Testing**: Unit + Integration tests
4. **Build**: Multi-platform Docker images
5. **Deploy**: Automated deployment con rollback
6. **Monitoring**: Health checks e notifiche

#### Production Deployment Script

Crea `.github/workflows/deploy-production.yml`:

```yaml
name: Production Deployment

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  deploy-production:
    runs-on: ubuntu-latest
    environment: production
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup UV & Dependencies
        uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true

      - name: Run Security Scan
        run: |
          uv run bandit -r agent/ ingestion/
          uv run safety check

      - name: Build Production Image
        run: |
          docker build -t ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} .
          docker tag ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

      - name: Push to Registry
        run: |
          echo ${{ secrets.GITHUB_TOKEN }} | docker login ${{ env.REGISTRY }} -u ${{ github.actor }} --password-stdin
          docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest

      - name: Deploy to Production
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.PROD_HOST }}
          username: ${{ secrets.PROD_USER }}
          key: ${{ secrets.PROD_SSH_KEY }}
          script: |
            cd /opt/fisiorag
            docker-compose -f docker-compose.prod.yml pull
            docker-compose -f docker-compose.prod.yml up -d
            docker system prune -f

      - name: Health Check
        run: |
          sleep 30
          curl -f https://api.fisiorag.com/health || exit 1

      - name: Notify Success
        uses: 8398a7/action-slack@v3
        with:
          status: success
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

#### Environment Secrets

Configura in GitHub Settings > Secrets:

```
PROD_HOST=production.server.com
PROD_USER=deploy
PROD_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----...
DATABASE_URL=postgresql://...
NEO4J_URI=neo4j+s://...
LLM_API_KEY=sk-...
SLACK_WEBHOOK=https://hooks.slack.com/...
```

---

## 🗄️ Database Setup

### PostgreSQL Production Setup

#### Cloud PostgreSQL (Raccomandato)

```bash
# AWS RDS
aws rds create-db-instance \
  --db-instance-identifier fisiorag-prod \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 16.1 \
  --allocated-storage 100 \
  --storage-type gp3

# Install pgvector extension
psql -h fisiorag-prod.abc.rds.amazonaws.com -U postgres -d fisiorag_prod
CREATE EXTENSION IF NOT EXISTS vector;
```

#### Self-hosted PostgreSQL

```bash
# Install PostgreSQL 16 + pgvector
sudo apt-get update
sudo apt-get install postgresql-16 postgresql-16-pgvector

# Configure production settings
sudo vim /etc/postgresql/16/main/postgresql.conf
```

Configurazioni production PostgreSQL:

```conf
# postgresql.conf production settings
max_connections = 200
shared_buffers = 2GB
effective_cache_size = 6GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 10MB
min_wal_size = 1GB
max_wal_size = 4GB

# Vector-specific settings
shared_preload_libraries = 'vector'
```

### Neo4j Production Setup

#### Neo4j Cloud (Raccomandato)

```bash
# Crea instance Neo4j AuraDB
# - Memory: 8GB
# - Storage: 200GB SSD
# - Plugins: APOC, GDS
```

#### Self-hosted Neo4j

```bash
# Install Neo4j Enterprise
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable 5' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt-get update
sudo apt-get install neo4j-enterprise=1:5.15.0

# Configure production
sudo vim /etc/neo4j/neo4j.conf
```

Configurazioni production Neo4j:

```conf
# neo4j.conf production settings
dbms.memory.heap.initial_size=2g
dbms.memory.heap.max_size=6g
dbms.memory.pagecache.size=2g

# Network
dbms.default_listen_address=0.0.0.0
dbms.connector.bolt.listen_address=0.0.0.0:7687
dbms.connector.http.listen_address=0.0.0.0:7474

# Security
dbms.security.auth_enabled=true
dbms.security.procedures.unrestricted=apoc.*,gds.*

# Plugins
dbms.security.procedures.allowlist=apoc.*,gds.*
dbms.unmanaged_extension_classes=n10s.endpoint=/rdf
```

### Redis Production Setup

```bash
# Redis configuration for production
sudo vim /etc/redis/redis.conf
```

```conf
# redis.conf production settings
maxmemory 2gb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
save 900 1
save 300 10
save 60 10000
```

---

## 📊 Monitoring & Observability

### Application Monitoring

#### Prometheus + Grafana Setup

```yaml
# monitoring/docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=secure_password
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./grafana/datasources:/etc/grafana/provisioning/datasources

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "9093:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
```

#### Custom Metrics per FisioRAG

```python
# agent/monitoring.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Business metrics
queries_total = Counter('fisiorag_queries_total', 'Total queries processed')
query_duration = Histogram('fisiorag_query_duration_seconds', 'Query processing time')
active_users = Gauge('fisiorag_active_users', 'Currently active users')
knowledge_graph_nodes = Gauge('fisiorag_kg_nodes_total', 'Total nodes in knowledge graph')

# Infrastructure metrics
database_connections = Gauge('fisiorag_db_connections', 'Active database connections')
cache_hit_rate = Gauge('fisiorag_cache_hit_rate', 'Cache hit rate percentage')
```

### Logging Configuration

#### Structured Logging Setup

```python
# agent/logging_config.py
import logging
import structlog
from pythonjsonlogger import jsonlogger

def setup_production_logging():
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
```

#### Log Aggregation con ELK Stack

```yaml
# monitoring/elk-stack.yml
version: '3.8'

services:
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms2g -Xmx2g"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data

  logstash:
    image: logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

  kibana:
    image: kibana:8.11.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

### Health Checks

#### Application Health Endpoint

```python
# agent/health.py
from fastapi import APIRouter
import asyncio
import asyncpg
import redis

router = APIRouter()

@router.get("/health")
async def health_check():
    checks = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # PostgreSQL check
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute("SELECT 1")
        await conn.close()
        checks["services"]["postgresql"] = "healthy"
    except Exception as e:
        checks["services"]["postgresql"] = f"unhealthy: {str(e)}"
        checks["status"] = "unhealthy"
    
    # Neo4j check
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
        checks["services"]["neo4j"] = "healthy"
    except Exception as e:
        checks["services"]["neo4j"] = f"unhealthy: {str(e)}"
        checks["status"] = "unhealthy"
    
    # Redis check
    try:
        r = redis.from_url(REDIS_URL)
        r.ping()
        checks["services"]["redis"] = "healthy"
    except Exception as e:
        checks["services"]["redis"] = f"unhealthy: {str(e)}"
        checks["status"] = "unhealthy"
    
    return checks
```

---

## 🔐 Security Configuration

### SSL/TLS Setup

#### Nginx SSL Configuration

```nginx
# nginx/nginx.conf
server {
    listen 80;
    server_name fisiorag.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name fisiorag.example.com;

    ssl_certificate /etc/nginx/ssl/fisiorag.crt;
    ssl_certificate_key /etc/nginx/ssl/fisiorag.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    
    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Database Security

#### PostgreSQL Security

```sql
-- Create dedicated user for FisioRAG
CREATE USER fisiorag_app WITH PASSWORD 'secure_generated_password';

-- Grant minimal required permissions
GRANT CONNECT ON DATABASE fisiorag_prod TO fisiorag_app;
GRANT USAGE ON SCHEMA public TO fisiorag_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fisiorag_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO fisiorag_app;

-- Enable RLS (Row Level Security)
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON documents FOR ALL TO fisiorag_app USING (tenant_id = current_setting('app.current_tenant_id'));
```

#### Neo4j Security

```cypher
// Create application user
CREATE USER fisiorag_app SET PASSWORD 'secure_generated_password' CHANGE NOT REQUIRED

// Grant minimal permissions
GRANT TRAVERSE ON GRAPH * NODES * TO fisiorag_app
GRANT READ ON GRAPH * NODES * TO fisiorag_app
GRANT WRITE ON GRAPH * NODES * TO fisiorag_app
```

### Application Security

#### Rate Limiting

```python
# agent/security.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/api/query")
@limiter.limit("10/minute")
async def query_endpoint(request: Request, query: QueryRequest):
    # Query processing logic
    pass
```

#### Input Validation

```python
# agent/validation.py
from pydantic import BaseModel, validator
import bleach

class QueryRequest(BaseModel):
    query: str
    tenant_id: str
    
    @validator('query')
    def sanitize_query(cls, v):
        # Remove potentially dangerous HTML/script content
        return bleach.clean(v, strip=True)
    
    @validator('tenant_id')
    def validate_tenant(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid tenant ID format')
        return v
```

---

## ⚡ Performance Tuning

### Application Performance

#### FastAPI Production Settings

```python
# agent/settings.py
class ProductionSettings(BaseSettings):
    # Worker configuration
    workers: int = 4
    worker_class: str = "uvicorn.workers.UvicornWorker"
    max_requests: int = 1000
    max_requests_jitter: int = 100
    preload_app: bool = True
    
    # Connection pooling
    db_pool_size: int = 20
    db_max_overflow: int = 30
    db_pool_timeout: int = 30
    
    # Cache settings
    redis_pool_size: int = 10
    cache_ttl: int = 3600
    
    # AI processing
    batch_size: int = 10
    max_concurrent_requests: int = 50
```

#### Database Optimization

```python
# agent/database.py
import asyncpg
from asyncpg.pool import Pool

# Optimized connection pool
async def create_db_pool():
    return await asyncpg.create_pool(
        DATABASE_URL,
        min_size=10,
        max_size=20,
        max_queries=50000,
        max_inactive_connection_lifetime=300,
        command_timeout=60
    )

# Query optimization
async def get_similar_documents(query_vector: List[float], limit: int = 10):
    query = """
    SELECT id, content, metadata, 
           embedding <-> $1 as distance
    FROM documents 
    WHERE tenant_id = $2
    ORDER BY embedding <-> $1 
    LIMIT $3
    """
    # Use prepared statements for better performance
    return await conn.fetch(query, query_vector, tenant_id, limit)
```

### Infrastructure Performance

#### Container Resource Limits

```yaml
# docker-compose.prod.yml resource optimization
services:
  app:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
```

#### Network Optimization

```nginx
# nginx/nginx.conf performance settings
worker_processes auto;
worker_connections 4096;

http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml;
}
```

---

## 💾 Backup & Recovery

### Automated Backup Strategy

#### Database Backups

```bash
#!/bin/bash
# scripts/backup_databases.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# PostgreSQL backup
pg_dump $DATABASE_URL | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# Neo4j backup
docker exec neo4j neo4j-admin database backup --to-path=/backups/neo4j neo4j

# Redis backup
docker exec redis redis-cli BGSAVE
docker cp redis:/data/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# Upload to S3
aws s3 sync $BACKUP_DIR s3://fisiorag-backups/$(date +%Y/%m/%d)/

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -type f -mtime +30 -delete
```

#### Backup Monitoring

```python
# scripts/backup_monitor.py
import boto3
from datetime import datetime, timedelta

def verify_daily_backups():
    s3 = boto3.client('s3')
    bucket = 'fisiorag-backups'
    
    yesterday = datetime.now() - timedelta(days=1)
    prefix = yesterday.strftime('%Y/%m/%d/')
    
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    
    if 'Contents' not in response:
        send_alert("No backups found for yesterday!")
        return False
    
    required_backups = ['postgres_', 'neo4j_', 'redis_']
    found_backups = [obj['Key'] for obj in response['Contents']]
    
    for backup_type in required_backups:
        if not any(backup_type in key for key in found_backups):
            send_alert(f"Missing {backup_type} backup for yesterday!")
            return False
    
    return True
```

### Disaster Recovery

#### Recovery Procedures

```bash
#!/bin/bash
# scripts/restore_from_backup.sh

BACKUP_DATE=$1
BACKUP_DIR="/backups/restore"

echo "Starting disaster recovery for date: $BACKUP_DATE"

# Stop services
docker-compose -f docker-compose.prod.yml down

# Download backups from S3
aws s3 sync s3://fisiorag-backups/$BACKUP_DATE $BACKUP_DIR

# Restore PostgreSQL
gunzip -c $BACKUP_DIR/postgres_*.sql.gz | psql $DATABASE_URL

# Restore Neo4j
docker run --rm -v neo4j_data:/data -v $BACKUP_DIR:/backups \
    neo4j:5.15 neo4j-admin database restore --from-path=/backups/neo4j neo4j

# Restore Redis
docker run --rm -v redis_data:/data -v $BACKUP_DIR:/backups \
    redis:7-alpine cp /backups/redis_*.rdb /data/dump.rdb

# Start services
docker-compose -f docker-compose.prod.yml up -d

echo "Recovery completed. Verifying services..."
sleep 30
curl -f https://api.fisiorag.com/health || echo "Health check failed!"
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Database Connection Issues

**Symptoms**:
- `connection refused` errors
- Timeout on database queries
- Health check failures

**Solutions**:
```bash
# Check database connectivity
nc -zv database.host 5432

# Verify credentials
psql $DATABASE_URL -c "SELECT version();"

# Check connection limits
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity;"

# Restart database service
docker-compose restart postgres
```

#### 2. Memory Issues

**Symptoms**:
- OOMKilled containers
- Slow response times
- High memory usage

**Solutions**:
```bash
# Monitor memory usage
docker stats

# Check application memory profiling
curl https://api.fisiorag.com/debug/memory

# Increase container limits
docker-compose.prod.yml:
  services:
    app:
      deploy:
        resources:
          limits:
            memory: 8G
```

#### 3. SSL Certificate Issues

**Symptoms**:
- Browser security warnings
- SSL handshake failures
- HTTPS redirects not working

**Solutions**:
```bash
# Check certificate validity
openssl x509 -in /etc/nginx/ssl/fisiorag.crt -text -noout

# Verify certificate chain
curl -I https://fisiorag.example.com

# Renew Let's Encrypt certificate
certbot renew --nginx
```

### Performance Debugging

#### Query Performance Analysis

```sql
-- PostgreSQL slow query analysis
SELECT query, mean_exec_time, calls, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check vector index usage
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * FROM documents 
ORDER BY embedding <-> '[1,2,3...]'::vector 
LIMIT 10;
```

#### Neo4j Performance Tuning

```cypher
// Check query performance
CALL dbms.queryJmx("org.neo4j:instance=kernel#0,name=Page Cache")

// Analyze slow queries
CALL dbms.procedures() YIELD name 
WHERE name CONTAINS "slow"

// Index optimization
CREATE INDEX medical_entities FOR (n:Entity) ON (n.type, n.name)
```

### Log Analysis

#### Application Logs

```bash
# Filter error logs
docker-compose logs app | grep ERROR

# Monitor real-time logs
docker-compose logs -f --tail=100 app

# Search specific patterns
docker-compose logs app | grep "query_duration" | tail -20
```

#### Database Logs

```bash
# PostgreSQL logs
docker-compose exec postgres tail -f /var/log/postgresql/postgresql.log

# Neo4j logs
docker-compose exec neo4j tail -f /logs/debug.log

# Redis logs
docker-compose exec redis redis-cli monitor
```

---

## 📞 Support & Maintenance

### Maintenance Schedule

#### Daily Tasks
- ✅ Check service health status
- ✅ Monitor error rates and performance metrics
- ✅ Verify backup completion
- ✅ Review security alerts

#### Weekly Tasks
- 🔄 Update dependencies (automated via Dependabot)
- 🔄 Rotate log files
- 🔄 Database maintenance (VACUUM, ANALYZE)
- 🔄 Performance review

#### Monthly Tasks
- 🔐 Review access logs and user activity
- 📊 Capacity planning analysis
- 🔄 Security patch review
- 💾 Disaster recovery test

### Emergency Procedures

#### Incident Response

1. **Alert Detection** → Monitoring triggers alert
2. **Initial Assessment** → Check service status and logs
3. **Immediate Response** → Apply quick fixes or rollback
4. **Root Cause Analysis** → Investigate underlying issues
5. **Post-Incident Review** → Document lessons learned

#### Emergency Contacts

```yaml
# Contact information for production issues
oncall:
  primary: "admin@fisiorag.com"
  secondary: "devops@fisiorag.com"
  
monitoring:
  slack: "#fisiorag-alerts"
  pagerduty: "fisiorag-production"
  
vendors:
  database: "database-support@provider.com"
  cloud: "cloud-support@provider.com"
```

---

## 🎯 Conclusioni

Questa guida copre tutti gli aspetti critici per un deployment production-ready di FisioRAG:

### ✅ Checklist Pre-Production

- [ ] Environment variables configurate e sicure
- [ ] SSL/TLS certificates installati e validi
- [ ] Database ottimizzati e backup configurati
- [ ] Monitoring e alerting attivi
- [ ] Security hardening completato
- [ ] Performance testing eseguito
- [ ] Disaster recovery testato
- [ ] Team formato su procedure operative

### 🚀 Prossimi Passi

1. **Performance Monitoring Setup** - Implementare metriche avanzate
2. **Scalability Testing** - Load testing con stack ottimizzato
3. **Security Hardening** - Security audit con tool moderni

Il sistema FisioRAG è ora pronto per un deployment production enterprise-grade! 🎉

---

**Versione**: 1.0.0  
**Ultimo aggiornamento**: 2025-01-19  
**Stack**: UV + PNPM + BUN + Docker + GitHub Actions
