# Frontend Package Manager Configuration

## Package Manager: pnpm

Il progetto frontend utilizza **pnpm** come package manager invece di npm per:

- **Performance**: Installazioni più veloci
- **Efficienza spazio**: Deduplicazione delle dipendenze
- **Sicurezza**: Migliore gestione delle dipendenze

## Comandi Standard

### Installazione

```cmd
venv\Scripts\activate && cd frontend && pnpm install
```

### Sviluppo

```cmd
venv\Scripts\activate && cd frontend && pnpm run dev
```

### Build

```cmd
venv\Scripts\activate && cd frontend && pnpm run build
```

### Test

```cmd
venv\Scripts\activate && cd frontend && pnpm run test
```

### Aggiungere Dipendenze

```cmd
venv\Scripts\activate && cd frontend && pnpm add [package]
venv\Scripts\activate && cd frontend && pnpm add -D [dev-package]
```

## Configurazione Progetto

Il frontend segue questa struttura con pnpm:

```
frontend/
├── package.json          # Configurazione pnpm
├── pnpm-lock.yaml       # Lock file pnpm
├── vite.config.ts       # Configurazione Vite
├── tailwind.config.js   # Configurazione Tailwind CSS
├── src/                 # Codice sorgente
│   ├── components/      # Componenti React
│   ├── pages/          # Pagine applicazione
│   ├── services/       # API services
│   ├── stores/         # Zustand stores
│   ├── types/          # TypeScript types
│   └── utils/          # Utility functions
├── public/              # Asset statici
└── dist/                # Build output
```

## Dipendenze Installate (Aggiornate)

### Production Dependencies

- `react` ^19.1.1 + `react-dom` ^19.1.1 - Framework React 19
- `tailwindcss` ^4.1.11 + `postcss` ^8.5.6 + `autoprefixer` ^10.4.21 - Styling
- `@tailwindcss/typography` ^0.5.16 - Typography plugin
- `react-router-dom` ^7.7.1 - **NUOVO**: Routing system
- `zustand` ^5.0.7 - State management
- `axios` ^1.11.0 - HTTP client
- `socket.io-client` ^4.8.1 - WebSocket client

### Development Dependencies

- `@tailwindcss/postcss` 4.1.11 - **NUOVO**: Plugin PostCSS per Tailwind 4.x
- `@types/node` ^24.2.0 - Node.js types
- `@types/react` ^19.1.9 + `@types/react-dom` ^19.1.7 - React types
- `@vitejs/plugin-react` ^4.7.0 - Plugin Vite per React
- `typescript` ~5.8.3 + `typescript-eslint` ^8.39.0 - TypeScript
- `vite` ^7.1.0 - Build tool
- `vitest` ^3.2.4 - Testing framework
- `@testing-library/react` ^16.3.0 + `@testing-library/jest-dom` ^6.6.4 - Testing utilities
- `eslint` ^9.32.0 + plugins - Linting

### ⚠️ Problemi Configurazione Tailwind CSS 4.x

**Stato attuale**: Tailwind CSS 4.x con @tailwindcss/postcss installato ma con errori di configurazione.

**Errore**: Classi custom come `text-text-primary` non riconosciute.

**Possibili soluzioni**:
1. Downgrade a Tailwind CSS 3.4.x
2. Aggiornare configurazione per compatibilità 4.x
3. Utilizzare solo variabili CSS native

## Note Agent OS

- **SEMPRE** usare pnpm invece di npm per il frontend
- **MANTENERE** l'attivazione dell'ambiente virtuale Python
- **VERIFICARE** che pnpm sia installato globalmente sul sistema
