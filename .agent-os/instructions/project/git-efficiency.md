# Git Efficiency Guide per FisioRAG Project

## Overview

Guida per operazioni Git efficienti nel progetto FisioRAG, ottimizzata per Windows e Agent OS workflows.

## Quick Commands Reference

### Status Check Rapido
```cmd
# Status compatto
git status -s

# Branch corrente
git branch --show-current

# Ultimo commit
git log --oneline -1
```

### Operazioni Standard

#### Workflow Completo in 4 Comandi
```cmd
git add .
git commit -m "feat: implement specific feature"
git push origin HEAD
git status -s
```

#### Branch Management
```cmd
# Creare feature branch
git checkout -b feature/task-name

# Switch a main
git checkout main

# Delete merged branch
git branch -d feature/task-name
```

## Project-Specific Workflows

### Per Task Agent OS
```cmd
# 1. Check environment
git branch --show-current
git status -s

# 2. Implement changes
# [development work]

# 3. Commit and push
git add .
git commit -m "feat: complete [TASK_NAME] from roadmap"
git push origin HEAD
```

### Per Hotfix
```cmd
# 1. Branch da main
git checkout main
git pull origin main
git checkout -b hotfix/issue-description

# 2. Fix and commit
git add .
git commit -m "fix: resolve issue description"
git push origin HEAD
```

### Per Feature Development
```cmd
# 1. Feature branch
git checkout -b feature/component-name

# 2. Iterative commits
git add specific-files
git commit -m "feat: add component foundation"

git add more-files
git commit -m "feat: implement component logic"

# 3. Push quando ready
git push origin HEAD
```

## FisioRAG Specific Patterns

### Frontend Changes
```cmd
# Typical frontend workflow
cd frontend
npm run lint
npm run type-check
cd ..

git add frontend/
git commit -m "feat: implement UI component"
git push origin HEAD
```

### Backend API Changes
```cmd
# Activate venv first (always!)
venv\Scripts\activate && python -m pytest tests/
venv\Scripts\activate && python -m ruff check .

git add agent/ ingestion/
git commit -m "feat: implement API endpoint"
git push origin HEAD
```

### Database Schema Changes
```cmd
git add sql/ scripts/
git commit -m "feat: update database schema"
git push origin HEAD
```

### Documentation Updates
```cmd
git add README.md docs/ .agent-os/
git commit -m "docs: update project documentation"
git push origin HEAD
```

## Commit Message Conventions

### Types
- `feat:` - Nuova feature
- `fix:` - Bug fix
- `docs:` - Solo documentazione
- `style:` - Formatting, no logic change
- `refactor:` - Code refactoring
- `test:` - Test aggiornati
- `chore:` - Build, dipendenze, config

### Examples per FisioRAG
```
feat: implement knowledge graph ingestion pipeline
fix: resolve Neo4j connection timeout issue
docs: update Agent OS workflow documentation
chore: update GitHub Actions CI/CD pipeline
test: add integration tests for RAG system
refactor: optimize vector similarity search
style: format Python code with black
```

## Error Prevention

### Pre-commit Checklist
```cmd
# 1. Virtual environment active?
echo %VIRTUAL_ENV%

# 2. No linting errors?
venv\Scripts\activate && ruff check .

# 3. Tests passing?
venv\Scripts\activate && pytest tests/ -x

# 4. Clean git status?
git status -s
```

### Common Mistake Prevention

#### ❌ Evitare
```cmd
# Commit senza test
git commit -m "fix: something" # senza verificare

# Messaggi generici
git commit -m "update"
git commit -m "fixes"

# Push forzato
git push --force

# Commit di file temp/cache
git add __pycache__/
git add node_modules/
```

#### ✅ Preferire
```cmd
# Commit dopo verifica
venv\Scripts\activate && pytest tests/ -x
git add .
git commit -m "fix: resolve authentication token validation"

# Messaggi specifici
git commit -m "feat: add document chunking optimization"

# Push standard
git push origin HEAD

# Ignorare file temp (in .gitignore)
```

## Integration con Agent OS

### Task Execution Pattern
```cmd
# Pattern standard per completare task da roadmap
git checkout main
git pull origin main
git checkout -b task/roadmap-item-name

# [implement task]

git add .
git commit -m "feat: complete [TASK] - [brief description]"
git push origin HEAD

# [create PR if needed]
```

### Roadmap Update Pattern
```cmd
# Quando si aggiorna la roadmap
git add .agent-os/product/ROADMAP.md
git commit -m "docs: update roadmap with completed task"
git push origin HEAD
```

## Performance Tips

### Faster Operations
```cmd
# Skip hooks per commit rapidi (solo quando sicuri)
git commit --no-verify -m "feat: safe commit"

# Amend ultimo commit invece di nuovo commit
git add .
git commit --amend --no-edit

# Stash rapido per switch branch
git stash
git checkout other-branch
git stash pop
```

### Batch Operations
```cmd
# Multiple files, single commit
git add file1 file2 file3
git commit -m "feat: implement related changes"

# Directory-specific commits
git add frontend/
git commit -m "feat: update frontend components"
git add agent/
git commit -m "feat: update backend API"
```

Questa guida assicura workflow Git veloci e affidabili per il progetto FisioRAG.
