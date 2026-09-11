import type { Metadata } from "next";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SectionReveal } from "@/components/ui/page-transition";
import {
  TrendingUp,
  BarChart3,
  Calendar,
  Layers,
  ArrowUpRight,
  Filter,
  Download,
  Sparkles,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Sales Intelligence | Gokul Text Print",
  description: "Predictive demand forecasting and order prioritization for textile mills.",
};

export default function SalesIntelligencePage() {
  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <SectionReveal delay={0}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-md bg-blue-500/10 text-blue-600 dark:text-blue-400">
                <TrendingUp className="w-5 h-5" />
              </span>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                Sales Intelligence
              </h2>
              <Badge variant="outline" className="text-[10px] font-semibold border-brand/30 text-brand">
                Step 6 Staging
              </Badge>
            </div>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Predictive 30-day meter demand forecasting, client volume rankings, and booking momentum.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <Button variant="outline" size="sm" className="text-xs gap-1.5 border-border">
              <Filter className="w-3.5 h-3.5" />
              <span>Filter Fabric</span>
            </Button>
            <Button size="sm" className="text-xs gap-1.5 font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Run Demand Model</span>
            </Button>
          </div>
        </div>
      </SectionReveal>

      {/* KPI Cards */}
      <SectionReveal delay={0.05}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-medium">30-Day Forecast Demand</CardDescription>
              <div className="flex items-baseline justify-between">
                <div className="text-2xl font-bold text-foreground">1,248,500 m</div>
                <PriorityBadge priority="SUCCESS" label="+8.4%" />
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Projected meters across all 6 fabric types</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-medium">Top Revenue Fabric</CardDescription>
              <div className="flex items-baseline justify-between">
                <div className="text-2xl font-bold text-brand">Cotton 60s Cambric</div>
                <Badge variant="outline" className="text-[10px] font-bold">42% Mix</Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Estimated ₹48.2L billing this cycle</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-medium">Active Mill Clients</CardDescription>
              <div className="flex items-baseline justify-between">
                <div className="text-2xl font-bold text-foreground">84 Parties</div>
                <PriorityBadge priority="LOW" label="Stable" />
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">12 repeat enterprise orders in queue</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-medium">Model Forecast Accuracy</CardDescription>
              <div className="flex items-baseline justify-between">
                <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">96.8%</div>
                <Badge variant="outline" className="text-[10px] font-semibold border-emerald-500/30 text-emerald-500">
                  Validated
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Cross-validated against 3,493 ERP orders</p>
            </CardContent>
          </Card>
        </div>
      </SectionReveal>

      {/* Preview Section */}
      <SectionReveal delay={0.1}>
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-base flex items-center justify-between">
              <span>Predictive Demand vs Production Capacity (Meters)</span>
              <span className="text-xs font-normal text-muted-foreground">Next 4 Weeks</span>
            </CardTitle>
            <CardDescription>
              Historical seasonal trends combined with pending print orders from ERP.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Visual Chart Placeholder */}
            <div className="h-64 rounded-xl border border-dashed border-border flex flex-col items-center justify-center p-6 text-center bg-muted/20">
              <BarChart3 className="w-10 h-10 text-muted-foreground/60 mb-2 animate-pulse" />
              <h4 className="text-sm font-semibold text-foreground">
                Recharts Demand Visualizer Ready
              </h4>
              <p className="text-xs text-muted-foreground max-w-md mt-1">
                Full interactive multi-series area chart connecting to Flask GET /api/sales/forecast will be rendered in Step 6.
              </p>
            </div>
          </CardContent>
        </Card>
      </SectionReveal>
    </div>
  );
}
