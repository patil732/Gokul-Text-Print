import type { Metadata } from "next";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SectionReveal } from "@/components/ui/page-transition";
import {
  Boxes,
  AlertTriangle,
  Layers,
  ArrowRight,
  RefreshCw,
  SlidersHorizontal,
  PackageCheck,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Inventory Intelligence | Gokul Text Print",
  description: "Grey cloth safety buffers, stock depletion monitoring, and shortage risk.",
};

export default function InventoryIntelligencePage() {
  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <SectionReveal delay={0}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400">
                <Boxes className="w-5 h-5" />
              </span>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                Inventory Intelligence
              </h2>
              <Badge variant="outline" className="text-[10px] font-semibold border-brand/30 text-brand">
                Step 7 Staging
              </Badge>
            </div>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Dynamic grey cloth buffer tracking, real-time shortage risk alerts, and stock reconciliation.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <Button variant="outline" size="sm" className="text-xs gap-1.5 border-border">
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Adjust Buffer Thresholds</span>
            </Button>
            <Button size="sm" className="text-xs gap-1.5 font-semibold">
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Sync Mill Bins</span>
            </Button>
          </div>
        </div>
      </SectionReveal>

      {/* KPI Cards */}
      <SectionReveal delay={0.05}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-medium">Total Grey Cloth on Hand</CardDescription>
              <div className="flex items-baseline justify-between">
                <div className="text-2xl font-bold text-foreground">486,200 m</div>
                <PriorityBadge priority="SUCCESS" label="Healthy" />
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Spread across 24 factory storage bins</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-medium">Shortage Risk Items</CardDescription>
              <div className="flex items-baseline justify-between">
                <div className="text-2xl font-bold text-rose-500">2 Items</div>
                <PriorityBadge priority="CRITICAL" label="Action Required" />
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Below 5,000m minimum production safety stock</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-medium">Stock Turnover Ratio</CardDescription>
              <div className="flex items-baseline justify-between">
                <div className="text-2xl font-bold text-foreground">4.8x</div>
                <PriorityBadge priority="LOW" label="Optimal" />
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Deadstock reduced by 34% since Sprint 4</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-medium">Allocated to Active Batches</CardDescription>
              <div className="flex items-baseline justify-between">
                <div className="text-2xl font-bold text-brand">142,800 m</div>
                <Badge variant="outline" className="text-[10px] font-semibold">Reserved</Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Locked for printing machines 1 through 6</p>
            </CardContent>
          </Card>
        </div>
      </SectionReveal>

      {/* Preview Section */}
      <SectionReveal delay={0.1}>
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-base flex items-center justify-between">
              <span>Grey Cloth Stock Ledger & Safety Threshold Meter</span>
              <span className="text-xs font-normal text-muted-foreground">Live Bin Audit</span>
            </CardTitle>
            <CardDescription>
              Real-time synchronization with Flask inventory endpoints and ERP bin tables.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 rounded-xl border border-dashed border-border flex flex-col items-center justify-center p-6 text-center bg-muted/20">
              <PackageCheck className="w-10 h-10 text-muted-foreground/60 mb-2 animate-pulse" />
              <h4 className="text-sm font-semibold text-foreground">
                Inventory Stock & Reorder Visualizer Ready
              </h4>
              <p className="text-xs text-muted-foreground max-w-md mt-1">
                Full interactive table, low-stock filter, and automated purchase order dispatch will be wired in Step 7.
              </p>
            </div>
          </CardContent>
        </Card>
      </SectionReveal>
    </div>
  );
}
