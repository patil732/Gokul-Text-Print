/**
 * frontend/lib/api/alerts.ts
 * ---------------------------
 * Typed client for Sprint 6 Dashboard Alerts endpoint.
 *
 * Endpoints covered:
 *   GET /api/dashboard/alerts
 */

import { apiGet } from "./client";

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

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * Fetch active operational alerts sorted by priority then recency.
 */
export async function getAlerts(params: GetAlertsParams = {}): Promise<AlertsResponse> {
  return apiGet<AlertsResponse>("/api/dashboard/alerts", {
    params: {
      status: params.status ?? "ACTIVE",
      ...(params.priority ? { priority: params.priority } : {}),
      ...(params.limit !== undefined ? { limit: params.limit } : {}),
    },
  });
}
