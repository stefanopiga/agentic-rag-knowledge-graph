#!/bin/bash
set -e

# FisioRAG Docker Production Entrypoint
# Gestisce variabili d'ambiente e validazione per deployment

echo "🚀 FisioRAG Production Container Starting..."

# Verifica variabili d'ambiente critiche
check_env_var() {
    local var_name="$1"
    local var_value="${!var_name}"
    
    if [ -z "$var_value" ]; then
        echo "❌ Error: $var_name environment variable not set"
        echo "📝 Please set required environment variables. See .env.example"
        return 1
    fi
    echo "✅ $var_name configured"
}

# Verifica variabili d'ambiente opzionali con defaults
set_default_env() {
    local var_name="$1"
    local default_value="$2"
    
    if [ -z "${!var_name}" ]; then
        export "$var_name"="$default_value"
        echo "🔧 $var_name set to default: $default_value"
    else
        echo "✅ $var_name configured: ${!var_name}"
    fi
}

echo "🔍 Checking environment configuration..."

# Variabili critiche (required)
if ! check_env_var "DATABASE_URL" || \
   ! check_env_var "NEO4J_URI" || \
   ! check_env_var "NEO4J_USER" || \
   ! check_env_var "NEO4J_PASSWORD" || \
   ! check_env_var "LLM_API_KEY"; then
    echo ""
    echo "💡 Quick setup for development:"
    echo "docker run -e DATABASE_URL=postgresql://... -e NEO4J_URI=bolt://... -e LLM_API_KEY=sk-... fisiorag:uv-modern"
    echo ""
    echo "💡 For production, create .env file with all required variables"
    exit 1
fi

# Variabili opzionali con defaults
set_default_env "REDIS_URL" "redis://localhost:6379"
set_default_env "APP_ENV" "production"
set_default_env "APP_HOST" "0.0.0.0"
set_default_env "APP_PORT" "8000"
set_default_env "LOG_LEVEL" "INFO"
set_default_env "LLM_PROVIDER" "openai"
set_default_env "LLM_CHOICE" "gpt-4o-mini"
set_default_env "EMBEDDING_PROVIDER" "openai"
set_default_env "EMBEDDING_MODEL" "text-embedding-3-small"
set_default_env "VECTOR_DIMENSION" "1536"

# Test connessioni database (opzionale, non blocking)
echo "🔌 Testing database connections..."

# Test PostgreSQL connection
if command -v pg_isready >/dev/null 2>&1; then
    if ! pg_isready -d "$DATABASE_URL" -t 5; then
        echo "⚠️  Warning: PostgreSQL connection test failed"
    else
        echo "✅ PostgreSQL connection OK"
    fi
fi

echo "🎯 Environment validated successfully!"
echo "🚀 Starting FisioRAG application..."

# Se il venv montato è vuoto (volume appena creato), inizializzalo dalla snapshot
if [ ! -d "/app/.venv/bin" ] || [ -z "$(ls -A /app/.venv 2>/dev/null)" ]; then
  echo "🧩 Initializing virtualenv in /app/.venv from image snapshot..."
  rm -rf /app/.venv
  cp -a /opt/app-venv /app/.venv
fi

# Esegui il comando passato
exec "$@"
