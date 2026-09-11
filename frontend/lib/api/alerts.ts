/**
 * frontend/lib/api/alerts.ts
 * ---------------------------
 * Typed client for Sprint 6 Dashboard Alerts endpoint.
 *
 * Endpoints covered:
 *   GET /api/dashboard/alerts
 */

import { apiGet, apiPatch } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type AlertPriority = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type AlertStatus = "ACTIVE" | "RESOLVED" | "ALL";

export interface Alert {
  alert_id: string;
  alert_type: string;
  priority: AlertPriority;
  message: string;
  status: string;
  created_at: string;
}

export interface AlertsResponse {
  status: "success" | "error";
  count: number;
  data: Alert[];
  elapsed_ms: number;
  message?: string;
}

export interface GetAlertsParams {
  status?: AlertStatus;
  priority?: AlertPriority;
  limit?: number;
}

export interface ResolveAlertResponse {
  status: "success" | "error";
  message: string;
  alert_id: string;
  new_status?: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * Fetch operational alerts sorted by priority then recency.
 */
export async function getAlerts(params: GetAlertsParams = {}): Promise<AlertsResponse> {
  return apiGet<AlertsResponse>("/api/dashboard/alerts", {
    params: {
      status: params.status ?? "ALL",
      ...(params.priority ? { priority: params.priority } : {}),
      ...(params.limit !== undefined ? { limit: params.limit } : {}),
    },
  });
}

/**
 * Update the status of an alert (mark as RESOLVED or ACTIVE).
 */
export async function resolveAlert(
  alertId: string,
  status: "RESOLVED" | "ACTIVE" = "RESOLVED"
): Promise<ResolveAlertResponse> {
  return apiPatch<ResolveAlertResponse>(`/api/dashboard/alerts/${alertId}`, {
    status,
  });
}

// ---------------------------------------------------------------------------
// Categorization Helpers
// ---------------------------------------------------------------------------

export function isCriticalAlert(alert: Alert): boolean {
  return alert.priority === "CRITICAL";
}

export function isLowStockAlert(alert: Alert): boolean {
  const type = alert.alert_type.toUpperCase();
  return type === "LOW_STOCK" || type === "OVERSTOCK";
}

export function isSalesDropAlert(alert: Alert): boolean {
  const type = alert.alert_type.toUpperCase();
  return type === "SALES_DROP" || type === "SALES_SPIKE";
}

export function isModelErrorAlert(alert: Alert): boolean {
  const type = alert.alert_type.toUpperCase();
  return (
    type === "MODEL_FAILURE" ||
    type === "ETL_FAILURE" ||
    type === "MISSING_DATA" ||
    type === "CONFIDENCE_DROP" ||
    type === "AI_CONFIDENCE_DROP"
  );
}
