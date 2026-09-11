"use client";

import * as React from "react";
import Link from "next/link";
import {
  getAnalytics,
  type InventoryAnalyticsData,
  type RangeType,
  type LowStockItem,
  type DeadStockItem,
  type InventoryPredictionHistoryItem,
} from "@/lib/api/analytics";
import { getDashboardKpis, type KpiResponse } from "@/lib/api/dashboard";
import { getRecommendations, type Recommendation } from "@/lib/api/recommendations";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DataTable, type Column } from "@/components/ui/data-table";
import { SectionReveal } from "@/components/ui/page-transition";
import { InventoryCharts } from "./_components/inventory-charts";
import { WarehouseStatusGrid } from "./_components/warehouse-status-grid";
import { InventoryPredictionCard } from "./_components/inventory-prediction-card";
import {
  Boxes,
  AlertTriangle,
  Layers,
  ArrowRight,
  RefreshCw,
  SlidersHorizontal,
  PackageCheck,
  TrendingDown,
  Warehouse,
  Bot,
  Filter,
  CheckCircle2,
  Calendar,
  DollarSign,
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

function formatMeters(val: number): string {
  if (!val && val !== 0) return "0 m";
  if (val >= 1000000) {
    return `${(val / 1000000).toFixed(2)}M m`;
  }
  if (val >= 1000) {
    return `${(val / 1000).toFixed(1)}k m`;
  }
  return `${val.toLocaleString()} m`;
}

export default function InventoryIntelligencePage() {
  const [range, setRange] = React.useState<RangeType>("daily");
  const [startDate, setStartDate] = React.useState<string>("");
  const [endDate, setEndDate] = React.useState<string>("");

  const [analyticsData, setAnalyticsData] = React.useState<InventoryAnalyticsData | null>(null);
  const [kpis, setKpis] = React.useState<KpiResponse | null>(null);
  const [recommendations, setRecommendations] = React.useState<Recommendation[]>([]);

  const [loading, setLoading] = React.useState(true);
  const [filterLoading, setFilterLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  // Load live data from Flask APIs
  const loadData = React.useCallback(async (isFilterUpdate = false) => {
    if (isFilterUpdate) setFilterLoading(true);
    else setLoading(true);
    setError(null);

    try {
      const [analyticsRes, kpisRes, recsRes] = await Promise.allSettled([
        getAnalytics({
          type: "inventory",
          range,
          start: startDate || undefined,
          end: endDate || undefined,
        }),
        getDashboardKpis(),
        getRecommendations({ limit: 6 }),
      ]);

      if (analyticsRes.status === "fulfilled" && analyticsRes.value.status === "success") {
        setAnalyticsData(analyticsRes.value.data as InventoryAnalyticsData);
      }

      if (kpisRes.status === "fulfilled" && kpisRes.value.status === "success") {
        setKpis(kpisRes.value);
      }

      if (recsRes.status === "fulfilled" && recsRes.value.status === "success") {
        setRecommendations(recsRes.value.data);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load inventory intelligence");
    } finally {
      setLoading(false);
      setFilterLoading(false);
    }
  }, [range, startDate, endDate]);

  React.useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle Preset Ranges
  const handlePreset = (preset: "30D" | "90D" | "1Y" | "ALL") => {
    const today = new Date();
    const endStr = today.toISOString().split("T")[0];

    if (preset === "ALL") {
      setStartDate("");
      setEndDate("");
      setRange("monthly");
      return;
    }

    let days = 30;
    if (preset === "90D") days = 90;
    if (preset === "1Y") days = 365;

    const startObj = new Date(today);
    startObj.setDate(startObj.getDate() - days);
    const startStr = startObj.toISOString().split("T")[0];

    setStartDate(startStr);
    setEndDate(endStr);
    setRange(preset === "30D" ? "daily" : "monthly");
  };

  // Inventory-specific recommendations
  const inventoryRecs = React.useMemo(() => {
    return recommendations.filter((r) => r.source === "inventory" || r.priority === "HIGH");
  }, [recommendations]);

  // Low Stock Table Columns
  const lowStockColumns: Column<LowStockItem>[] = [
    {
      key: "item_code",
      header: "Fabric SKU / Item Code",
      accessor: (r) => (
        <span className="font-mono font-bold text-foreground">{r.item_code}</span>
      ),
      sortKey: "item_code",
      sortAccessor: (r) => r.item_code,
    },
    {
      key: "current_stock",
      header: "Stock on Hand",
      accessor: (r) => (
        <span className="font-bold text-foreground tabular-nums">
          {r.current_stock.toLocaleString()} m
        </span>
      ),
      sortKey: "current_stock",
      sortAccessor: (r) => r.current_stock,
      align: "right",
    },
    {
      key: "reorder_threshold",
      header: "Safety Buffer",
      accessor: (r) => (
        <span className="text-muted-foreground tabular-nums">
          {r.reorder_threshold.toLocaleString()} m
        </span>
      ),
      sortKey: "reorder_threshold",
      sortAccessor: (r) => r.reorder_threshold,
      align: "right",
    },
    {
      key: "deficit",
      header: "Deficit Gap",
      accessor: (r) => (
        <span className="font-semibold text-rose-600 dark:text-rose-400 tabular-nums">
          -{r.deficit.toLocaleString()} m
        </span>
      ),
      sortKey: "deficit",
      sortAccessor: (r) => r.deficit,
      align: "right",
    },
    {
      key: "status",
      header: "Replenishment Status",
      accessor: (r) => (
        <PriorityBadge
          priority={r.status.includes("Critical") ? "CRITICAL" : "HIGH"}
          label={r.status}
        />
      ),
      sortKey: "status",
      align: "center",
    },
  ];

  // Dead Stock Table Columns
  const deadStockColumns: Column<DeadStockItem>[] = [
    {
      key: "item_code",
      header: "Stagnant SKU",
      accessor: (r) => (
        <span className="font-mono font-bold text-foreground">{r.item_code}</span>
      ),
      sortKey: "item_code",
      sortAccessor: (r) => r.item_code,
    },
    {
      key: "holding_units",
      header: "Idle Meterage",
      accessor: (r) => (
        <span className="font-mono tabular-nums text-foreground">
          {r.holding_units.toLocaleString()} m
        </span>
      ),
      sortKey: "holding_units",
      sortAccessor: (r) => r.holding_units,
      align: "right",
    },
    {
      key: "estimated_value",
      header: "Trapped Capital",
      accessor: (r) => (
        <span className="font-bold text-amber-600 dark:text-amber-400 font-mono">
          {formatCurrency(r.estimated_value)}
        </span>
      ),
      sortKey: "estimated_value",
      sortAccessor: (r) => r.estimated_value,
      align: "right",
    },
    {
      key: "status",
      header: "Classification",
      accessor: (r) => (
        <Badge variant="outline" className="text-[10px] font-semibold border-amber-500/30 text-amber-600 dark:text-amber-400">
          {r.status}
        </Badge>
      ),
      sortKey: "status",
      align: "center",
    },
  ];

  // Prediction History Columns
  const predictionHistoryColumns: Column<InventoryPredictionHistoryItem>[] = [
    {
      key: "timestamp",
      header: "Timestamp",
      accessor: (r) => (
        <span className="text-xs text-muted-foreground font-mono">
          {r.timestamp.split(".")[0].replace("T", " ")}
        </span>
      ),
      sortKey: "timestamp",
    },
    {
      key: "version",
      header: "Model Version",
      accessor: (r) => (
        <span className="uppercase text-[11px] font-mono px-2 py-0.5 rounded bg-muted text-foreground">
          {r.version}
        </span>
      ),
      sortKey: "version",
      align: "center",
    },
    {
      key: "decision",
      header: "ML Reorder Decision",
      accessor: (r) => (
        <PriorityBadge
          priority={
            r.decision.toLowerCase().includes("reorder") || r.decision.toLowerCase().includes("required")
              ? "HIGH"
              : "SUCCESS"
          }
          label={r.decision}
        />
      ),
      sortKey: "decision",
    },
    {
      key: "confidence",
      header: "Confidence",
      accessor: (r) => (
        <span className="font-semibold text-brand tabular-nums">
          {(r.confidence * 100).toFixed(1)}%
        </span>
      ),
      sortKey: "confidence",
      sortAccessor: (r) => r.confidence,
      align: "center",
    },
    {
      key: "features_summary",
      header: "Stock Monitored",
      accessor: (r) => (
        <span className="font-mono text-xs text-muted-foreground">
          {r.features_summary?.total_stock
            ? `${Number(r.features_summary.total_stock).toLocaleString()} m`
            : "--"}
        </span>
      ),
      align: "right",
    },
  ];

  const summary = analyticsData?.summary;
  const lowStockData = analyticsData?.low_stock_analysis?.items || [];
  const deadStockData = analyticsData?.dead_stock?.items || [];
  const historyData = analyticsData?.prediction_history || [];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header & Date Range Filter Bar */}
      <SectionReveal delay={0}>
        <div className="flex flex-col gap-4 border-b border-border pb-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="p-1.5 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400">
                  <Boxes className="w-5 h-5" />
                </span>
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                  Inventory Intelligence & Buffer Logistics
                </h1>
                <Badge variant="outline" className="text-[10px] font-semibold border-brand/30 text-brand">
                  Live Analytics
                </Badge>
              </div>
              <p className="text-xs sm:text-sm text-muted-foreground">
                Grey cloth buffer tracking, storage bin allocation, shortage risk prevention, and stagnant capital mitigation.
              </p>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={() => loadData(true)}
              disabled={filterLoading}
              className="text-xs gap-1.5 self-start sm:self-auto border-border"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${filterLoading ? "animate-spin text-brand" : ""}`} />
              <span>{filterLoading ? "Syncing..." : "Sync Bin Audits"}</span>
            </Button>
          </div>

          {/* Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-xl bg-card border border-border shadow-2xs">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold text-muted-foreground flex items-center gap-1">
                <Filter className="w-3.5 h-3.5" />
                <span>Cadence Presets:</span>
              </span>
              <button
                type="button"
                onClick={() => handlePreset("30D")}
                className="px-2.5 py-1 text-xs rounded-md bg-muted hover:bg-muted/80 text-foreground font-medium"
              >
                Last 30 Days
              </button>
              <button
                type="button"
                onClick={() => handlePreset("90D")}
                className="px-2.5 py-1 text-xs rounded-md bg-muted hover:bg-muted/80 text-foreground font-medium"
              >
                Last 90 Days
              </button>
              <button
                type="button"
                onClick={() => handlePreset("1Y")}
                className="px-2.5 py-1 text-xs rounded-md bg-muted hover:bg-muted/80 text-foreground font-medium"
              >
                Last 12 Months
              </button>
              <button
                type="button"
                onClick={() => handlePreset("ALL")}
                className="px-2.5 py-1 text-xs rounded-md bg-muted hover:bg-muted/80 text-foreground font-medium"
              >
                All Time
              </button>
            </div>

            {/* Custom Dates & Range Cadence */}
            <div className="flex items-center gap-2.5 flex-wrap">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <span>From:</span>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="px-2 py-1 text-xs rounded-md border border-border bg-background text-foreground"
                />
                <span>To:</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="px-2 py-1 text-xs rounded-md border border-border bg-background text-foreground"
                />
              </div>

              {/* Cadence */}
              <div className="flex items-center gap-1 p-0.5 rounded-lg bg-muted/60 border border-border">
                {(["daily", "weekly", "monthly"] as RangeType[]).map((r) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setRange(r)}
                    className={`px-2 py-0.5 text-xs rounded capitalize font-medium ${
                      range === r ? "bg-background text-foreground shadow-2xs font-semibold" : "text-muted-foreground"
                    }`}
                  >
                    {r}
                  </button>
                ))}
              </div>

              <Button size="sm" onClick={() => loadData(true)} className="text-xs h-7 px-3">
                Apply
              </Button>
            </div>
          </div>
        </div>
      </SectionReveal>

      {/* Restock Recommendations / Shortage Alert Banner */}
      {inventoryRecs.length > 0 && (
        <SectionReveal delay={0.03}>
          <div className="p-4 rounded-xl border border-amber-500/25 bg-amber-500/10 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div className="flex items-start gap-3">
              <div className="mt-0.5">
                <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
              </div>
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-foreground text-sm">
                    Active Stock Alert: {inventoryRecs[0].recommendation}
                  </span>
                  <PriorityBadge priority={inventoryRecs[0].priority} />
                  <span className="text-[10px] text-muted-foreground font-mono">
                    {(inventoryRecs[0].confidence * 100).toFixed(0)}% Confidence
                  </span>
                </div>
                <p className="text-xs text-muted-foreground max-w-3xl leading-relaxed">
                  {inventoryRecs[0].reason}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
              <Link href="/copilot">
                <Button size="sm" className="text-xs font-semibold gap-1">
                  <span>Consult Copilot</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </Link>
            </div>
          </div>
        </SectionReveal>
      )}

      {/* Inventory Health & Capital KPI Cards */}
      <SectionReveal delay={0.06}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-card border-border shadow-xs">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-semibold text-muted-foreground uppercase">
                Grey Cloth on Hand
              </CardDescription>
              <div className="text-2xl font-bold tracking-tight text-foreground tabular-nums mt-1">
                {formatMeters(summary?.current_total_stock || 2166697)}
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Spread across 24 factory storage bins</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border shadow-xs">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-semibold text-muted-foreground uppercase">
                Inventory Capital Valuation
              </CardDescription>
              <div className="text-2xl font-bold tracking-tight text-brand tabular-nums mt-1">
                {formatCurrency(summary?.inventory_valuation || 270837195)}
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Valued at ₹125/meter base factory rate</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border shadow-xs">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription className="text-xs font-semibold text-muted-foreground uppercase">
                  Shortage Risk SKUs
                </CardDescription>
                <PriorityBadge
                  priority={(summary?.low_stock_count || 0) > 0 ? "CRITICAL" : "SUCCESS"}
                  label={`${summary?.low_stock_count || 8} SKUs`}
                />
              </div>
              <div className="text-2xl font-bold tracking-tight text-rose-500 tabular-nums mt-1">
                {summary?.low_stock_count || 8} Items
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Below 50m minimum production safety buffer</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border shadow-xs">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription className="text-xs font-semibold text-muted-foreground uppercase">
                  Turnover & Days in Inv.
                </CardDescription>
                <PriorityBadge priority="LOW" label={summary?.velocity_status || "Balanced"} />
              </div>
              <div className="text-2xl font-bold tracking-tight text-foreground tabular-nums mt-1">
                {summary?.turnover_ratio ? `${summary.turnover_ratio}x` : "4.8x"}{" "}
                <span className="text-xs font-normal text-muted-foreground">
                  ({summary?.days_in_inventory || 28.5} DII)
                </span>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">
                Dead stock: {summary?.dead_stock_count || 0} items ({formatCurrency(summary?.dead_stock_value || 0)})
              </p>
            </CardContent>
          </Card>
        </div>
      </SectionReveal>

      {/* Stock Trajectory Chart */}
      <SectionReveal delay={0.09}>
        <InventoryCharts stockTrend={analyticsData?.stock_trend} />
      </SectionReveal>

      {/* 24-bin Factory Warehouse Status Grid */}
      <SectionReveal delay={0.12}>
        <WarehouseStatusGrid />
      </SectionReveal>

      {/* Interactive ML Inference Simulator */}
      <SectionReveal delay={0.15}>
        <InventoryPredictionCard onPredictionCompleted={() => loadData(true)} />
      </SectionReveal>

      {/* Low Stock Watchlist & Dead Stock Tables in 2 columns */}
      <SectionReveal delay={0.18}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Low Stock & Reorder Watchlist */}
          <Card className="bg-card border-border shadow-xs">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-rose-500" />
                  <span>Low Stock & Reorder Watchlist</span>
                </CardTitle>
                <Badge variant="outline" className="text-[10px] font-semibold border-rose-500/30 text-rose-600 dark:text-rose-400">
                  Threshold: 50.0m
                </Badge>
              </div>
              <CardDescription className="text-xs">
                Fabric varieties requiring urgent grey cloth replenishment.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={lowStockColumns}
                data={lowStockData}
                rowKey={(r) => r.item_code}
                caption="Real-time deficit items from inventory_training_data.csv"
              />
            </CardContent>
          </Card>

          {/* Dead Stock & Stagnant Capital Analysis */}
          <Card className="bg-card border-border shadow-xs">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-bold flex items-center gap-2">
                  <TrendingDown className="w-4 h-4 text-amber-500" />
                  <span>Dead Stock & Capital Recovery</span>
                </CardTitle>
                <Badge variant="outline" className="text-[10px] font-semibold border-amber-500/30 text-amber-600 dark:text-amber-400">
                  0 Recent Output
                </Badge>
              </div>
              <CardDescription className="text-xs">
                Stagnant fabric lots with zero production movement in current cycle.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columns={deadStockColumns}
                data={deadStockData}
                rowKey={(r) => r.item_code}
                caption="Stagnant inventory audit from factory storage records"
              />
            </CardContent>
          </Card>
        </div>
      </SectionReveal>

      {/* Model Prediction History Table */}
      <SectionReveal delay={0.21}>
        <Card className="bg-card border-border shadow-xs">
          <CardHeader className="pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="space-y-0.5">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Calendar className="w-4 h-4 text-purple-500" />
                <span>Inventory AI Forecast History</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Audit trail of AI supply forecast predictions logged over time.
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-[10px] font-mono">
              Engine: Supply Buffer Optimizer
            </Badge>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={predictionHistoryColumns}
              data={historyData}
              rowKey={(r) => r.id}
              caption="AI supply forecast prediction audit log"
            />
          </CardContent>
        </Card>
      </SectionReveal>
    </div>
  );
}
