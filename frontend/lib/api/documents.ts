/**
 * frontend/lib/api/documents.ts
 * ------------------------------
 * Typed client for Sprint 4 Document Management & RAG Semantic Search endpoints.
 *
 * Endpoints covered:
 *   GET    /api/documents             – List all active documents
 *   POST   /api/documents/upload      – Upload a PDF file (multipart/form-data)
 *   DELETE /api/documents/<id>        – Soft-delete document + remove from disk
 *   POST   /api/rag/search            – Semantic similarity search over document chunks
 */

import { apiGet, apiPost, apiDelete, API_BASE_URL, ApiError } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DocumentRecord {
  document_id: string;
  document_name: string;
  document_type: string;
  upload_date: string;
  uploaded_by: string;
  status: "active" | "processing" | "processed" | "failed" | "deleted" | string;
  file_path: string;
  file_hash: string;
  [key: string]: unknown;
}

export interface DocumentListResponse {
  status: "success" | "error";
  count: number;
  documents: DocumentRecord[];
  message?: string;
}

export interface DocumentUploadResponse {
  status: "success" | "error";
  document: DocumentRecord;
  message?: string;
}

export interface DocumentDeleteResponse {
  status: "success" | "error";
  message: string;
  document_id: string;
}

export interface RagSearchChunk {
  chunk_id: string;
  chunk_text: string;
  page_number: number;
  source_document: string;
  score: number;
}

export interface RagSearchResponse {
  status: "success" | "error";
  query: string;
  top_k: number;
  elapsed_ms: number;
  chunks: RagSearchChunk[];
  sources: string[];
  message?: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

/**
 * Retrieve all active documents from the knowledge repository.
 */
export async function listDocuments(): Promise<DocumentListResponse> {
  return apiGet<DocumentListResponse>("/api/documents");
}

/**
 * Upload a PDF document via multipart/form-data.
 */
export async function uploadDocument(
  file: File,
  uploadedBy?: string,
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (uploadedBy) {
    formData.append("uploaded_by", uploadedBy);
  }

  const url = `${API_BASE_URL}/api/documents/upload`;
  const response = await fetch(url, {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  const data = (await response.json()) as DocumentUploadResponse;
  if (!response.ok) {
    throw new ApiError(response.status, response.statusText, data, data.message);
  }

  return data;
}

/**
 * Soft-delete a document record and remove its file from disk.
 */
export async function deleteDocument(documentId: string): Promise<DocumentDeleteResponse> {
  return apiDelete<DocumentDeleteResponse>(`/api/documents/${documentId}`);
}

/**
 * Semantic similarity search over all uploaded and indexed documents.
 */
export async function searchRag(
  query: string,
  top_k: number = 5,
): Promise<RagSearchResponse> {
  return apiPost<RagSearchResponse>("/api/rag/search", { query, top_k });
}
