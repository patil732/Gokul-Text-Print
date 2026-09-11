/**
 * frontend/lib/api/sales.ts
 * --------------------------
 * Typed client for Sprint 2 Sales ML API endpoints.
 *
 * Endpoints covered:
 *   POST /api/ml/sales/train          – Trigger sales model training
 *   GET  /api/ml/sales/predict        – Run inference (GET)
 *   POST /api/ml/sales/predict        – Run inference (POST)
 *   GET  /api/ml/sales/metrics        – Latest model evaluation metrics
 *   POST /api/sales/forecast          – Generate 7/30/90-day forecast
 *   GET  /api/sales/recommendation    – Rules-based business recommendation
 *   GET  /api/sales/dashboard_data    – Sales Intelligence Dashboard panel data
 *   GET  /api/sales/history           – Paginated prediction history
 */

import { apiGet, apiPost } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ForecastPeriod = "7_days" | "30_days" | "90_days";

export interface SalesTrainResponse {
  status: "success" | "error";
  message: string;
  data: Record<string, unknown>;
}

export interface SalesPredictResponse {
  status: "success" | "error";
  [key: string]: unknown;
}

export interface ModelMetrics {
  status: "success" | "error";
  model_name: string;
  version: string;
  model_type: string;
  accuracy: number;
  trained_at: string;
  metrics: Record<string, number>;
  message?: string;
}

export interface SalesForecastResponse {
  status: "success" | "error";
  forecast_period: ForecastPeriod;
  predicted_sales: number;
  growth_rate: number;
  confidence: number;
  explanation: string[];
  model_type: string;
  version: string;
  elapsed_ms: number;
  message?: string;
}

export interface SalesRecommendationResponse {
  status: "success" | "error";
  decision: string;
  reason: string;
  confidence: number;
  growth_rate: number;
  forecast_period: ForecastPeriod;
  predicted_sales: number;
  model_type: string;
  version: string;
  stored_id: number | null;
  message?: string;
}

export interface SalesDashboardDataResponse {
  status: "success" | "error";
  kpis: { total_revenue: number; growth_rate: number; record_count: number };
  sales_trend: { dates: string[]; volume: number[] };
  revenue_trend: { dates: string[]; revenue: number[] };
  product_performance: { products: string[]; revenues: number[] };
  monthly_comparison: { months: string[]; revenues: number[] };
  message?: string;
}

export interface SalesPredictionHistoryRecord {
  prediction_id: string;
  prediction_date: string;
  forecast_period: ForecastPeriod;
  forecast_value: number;
  recommendation: string;
  confidence: number;
  model_version: string;
}

export interface SalesHistoryResponse {
  status: "success" | "error";
  page: number;
  per_page: number;
  total_records: number;
  total_pages: number;
  data: SalesPredictionHistoryRecord[];
  message?: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/** Trigger Sales ML model training. */
export async function trainSalesModel(version?: string): Promise<SalesTrainResponse> {
  return apiPost<SalesTrainResponse>("/api/ml/sales/train", { version });
}

/** Run Sales ML prediction (POST body). */
export async function predictSales(
  features: Record<string, number | string>,
): Promise<SalesPredictResponse> {
  return apiPost<SalesPredictResponse>("/api/ml/sales/predict", features);
}

/** Get latest Sales ML model metrics. */
export async function getSalesMetrics(): Promise<ModelMetrics> {
  return apiGet<ModelMetrics>("/api/ml/sales/metrics");
}

/** Generate a Sales forecast for 7, 30, or 90 days. */
export async function getSalesForecast(
  forecastPeriod: ForecastPeriod,
  baselineFeatures?: Record<string, number>,
): Promise<SalesForecastResponse> {
  return apiPost<SalesForecastResponse>("/api/sales/forecast", {
    forecast_period: forecastPeriod,
    ...baselineFeatures,
  });
}

/** Get rules-based sales recommendation. */
export async function getSalesRecommendation(
  forecastPeriod: ForecastPeriod = "30_days",
): Promise<SalesRecommendationResponse> {
  return apiGet<SalesRecommendationResponse>("/api/sales/recommendation", {
    params: { forecast_period: forecastPeriod },
  });
}

/** Get comprehensive sales dashboard data for chart panels. */
export async function getSalesDashboardData(): Promise<SalesDashboardDataResponse> {
  return apiGet<SalesDashboardDataResponse>("/api/sales/dashboard_data");
}

/** Get paginated sales prediction history. */
export async function getSalesHistory(params: {
  page?: number;
  limit?: number;
} = {}): Promise<SalesHistoryResponse> {
  return apiGet<SalesHistoryResponse>("/api/sales/history", {
    params: { page: params.page ?? 1, limit: params.limit ?? 10 },
  });
}
