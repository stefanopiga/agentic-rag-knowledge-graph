import { apiClient } from "./api";
import { type TenantMetrics, type Document } from "../types/api";

class TenantService {
  async getMetrics(tenantId: string): Promise<TenantMetrics> {
    return apiClient.get<TenantMetrics>(`/tenants/${tenantId}/metrics`);
  }

  async getDocuments(tenantId: string): Promise<Document[]> {
    return apiClient.get<Document[]>(`/tenants/${tenantId}/documents`);
  }

  async uploadDocument(
    tenantId: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<Document> {
    return apiClient.uploadFile<Document>(
      `/tenants/${tenantId}/documents/upload`,
      file,
      onProgress
    );
  }

  async deleteDocument(tenantId: string, documentId: string): Promise<void> {
    return apiClient.delete<void>(
      `/tenants/${tenantId}/documents/${documentId}`
    );
  }

  async getDocumentStatus(
    tenantId: string,
    documentId: string
  ): Promise<{
    status: Document["status"];
    progress?: number;
    error?: string;
  }> {
    return apiClient.get(`/tenants/${tenantId}/documents/${documentId}/status`);
  }

  async reprocessDocument(tenantId: string, documentId: string): Promise<void> {
    return apiClient.post<void>(
      `/tenants/${tenantId}/documents/${documentId}/reprocess`
    );
  }

  async getStorageInfo(tenantId: string): Promise<{
    usedStorage: number;
    totalStorage: number;
    documentCount: number;
    chunkCount: number;
  }> {
    return apiClient.get(`/tenants/${tenantId}/storage`);
  }

  async getTenantSettings(tenantId: string): Promise<{
    maxDocuments: number;
    maxStorageSize: number;
    allowedFileTypes: string[];
    chunkingStrategy: "semantic" | "simple";
  }> {
    return apiClient.get(`/tenants/${tenantId}/settings`);
  }

  async updateTenantSettings(
    tenantId: string,
    settings: {
      chunkingStrategy?: "semantic" | "simple";
      maxChunkSize?: number;
      chunkOverlap?: number;
    }
  ): Promise<void> {
    return apiClient.patch(`/tenants/${tenantId}/settings`, settings);
  }
}

export const tenantService = new TenantService();
