/**
 * frontend/lib/api/chat.ts
 * -------------------------
 * Typed client for Sprint 4 RAG Chat endpoints.
 *
 * Endpoints covered:
 *   POST /api/chat              – Single-turn RAG Q&A
 *   GET  /api/chat/history      – Paginated chat history
 */

import { apiGet, apiPost } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ChatSource {
  document: string;
  page?: number;
  score?: number;
}

export interface ChatResponse {
  status: "success" | "error";
  chat_id?: string;
  question: string;
  answer: string;
  sources: ChatSource[];
  elapsed_ms: number;
  message?: string;
}

export interface ChatHistoryEntry {
  chat_id: string;
  user: string;
  question: string;
  answer: string;
  retrieved_documents: ChatSource[];
  timestamp: string;
}

export interface ChatHistoryResponse {
  status: "success" | "error";
  page: number;
  limit: number;
  total: number;
  pages: number;
  history: ChatHistoryEntry[];
}

export interface GetChatHistoryParams {
  page?: number;
  limit?: number;
  user?: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * Ask a single-turn RAG question.
 */
export async function askChat(question: string, user?: string): Promise<ChatResponse> {
  return apiPost<ChatResponse>("/api/chat", { question, user });
}

/**
 * Retrieve paginated chat history.
 */
export async function getChatHistory(
  params: GetChatHistoryParams = {},
): Promise<ChatHistoryResponse> {
  return apiGet<ChatHistoryResponse>("/api/chat/history", {
    params: {
      page: params.page ?? 1,
      limit: params.limit ?? 20,
      ...(params.user ? { user: params.user } : {}),
    },
  });
}
