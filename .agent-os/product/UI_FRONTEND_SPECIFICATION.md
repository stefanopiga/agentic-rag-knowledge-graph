# Specifica Tecnica: Interfaccia Utente Frontend per Sistema RAG Medico

## Panoramica

Sviluppo di un'interfaccia utente web moderna per il sistema RAG agentic multi-tenant FisioRAG, implementando un frontend responsive e intuitivo per interazione con l'agente AI medico.

### Obiettivi Primari

- Interfaccia chat conversazionale per interazione con l'agente AI
- Dashboard tenant per gestione documenti e sessioni
- Sistema di autenticazione e autorizzazione multi-tenant
- Visualizzazione risultati di ricerca con citazioni mediche
- Monitoraggio performance e utilizzo risorse

---

## Architettura Frontend

### Stack Tecnologico

- **Framework**: React 18 con TypeScript
- **Build Tool**: Vite per development rapido
- **Styling**: Tailwind CSS + Shadcn/ui components
- **State Management**: Zustand per stato globale
- **HTTP Client**: Axios con interceptors per auth
- **WebSocket**: Socket.io-client per chat real-time
- **Testing**: Vitest + React Testing Library

### Struttura Directory

```
frontend/
├── src/
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── SourceCitation.tsx
│   │   │   └── TypingIndicator.tsx
│   │   ├── dashboard/
│   │   │   ├── TenantDashboard.tsx
│   │   │   ├── DocumentManager.tsx
│   │   │   ├── SessionHistory.tsx
│   │   │   └── AnalyticsPanel.tsx
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── TenantSelector.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   └── ui/
│   │       ├── Button.tsx
│   │       ├── Input.tsx
│   │       ├── Modal.tsx
│   │       └── Spinner.tsx
│   ├── pages/
│   │   ├── ChatPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── LoginPage.tsx
│   │   └── DocumentsPage.tsx
│   ├── services/
│   │   ├── api.ts
│   │   ├── websocket.ts
│   │   └── auth.ts
│   ├── stores/
│   │   ├── authStore.ts
│   │   ├── chatStore.ts
│   │   └── tenantStore.ts
│   ├── types/
│   │   ├── api.ts
│   │   ├── chat.ts
│   │   └── tenant.ts
│   └── utils/
│       ├── formatters.ts
│       ├── validators.ts
│       └── constants.ts
├── public/
├── tests/
└── docs/
```

---

## Componenti Core

### 1. Chat Interface

**File**: `src/components/chat/ChatInterface.tsx`

#### Funzionalità

- Input message con markdown support
- Display messaggi con formattazione medica
- Citazioni fonti interattive
- Typing indicators durante elaborazione AI
- History conversazione persistente

#### Implementazione

```typescript
interface ChatMessage {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: Date;
  sources?: Source[];
  toolCalls?: ToolCall[];
}

interface Source {
  title: string;
  page?: number;
  relevanceScore: number;
  excerpt: string;
}

const ChatInterface: React.FC = () => {
  const { messages, sendMessage, isLoading } = useChatStore();
  const { tenant } = useAuthStore();

  // WebSocket connection per real-time updates
  const { socket } = useWebSocket(`/chat/${tenant.id}`);

  return (
    <div className="flex flex-col h-full">
      <ChatHistory messages={messages} />
      <MessageInput onSend={sendMessage} disabled={isLoading} />
    </div>
  );
};
```

#### Features Avanzate

- **Markdown Rendering**: Supporto per formattazione medica
- **Source Preview**: Modal per anteprima documenti citati
- **Message Export**: Export conversazioni in PDF/Word
- **Search History**: Ricerca nelle conversazioni precedenti

### 2. Tenant Dashboard

**File**: `src/components/dashboard/TenantDashboard.tsx`

#### Metriche Display

- Documenti ingeriti per tenant
- Query eseguite (ultimi 30 giorni)
- Performance tempi risposta
- Utilizzo storage database

#### Analytics Panel

```typescript
interface TenantMetrics {
  documentsCount: number;
  queriesCount: number;
  avgResponseTime: number;
  storageUsed: number;
  activeUsers: number;
}

const AnalyticsPanel: React.FC = () => {
  const { metrics } = useTenantStore();

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <MetricCard
        title="Documenti"
        value={metrics.documentsCount}
        icon={DocumentIcon}
      />
      <MetricCard
        title="Query (30gg)"
        value={metrics.queriesCount}
        icon={SearchIcon}
      />
      <MetricCard
        title="Tempo Risposta"
        value={`${metrics.avgResponseTime}ms`}
        icon={ClockIcon}
      />
    </div>
  );
};
```

### 3. Document Manager

**File**: `src/components/dashboard/DocumentManager.tsx`

#### Upload Documents

- Drag & drop interface per file DOCX
- Progress tracking per upload
- Preview estratto documento
- Status ingestione real-time

#### Document Library

```typescript
interface Document {
  id: string;
  title: string;
  filename: string;
  uploadedAt: Date;
  status: "uploading" | "processing" | "completed" | "error";
  chunksCount?: number;
  fileSize: number;
}

const DocumentManager: React.FC = () => {
  const { documents, uploadDocument, deleteDocument } = useDocumentStore();

  return (
    <div className="space-y-6">
      <UploadZone onUpload={uploadDocument} />
      <DocumentList documents={documents} onDelete={deleteDocument} />
    </div>
  );
};
```

---

## State Management

### Auth Store

**File**: `src/stores/authStore.ts`

```typescript
interface AuthState {
  user: User | null;
  tenant: Tenant | null;
  token: string | null;
  isAuthenticated: boolean;
}

interface AuthActions {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  selectTenant: (tenantId: string) => Promise<void>;
  refreshToken: () => Promise<void>;
}

export const useAuthStore = create<AuthState & AuthActions>((set, get) => ({
  user: null,
  tenant: null,
  token: localStorage.getItem("token"),
  isAuthenticated: false,

  login: async (credentials) => {
    const response = await authService.login(credentials);
    set({
      user: response.user,
      tenant: response.tenant,
      token: response.token,
      isAuthenticated: true,
    });
    localStorage.setItem("token", response.token);
  },

  logout: () => {
    set({ user: null, tenant: null, token: null, isAuthenticated: false });
    localStorage.removeItem("token");
  },
}));
```

### Chat Store

**File**: `src/stores/chatStore.ts`

```typescript
interface ChatState {
  messages: ChatMessage[];
  currentSession: string | null;
  isLoading: boolean;
  error: string | null;
}

interface ChatActions {
  sendMessage: (content: string) => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState & ChatActions>((set, get) => ({
  messages: [],
  currentSession: null,
  isLoading: false,
  error: null,

  sendMessage: async (content) => {
    const { tenant } = useAuthStore.getState();
    set({ isLoading: true, error: null });

    try {
      const userMessage: ChatMessage = {
        id: generateId(),
        content,
        role: "user",
        timestamp: new Date(),
      };

      set((state) => ({ messages: [...state.messages, userMessage] }));

      const response = await chatService.sendMessage({
        message: content,
        sessionId: get().currentSession,
        tenantId: tenant?.id,
      });

      const assistantMessage: ChatMessage = {
        id: generateId(),
        content: response.message,
        role: "assistant",
        timestamp: new Date(),
        sources: response.sources,
        toolCalls: response.toolCalls,
      };

      set((state) => ({
        messages: [...state.messages, assistantMessage],
        currentSession: response.sessionId,
      }));
    } catch (error) {
      set({ error: error.message });
    } finally {
      set({ isLoading: false });
    }
  },
}));
```

---

## API Integration

### HTTP Client Setup

**File**: `src/services/api.ts`

```typescript
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor per auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = useAuthStore.getState().token;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor per error handling
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          useAuthStore.getState().logout();
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }
    );
  }

  async post<T>(url: string, data?: any): Promise<T> {
    const response = await this.client.post(url, data);
    return response.data;
  }

  async get<T>(url: string, params?: any): Promise<T> {
    const response = await this.client.get(url, { params });
    return response.data;
  }
}

export const apiClient = new ApiClient();
```

### Chat Service

**File**: `src/services/chatService.ts`

```typescript
interface SendMessageRequest {
  message: string;
  sessionId?: string;
  tenantId: string;
}

interface SendMessageResponse {
  message: string;
  sessionId: string;
  sources: Source[];
  toolCalls: ToolCall[];
}

class ChatService {
  async sendMessage(request: SendMessageRequest): Promise<SendMessageResponse> {
    return apiClient.post("/chat", request);
  }

  async getSessionHistory(sessionId: string): Promise<ChatMessage[]> {
    return apiClient.get(`/chat/sessions/${sessionId}/history`);
  }

  async getSessions(tenantId: string): Promise<ChatSession[]> {
    return apiClient.get(`/chat/sessions`, { tenantId });
  }
}

export const chatService = new ChatService();
```

### WebSocket Integration

**File**: `src/services/websocket.ts`

```typescript
class WebSocketService {
  private socket: Socket | null = null;

  connect(tenantId: string): Socket {
    if (this.socket?.connected) {
      return this.socket;
    }

    this.socket = io(API_BASE_URL, {
      auth: {
        token: useAuthStore.getState().token,
      },
      query: {
        tenantId,
      },
    });

    this.socket.on("connect", () => {
      console.log("WebSocket connected");
    });

    this.socket.on("message_chunk", (data) => {
      // Handle streaming message chunks
      useChatStore.getState().appendMessageChunk(data);
    });

    this.socket.on("message_complete", (data) => {
      // Handle message completion
      useChatStore.getState().completeMessage(data);
    });

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
}

export const wsService = new WebSocketService();
```

---

## UI/UX Design

### Design System

#### Color Palette

```css
:root {
  /* Medical/Healthcare Theme */
  --primary: #2563eb; /* Blue professional */
  --primary-dark: #1d4ed8;
  --secondary: #059669; /* Green medical */
  --accent: #dc2626; /* Red alerts */

  /* Neutral Colors */
  --background: #fafafa;
  --surface: #ffffff;
  --text-primary: #1f2937;
  --text-secondary: #6b7280;
  --border: #e5e7eb;

  /* Status Colors */
  --success: #10b981;
  --warning: #f59e0b;
  --error: #ef4444;
  --info: #3b82f6;
}
```

#### Typography

```css
/* Medical-friendly typography */
.text-medical {
  font-family: "Inter", "Helvetica Neue", sans-serif;
  line-height: 1.6;
  letter-spacing: 0.01em;
}

.text-heading {
  font-weight: 600;
  color: var(--text-primary);
}

.text-body {
  font-weight: 400;
  color: var(--text-primary);
}

.text-caption {
  font-size: 0.875rem;
  color: var(--text-secondary);
}
```

### Responsive Design

#### Breakpoints

```typescript
export const breakpoints = {
  sm: "640px", // Mobile
  md: "768px", // Tablet
  lg: "1024px", // Desktop
  xl: "1280px", // Large Desktop
  "2xl": "1536px", // Extra Large
};
```

#### Layout Components

```typescript
const ResponsiveLayout: React.FC = ({ children }) => {
  return (
    <div className="min-h-screen bg-background">
      {/* Mobile Header */}
      <div className="lg:hidden">
        <MobileHeader />
      </div>

      <div className="flex">
        {/* Desktop Sidebar */}
        <div className="hidden lg:block lg:w-64">
          <Sidebar />
        </div>

        {/* Main Content */}
        <div className="flex-1 lg:ml-64">
          <div className="container mx-auto px-4 py-6">{children}</div>
        </div>
      </div>
    </div>
  );
};
```

---

## Testing Strategy

### Component Testing

**File**: `tests/components/ChatInterface.test.tsx`

```typescript
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { ChatInterface } from "@/components/chat/ChatInterface";

// Mock stores
vi.mock("@/stores/chatStore", () => ({
  useChatStore: () => ({
    messages: [],
    sendMessage: vi.fn(),
    isLoading: false,
  }),
}));

describe("ChatInterface", () => {
  test("renderizza correttamente", () => {
    render(<ChatInterface />);
    expect(
      screen.getByPlaceholderText("Scrivi un messaggio...")
    ).toBeInTheDocument();
  });

  test("invia messaggio quando premuto Enter", async () => {
    const mockSendMessage = vi.fn();
    vi.mocked(useChatStore).mockReturnValue({
      messages: [],
      sendMessage: mockSendMessage,
      isLoading: false,
    });

    render(<ChatInterface />);

    const input = screen.getByPlaceholderText("Scrivi un messaggio...");
    fireEvent.change(input, { target: { value: "Test message" } });
    fireEvent.keyDown(input, { key: "Enter" });

    await waitFor(() => {
      expect(mockSendMessage).toHaveBeenCalledWith("Test message");
    });
  });
});
```

### Integration Testing

**File**: `tests/integration/chat-flow.test.tsx`

```typescript
describe("Chat Flow Integration", () => {
  test("complete chat interaction", async () => {
    // Setup mock API responses
    const mockResponse = {
      message: "Risposta del sistema AI",
      sessionId: "session-123",
      sources: [
        {
          title: "Documento Medico",
          page: 42,
          relevanceScore: 0.95,
          excerpt: "Estratto rilevante...",
        },
      ],
    };

    vi.mocked(chatService.sendMessage).mockResolvedValue(mockResponse);

    render(<ChatPage />);

    // User sends message
    const input = screen.getByPlaceholderText("Scrivi un messaggio...");
    fireEvent.change(input, { target: { value: "Cosa sono le fratture?" } });
    fireEvent.click(screen.getByText("Invia"));

    // Wait for AI response
    await waitFor(() => {
      expect(screen.getByText("Risposta del sistema AI")).toBeInTheDocument();
    });

    // Check sources are displayed
    expect(screen.getByText("Documento Medico")).toBeInTheDocument();
    expect(screen.getByText("Pagina 42")).toBeInTheDocument();
  });
});
```

### Performance Testing

```typescript
describe("Performance Tests", () => {
  test("chat interface renders within 100ms", async () => {
    const startTime = performance.now();
    render(<ChatInterface />);
    const endTime = performance.now();

    expect(endTime - startTime).toBeLessThan(100);
  });

  test("handles large message history efficiently", () => {
    const largeMessageList = Array.from({ length: 1000 }, (_, i) => ({
      id: `msg-${i}`,
      content: `Message ${i}`,
      role: "user" as const,
      timestamp: new Date(),
    }));

    const { rerender } = render(
      <ChatHistory messages={largeMessageList.slice(0, 100)} />
    );

    // Measure rerender time with virtualization
    const startTime = performance.now();
    rerender(<ChatHistory messages={largeMessageList} />);
    const endTime = performance.now();

    expect(endTime - startTime).toBeLessThan(50);
  });
});
```

---

## Deployment e Build

### Build Configuration

**File**: `vite.config.ts`

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["react", "react-dom"],
          ui: ["@radix-ui/react-dialog", "@radix-ui/react-dropdown-menu"],
          utils: ["axios", "zustand", "socket.io-client"],
        },
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
```

### Docker Configuration

**File**: `frontend/Dockerfile`

```dockerfile
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Environment Configuration

**File**: `.env.example`

```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000

# Feature Flags
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_EXPORT=true
VITE_DEBUG_MODE=false

# Branding
VITE_APP_NAME=FisioRAG
VITE_APP_VERSION=1.0.0
```

---

## Sicurezza Frontend

### Authentication Flow

```typescript
// Token refresh mechanism
class AuthService {
  private refreshPromise: Promise<string> | null = null;

  async refreshToken(): Promise<string> {
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.performRefresh();

    try {
      const newToken = await this.refreshPromise;
      return newToken;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async performRefresh(): Promise<string> {
    const refreshToken = localStorage.getItem("refreshToken");
    if (!refreshToken) {
      throw new Error("No refresh token available");
    }

    const response = await fetch("/auth/refresh", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${refreshToken}`,
      },
    });

    if (!response.ok) {
      throw new Error("Token refresh failed");
    }

    const { token } = await response.json();
    localStorage.setItem("token", token);
    return token;
  }
}
```

### Input Sanitization

```typescript
// XSS Protection
const sanitizeHtml = (content: string): string => {
  return DOMPurify.sanitize(content, {
    ALLOWED_TAGS: ["p", "br", "strong", "em", "code", "pre"],
    ALLOWED_ATTR: [],
  });
};

// Medical content validation
const validateMedicalQuery = (query: string): boolean => {
  const prohibitedPatterns = [/script/i, /javascript/i, /onclick/i, /onerror/i];

  return !prohibitedPatterns.some((pattern) => pattern.test(query));
};
```

### CSP Headers

```typescript
// Content Security Policy
const cspDirectives = {
  "default-src": ["'self'"],
  "script-src": ["'self'", "'unsafe-inline'"],
  "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
  "font-src": ["'self'", "https://fonts.gstatic.com"],
  "img-src": ["'self'", "data:", "https:"],
  "connect-src": ["'self'", process.env.VITE_API_BASE_URL],
};
```

---

## Performance Optimization

### Code Splitting

```typescript
// Lazy loading per routes
const ChatPage = lazy(() => import("@/pages/ChatPage"));
const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
const DocumentsPage = lazy(() => import("@/pages/DocumentsPage"));

const AppRouter: React.FC = () => {
  return (
    <Router>
      <Suspense fallback={<LoadingSpinner />}>
        <Routes>
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
        </Routes>
      </Suspense>
    </Router>
  );
};
```

### Virtualization

```typescript
// Virtual scrolling per chat history
import { FixedSizeList as List } from "react-window";

const VirtualizedChatHistory: React.FC<{ messages: ChatMessage[] }> = ({
  messages,
}) => {
  const Row = ({ index, style }: { index: number; style: any }) => (
    <div style={style}>
      <MessageBubble message={messages[index]} />
    </div>
  );

  return (
    <List
      height={600}
      itemCount={messages.length}
      itemSize={80}
      className="chat-history"
    >
      {Row}
    </List>
  );
};
```

### Caching Strategy

```typescript
// React Query per API caching
const useDocuments = (tenantId: string) => {
  return useQuery({
    queryKey: ["documents", tenantId],
    queryFn: () => documentService.getDocuments(tenantId),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  });
};

// Service Worker per static asset caching
const CACHE_NAME = "fisiorag-v1";
const urlsToCache = ["/", "/static/js/bundle.js", "/static/css/main.css"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(urlsToCache))
  );
});
```

---

## Accessibility (A11y)

### ARIA Implementation

```typescript
const ChatMessage: React.FC<{ message: ChatMessage }> = ({ message }) => {
  return (
    <div
      role="article"
      aria-label={`Messaggio da ${message.role}`}
      className="message-bubble"
    >
      <div
        className="message-content"
        aria-describedby={`timestamp-${message.id}`}
      >
        {message.content}
      </div>
      <time
        id={`timestamp-${message.id}`}
        dateTime={message.timestamp.toISOString()}
        className="sr-only"
      >
        {formatTime(message.timestamp)}
      </time>
    </div>
  );
};
```

### Keyboard Navigation

```typescript
const ChatInput: React.FC = () => {
  const [message, setMessage] = useState("");

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-input-container">
      <label htmlFor="message-input" className="sr-only">
        Inserisci il tuo messaggio
      </label>
      <textarea
        id="message-input"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Scrivi un messaggio..."
        aria-describedby="input-help"
        className="message-input"
      />
      <div id="input-help" className="sr-only">
        Premi Invio per inviare, Shift+Invio per nuova riga
      </div>
    </div>
  );
};
```

---

## Monitoraggio e Analytics

### Error Tracking

```typescript
// Error boundary con reporting
class ErrorBoundary extends React.Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to monitoring service
    errorReportingService.reportError(error, {
      componentStack: errorInfo.componentStack,
      userId: useAuthStore.getState().user?.id,
      tenantId: useAuthStore.getState().tenant?.id,
      url: window.location.href,
      timestamp: new Date().toISOString(),
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-fallback">
          <h2>Qualcosa è andato storto</h2>
          <button onClick={() => window.location.reload()}>
            Ricarica la pagina
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### Performance Metrics

```typescript
// Web Vitals tracking
import { getCLS, getFID, getFCP, getLCP, getTTFB } from "web-vitals";

const vitalsReporter = (metric: any) => {
  analytics.track("web_vital", {
    name: metric.name,
    value: metric.value,
    id: metric.id,
    tenantId: useAuthStore.getState().tenant?.id,
  });
};

getCLS(vitalsReporter);
getFID(vitalsReporter);
getFCP(vitalsReporter);
getLCP(vitalsReporter);
getTTFB(vitalsReporter);
```

---

## Deployment Pipeline

### CI/CD Configuration

**File**: `.github/workflows/frontend-deploy.yml`

```yaml
name: Frontend Deploy

on:
  push:
    branches: [main]
    paths: ["frontend/**"]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: "18"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Run linting
        working-directory: frontend
        run: npm run lint

      - name: Run type checking
        working-directory: frontend
        run: npm run type-check

      - name: Run tests
        working-directory: frontend
        run: npm run test -- --coverage

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: "18"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Build application
        working-directory: frontend
        run: npm run build
        env:
          VITE_API_BASE_URL: ${{ secrets.API_BASE_URL }}

      - name: Build Docker image
        run: |
          docker build -t fisiorag-frontend:${{ github.sha }} frontend/
          docker tag fisiorag-frontend:${{ github.sha }} fisiorag-frontend:latest

      - name: Deploy to staging
        if: github.ref == 'refs/heads/main'
        run: |
          # Deploy commands
          echo "Deploying to staging environment"
```

---

## Roadmap Implementazione

### Milestone 1: Foundation (Settimane 1-2)

- ✅ Setup progetto con Vite + React + TypeScript
- ✅ Configurazione Tailwind CSS + Shadcn/ui
- ✅ Implementazione auth store e routing base
- ✅ Configurazione API client con interceptors

### Milestone 2: Chat Interface (Settimane 3-4)

- 🔄 Implementazione componente chat completo
- 🔄 WebSocket integration per real-time updates
- 🔄 Gestione citazioni e sources display
- 🔄 Mobile-responsive chat interface

### Milestone 3: Dashboard (Settimane 5-6)

- 📋 Tenant dashboard con metriche
- 📋 Document manager con upload
- 📋 Session history e search
- 📋 Analytics panel implementation

### Milestone 4: Advanced Features (Settimane 7-8)

- 📋 Export functionality (PDF/Word)
- 📋 Advanced search e filters
- 📋 User preferences e settings
- 📋 Notification system

### Milestone 5: Testing e Deployment (Settimane 9-10)

- 📋 Test suite completa (>80% coverage)
- 📋 Performance optimization
- 📋 Security audit e fixes
- 📋 Production deployment setup

---

## Success Metrics

### Technical KPIs

- **First Contentful Paint**: <1.5s
- **Largest Contentful Paint**: <2.5s
- **Cumulative Layout Shift**: <0.1
- **First Input Delay**: <100ms
- **Bundle Size**: <500KB gzipped
- **Test Coverage**: >80%

### User Experience KPIs

- **Time to First Interaction**: <3s
- **Chat Response Time**: <500ms per message
- **Error Rate**: <1% di sessioni con errori
- **Mobile Usability**: 100% Google PageSpeed
- **Accessibility Score**: WCAG 2.1 AA compliant

### Business KPIs

- **User Adoption**: >80% utenti attivi settimanali
- **Session Duration**: >10 minuti media
- **Feature Usage**: >60% utilizzo funzionalità core
- **User Satisfaction**: >4.5/5 rating

---

La specifica tecnica definisce un'interfaccia utente moderna, scalabile e user-friendly per il sistema RAG medico, seguendo best practices di sviluppo React e garantendo performance, sicurezza e accessibilità enterprise-grade.
