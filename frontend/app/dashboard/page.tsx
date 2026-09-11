/**
 * app/dashboard/page.tsx
 * ----------------------
 * Sprint 7 Smoke Test — GET /api/dashboard/kpis
 *
 * This server component fetches the KPI endpoint at render time and
 * renders the raw JSON response so we can confirm:
 *   1. The Flask server is reachable from Next.js
 *   2. CORS is configured correctly (no browser-side errors in dev)
 *   3. The typed API client (lib/api/dashboard.ts) returns the right shape
 *
 * Once smoke test passes, this page evolves into the full dashboard UI.
 */

import type { Metadata } from "next";
import { getDashboardKpis, type KpiResponse } from "@/lib/api/dashboard";
import { API_BASE_URL } from "@/lib/api/client";

export const metadata: Metadata = {
  title: "Dashboard KPI Smoke Test | Gokul Text Print",
  description: "Sprint 7 smoke test — verifies the typed API client can call GET /api/dashboard/kpis.",
};

// Disable Next.js caching so every page load hits Flask fresh
export const dynamic = "force-dynamic";

// ---------------------------------------------------------------------------
// Smoke-test component
// ---------------------------------------------------------------------------

export default async function DashboardPage() {
  let kpiData: KpiResponse | null = null;
  let errorMessage: string | null = null;
  let durationMs: number | null = null;

  const t0 = Date.now();

  try {
    kpiData = await getDashboardKpis();
    durationMs = Date.now() - t0;
  } catch (err: unknown) {
    durationMs = Date.now() - t0;
    if (err instanceof Error) {
      errorMessage = err.message;
    } else {
      errorMessage = "Unknown error occurred while fetching KPIs.";
    }
  }

  const isSuccess = kpiData?.status === "success";

  return (
    <main className="min-h-screen bg-gray-950 text-gray-100 p-8 font-mono">
      {/* ── Header ─────────────────────────────────────────────────────── */}
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <span className="text-2xl">🏭</span>
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Gokul Text Print — Enterprise AI Platform
            </h1>
          </div>
          <p className="text-gray-400 text-sm">
            Sprint 7 · API Client Smoke Test
          </p>
        </div>

        {/* ── Test Target Info ───────────────────────────────────────────── */}
        <div className="mb-6 rounded-xl border border-gray-800 bg-gray-900 p-5">
          <h2 className="text-base font-semibold text-gray-200 mb-3">
            🔬 Smoke Test: <code className="text-emerald-400">GET /api/dashboard/kpis</code>
          </h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Base URL</span>
              <div className="text-blue-400 mt-0.5">{API_BASE_URL}</div>
            </div>
            <div>
              <span className="text-gray-500">Full endpoint</span>
              <div className="text-blue-400 mt-0.5">{API_BASE_URL}/api/dashboard/kpis</div>
            </div>
            <div>
              <span className="text-gray-500">Response time</span>
              <div className="text-purple-400 mt-0.5">
                {durationMs !== null ? `${durationMs} ms` : "—"}
              </div>
            </div>
            <div>
              <span className="text-gray-500">Status</span>
              <div className="mt-0.5">
                {isSuccess ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-900/60 px-3 py-0.5 text-emerald-300 text-xs font-semibold ring-1 ring-emerald-700">
                    ✅ SUCCESS
                  </span>
                ) : errorMessage ? (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-red-900/60 px-3 py-0.5 text-red-300 text-xs font-semibold ring-1 ring-red-700">
                    ❌ ERROR
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-800 px-3 py-0.5 text-gray-400 text-xs font-semibold ring-1 ring-gray-700">
                    ⏳ PENDING
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ── Error Panel ────────────────────────────────────────────────── */}
        {errorMessage && (
          <div className="mb-6 rounded-xl border border-red-800 bg-red-950/50 p-5">
            <h2 className="text-sm font-semibold text-red-400 mb-2">⚠️ Error Details</h2>
            <p className="text-red-300 text-sm">{errorMessage}</p>
            <p className="mt-3 text-gray-500 text-xs">
              Common causes: Flask not running on port 5001, CORS misconfiguration, or
              NEXT_PUBLIC_API_BASE_URL not set in frontend/.env.local
            </p>
          </div>
        )}

        {/* ── KPI Quick Summary ──────────────────────────────────────────── */}
        {isSuccess && kpiData?.data && (
          <div className="mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Total Sales", value: kpiData.data.total_sales.toLocaleString() },
              {
                label: "Revenue",
                value: `₹${Number(kpiData.data.revenue).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`,
              },
              {
                label: "Sales Growth",
                value: `${kpiData.data.sales_growth > 0 ? "+" : ""}${kpiData.data.sales_growth.toFixed(1)}%`,
              },
              {
                label: "Business Health",
                value: `${kpiData.data.business_health.score.toFixed(1)} — ${kpiData.data.business_health.status}`,
              },
            ].map(({ label, value }) => (
              <div
                key={label}
                className="rounded-xl border border-gray-800 bg-gray-900 p-4"
              >
                <div className="text-gray-500 text-xs mb-1">{label}</div>
                <div className="text-white font-semibold text-sm">{value}</div>
              </div>
            ))}
          </div>
        )}

        {/* ── Raw JSON ───────────────────────────────────────────────────── */}
        <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
          <div className="flex items-center justify-between px-5 py-3 border-b border-gray-800">
            <h2 className="text-sm font-semibold text-gray-300">
              📦 Raw API Response
            </h2>
            <span className="text-xs text-gray-600">JSON</span>
          </div>
          <pre className="overflow-auto p-5 text-xs leading-relaxed text-gray-300 max-h-[60vh]">
            {kpiData
              ? JSON.stringify(kpiData, null, 2)
              : errorMessage
                ? `Error: ${errorMessage}`
                : "No data received."}
          </pre>
        </div>

        {/* ── Footer ─────────────────────────────────────────────────────── */}
        <p className="mt-6 text-center text-gray-700 text-xs">
          Sprint 7 — Enterprise UI Platform · Next.js {"{"}App Router{"}"} + Tailwind CSS + Shadcn UI + Framer Motion + Recharts
        </p>
      </div>
    </main>
  );
}
