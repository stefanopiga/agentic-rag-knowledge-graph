# Architettura Frontend FisioRAG

## Stato Implementazione

### ✅ MILESTONE 3 COMPLETATA ✅

#### 1. **Setup Base e Configurazione**

- React 18 + TypeScript + Vite ✅
- pnpm come package manager ✅
- Tailwind CSS 4.x con @tailwindcss/postcss ✅
- PostCSS config aggiornata ✅
- TypeScript strict mode con verbatimModuleSyntax ✅
- Alias @/ configurato correttamente ✅

#### 2. **State Management Completo**

- Zustand stores implementati e funzionanti:
  - `useAuthStore` - Autenticazione e multi-tenancy ✅
  - `useChatStore` - Gestione chat e messaggi ✅
  - `useTenantStore` - Metriche e dati tenant ✅
- **CORREZIONE**: Risolto conflitto `refreshToken` → `refreshAuthToken` ✅

#### 3. **API Integration**

- `apiClient` - HTTP client con interceptors ✅
- `authService` - Autenticazione completa ✅
- `chatService` - Chat e sessioni ✅
- `tenantService` - Gestione tenant ✅
- `wsService` - WebSocket real-time con reconnection ✅

#### 4. **TypeScript Types**

- `types/api.ts` - Interface API backend ✅
- `types/chat.ts` - Types per chat system ✅
- `types/tenant.ts` - Types per multi-tenancy ✅
- **CORREZIONE**: Import types con `type` keyword per verbatimModuleSyntax ✅

#### 5. **Componenti UI Base Implementati**

- `src/components/ui/Button.tsx` ✅
- `src/components/ui/Input.tsx` ✅
- `src/components/ui/Modal.tsx` ✅
- `src/components/ui/Spinner.tsx` ✅

#### 6. **Componenti Chat Implementati**

- `src/components/chat/ChatInterface.tsx` ✅
- `src/components/chat/MessageBubble.tsx` ✅
- `src/components/chat/MessageInput.tsx` ✅
- `src/components/chat/SourceCitation.tsx` ✅
- `src/components/chat/TypingIndicator.tsx` ✅

#### 7. **Pagine Base Implementate**

- `src/pages/ChatPage.tsx` ✅
- `src/pages/LoginPage.tsx` ✅

#### 8. **Routing System Completo**

- React Router 7.x setup ✅
- Protected routes con `ProtectedRoute` component ✅
- Public routes con `PublicRoute` component ✅
- Layout components con `AppLayout` ✅
- Navigazione automatica e redirect ✅

#### 9. **Dipendenze Aggiornate**

- **Frontend** (`package.json`):
  - react-router-dom: ^7.7.1 ✅
  - @tailwindcss/postcss: 4.1.11 ✅
- **Backend** (`requirements.txt`): Già completo ✅

## Architettura Stores

### AuthStore (Implementato e Corretto)

```typescript
interface AuthStore extends AuthState, AuthActions {
  // State
  user: User | null;
  tenant: Tenant | null;
  token: string | null;
  refreshToken: string | null; // TOKEN STATE
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  login: (credentials) => Promise<void>;
  logout: () => void;
  selectTenant: (tenantId) => Promise<void>;
  refreshAuthToken: () => Promise<void>; // RINOMINATO per evitare conflitto
  setLoading: (loading: boolean) => void;
}
```

**CORREZIONE IMPORTANTE**: Il metodo `refreshToken()` è stato rinominato in `refreshAuthToken()` per evitare conflitto con la proprietà state `refreshToken`.

### ChatStore (Implementato)

```typescript
interface ChatStore {
  // State
  messages: ChatMessage[];
  currentSession: string | null;
  isLoading: boolean;
  isConnected: boolean;

  // Actions
  sendMessage: (content) => Promise<void>;
  loadSession: (sessionId) => Promise<void>;
  appendMessageChunk: (chunk) => void;
  completeMessage: (data) => void;
}
```

## API Services Architecture

### Struttura Completa

- `apiClient` - Base HTTP client con token refresh
- `authService` - Login, logout, tenant selection
- `chatService` - Messaggi, sessioni, export
- `tenantService` - Metriche, documenti, settings
- `wsService` - WebSocket real-time con reconnection

### Error Handling

- Automatic token refresh su 401
- Logout automatico su refresh failure
- Error boundaries per componenti
- Toast notifications per errori

## Code Style Standard

### TypeScript Rules

- Strict mode abilitato
- Double quotes per strings
- Trailing commas
- 2-space indentation
- Import paths relativi con alias `@/`

### Naming Conventions

- PascalCase per componenti React
- camelCase per funzioni e variabili
- kebab-case per file CSS/directories
- SCREAMING_SNAKE_CASE per costanti

## Performance Optimization

### Implementato

- Code splitting con lazy loading
- Bundle optimization con Vite
- Zustand persistence per auth
- Connection pooling per API

### Da Implementare

- Virtual scrolling per chat history
- Image lazy loading
- Service Worker per caching
- React Query per API caching

## Security Implementation

### Implementato

- Token-based authentication
- Automatic token refresh
- Multi-tenant data isolation
- Input sanitization preparata

### Da Implementare

- CSP headers
- XSS protection
- CSRF protection
- Rate limiting UI feedback

## ❓ PROBLEMI ATTUALI E INTERROGATIVI

### 🚨 Problema Critico: Tailwind CSS 4.x Configurazione

**Errore attuale**:

```
Error: Cannot apply unknown utility class `text-text-primary`.
Are you using CSS modules or similar and missing @reference?
```

**Possibili cause**:

1. **Tailwind CSS 4.x Compatibility**: Le classi custom definite in `tailwind.config.js` non vengono riconosciute
2. **PostCSS Configuration**: Il plugin `@tailwindcss/postcss` potrebbe non leggere correttamente la configurazione
3. **CSS Variables vs Classes**: Conflitto tra variabili CSS (--text-primary) e classi Tailwind (text-text-primary)

**Strategie di risoluzione da testare**:

#### A. **Downgrade a Tailwind CSS 3.x** (Soluzione Conservativa)

```bash
pnpm remove tailwindcss @tailwindcss/postcss
pnpm add -D tailwindcss@^3.4.0 @tailwindcss/typography
# Ripristinare postcss.config.js classico
```

#### B. **Aggiornare configurazione per Tailwind 4.x** (Soluzione Moderna)

- Verificare documentazione Tailwind CSS 4.x per custom colors
- Utilizzare solo variabili CSS native invece di extend config
- Testare approccio @import tailwindcss/theme

#### C. **Approccio CSS-in-JS** (Soluzione Alternativa)

- Migrare a styled-components o emotion
- Mantenere design system in JavaScript

### 🔍 Test Necessari

1. **Verifica funzionamento base**:

   - Il server Vite si avvia? ✅ (porta 3001)
   - I componenti React vengono compilati? ❌ (errore CSS)
   - Il routing funziona? ⏳ (dipende da risoluzione CSS)

2. **Verifica integrazione backend**:
   - Stores Zustand funzionano? ✅ (logica implementata)
   - API calls vengono eseguite? ⏳ (da testare con backend)
   - WebSocket connection? ⏳ (da testare con backend)

### 📋 Next Steps Consigliati

1. **PRIORITÀ ALTA**: Risolvere configurazione Tailwind CSS
2. **TEST**: Verificare che almeno una pagina si carichi correttamente
3. **INTEGRATION**: Testare comunicazione frontend-backend
4. **DEPLOYMENT**: Preparare build di produzione

**DOMANDA APERTA**: Quale approccio preferire per risolvere il problema Tailwind CSS 4.x? La migrazione a v4 offre benefici significativi ma introduce complessità di configurazione.
