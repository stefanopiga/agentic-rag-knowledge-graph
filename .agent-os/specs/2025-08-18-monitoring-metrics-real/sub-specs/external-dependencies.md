# External Dependencies

This specification requires new external dependencies for system monitoring and metrics collection.

## New Dependencies Required

- **psutil** (>=5.9.0) - System and process monitoring library
  - **Justification:** Standard library per memory usage, CPU usage, system stats monitoring con API cross-platform
  - **Usage:** Memory usage del processo, CPU usage, system resource monitoring per health endpoint

## Installation Commands

```bash
pip install psutil>=5.9.0
```

## Configuration Requirements

- **Resource Sampling**: Configurare sampling rate per expensive metrics (memory, CPU) per evitare performance impact
- **Metric Collection Frequency**: Limitare frequency di metric collection (es. ogni 30 secondi) per balance tra accuracy e overhead
- **Error Handling**: Implementare fallback se psutil non disponibile (skip system metrics, log warning)