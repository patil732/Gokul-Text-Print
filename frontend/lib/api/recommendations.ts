/**
 * frontend/lib/api/recommendations.ts
 * -------------------------------------
 * Typed client for Sprint 6 Dashboard Recommendations endpoint.
 *
 * Endpoints covered:
 *   GET /api/dashboard/recommendations
 */

import { apiGet } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type RecommendationPriority = "HIGH" | "MEDIUM" | "LOW";
export type RecommendationSource = "sales" | "inventory" | "knowledge" | "manager";

export interface Recommendation {
  recommendation: string;
  reason: string;
  confidence: number;
  priority: RecommendationPriority;
  source: RecommendationSource;
  timestamp: string;
}

export interface RecommendationsResponse {
  status: "success" | "error";
  count: number;
  data: Recommendation[];
  elapsed_ms: number;
  message?: string;
}

export interface GetRecommendationsParams {
  priority?: Lowercase<RecommendationPriority>;
  limit?: number;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * Fetch aggregated, priority-sorted business recommendations.
 */
export async function getRecommendations(
  params: GetRecommendationsParams = {},
): Promise<RecommendationsResponse> {
  return apiGet<RecommendationsResponse>("/api/dashboard/recommendations", {
    params: {
      ...(params.priority ? { priority: params.priority } : {}),
      ...(params.limit !== undefined ? { limit: params.limit } : {}),
    },
  });
}
