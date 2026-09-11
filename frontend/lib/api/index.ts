/**
 * frontend/lib/api/index.ts
 * --------------------------
 * Barrel re-export for the entire typed API client layer.
 *
 * Usage:
 *   import { getDashboardKpis, getAlerts, orchestrateManager } from "@/lib/api";
 */

// Core
export * from "./client";

// Domain modules
export * from "./dashboard";
export * from "./analytics";
export * from "./alerts";
export * from "./recommendations";
export * from "./reports";
export * from "./chat";
export * from "./agents";
export * from "./sales";
export * from "./inventory";
export * from "./documents";
