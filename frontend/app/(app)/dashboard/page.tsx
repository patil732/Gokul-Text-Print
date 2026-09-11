import type { Metadata } from "next";
import Link from "next/link";
import { getDashboardKpis, type KpiResponse } from "@/lib/api/dashboard";
import { API_BASE_URL } from "@/lib/api/client";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { SkeletonCard } from "@/components/ui/skeleton";
import { SectionReveal } from "@/components/ui/page-transition";
import { DemoTable } from "./_components/demo-table";
import {
  TrendingUp,
  Boxes,
  Bot,
  BookOpen,
  FileText,
  Bell,
  ArrowRight,
  Activity,
  Sparkles,
  ShieldCheck,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Executive Dashboard | Gokul Text Print",
  description: "Autonomous industrial textile mill intelligence hub.",
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
    <div className="p-4 sm:p-6 lg:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Welcome Banner */}
      <SectionReveal delay={0}>
        <div className="rounded-2xl p-6 bg-gradient-to-r from-brand/15 via-brand/5 to-transparent border border-brand/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="inline-flex items-center gap-2">
              <Badge variant="outline" className="text-[10px] uppercase font-bold border-brand/40 bg-brand/10 text-brand">
                Live Operations
              </Badge>
              <span className="text-xs text-muted-foreground">Mill Dispatcher v2.4</span>
            </div>
            <h2 className="text-xl sm:text-2xl font-extrabold tracking-tight text-foreground">
              Executive Mill Overview
            </h2>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Autonomous textile intelligence unifying sales predictions, grey cloth buffers, and agent consensus.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Link
              href="/copilot"
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold bg-brand text-brand-fg shadow-xs hover:opacity-95 transition-opacity"
            >
              <Sparkles className="w-4 h-4" />
              <span>Launch AI Copilot</span>
            </Link>
          </div>
        </div>
      </SectionReveal>

      {/* KPI Highlight Grid */}
      <SectionReveal delay={0.05}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-medium">Business Health Score</CardDescription>
              <div className="flex items-baseline justify-between">
                <div className="text-2xl font-bold tracking-tight text-foreground tabular-nums">
                  {kpi ? `${kpi.business_health.score.toFixed(1)} / 100` : "--"}
                </div>
                {kpi && (
                  <PriorityBadge
                    priority={
                      kpi.business_health.score >= 70
                        ? "SUCCESS"
                        : kpi.business_health.score >= 40
                          ? "MEDIUM"
                          : "CRITICAL"
                    }
                    label={kpi.business_health.status}
                  />
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Aggregated across sales velocity and margins</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-medium">Sales Momentum</CardDescription>
              <div className="flex items-baseline justify-between">
                <div className="text-2xl font-bold tracking-tight text-foreground tabular-nums">
                  {kpi ? `${kpi.sales_growth > 0 ? "+" : ""}${kpi.sales_growth.toFixed(1)}%` : "--"}
                </div>
                {kpi && (
                  <PriorityBadge
                    priority={kpi.sales_growth > 0 ? "SUCCESS" : "HIGH"}
                    label={kpi.sales_growth > 0 ? "Growing" : "Declining"}
                  />
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Month-over-month revenue trend</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-medium">Inventory Stock Buffer</CardDescription>
              <div className="flex items-baseline justify-between">
                <div className="text-2xl font-bold tracking-tight text-foreground">
                  {kpi?.inventory_health ?? "--"}
                </div>
                {kpi && (
                  <PriorityBadge
                    priority={kpi.inventory_health === "Healthy" ? "SUCCESS" : "HIGH"}
                    label={`${kpi.low_stock_products_count} Critical`}
                  />
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Grey cloth meters vs minimum safety threshold</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-medium">Active AI Interventions</CardDescription>
              <div className="flex items-baseline justify-between">
                <div className="text-2xl font-bold tracking-tight text-brand tabular-nums">
                  {kpi?.ai_recommendations_count ?? "--"}
                </div>
                <Badge variant="outline" className="text-[10px] font-semibold border-brand/30 text-brand">
                  Consensus
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Production & chemical dye optimizations pending</p>
            </CardContent>
          </Card>
        </div>
      </SectionReveal>

      {/* Backend API Smoke Test Card */}
      <SectionReveal delay={0.1}>
        <Card className="bg-card border-border">
          <CardHeader
            action={
              isSuccess ? (
                <PriorityBadge priority="SUCCESS" label="Connected" />
              ) : (
                <PriorityBadge priority="CRITICAL" label="Error" />
              )
            }
          >
            <CardTitle className="text-base">Flask API Connectivity Smoke Test</CardTitle>
            <CardDescription>
              Endpoint: <code className="text-xs text-foreground font-mono bg-muted px-1.5 py-0.5 rounded">{API_BASE_URL}/api/dashboard/kpis</code> · Latency: {durationMs !== null ? `${durationMs} ms` : "--"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isSuccess && kpi ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                <div className="p-3 rounded-lg bg-muted/40 border border-border/60">
                  <span className="text-muted-foreground block">Pipeline Status</span>
                  <span className="font-semibold text-foreground mt-0.5 block">{kpi.business_health.status}</span>
                </div>
                <div className="p-3 rounded-lg bg-muted/40 border border-border/60">
                  <span className="text-muted-foreground block">Cache Policy</span>
                  <span className="font-semibold text-foreground mt-0.5 block">{kpi.cached ? "Cached" : "Live Real-Time"}</span>
                </div>
                <div className="p-3 rounded-lg bg-muted/40 border border-border/60">
                  <span className="text-muted-foreground block">Low-Stock Watchlist</span>
                  <span className="font-semibold text-foreground mt-0.5 block">{kpi.low_stock_products_count} fabric rolls</span>
                </div>
                <div className="p-3 rounded-lg bg-muted/40 border border-border/60">
                  <span className="text-muted-foreground block">AI Swarm Status</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400 mt-0.5 block">4/4 Consensus Ready</span>
                </div>
              </div>
            ) : (
              <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-xs text-destructive">
                {errorMessage || "Failed to reach backend."}
              </div>
            )}
          </CardContent>
        </Card>
      </SectionReveal>

      {/* Sortable DataTable */}
      <SectionReveal delay={0.15}>
        <div className="space-y-3">
          <div>
            <h3 className="text-base font-bold text-foreground">Operational Metric Audit</h3>
            <p className="text-xs text-muted-foreground">Interactive table demonstrating sorting and priority badges.</p>
          </div>
          <DemoTable kpi={kpi} />
        </div>
      </SectionReveal>

      {/* Quick Navigation Cards */}
      <SectionReveal delay={0.2}>
        <div>
          <h3 className="text-base font-bold text-foreground mb-3">Mill Intelligence Modules</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <Link
              href="/sales"
              className="p-4 rounded-xl bg-card border border-border hover:border-brand/40 hover:shadow-md transition-all group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4" />
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-brand group-hover:translate-x-1 transition-all" />
              </div>
              <h4 className="text-sm font-bold text-foreground group-hover:text-brand transition-colors">
                Sales Intelligence
              </h4>
              <p className="text-xs text-muted-foreground mt-1">
                Forecast future meter demand and prioritize profitable client bookings.
              </p>
            </Link>

            <Link
              href="/inventory"
              className="p-4 rounded-xl bg-card border border-border hover:border-brand/40 hover:shadow-md transition-all group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                  <Boxes className="w-4 h-4" />
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-brand group-hover:translate-x-1 transition-all" />
              </div>
              <h4 className="text-sm font-bold text-foreground group-hover:text-brand transition-colors">
                Inventory Intelligence
              </h4>
              <p className="text-xs text-muted-foreground mt-1">
                Maintain 5,000m safety stock buffers and eliminate deadstock pileup.
              </p>
            </Link>

            <Link
              href="/copilot"
              className="p-4 rounded-xl bg-card border border-border hover:border-brand/40 hover:shadow-md transition-all group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center">
                  <Bot className="w-4 h-4" />
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-brand group-hover:translate-x-1 transition-all" />
              </div>
              <h4 className="text-sm font-bold text-foreground group-hover:text-brand transition-colors">
                AI Copilot
              </h4>
              <p className="text-xs text-muted-foreground mt-1">
                Multi-agent chat with access to orders, dye formulations, and dispatcher consensus.
              </p>
            </Link>

            <Link
              href="/knowledge"
              className="p-4 rounded-xl bg-card border border-border hover:border-brand/40 hover:shadow-md transition-all group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                  <BookOpen className="w-4 h-4" />
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-brand group-hover:translate-x-1 transition-all" />
              </div>
              <h4 className="text-sm font-bold text-foreground group-hover:text-brand transition-colors">
                Knowledge Base
              </h4>
              <p className="text-xs text-muted-foreground mt-1">
                Browse chemical dye recipes, technical mill manuals, and defect mitigation SOPs.
              </p>
            </Link>

            <Link
              href="/reports"
              className="p-4 rounded-xl bg-card border border-border hover:border-brand/40 hover:shadow-md transition-all group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 rounded-lg bg-sky-500/10 text-sky-600 dark:text-sky-400 flex items-center justify-center">
                  <FileText className="w-4 h-4" />
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-brand group-hover:translate-x-1 transition-all" />
              </div>
              <h4 className="text-sm font-bold text-foreground group-hover:text-brand transition-colors">
                Executive Reports
              </h4>
              <p className="text-xs text-muted-foreground mt-1">
                Generate production audit summaries and download compliance reports.
              </p>
            </Link>

            <Link
              href="/alerts"
              className="p-4 rounded-xl bg-card border border-border hover:border-brand/40 hover:shadow-md transition-all group"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="w-8 h-8 rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400 flex items-center justify-center">
                  <Bell className="w-4 h-4" />
                </div>
                <ArrowRight className="w-4 h-4 text-muted-foreground group-hover:text-brand group-hover:translate-x-1 transition-all" />
              </div>
              <h4 className="text-sm font-bold text-foreground group-hover:text-brand transition-colors">
                Operational Alerts
              </h4>
              <p className="text-xs text-muted-foreground mt-1">
                Real-time queue for low-stock alarms, defect spikes, and swarm consensus flags.
              </p>
            </Link>
          </div>
        </div>
      </SectionReveal>
    </div>
  );
}
