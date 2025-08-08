# FisioRAG Load Testing - Installation Guide

## Modern Setup with UV (Recommended)

FisioRAG uses **UV** package manager for ultra-fast Python dependency management (10-100x faster than pip).

### Prerequisites

1. **UV** installed globally:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Node.js** with **PNPM** (for full development environment):
```bash
npm install -g pnpm
```

### Installation Methods

#### Method 1: Install Load Testing Extensions (Recommended)

From the project root:

```bash
# Install load testing dependencies as extras
uv pip install --extra load_testing -e .

# Verify installation
uv run python -c "import locust, psutil, plotly; print('✅ Load testing dependencies installed')"
```

#### Method 2: Install Specific Tools

```bash
# Core load testing tools
uv pip install locust>=2.31.0 psutil>=6.0.0 plotly>=5.18.0 faker>=30.0.0

# Optional: Global Locust installation
uv tool install locust

# Verify
uv run locust --version
```

#### Method 3: Development Environment

For complete development environment:

```bash
# Install all development dependencies
uv pip install --extra dev --extra load_testing --extra monitoring -e .

# Run tests to verify setup
uv run python -m pytest tests/ -v
```

### Quick Verification

```bash
# Test basic import
uv run python -c "
import sys
sys.path.append('load_testing')
import config
print('✅ Load testing suite ready!')
"

# Test CLI
uv run python load_testing/run_scalability_tests.py --help
```

### Environment Configuration

Create `.env` file in project root:

```bash
# Required for load testing
LOAD_TEST_API_URL=http://localhost:8000
DATABASE_URL=postgresql://user:password@localhost/fisiorag
NEO4J_URI=neo4j://localhost:7687  
REDIS_URL=redis://localhost:6379/0

# Optional for advanced features  
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3001
```

### First Test Run

```bash
# Quick 5-minute baseline test
uv run python load_testing/run_scalability_tests.py --quick

# Expected output:
# 🚀 Running Quick Baseline Test (5 minutes)
# ✅ Test Status: PASSED
# 📊 Max Throughput: XX.X RPS
# ⏱️  Avg Response Time: XX.X ms
```

## Legacy Setup (Not Recommended)

If you cannot use UV:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[load_testing]"

# Run tests
python load_testing/run_scalability_tests.py --quick
```

## Troubleshooting

### UV Command Not Found

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload shell
source ~/.bashrc  # or restart terminal
```

### Import Errors

```bash
# Ensure you're in project root
cd path/to/agentic-rag-knowledge-graph

# Reinstall with editable mode
uv pip install -e .

# Check Python path
uv run python -c "import sys; print('\n'.join(sys.path))"
```

### Performance Issues

```bash
# Use UV caching for faster installs
uv pip install --extra load_testing -e . --cache-dir ~/.uv-cache

# Parallel installation
uv pip install --extra load_testing -e . --concurrent-installs
```

### Windows-Specific Issues

```bash
# Use Windows-compatible commands
uv run python load_testing\run_scalability_tests.py --quick

# PowerShell execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Integration with Project Workflow

### With PNPM (Full Stack Development)

```bash
# Setup entire project (from root)
pnpm setup  # Installs frontend + backend dependencies including load testing

# Run development stack
pnpm dev    # Starts API + Frontend + Hot reload

# Run load tests against dev stack
uv run python load_testing/run_scalability_tests.py --quick
```

### With Docker

```bash
# Build with load testing capabilities
docker build -t fisiorag:latest .

# Run load tests against containerized app
LOAD_TEST_API_URL=http://localhost:8000 uv run python load_testing/run_scalability_tests.py --quick
```

## Production Deployment

```bash
# Install only production dependencies
uv pip install --no-dev -e .

# Run production readiness validation
uv run python load_testing/run_scalability_tests.py --full-suite

# Generate reports for deployment approval
ls load_testing/results/scalability_suite_report_*.json
```

---

**Need Help?** Check the main [README.md](README.md) for detailed usage instructions or troubleshooting guide.
