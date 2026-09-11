"use client";

import * as React from "react";
import { type ReportType } from "@/lib/api/reports";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import {
  FileText,
  TrendingUp,
  Boxes,
  ShieldCheck,
  AlertTriangle,
  Bot,
  Calendar,
  Building2,
  CheckCircle2,
} from "lucide-react";

interface ReportPreviewCardProps {
  reportType: ReportType;
  startDate?: string;
  endDate?: string;
}

export function ReportPreviewCard({
  reportType,
  startDate,
  endDate,
}: ReportPreviewCardProps) {
  const getTitle = () => {
    switch (reportType) {
      case "daily":
        return "Daily Executive Performance Briefing";
      case "weekly":
        return "Weekly Plant & Demand Intelligence Summary";
      case "monthly":
        return "Monthly Enterprise Business Audit & Variance";
      case "custom":
        return `Custom Period Audit (${startDate || "Start"} to ${endDate || "Today"})`;
    }
  };

  const getScope = () => {
    switch (reportType) {
      case "daily":
        return "24-Hour Production Cycle • Shed 1 & Shed 2 • Rotary Machines 1-6";
      case "weekly":
        return "7-Day Aggregation • Client Order Run Rates • Safety Buffer Compliance";
      case "monthly":
        return "30-Day Closed Period • Financial Revenue Reconciliation • Dead Stock Audit";
      case "custom":
        return "Custom Range Analytics • Multi-Domain Synthesis";
    }
  };

  const getMetrics = () => {
    switch (reportType) {
      case "daily":
        return {
          revenue: "₹1.15 Cr",
          volume: "4,820 m",
          stock: "2.17M m",
          valuation: "₹27.08 Cr",
          growth: "+5.2%",
          health: "92 / 100",
          reorderCount: "2 Items",
          recommendation: "Maintain steady printing run on Cotton 60s rotary line #2.",
        };
      case "weekly":
        return {
          revenue: "₹8.42 Cr",
          volume: "35,400 m",
          stock: "2.14M m",
          valuation: "₹26.75 Cr",
          growth: "+12.4%",
          health: "88 / 100",
          reorderCount: "3 Items",
          recommendation: "Scale reactive dye orders for Rayon 30s print base to avert deficit.",
        };
      case "monthly":
        return {
          revenue: "₹34.80 Cr",
          volume: "147,894 m",
          stock: "2.16M m",
          valuation: "₹27.08 Cr",
          growth: "+8.7%",
          health: "85 / 100",
          reorderCount: "8 Items",
          recommendation: "Execute discount dispatch on 1,420m stagnant satin stock.",
        };
      case "custom":
        return {
          revenue: "₹14.20 Cr",
          volume: "62,100 m",
          stock: "2.15M m",
          valuation: "₹26.90 Cr",
          growth: "+10.1%",
          health: "87 / 100",
          reorderCount: "4 Items",
          recommendation: "Balanced replenishment across Sheds 1 & 2.",
        };
    }
  };

  const m = getMetrics();

  return (
    <Card className="bg-card border-border shadow-md overflow-hidden">
      {/* Mill Header Banner */}
      <div className="bg-muted/40 border-b border-border p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand/10 border border-brand/20 flex items-center justify-center text-brand shrink-0">
            <Building2 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-base text-foreground tracking-tight">
                {getTitle()}
              </h3>
              <Badge variant="outline" className="uppercase font-mono text-[10px] text-brand border-brand/30">
                Official Report
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">{getScope()}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto text-xs text-muted-foreground font-mono">
          <Calendar className="w-3.5 h-3.5" />
          <span>Generated: {new Date().toLocaleDateString("en-IN", { month: "short", day: "numeric", year: "numeric" })}</span>
        </div>
      </div>

      <CardContent className="p-4 sm:p-6 space-y-6">
        {/* Executive Summary Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="p-3 rounded-xl border border-border bg-card/60 space-y-1">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase flex items-center gap-1">
              <TrendingUp className="w-3.5 h-3.5 text-blue-500" />
              <span>Revenue Total</span>
            </span>
            <div className="text-lg sm:text-xl font-bold font-mono text-foreground">{m.revenue}</div>
            <div className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold">{m.growth} vs prior</div>
          </div>

          <div className="p-3 rounded-xl border border-border bg-card/60 space-y-1">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase flex items-center gap-1">
              <Boxes className="w-3.5 h-3.5 text-amber-500" />
              <span>Grey Cloth Stock</span>
            </span>
            <div className="text-lg sm:text-xl font-bold font-mono text-foreground">{m.stock}</div>
            <div className="text-[11px] text-muted-foreground">Valuation: {m.valuation}</div>
          </div>

          <div className="p-3 rounded-xl border border-border bg-card/60 space-y-1">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase flex items-center gap-1">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />
              <span>Shortage Risk</span>
            </span>
            <div className="text-lg sm:text-xl font-bold font-mono text-rose-500">{m.reorderCount}</div>
            <div className="text-[11px] text-muted-foreground">&lt; 50m buffer safety</div>
          </div>

          <div className="p-3 rounded-xl border border-border bg-card/60 space-y-1">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
              <span>Health Score</span>
            </span>
            <div className="text-lg sm:text-xl font-bold font-mono text-emerald-600 dark:text-emerald-400">{m.health}</div>
            <div className="text-[11px] text-muted-foreground">Optimal Operational Index</div>
          </div>
        </div>

        {/* Section 1: Strategic AI Directive */}
        <div className="p-3.5 rounded-xl border border-purple-500/20 bg-purple-500/5 text-xs flex items-start gap-3">
          <Bot className="w-4 h-4 text-purple-600 dark:text-purple-400 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-bold text-foreground">Orchestrated Executive Directive:</span>
            <p className="text-muted-foreground leading-relaxed">{m.recommendation}</p>
          </div>
        </div>

        {/* Section 2: Key Operational Highlights in Report */}
        <div className="space-y-2.5 pt-1">
          <span className="text-xs font-bold text-foreground flex items-center gap-1.5 uppercase tracking-wider">
            <FileText className="w-3.5 h-3.5 text-brand" />
            <span>Document Sections Included in Export</span>
          </span>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
            <div className="p-2.5 rounded-lg border border-border/60 bg-muted/20 flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
              <span className="text-foreground">Revenue Breakdown & Client Sales Volume Ledger</span>
            </div>
            <div className="p-2.5 rounded-lg border border-border/60 bg-muted/20 flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
              <span className="text-foreground">24 Factory Bins Grey Cloth Inventory & Safety Buffer Audit</span>
            </div>
            <div className="p-2.5 rounded-lg border border-border/60 bg-muted/20 flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
              <span className="text-foreground">XGBoost & Prophet Multi-Horizon Demand Projections</span>
            </div>
            <div className="p-2.5 rounded-lg border border-border/60 bg-muted/20 flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
              <span className="text-foreground">Operational Alerts Log & Automated Reorder Dispatchers</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
