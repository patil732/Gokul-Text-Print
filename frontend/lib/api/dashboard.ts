/**
 * frontend/lib/api/dashboard.ts
 * ------------------------------
 * Typed client for Sprint 6 Dashboard KPI endpoints.
 *
 * Endpoints covered:
 *   GET /api/dashboard/kpis
 *   GET /api/dashboard/preferences
 *   POST /api/dashboard/preferences
 */

import { apiGet, apiPost } from "./client";

// ---------------------------------------------------------------------------
// Response types
// ---------------------------------------------------------------------------

export interface BusinessHealthScore {
  score: number;
  status: string;
  sales_score: number;
  inventory_score: number;
  alert_score: number;
  formula: string;
}

export interface KpiData {
  total_sales: number;
  revenue: number;
  sales_growth: number;
  inventory_value: number;
  inventory_health: string;
  low_stock_products_count: number;
  ai_recommendations_count: number;
  business_health: BusinessHealthScore;
  timestamp: string;
  elapsed_ms: number;
  cached: boolean;
}

export interface KpiResponse {
  status: "success" | "error";
  data: KpiData;
  message?: string;
}

export interface DashboardPreferences {
  theme?: string;
  llm_provider?: "gemini" | "openai";
  api_keys?: {
    gemini?: string;
    openai?: string;
  };
  notifications?: {
    email_alerts?: boolean;
    critical_sms?: boolean;
    daily_digest?: boolean;
    weekly_pdf?: boolean;
  };
  profile?: {
    full_name?: string;
    email?: string;
    phone?: string;
    role?: string;
  };
  company?: {
    mill_name?: string;
    gstin?: string;
    address?: string;
    printing_capacity?: string;
    active_machinery?: string;
  };
  pinned_widgets?: string[];
  widget_order?: string[];
  chart_filters?: {
    sales_range: string;
    inventory_range: string;
    start_date: string;
    end_date: string;
  };
  collapsed_sections?: string[];
}

export interface PreferencesResponse {
  status: "success" | "error";
  user: string;
  data: DashboardPreferences;
  updated_at?: string;
  is_default?: boolean;
}

export interface LlmProviderResponse {
  status: "success" | "error";
  provider: "gemini" | "openai";
  model?: string;
  available_providers: string[];
  message?: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * Fetch comprehensive KPI metrics and composite Business Health Score.
 * @param forceRefresh - Bypass the backend 30s in-memory cache.
 */
export async function getDashboardKpis(forceRefresh = false): Promise<KpiResponse> {
  return apiGet<KpiResponse>("/api/dashboard/kpis", {
    params: forceRefresh ? { refresh: "true" } : undefined,
  });
}

/**
 * Retrieve personalized dashboard preferences for a user.
 */
export async function getDashboardPreferences(userId?: string): Promise<PreferencesResponse> {
  return apiGet<PreferencesResponse>("/api/dashboard/preferences", {
    params: userId ? { user: userId } : undefined,
  });
}

/**
 * Persist personalized dashboard preferences for a user.
 */
export async function saveDashboardPreferences(
  preferences: Partial<DashboardPreferences>,
  userId?: string,
): Promise<PreferencesResponse> {
  return apiPost<PreferencesResponse>("/api/dashboard/preferences", {
    user: userId,
    preferences,
  });
}

/**
 * Read the active LLM provider from backend config.
 */
export async function getLlmProviderSetting(): Promise<LlmProviderResponse> {
  return apiGet<LlmProviderResponse>("/api/settings/llm_provider");
}

/**
 * Set the active LLM provider in backend config.
 */
export async function setLlmProviderSetting(
  provider: "gemini" | "openai",
): Promise<LlmProviderResponse> {
  return apiPost<LlmProviderResponse>("/api/settings/llm_provider", { provider });
}
