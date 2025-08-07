import type { Tenant, User, TenantMetrics } from "./api";

export interface AuthState {
  user: User | null;
  tenant: Tenant | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface AuthActions {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  selectTenant: (tenantId: string) => Promise<void>;
  refreshAuthToken: () => Promise<void>;
  setLoading: (loading: boolean) => void;
}

export interface TenantState {
  metrics: TenantMetrics | null;
  isLoading: boolean;
  error: string | null;
}

export interface TenantActions {
  loadMetrics: (tenantId: string) => Promise<void>;
  refreshMetrics: () => Promise<void>;
  setError: (error: string | null) => void;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface TenantSelectorProps {
  tenants: Tenant[];
  selectedTenant: Tenant | null;
  onSelect: (tenant: Tenant) => void;
}

export interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: User["role"];
}
