# Modern Setup Instructions - FisioRAG con UV + PNPM + BUN

## 📋 **Agent OS Instructions: Modern Tooling Setup**

**Purpose**: Questa guida fornisce istruzioni specifiche per Agent OS su come gestire il progetto FisioRAG con il nuovo stack modernizzato.

**Context**: Il progetto è stato completamente migrato da pip/npm a UV/PNPM/BUN per performance 5-10x migliorate.

---

## 🎯 **Agent OS Quick Reference**

### **Status Check Commands**

```bash
# Verifica setup moderno completato
python test_modern_setup.py

# Check tool versions
uv --version          # Should be latest
pnpm --version        # Should be 9.0+
bun --version         # Optional, for ultra-fast runtime

# Verifica project structure
ls -la pyproject.toml pnpm-workspace.yaml package.json
```

### **Development Workflow per Agent OS**

```bash
# 1. Setup iniziale (ZERO-CONFIG)
pnpm setup            # Auto-installa tutto in 8s vs 45s

# 2. Development
pnpm dev              # Full-stack development
pnpm dev:frontend     # Frontend only (PNPM)
pnpm dev:backend      # Backend only (UV)
pnpm dev:bun          # Frontend with BUN runtime

# 3. Testing
pnpm test             # Full test suite
pnpm test:frontend    # Frontend tests (Vitest)
pnpm test:backend     # Backend tests (pytest)

# 4. Building
pnpm build            # Production build
pnpm build:frontend   # Frontend only
pnpm build:backend    # Backend only

# 5. Maintenance
pnpm clean:all        # Complete cleanup
pnpm reset            # Clean + setup
```

---

## 🛠️ **Tool-Specific Instructions**

### **UV (Python Package Manager)**

```bash
# Dependency management
uv add <package>           # Add dependency
uv add <package> --group dev  # Add dev dependency
uv remove <package>        # Remove dependency
uv sync                    # Sync with pyproject.toml
uv lock                    # Update lock file

# Virtual environment (AUTO-MANAGED)
# UV automatically detects and creates .venv
# No manual activation needed!

# Run scripts
uv run python script.py   # Auto-activates venv
uv run pytest             # Auto-activates venv
```

### **PNPM (Frontend Package Manager)**

```bash
# Workspace commands
pnpm --filter frontend <command>  # Run command in frontend
pnpm -r <command>                 # Run in all workspaces
pnpm --filter frontend add <pkg>  # Add to specific workspace

# Catalog management
pnpm catalog              # Show catalog versions
pnpm update               # Update all dependencies

# Performance monitoring
pnpm store path           # Show store location
pnpm store prune          # Clean unused packages
```

### **BUN (Optional Ultra-Fast Runtime)**

```bash
# Installation check
bun --version

# Development with BUN
bun run frontend/src/main.tsx     # Direct file execution
bunx vite                         # Use BUN with Vite
pnpm dev:bun                      # Use via PNPM script

# Package management (alternative)
bun install                       # Alternative to pnpm install
bun add <package>                 # Alternative to pnpm add
```

---

## 📊 **Performance Monitoring per Agent OS**

### **Benchmarking Commands**

```bash
# Timing setup (for comparison)
time pnpm setup           # Should be ~8s

# Monitor disk usage
du -sh node_modules .venv pnpm-lock.yaml uv.lock

# Development performance
time pnpm build           # Should be ~9s vs 25s before
time pnpm test            # Monitor test performance
```

### **Expected Performance Metrics**

| **Operation** | **Target Time** | **Previous Time** | **Speedup** |
| ------------- | --------------- | ----------------- | ----------- |
| Setup         | 8s              | 45s               | 5.6x        |
| Install       | 4s              | 30s               | 7.5x        |
| Build         | 9s              | 25s               | 2.8x        |
| Hot Reload    | 200ms           | 800ms             | 4x          |

---

## 🚨 **Troubleshooting per Agent OS**

### **Common Issues & Solutions**

1. **Tool Not Found**

   ```bash
   # Install missing tools
   curl -LsSf https://astral.sh/uv/install.sh | sh
   npm install -g pnpm
   ```

2. **Old Dependencies Conflict**

   ```bash
   # Complete reset
   pnpm clean:all
   rm -rf .venv node_modules
   pnpm setup
   ```

3. **Performance Regression**

   ```bash
   # Check if using old tools
   which pip python npm node
   # Should use: uv, pnpm, optionally bun
   ```

4. **Lock File Issues**
   ```bash
   # Regenerate lock files
   rm uv.lock pnpm-lock.yaml
   pnpm install
   uv sync
   ```

### **Health Check Script**

```bash
# Run automated validation
python test_modern_setup.py

# Expected output:
# 🎉 All tests passed! Modern setup is working correctly.
```

---

## 📁 **File Structure per Agent OS**

### **Root Level Files**

```
agentic-rag-knowledge-graph/
├── pyproject.toml              # Python project config (replaces requirements.txt)
├── uv.lock                     # Python dependency lock file
├── .uvrc                       # UV configuration
├── pnpm-workspace.yaml         # PNPM workspace config
├── package.json                # Root package.json with unified scripts
├── pnpm-lock.yaml             # PNPM lock file
├── bun.lockb                  # BUN lock file (if using BUN)
├── MIGRATION_GUIDE.md         # Complete migration guide
└── test_modern_setup.py       # Validation script
```

### **Configuration Priorities**

1. **pyproject.toml** - Source of truth for Python dependencies
2. **pnpm-workspace.yaml** - Defines workspace structure
3. **package.json (root)** - Unified development scripts
4. **frontend/package.json** - Frontend-specific config with catalog refs

---

## 🎯 **Agent OS Best Practices**

### **When Working on Backend**

```bash
# Always use UV for Python operations
uv run python script.py        # Instead of: python script.py
uv add dependency              # Instead of: pip install dependency
uv sync                        # Sync environment

# Check UV is managing venv
echo $VIRTUAL_ENV              # Should show .venv path
```

### **When Working on Frontend**

```bash
# Always use PNPM for Node operations
pnpm dev:frontend              # Instead of: cd frontend && npm run dev
pnpm --filter frontend add pkg # Instead of: cd frontend && npm add pkg

# For maximum speed, optionally use BUN
pnpm dev:bun                   # 2-4x faster runtime
```

### **When Making Changes**

```bash
# After modifying dependencies
uv sync                        # For Python changes
pnpm install                   # For frontend changes

# Before committing
pnpm lint:fix                  # Auto-fix linting
pnpm test                      # Run full test suite
pnpm build                     # Verify production build
```

---

## 📚 **Additional Resources per Agent OS**

- **Migration Guide**: `MIGRATION_GUIDE.md` - Complete transition guide
- **Performance Benchmarks**: `.agent-os/milestone-4-completion-report.md`
- **Project Status**: `.agent-os/project-status.md` - Updated with modernization
- **Roadmap**: `.agent-os/product/ROADMAP.md` - Phase 2 completed

### **External Documentation**

- **UV**: https://docs.astral.sh/uv/
- **PNPM**: https://pnpm.io/
- **BUN**: https://bun.sh/docs
- **pyproject.toml**: https://peps.python.org/pep-0621/

---

**Last Updated**: 2025-01-19  
**Agent OS Compatibility**: Full support for modern tooling workflow  
**Status**: ✅ **Production Ready with Modern Stack**
