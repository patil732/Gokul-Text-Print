"use client";

/*
 * app/dashboard/_components/demo-table.tsx
 * ------------------------------------------
 * Client component wrapper for the design-system DataTable demo.
 *
 * Must be "use client" because DataTable uses useState internally,
 * and its column accessor/rowKey props are functions that cannot be
 * serialized across the RSC boundary from a Server Component.
 */

import { DataTable, type Column } from "@/components/ui/data-table";
import { PriorityBadge } from "@/components/ui/badge";
import type { KpiResponse } from "@/lib/api/dashboard";

interface DemoRow {
  metric: string;
  value: string;
  status: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "SUCCESS";
  trend: string;
}

interface DemoTableProps {
  kpi: KpiResponse["data"] | undefined;
}

export function DemoTable({ kpi }: DemoTableProps) {
  const rows: DemoRow[] = [
    {
      metric: "Business Health Score",
      value: kpi ? `${kpi.business_health.score.toFixed(1)}` : "-",
      status:
        (kpi?.business_health.score ?? 0) >= 70
          ? "SUCCESS"
          : (kpi?.business_health.score ?? 0) >= 40
            ? "MEDIUM"
            : "CRITICAL",
      trend: kpi?.business_health.status ?? "-",
    },
    {
      metric: "Sales Growth",
      value: kpi
        ? `${kpi.sales_growth > 0 ? "+" : ""}${kpi.sales_growth.toFixed(1)}%`
        : "-",
      status:
        (kpi?.sales_growth ?? 0) > 0
          ? "SUCCESS"
          : (kpi?.sales_growth ?? 0) > -10
            ? "MEDIUM"
            : "HIGH",
      trend: (kpi?.sales_growth ?? 0) > 0 ? "Growing" : "Declining",
    },
    {
      metric: "Inventory Health",
      value: kpi?.inventory_health ?? "-",
      status:
        kpi?.inventory_health === "Healthy"
          ? "SUCCESS"
          : kpi?.inventory_health === "Low"
            ? "HIGH"
            : "CRITICAL",
      trend: `${kpi?.low_stock_products_count ?? 0} low-stock items`,
    },
    {
      metric: "AI Recommendations",
      value: String(kpi?.ai_recommendations_count ?? "-"),
      status: "LOW",
      trend: "Available",
    },
  ];

  const columns: Column<DemoRow>[] = [
    {
      key: "metric",
      header: "Metric",
      accessor: (r) => r.metric,
      sortKey: "metric",
    },
    {
      key: "value",
      header: "Value",
      accessor: (r) => (
        <span className="font-semibold tabular-nums">{r.value}</span>
      ),
      sortKey: "value",
      sortAccessor: (r) => r.value,
    },
    {
      key: "status",
      header: "Status",
      accessor: (r) => <PriorityBadge priority={r.status} />,
      sortKey: "status",
      sortAccessor: (r) => r.status,
      align: "center",
    },
    {
      key: "trend",
      header: "Details",
      accessor: (r) => (
        <span className="text-muted-foreground">{r.trend}</span>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={rows}
      rowKey={(r) => r.metric}
      caption="Live KPI data from GET /api/dashboard/kpis -- click column headers to sort"
    />
  );
}
