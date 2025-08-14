import { apiClient } from "./api";
import { type LoginCredentials, type AuthResponse, type User, type Tenant } from "../types/api";

class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>("/auth/login", credentials);
  }

  async logout(): Promise<void> {
    return apiClient.post<void>("/auth/logout");
  }

  async refreshToken(
    refreshToken: string
  ): Promise<{ token: string; refreshToken: string }> {
    return apiClient.post<{ token: string; refreshToken: string }>(
      "/auth/refresh",
      {
        refreshToken,
      }
    );
  }

  async selectTenant(
    tenantId: string
  ): Promise<{ tenant: Tenant; token: string; refreshToken: string }> {
    return apiClient.post<{
      tenant: Tenant;
      token: string;
      refreshToken: string;
    }>("/auth/select-tenant", {
      tenantId,
    });
  }

  async getCurrentUser(): Promise<User> {
    return apiClient.get<User>("/auth/me");
  }

  async getUserTenants(): Promise<Tenant[]> {
    return apiClient.get<Tenant[]>("/auth/tenants");
  }

  async register(userData: {
    email: string;
    password: string;
    name: string;
    tenantId?: string;
  }): Promise<AuthResponse> {
    return apiClient.post<AuthResponse>("/auth/register", userData);
  }

  async resetPassword(email: string): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>("/auth/reset-password", {
      email,
    });
  }

  async confirmPasswordReset(
    token: string,
    newPassword: string
  ): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>("/auth/confirm-reset", {
      token,
      password: newPassword,
    });
  }

  async changePassword(
    currentPassword: string,
    newPassword: string
  ): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>("/auth/change-password", {
      currentPassword,
      newPassword,
    });
  }

  async updateProfile(userData: Partial<User>): Promise<User> {
    return apiClient.patch<User>("/auth/profile", userData);
  }
}

export const authService = new AuthService();
