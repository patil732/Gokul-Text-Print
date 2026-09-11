/**
 * frontend/lib/api/analytics.ts
 * ------------------------------
 * Typed client for Sprint 6 Dashboard Analytics endpoint.
 *
 * Endpoints covered:
 *   GET /api/dashboard/analytics
 */

import { apiGet } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type AnalyticsType = "sales" | "inventory";
export type RangeType = "daily" | "weekly" | "monthly";

export interface SalesAnalyticsData {
  dates: string[];
  revenue: number[];
  quantity: number[];
  [key: string]: unknown;
}

export interface InventoryAnalyticsData {
  products: string[];
  stock_levels: number[];
  reorder_points: number[];
  [key: string]: unknown;
}

export interface AnalyticsResponse {
  status: "success" | "error";
  analytics_type: AnalyticsType;
  range: RangeType;
  start_date: string | null;
  end_date: string | null;
  data: SalesAnalyticsData | InventoryAnalyticsData;
  elapsed_ms: number;
  message?: string;
}

export interface GetAnalyticsParams {
  type?: AnalyticsType;
  range?: RangeType;
  start?: string;
  end?: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * Fetch chart-ready analytics data for Sales or Inventory domains.
 */
export async function getAnalytics(params: GetAnalyticsParams = {}): Promise<AnalyticsResponse> {
  return apiGet<AnalyticsResponse>("/api/dashboard/analytics", {
    params: {
      type: params.type ?? "sales",
      range: params.range ?? "daily",
      ...(params.start ? { start: params.start } : {}),
      ...(params.end ? { end: params.end } : {}),
    },
  });
}
