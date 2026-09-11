/*
 * app/dashboard/page.tsx
 * ----------------------
 * Sprint 7 -- Design System Showcase + KPI Smoke Test
 *
 * Server Component that:
 *   1. Fetches GET /api/dashboard/kpis (confirms API client + CORS)
 *   2. Renders all design-system primitives as a visual showcase:
 *      Card, PriorityBadge, SkeletonCard, ThemeToggle, SectionReveal
 *   3. Delegates the sortable DataTable to <DemoTable> (client component)
 */

import type { Metadata } from "next";
import { getDashboardKpis, type KpiResponse } from "@/lib/api/dashboard";
import { API_BASE_URL } from "@/lib/api/client";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge } from "@/components/ui/badge";
import { SkeletonCard } from "@/components/ui/skeleton";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { SectionReveal } from "@/components/ui/page-transition";
import { DemoTable } from "./_components/demo-table";

export const metadata: Metadata = {
  title: "Dashboard | Gokul Text Print",
  description: "Sprint 7 design system showcase and KPI smoke test.",
};

export const dynamic = "force-dynamic";

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
    errorMessage = err instanceof Error ? err.message : "Unknown error";
  }

  const isSuccess = kpiData?.status === "success";
  const kpi = kpiData?.data;

  return (
    <main className="min-h-screen bg-background text-foreground">

      {/* Sticky top bar with ThemeToggle */}
      <header className="sticky top-0 z-10 border-b border-[var(--surface-border)] bg-[var(--surface-1)] backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
          <div className="flex items-center gap-2.5">
            <span className="text-lg" aria-hidden="true">🏭</span>
            <div>
              <h1 className="text-sm font-semibold text-foreground leading-tight">
                Gokul Text Print
              </h1>
              <p className="text-xs text-muted-foreground">Enterprise AI Platform</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground hidden sm:block">Sprint 7</span>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-8 space-y-10">

        {/* Section 1: API Smoke Test */}
        <SectionReveal delay={0}>
          <div className="mb-6">
            <h2 className="text-xl font-bold tracking-tight text-foreground">
              API Client Smoke Test
            </h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Verifies{" "}
              <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs text-foreground">
                GET /api/dashboard/kpis
              </code>{" "}
              is reachable from Next.js with CORS configured correctly.
            </p>
          </div>

          <Card variant="default">
            <CardHeader
              action={
                isSuccess ? (
                  <PriorityBadge priority="SUCCESS" label="Success" />
                ) : (
                  <PriorityBadge priority="CRITICAL" label="Error" />
                )
              }
            >
              <CardTitle>{API_BASE_URL}/api/dashboard/kpis</CardTitle>
              <CardDescription>
                Response time: {durationMs !== null ? `${durationMs} ms` : "--"}
                {kpi?.cached ? " · cached" : " · live"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {errorMessage ? (
                <p className="text-sm text-destructive">{errorMessage}</p>
              ) : (
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  {[
                    { label: "Total Sales", value: kpi?.total_sales?.toLocaleString() ?? "-" },
                    {
                      label: "Revenue",
                      value: kpi
                        ? `INR ${Number(kpi.revenue).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`
                        : "-",
                    },
                    {
                      label: "Sales Growth",
                      value: kpi
                        ? `${kpi.sales_growth > 0 ? "+" : ""}${kpi.sales_growth.toFixed(1)}%`
                        : "-",
                    },
                    {
                      label: "Business Health",
                      value: kpi
                        ? `${kpi.business_health.score.toFixed(0)} -- ${kpi.business_health.status}`
                        : "-",
                    },
                  ].map(({ label, value }) => (
                    <div
                      key={label}
                      className="rounded-lg bg-[var(--surface-2)] p-3 border border-[var(--surface-border)]"
                    >
                      <p className="text-xs font-medium text-muted-foreground mb-1">{label}</p>
                      <p className="text-base font-semibold tabular-nums text-foreground">{value}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </SectionReveal>

        {/* Section 2: Component Showcase */}
        <SectionReveal delay={0.08}>
          <h2 className="text-xl font-bold tracking-tight text-foreground mb-6">
            Design System Components
          </h2>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">

            {/* Priority Badges */}
            <Card variant="default">
              <CardHeader>
                <CardTitle>Priority Badges</CardTitle>
                <CardDescription>
                  Maps directly to Flask alert / recommendation priority strings
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex flex-wrap gap-2">
                    {(["CRITICAL", "HIGH", "MEDIUM", "LOW", "SUCCESS"] as const).map((p) => (
                      <PriorityBadge key={p} priority={p} />
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {(["CRITICAL", "HIGH", "MEDIUM", "LOW", "SUCCESS"] as const).map((p) => (
                      <PriorityBadge key={p} priority={p} showDot={false} />
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-2 items-center">
                    {(["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const).map((p) => (
                      <PriorityBadge key={p} priority={p} label={`Alert: ${p}`} />
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Card variants */}
            <Card variant="default">
              <CardHeader>
                <CardTitle>Card Variants</CardTitle>
                <CardDescription>default · elevated · outline · ghost</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(["default", "elevated", "outline", "ghost"] as const).map((v) => (
                    <Card key={v} variant={v} padding="sm">
                      <span className="text-xs font-mono text-muted-foreground">
                        variant=&quot;{v}&quot;
                      </span>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Skeleton loaders */}
            <Card variant="default">
              <CardHeader>
                <CardTitle>Skeleton Loaders</CardTitle>
                <CardDescription>
                  Displayed while data is fetching -- also used inside DataTable rows
                </CardDescription>
              </CardHeader>
              <CardContent>
                <SkeletonCard bodyLines={2} showFooter />
              </CardContent>
            </Card>

            {/* Typography */}
            <Card variant="default">
              <CardHeader>
                <CardTitle>Typography Scale</CardTitle>
                <CardDescription>Named type constants from lib/design-system</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <p className="text-2xl font-bold tracking-tight text-foreground">Page Title -- 2xl bold</p>
                  <p className="text-lg font-semibold tracking-tight text-foreground">Section Title -- lg semibold</p>
                  <p className="text-sm font-semibold text-foreground">Card Title -- sm semibold</p>
                  <p className="text-sm text-foreground">Body -- sm regular</p>
                  <p className="text-sm text-muted-foreground">Body Muted -- sm muted</p>
                  <p className="text-xs text-muted-foreground">Caption -- xs muted</p>
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                    Label -- xs upper tracked
                  </p>
                  <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs text-foreground">
                    code -- mono xs
                  </code>
                </div>
              </CardContent>
            </Card>

          </div>
        </SectionReveal>

        {/* Section 3: DataTable demo (client component) */}
        <SectionReveal delay={0.16}>
          <h2 className="text-xl font-bold tracking-tight text-foreground mb-4">
            DataTable -- Sortable Demo
          </h2>
          <DemoTable kpi={kpi} />
        </SectionReveal>

        <footer className="pt-4 border-t border-[var(--surface-border)] text-center">
          <p className="text-xs text-muted-foreground">
            Sprint 7 · Next.js App Router · Tailwind CSS v4 · Shadcn UI · Framer Motion · Recharts
          </p>
        </footer>

      </div>
    </main>
  );
}
