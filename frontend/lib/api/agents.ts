/**
 * frontend/lib/api/agents.ts
 * ---------------------------
 * Typed client for Sprint 5 Multi-Agent Executive Copilot endpoints.
 *
 * Endpoints covered:
 *   GET  /api/agent/status      – Health check + registered agent list
 *   POST /api/agent/ask         – Orchestrated multi-agent answer (legacy)
 *   POST /api/agents/sales      – Run SalesAgent directly
 *   POST /api/agents/inventory  – Run InventoryAgent directly
 *   POST /api/agents/knowledge  – Run KnowledgeAgent directly
 *   POST /api/agents/manager    – Full orchestration pipeline
 */

import { apiGet, apiPost } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AgentStatusResponse {
  status: string;
  registered_agents: string[];
  description: string;
}

// Generic agent response (sales / inventory / knowledge)
export interface AgentResponse<TData = Record<string, unknown>> {
  status: "success" | "warning" | "error";
  agent_name: string;
  data: TData;
  confidence: number;
  timestamp: string;
  message?: string;
}

export interface SalesAgentData {
  sales_growth: number;
  forecast: number;
  recommendation: string;
  market_trend: string;
  top_product: string;
  forecast_period: string;
}

export interface InventoryAgentData {
  stock_health: string;
  remaining_days: number;
  recommendation: string;
  decision: string;
  confidence_level: string;
  model_version: string;
  model_type: string;
  model_accuracy: number;
}

export interface KnowledgeAgentData {
  policy: string;
  sources: string[];
  source_details: Array<{ document: string; page: number; score: number }>;
  relevant_chunks: number;
  query_used: string;
}

export interface ManagerOrchestrationResponse {
  status: "success" | "error";
  question: string;
  answer: string;
  agents_used: string[];
  confidence: number;
  agent_details: {
    sales?: AgentResponse<SalesAgentData>;
    inventory?: AgentResponse<InventoryAgentData>;
    knowledge?: AgentResponse<KnowledgeAgentData>;
  };
  chat_id?: string;
  message?: string;
}

export interface AgentAskResponse {
  status: "success" | "error";
  question: string;
  answer: string;
  agents_used: string[];
  raw_data: {
    sales?: unknown;
    inventory?: unknown;
    knowledge?: unknown;
  };
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/** Health check — returns registered sub-agent list. */
export async function getAgentStatus(): Promise<AgentStatusResponse> {
  return apiGet<AgentStatusResponse>("/api/agent/status");
}

/** Legacy single-call orchestration (Sprint 4 compatible). */
export async function agentAsk(question: string): Promise<AgentAskResponse> {
  return apiPost<AgentAskResponse>("/api/agent/ask", { question });
}

/** Run SalesAgent directly. */
export async function runSalesAgent(
  question?: string,
): Promise<AgentResponse<SalesAgentData>> {
  return apiPost<AgentResponse<SalesAgentData>>("/api/agents/sales", { question });
}

/** Run InventoryAgent directly. */
export async function runInventoryAgent(
  question?: string,
): Promise<AgentResponse<InventoryAgentData>> {
  return apiPost<AgentResponse<InventoryAgentData>>("/api/agents/inventory", { question });
}

/** Run KnowledgeAgent directly. */
export async function runKnowledgeAgent(
  question?: string,
): Promise<AgentResponse<KnowledgeAgentData>> {
  return apiPost<AgentResponse<KnowledgeAgentData>>("/api/agents/knowledge", { question });
}

/** Full multi-agent orchestration pipeline (recommended). */
export async function orchestrateManager(
  question: string,
): Promise<ManagerOrchestrationResponse> {
  return apiPost<ManagerOrchestrationResponse>("/api/agents/manager", { question });
}
