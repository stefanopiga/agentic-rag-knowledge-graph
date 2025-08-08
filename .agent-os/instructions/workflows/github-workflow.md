# GitHub Workflow Best Practices per Agent OS

## Panoramica

Questa guida fornisce procedure ottimizzate per il workflow GitHub su Windows, evitando errori comuni con virgolette, caratteri speciali e comandi multilinea.

## Ambiente Windows - Problemi Comuni

### ❌ PROBLEMI FREQUENTI:
- Messaggio di commit multilinea con virgolette
- Comandi PowerShell con escape characters complessi
- Terminal bloccato nel pager (git branch, git log)
- Encoding line endings (LF vs CRLF)

### ✅ SOLUZIONI OTTIMIZZATE:

## Workflow Git Ottimizzato

### 1. Checking Status e Branch

```cmd
# Status rapido
git status --porcelain

# Branch corrente (evita pager)
git branch --show-current

# Lista branch (formato compatto)
git branch --format="%(refname:short)"
```

### 2. Staging e Commit

```cmd
# Staging
git add .

# Commit con messaggio semplice (SEMPRE single-line)
git commit -m "feat: implement feature description"

# Alternative per commit complessi
git commit -m "feat: implement CI/CD pipeline optimization"
```

### 3. Push e Branch Management

```cmd
# Push branch corrente
git push origin HEAD

# Creare e switch branch
git checkout -b feature-branch-name

# Switch branch esistente
git checkout branch-name
```

### 4. Commit Message Standards

#### ✅ FORMATO CORRETTO:
```
type: brief description (max 50 chars)

Examples:
- feat: add CI/CD pipeline
- fix: resolve authentication issue  
- docs: update API documentation
- chore: update dependencies
```

#### ❌ EVITARE:
```cmd
# NON usare messaggi multilinea in PowerShell
git commit -m "feat: implement something
- with multiple lines
- that break on Windows"

# NON usare virgolette annidate complesse
```

## Workflow GitHub Actions

### 1. Test Locale Pre-Push

```cmd
# Verificare che il workspace sia pulito
git status --porcelain

# Test rapido (se disponibile)
npm test --silent
```

### 2. Sequenza Push Ottimizzata

```cmd
# 1. Status check
git status --porcelain

# 2. Add changes
git add .

# 3. Commit (single line)
git commit -m "feat: implement feature name"

# 4. Push
git push origin HEAD
```

### 3. Branch e Pull Request

```cmd
# Creare feature branch
git checkout -b feature/task-name

# Dopo sviluppo, push
git push origin feature/task-name

# URL PR viene mostrato automaticamente nel terminal
```

## Gestione Errori Comuni

### Terminal Bloccato nel Pager

**Problema**: `git branch` o `git log` bloccano il terminal

**Soluzione**:
```cmd
# Usare flag --no-pager
git --no-pager branch
git --no-pager log --oneline -10

# O configurare globally
git config --global pager.branch false
```

### Problemi Line Endings

**Problema**: Warning "LF will be replaced by CRLF"

**Soluzione**:
```cmd
# Configurazione una volta
git config core.autocrlf true
```

### PowerShell Escape Issues

**Problema**: Caratteri speciali nei comandi

**Soluzione**:
```cmd
# Preferire cmd standard per Git
# Evitare powershell -Command per Git operations

# ✅ BUONO
git commit -m "feat: add feature"

# ❌ EVITARE  
powershell -Command "git commit -m 'complex message with issues'"
```

## Workflow Automatizzato Agent OS

### Sequenza Tipo per Task Completion

```cmd
# 1. Check current status
git status --porcelain
git branch --show-current

# 2. Add all changes
git add .

# 3. Simple commit
git commit -m "feat: complete task name"

# 4. Push current branch
git push origin HEAD
```

### Multi-commit Workflow

Se il task richiede più commit:

```cmd
# Commit incrementali
git add specific-files
git commit -m "feat: implement component A"

git add other-files  
git commit -m "feat: implement component B"

# Push finale
git push origin HEAD
```

## GitHub Actions Integration

### Verificare Workflow Success

```cmd
# Controllare se il push ha triggerato GitHub Actions
# URL del workflow viene mostrato nel push output

# Verificare status online:
# https://github.com/USER/REPO/actions
```

### Debug CI/CD Issues

```cmd
# Se CI fallisce, controllare locally:
npm run lint     # Frontend linting
pytest           # Python tests (con venv attivo)
docker build .   # Build test
```

## Best Practices Riassunto

### ✅ DO:
- Usare messaggi commit single-line
- Preferire `git push origin HEAD` 
- Controllare status prima di ogni operazione
- Usare branch nomi descrittivi
- Committare frequentemente con messaggi chiari

### ❌ DON'T:
- Messaggi commit multilinea in Windows
- Comandi PowerShell complessi per Git
- Commit massivi con troppi cambiamenti
- Branch nomi generici (feature, fix, update)
- Skip dei controlli pre-push

## Troubleshooting Rapido

### Comando Bloccato
**Soluzione**: `Ctrl+C` e retry con flag `--no-pager`

### Push Rejected  
**Soluzione**: `git pull origin branch-name` poi `git push origin HEAD`

### Merge Conflicts
**Soluzione**: Risolvere manualmente, poi `git add .` e `git commit -m "resolve merge conflicts"`

### Commit Message Sbagliato
**Soluzione**: `git commit --amend -m "new message"` (solo se non ancora pushato)

Questa guida garantisce workflow Git affidabili e rapidi su Windows per Agent OS.
