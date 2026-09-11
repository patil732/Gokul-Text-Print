/**
 * frontend/lib/api/admin.ts
 * -------------------------
 * Typed API client for Gokul Text Print Admin Operations Center:
 * System Monitoring, ML Model Telemetry, Pipeline Sync, and User Access Management.
 */

import { apiGet, apiPost } from "./client";

export interface AdminSystemStatus {
  environment: string;
  flask_port: number;
  orchestrator: string;
  rag_vector_ready: boolean;
}

export interface ModelStatus {
  loaded: boolean;
  path: string;
  shap_loaded: boolean;
}

export interface DataPipelineStatus {
  rows: number;
  last_updated: string;
}

export interface AdminMonitorResponse {
  status: string;
  system: AdminSystemStatus;
  models: {
    sales: ModelStatus;
    inventory: ModelStatus;
  };
  data: {
    sales: DataPipelineStatus;
    inventory: DataPipelineStatus;
  };
}

export interface AdminUserRecord {
  id: number;
  username: string;
  role: string;
  email: string;
}

export interface AdminUsersResponse {
  status: string;
  users: AdminUserRecord[];
}

export interface AdminSyncResponse {
  status: string;
  message: string;
}

/**
 * Fetch ML model status, ChromaDB vector status, and data pipeline statistics.
 */
export async function getAdminMonitor(): Promise<AdminMonitorResponse> {
  return apiGet<AdminMonitorResponse>("/api/admin/monitor");
}

/**
 * Fetch registered user accounts for User Access Management.
 */
export async function getAdminUsers(): Promise<AdminUsersResponse> {
  return apiGet<AdminUsersResponse>("/api/admin/users");
}

/**
 * Trigger immediate manual background ERP data ingestion.
 */
export async function triggerAdminSync(): Promise<AdminSyncResponse> {
  return apiPost<AdminSyncResponse>("/api/admin/sync", {});
}
