/**
 * frontend/lib/api/inventory.ts
 * ------------------------------
 * Typed client for Sprint 2 Inventory ML API endpoints.
 *
 * Endpoints covered:
 *   POST /api/ml/inventory/train    – Trigger inventory model training
 *   GET  /api/ml/inventory/predict  – Run inference (GET)
 *   POST /api/ml/inventory/predict  – Run inference (POST)
 *   GET  /api/ml/inventory/metrics  – Latest model evaluation metrics
 */

import { apiGet, apiPost } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface InventoryTrainResponse {
  status: "success" | "error";
  message: string;
  data: Record<string, unknown>;
}

export interface InventoryPredictResponse {
  status: "success" | "error";
  [key: string]: unknown;
}

export interface InventoryModelMetrics {
  status: "success" | "error";
  model_name: string;
  version: string;
  model_type: string;
  accuracy: number;
  trained_at: string;
  metrics: Record<string, number>;
  message?: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/** Trigger Inventory ML model training. */
export async function trainInventoryModel(version?: string): Promise<InventoryTrainResponse> {
  return apiPost<InventoryTrainResponse>("/api/ml/inventory/train", { version });
}

/** Run Inventory ML prediction (POST body). */
export async function predictInventory(
  features: Record<string, number | string>,
): Promise<InventoryPredictResponse> {
  return apiPost<InventoryPredictResponse>("/api/ml/inventory/predict", features);
}

/** Run Inventory ML prediction (GET query params — convenience wrapper). */
export async function predictInventoryGet(
  features: Record<string, string | number>,
): Promise<InventoryPredictResponse> {
  return apiGet<InventoryPredictResponse>("/api/ml/inventory/predict", {
    params: features as Record<string, string>,
  });
}

/** Get latest Inventory ML model metrics. */
export async function getInventoryMetrics(): Promise<InventoryModelMetrics> {
  return apiGet<InventoryModelMetrics>("/api/ml/inventory/metrics");
}
