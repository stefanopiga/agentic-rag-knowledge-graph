# Stage 1: Build delle dipendenze con UV
FROM python:3.13-slim AS builder

WORKDIR /app

# Installa le dipendenze di sistema necessarie per UV e build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Installa UV - ultra-fast Python package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    mv /root/.local/bin/uv /usr/local/bin/uv && \
    mv /root/.local/bin/uvx /usr/local/bin/uvx

# Configura UV per usare cache globale
ENV UV_CACHE_DIR=/opt/uv-cache

# Copia tutto il codice sorgente necessario per installazione editable
COPY . .

# Installa le dipendenze come nel setup locale funzionante
RUN uv venv .venv && \
    uv pip install -e .

# Stage 2: Immagine finale ottimizzata
FROM python:3.13-slim

WORKDIR /app

# Installa solo le dipendenze runtime necessarie
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia UV e UVX dal builder stage (più efficiente)
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /usr/local/bin/uvx /usr/local/bin/uvx

# Copia l'ambiente virtuale UV dallo stage di build
COPY --from=builder /app/.venv /app/.venv

# Attiva l'ambiente virtuale UV
ENV PATH="/app/.venv/bin:$PATH"

# Copia tutto il codice sorgente
COPY . .

# Configura variabili ambiente per produzione
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

# Esponi la porta API
EXPOSE 8000

# Copia file di configurazione environment di esempio
COPY .env.example /app/.env.example

# Script di avvio ottimizzato per production
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Health check per Docker Swarm/Kubernetes
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Entrypoint che gestisce le variabili d'ambiente
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Comando ottimizzato per produzione con UV
CMD ["uv", "run", "uvicorn", "agent.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
