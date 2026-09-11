/**
 * frontend/lib/api/reports.ts
 * ----------------------------
 * Typed client for Sprint 6 Report Generation endpoint.
 *
 * Endpoints covered:
 *   GET /api/reports/generate   → returns a downloadable file (PDF / CSV)
 */

import { API_BASE_URL } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ReportType = "daily" | "weekly" | "monthly" | "custom";
export type ExportFormat = "pdf" | "csv";

export interface GenerateReportParams {
  type?: ReportType;
  format?: ExportFormat;
  start?: string; // YYYY-MM-DD
  end?: string;   // YYYY-MM-DD
}

// ---------------------------------------------------------------------------
// API function
// ---------------------------------------------------------------------------

/**
 * Build the URL for report download without fetching it (useful for <a href>).
 */
export function getReportDownloadUrl(params: GenerateReportParams = {}): string {
  const url = new URL(`${API_BASE_URL}/api/reports/generate`);
  if (params.type) url.searchParams.set("type", params.type);
  if (params.format) url.searchParams.set("format", params.format);
  if (params.start) url.searchParams.set("start", params.start);
  if (params.end) url.searchParams.set("end", params.end);
  return url.toString();
}

/**
 * Fetch a generated executive report as a Blob (PDF or CSV).
 * The caller is responsible for triggering browser download.
 *
 * @example
 * const { blob, filename } = await generateReport({ type: "daily", format: "pdf" });
 * const href = URL.createObjectURL(blob);
 * const a = document.createElement("a");
 * a.href = href; a.download = filename; a.click();
 */
export async function generateReport(
  params: GenerateReportParams = {},
): Promise<{ blob: Blob; filename: string; contentType: string }> {
  const url = getReportDownloadUrl(params);

  const response = await fetch(url, { credentials: "include" });
  if (!response.ok) {
    let body: unknown;
    try { body = await response.json(); } catch { body = await response.text(); }
    throw new Error(`Report generation failed (${response.status}): ${JSON.stringify(body)}`);
  }

  const contentType = response.headers.get("content-type") ?? "application/octet-stream";
  const disposition = response.headers.get("content-disposition") ?? "";
  const filenameMatch = disposition.match(/filename="?([^";\s]+)"?/);
  const filename = filenameMatch?.[1] ?? `report.${params.format ?? "pdf"}`;

  const blob = await response.blob();
  return { blob, filename, contentType };
}
