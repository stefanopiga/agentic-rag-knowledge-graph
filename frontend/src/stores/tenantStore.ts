import { create } from "zustand";
import { type TenantState, type TenantActions } from "../types/tenant";
import { tenantService } from "../services/tenant";

interface TenantStore extends TenantState, TenantActions {}

export const useTenantStore = create<TenantStore>((set, get) => ({
  // State
  metrics: null,
  isLoading: false,
  error: null,

  // Actions
  loadMetrics: async (tenantId: string) => {
    set({ isLoading: true, error: null });
    try {
      const metrics = await tenantService.getMetrics(tenantId);
      set({
        metrics,
        isLoading: false,
      });
    } catch (error) {
      set({
        error:
          error instanceof Error ? error.message : "Failed to load metrics",
        isLoading: false,
      });
      throw error;
    }
  },

  refreshMetrics: async () => {
    const { loadMetrics: _ } = get();
    // This would require tenant ID from auth store
    // For now, we'll implement this when we have the tenant context
    console.log("Refresh metrics called");
  },

  setError: (error: string | null) => {
    set({ error });
  },
}));
