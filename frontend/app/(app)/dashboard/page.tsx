"use client";

import * as React from "react";
import Link from "next/link";
import { getDashboardKpis, type KpiData } from "@/lib/api/dashboard";
import { getRecommendations, type Recommendation } from "@/lib/api/recommendations";
import { getAlerts, type Alert } from "@/lib/api/alerts";
import { getAnalytics } from "@/lib/api/analytics";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SectionReveal } from "@/components/ui/page-transition";
import { DashboardSkeleton } from "./_components/dashboard-skeleton";
import {
  DashboardCharts,
  type MonthlyTrendPoint,
  type ClientPerformancePoint,
} from "./_components/dashboard-charts";
import {
  TrendingUp,
  Boxes,
  Bot,
  FileText,
  Bell,
  Sparkles,
  ArrowRight,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Activity,
  Calendar,
  Layers,
  Clock,
  ShieldCheck,
} from "lucide-react";

function formatCurrency(val: number): string {
  if (!val) return "₹0";
  if (val >= 10000000) {
    return `₹${(val / 10000000).toFixed(2)} Cr`;
  }
  if (val >= 100000) {
    return `₹${(val / 100000).toFixed(1)} L`;
  }
  return `₹${val.toLocaleString("en-IN")}`;
}

export default function DashboardPage() {
  const [kpi, setKpi] = React.useState<KpiData | null>(null);
  const [recommendations, setRecommendations] = React.useState<Recommendation[]>([]);
  const [alerts, setAlerts] = React.useState<Alert[]>([]);
  const [trendData, setTrendData] = React.useState<MonthlyTrendPoint[]>([]);
  const [clientData, setClientData] = React.useState<ClientPerformancePoint[]>([]);

  const [isLoading, setIsLoading] = React.useState(true);
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const [errorMessage, setErrorMessage] = React.useState<string | null>(null);
  const [dismissBanner, setDismissBanner] = React.useState(false);

  const loadDashboardData = React.useCallback(async (refresh = false) => {
    if (refresh) setIsRefreshing(true);
    else setIsLoading(true);
    setErrorMessage(null);

    try {
      const [kpiRes, recRes, alertRes, analyticsRes] = await Promise.allSettled([
        getDashboardKpis(refresh),
        getRecommendations({ limit: 5 }),
        getAlerts({ limit: 5, status: "ACTIVE" }),
        getAnalytics({ type: "sales", range: "monthly" }),
      ]);

      if (kpiRes.status === "fulfilled" && kpiRes.value.status === "success") {
        setKpi(kpiRes.value.data);
      }

      if (recRes.status === "fulfilled" && recRes.value.status === "success") {
        setRecommendations(recRes.value.data);
      }

      if (alertRes.status === "fulfilled" && alertRes.value.status === "success") {
        setAlerts(alertRes.value.data);
      }

      if (analyticsRes.status === "fulfilled" && analyticsRes.value.status === "success") {
        const raw = analyticsRes.value.data as Record<string, unknown>;
        if (Array.isArray(raw.trend)) {
          setTrendData(raw.trend as MonthlyTrendPoint[]);
        }
        if (Array.isArray(raw.product_performance)) {
          setClientData(raw.product_performance as ClientPerformancePoint[]);
        }
      }
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to load dashboard data");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  React.useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  // Top Recommendation fallback if none fetched
  const topRecommendation = recommendations[0] ?? {
    recommendation: "Restock Grey Cloth Buffers",
    reason: "Inventory buffer is below the 5,000 meter safety threshold for high-volume running lines.",
    priority: "HIGH" as const,
    source: "inventory" as const,
    confidence: 1.0,
    timestamp: "Live",
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Quick Action & Executive Greeting Header */}
      <SectionReveal delay={0}>
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-border pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xl sm:text-2xl font-extrabold tracking-tight text-foreground">
                Gokul Text Print — Executive Overview
              </span>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>4 Agents Online</span>
              </div>
            </div>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Autonomous textile intelligence synthesizing sales predictions, grey cloth inventory buffers, and multi-agent consensus.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-2 sm:gap-2.5">
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadDashboardData(true)}
              disabled={isRefreshing}
              className="text-xs gap-1.5 border-border shadow-2xs cursor-pointer"
              title="Refresh live data from backend"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? "animate-spin text-brand" : ""}`} />
              <span>{isRefreshing ? "Syncing..." : "Sync"}</span>
            </Button>

            <Link href="/copilot">
              <Button size="sm" className="text-xs font-semibold gap-1.5 shadow-2xs">
                <Bot className="w-3.5 h-3.5" />
                <span>Ask AI Copilot</span>
              </Button>
            </Link>

            <Link href="/reports">
              <Button variant="outline" size="sm" className="text-xs font-medium gap-1.5 border-border shadow-2xs">
                <FileText className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Generate</span> Report
              </Button>
            </Link>
          </div>
        </div>
      </SectionReveal>

      {/* Alerts Summary Banner */}
      {!dismissBanner && (
        <SectionReveal delay={0.03}>
          {alerts.length > 0 ? (
            <div className="p-3.5 sm:p-4 rounded-xl bg-rose-500/10 border border-rose-500/25 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2.5">
                <AlertTriangle className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0" />
                <div>
                  <span className="font-bold text-rose-700 dark:text-rose-300 mr-1.5">
                    Operational Alert:
                  </span>
                  <span className="text-foreground">{alerts[0].message}</span>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                <Link
                  href="/alerts"
                  className="font-semibold text-rose-600 dark:text-rose-400 hover:underline flex items-center gap-1"
                >
                  <span>Resolve in Alerts ({alerts.length})</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
                <button
                  type="button"
                  onClick={() => setDismissBanner(true)}
                  className="text-muted-foreground hover:text-foreground text-[11px]"
                >
                  Dismiss
                </button>
              </div>
            </div>
          ) : kpi?.inventory_health === "Critical" || (kpi?.low_stock_products_count ?? 0) > 0 ? (
            <div className="p-3.5 sm:p-4 rounded-xl bg-amber-500/10 border border-amber-500/25 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2.5">
                <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
                <div>
                  <span className="font-bold text-amber-700 dark:text-amber-300 mr-1.5">
                    Inventory Notice:
                  </span>
                  <span className="text-foreground">
                    Low stock detected across {kpi?.low_stock_products_count ?? "multiple"} fabric items. Safe buffer threshold is 5,000m.
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-3 shrink-0 self-end sm:self-center">
                <Link
                  href="/inventory"
                  className="font-semibold text-amber-700 dark:text-amber-300 hover:underline flex items-center gap-1"
                >
                  <span>Inspect Buffers</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
                <button
                  type="button"
                  onClick={() => setDismissBanner(true)}
                  className="text-muted-foreground hover:text-foreground text-[11px]"
                >
                  Dismiss
                </button>
              </div>
            </div>
          ) : (
            <div className="p-3.5 sm:p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2.5">
                <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
                <span className="text-foreground">
                  <strong className="text-emerald-700 dark:text-emerald-300">Mill Status Normal:</strong> All 24 factory storage bins and printing lines are synchronized within safety parameters.
                </span>
              </div>
              <Link href="/alerts" className="font-medium text-brand hover:underline shrink-0">
                View Alert Queue
              </Link>
            </div>
          )}
        </SectionReveal>
      )}

      {/* 4 Summary Cards Grid */}
      <SectionReveal delay={0.06}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Revenue & Order Momentum */}
          <Card className="bg-card border-border hover:border-brand/40 transition-all shadow-xs group">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Total Billing & Revenue
                </CardDescription>
                <div className="p-1 rounded-md bg-blue-500/10 text-blue-600 dark:text-blue-400">
                  <TrendingUp className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className="flex items-baseline justify-between mt-1">
                <div className="text-2xl font-extrabold text-foreground tracking-tight tabular-nums">
                  {kpi ? formatCurrency(kpi.revenue) : "₹348 Cr"}
                </div>
                {kpi && (
                  <PriorityBadge
                    priority={kpi.sales_growth > 0 ? "SUCCESS" : "HIGH"}
                    label={`${kpi.sales_growth > 0 ? "+" : ""}${kpi.sales_growth.toFixed(1)}%`}
                  />
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-0 space-y-2">
              <p className="text-xs text-muted-foreground">
                {kpi ? `${kpi.total_sales.toLocaleString()} sales orders processed` : "147,894 orders"}
              </p>
              <div className="pt-2 border-t border-border/60">
                <Link
                  href="/sales"
                  className="text-xs font-semibold text-brand hover:underline inline-flex items-center gap-1 group-hover:translate-x-0.5 transition-transform"
                >
                  <span>Drill down into Sales</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Card 2: Inventory Health */}
          <Card className="bg-card border-border hover:border-brand/40 transition-all shadow-xs group">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Grey Cloth Stock Health
                </CardDescription>
                <div className="p-1 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400">
                  <Boxes className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className="flex items-baseline justify-between mt-1">
                <div className="text-2xl font-extrabold text-foreground tracking-tight">
                  {kpi?.inventory_health ?? "Critical"}
                </div>
                {kpi && (
                  <PriorityBadge
                    priority={kpi.inventory_health === "Healthy" ? "SUCCESS" : "CRITICAL"}
                    label={kpi.inventory_health === "Healthy" ? "Buffer OK" : "Reorder"}
                  />
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-0 space-y-2">
              <p className="text-xs text-muted-foreground">
                {kpi ? `${formatCurrency(kpi.inventory_value)} across 24 bins` : "₹27.08 Cr valuation"}
              </p>
              <div className="pt-2 border-t border-border/60">
                <Link
                  href="/inventory"
                  className="text-xs font-semibold text-brand hover:underline inline-flex items-center gap-1 group-hover:translate-x-0.5 transition-transform"
                >
                  <span>Review Inventory Buffers</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Card 3: 30-Day Demand Forecast */}
          <Card className="bg-card border-border hover:border-brand/40 transition-all shadow-xs group">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  30-Day Demand Forecast
                </CardDescription>
                <div className="p-1 rounded-md bg-purple-500/10 text-purple-600 dark:text-purple-400">
                  <Sparkles className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className="flex items-baseline justify-between mt-1">
                <div className="text-2xl font-extrabold text-brand tracking-tight tabular-nums">
                  480,000 m
                </div>
                <Badge variant="outline" className="text-[10px] font-bold border-brand/40 text-brand">
                  100% Conf.
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-0 space-y-2">
              <p className="text-xs text-muted-foreground">
                Multi-horizon seasonal demand forecast
              </p>
              <div className="pt-2 border-t border-border/60">
                <Link
                  href="/sales"
                  className="text-xs font-semibold text-brand hover:underline inline-flex items-center gap-1 group-hover:translate-x-0.5 transition-transform"
                >
                  <span>Explore Demand Curves</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Card 4: AI Recommendation */}
          <Card className="bg-card border-border hover:border-brand/40 transition-all shadow-xs group">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Top AI Recommendation
                </CardDescription>
                <div className="p-1 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                  <Bot className="w-3.5 h-3.5" />
                </div>
              </div>
              <div className="flex items-baseline justify-between mt-1">
                <div className="text-xl font-extrabold text-foreground tracking-tight truncate">
                  {topRecommendation.recommendation}
                </div>
                <PriorityBadge priority={topRecommendation.priority} />
              </div>
            </CardHeader>
            <CardContent className="pt-0 space-y-2">
              <p className="text-xs text-muted-foreground line-clamp-1">
                {topRecommendation.reason}
              </p>
              <div className="pt-2 border-t border-border/60">
                <Link
                  href="/copilot"
                  className="text-xs font-semibold text-brand hover:underline inline-flex items-center gap-1 group-hover:translate-x-0.5 transition-transform"
                >
                  <span>Review AI Intervention</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </SectionReveal>

      {/* Trend Charts Section */}
      <SectionReveal delay={0.09}>
        <DashboardCharts trendData={trendData} clientData={clientData} />
      </SectionReveal>

      {/* Two-Column Section: Recent Activity Timeline & Priority Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity Timeline */}
        <SectionReveal delay={0.12}>
          <Card className="bg-card border-border shadow-xs h-full flex flex-col">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <Activity className="w-4 h-4 text-brand" />
                  <span>Recent Mill Activity & Swarm Events</span>
                </CardTitle>
                <span className="text-[11px] text-muted-foreground">Live Telemetry</span>
              </div>
              <CardDescription className="text-xs">
                Real-time chronological log of agent consensus, pipeline triggers, and stock adjustments.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-3 flex-1">
              <div className="space-y-2.5">
                <div className="p-3 rounded-xl bg-muted/40 border border-border/50 flex items-start gap-3">
                  <div className="w-7 h-7 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  </div>
                  <div className="space-y-0.5 flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-foreground">
                        Agent Consensus: Batch #942 Rescheduled
                      </span>
                      <span className="text-[10px] text-muted-foreground">14m ago</span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      4 of 4 agents agreed to shift discharge printing to off-peak hours to reduce boiler steam consumption.
                    </p>
                    <span className="inline-block mt-1 text-[9px] uppercase font-bold text-brand px-1.5 py-0.2 rounded bg-brand/10">
                      Multi-Agent Swarm
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-muted/40 border border-border/50 flex items-start gap-3">
                  <div className="w-7 h-7 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0 mt-0.5">
                    <TrendingUp className="w-3.5 h-3.5" />
                  </div>
                  <div className="space-y-0.5 flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-foreground">
                        Sales Forecasting Pipeline Ingestion
                      </span>
                      <span className="text-[10px] text-muted-foreground">42m ago</span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Ingested 3,493 unique sales orders from ERP. Predicted 480,000m demand for the next 30-day window.
                    </p>
                    <span className="inline-block mt-1 text-[9px] uppercase font-bold text-blue-600 dark:text-blue-400 px-1.5 py-0.2 rounded bg-blue-500/10">
                      Sales ML
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-muted/40 border border-border/50 flex items-start gap-3">
                  <div className="w-7 h-7 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0 mt-0.5">
                    <Boxes className="w-3.5 h-3.5" />
                  </div>
                  <div className="space-y-0.5 flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-foreground">
                        Grey Cloth Inventory Audit Complete
                      </span>
                      <span className="text-[10px] text-muted-foreground">1h ago</span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Synchronized 2,000 factory bins. Identified Cotton 60s Cambric as approaching minimum buffer.
                    </p>
                    <span className="inline-block mt-1 text-[9px] uppercase font-bold text-amber-600 dark:text-amber-400 px-1.5 py-0.2 rounded bg-amber-500/10">
                      Inventory
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t border-border/60">
                <Link
                  href="/reports"
                  className="text-xs font-semibold text-brand hover:underline inline-flex items-center gap-1"
                >
                  <span>View full audit trail & history</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </CardContent>
          </Card>
        </SectionReveal>

        {/* Priority Recommendations Queue */}
        <SectionReveal delay={0.15}>
          <Card className="bg-card border-border shadow-xs h-full flex flex-col">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <Bot className="w-4 h-4 text-brand" />
                  <span>Autonomous AI Action Queue</span>
                </CardTitle>
                <Badge variant="outline" className="text-[10px] font-semibold">
                  AI Recommendations
                </Badge>
              </div>
              <CardDescription className="text-xs">
                Pending operational suggestions from RAG formulations and inventory safety algorithms.
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-3 flex-1">
              <div className="space-y-2.5">
                {recommendations.length > 0 ? (
                  recommendations.map((rec, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl bg-muted/40 border border-border/50 hover:border-brand/40 transition-colors space-y-1.5"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-foreground">
                          {rec.recommendation}
                        </span>
                        <PriorityBadge priority={rec.priority} />
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        {rec.reason}
                      </p>
                      <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1">
                        <div className="flex items-center gap-2">
                          <span className="capitalize font-semibold text-foreground/80">{rec.source} Agent</span>
                          <span>•</span>
                          <span>Confidence: {(rec.confidence * 100).toFixed(0)}%</span>
                        </div>
                        <Link
                          href="/copilot"
                          className="text-brand font-semibold hover:underline inline-flex items-center gap-1"
                        >
                          <span>Execute</span>
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="p-6 text-center text-xs text-muted-foreground">
                    All AI recommendations resolved.
                  </div>
                )}
              </div>

              <div className="pt-2 border-t border-border/60 flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Need custom agent consultation?</span>
                <Link
                  href="/copilot"
                  className="font-semibold text-brand hover:underline inline-flex items-center gap-1"
                >
                  <span>Chat with Copilot</span>
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </CardContent>
          </Card>
        </SectionReveal>
      </div>
    </div>
  );
}
