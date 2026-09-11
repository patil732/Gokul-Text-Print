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

export interface SalesTrendPoint {
  date: string;
  revenue: number;
  volume: number;
}

export interface ProductPerformanceItem {
  product: string;
  revenue: number;
  share_pct: number;
  volume: number;
}

export interface SalesForecastItem {
  prediction_id: string;
  prediction_date: string;
  forecast_period: string;
  forecast_value: number;
  recommendation: string;
  confidence: number;
  model_version: string;
}

export interface SalesSummaryMetrics {
  total_revenue: number;
  total_volume: number;
  avg_order_value: number;
  records_count: number;
  min_date?: string;
  max_date?: string;
}

export interface SalesAnalyticsData {
  dates?: string[];
  revenue?: number[];
  quantity?: number[];
  summary?: SalesSummaryMetrics;
  trend?: SalesTrendPoint[];
  product_performance?: ProductPerformanceItem[];
  forecasts?: SalesForecastItem[];
  [key: string]: unknown;
}

export interface StockTrendPoint {
  date: string;
  stock: number;
  production: number;
  stock_ratio: number;
}

export interface LowStockItem {
  item_code: string;
  current_stock: number;
  reorder_threshold: number;
  deficit: number;
  status: string;
}

export interface DeadStockItem {
  item_code: string;
  holding_units: number;
  estimated_value: number;
  status: string;
}

export interface InventoryPredictionHistoryItem {
  id: number;
  timestamp: string;
  version: string;
  decision: string;
  confidence: number;
  features_summary: {
    total_stock?: number;
    warehouse_count?: number | null;
    [key: string]: unknown;
  };
}

export interface InventorySummaryMetrics {
  current_total_stock: number;
  inventory_valuation: number;
  dead_stock_count: number;
  dead_stock_value: number;
  low_stock_count: number;
  days_in_inventory: number;
  turnover_ratio: number;
  velocity_status: string;
  range_type?: string;
}

export interface InventoryAnalyticsData {
  products?: string[];
  stock_levels?: number[];
  reorder_points?: number[];
  summary?: InventorySummaryMetrics;
  stock_trend?: StockTrendPoint[];
  low_stock_analysis?: {
    threshold: number;
    total_low_stock_count: number;
    critical_count: number;
    warning_count: number;
    items: LowStockItem[];
  };
  dead_stock?: {
    total_dead_stock_count: number;
    dead_stock_units: number;
    dead_stock_value: number;
    dead_stock_ratio_pct: number;
    items: DeadStockItem[];
  };
  prediction_history?: InventoryPredictionHistoryItem[];
  inventory_turnover?: {
    annualized_sales_units: number;
    avg_stock_units: number;
    days_in_inventory: number;
    turnover_ratio: number;
    velocity_status: string;
  };
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
