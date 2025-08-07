export interface User {
  id: string;
  email: string;
  name: string;
  role: "student" | "educator" | "admin";
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  tenant: Tenant;
  token: string;
  refreshToken: string;
}

export interface ApiError {
  error: string;
  message: string;
  details?: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: Date;
  sources?: Source[];
  toolCalls?: ToolCall[];
}

export interface Source {
  title: string;
  page?: number;
  relevanceScore: number;
  excerpt: string;
}

export interface ToolCall {
  tool_name: string;
  args: Record<string, any>;
  tool_call_id?: string;
}

export interface SendMessageRequest {
  message: string;
  sessionId?: string;
  tenantId: string;
}

export interface SendMessageResponse {
  message: string;
  sessionId: string;
  sources: Source[];
  toolCalls: ToolCall[];
}

export interface ChatSession {
  id: string;
  title?: string;
  created_at: string;
  updated_at: string;
  messageCount: number;
}

export interface Document {
  id: string;
  title: string;
  filename: string;
  uploadedAt: Date;
  status: "uploading" | "processing" | "completed" | "error";
  chunksCount?: number;
  fileSize: number;
}

export interface TenantMetrics {
  documentsCount: number;
  queriesCount: number;
  avgResponseTime: number;
  storageUsed: number;
  activeUsers: number;
}
