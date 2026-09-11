import * as React from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  TrendingDown,
  Clock,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Award,
  ArrowRight,
} from "lucide-react";

interface RoiMetric {
  stat: string;
  label: string;
  subtext: string;
  icon: React.ComponentType<{ className?: string }>;
  accentColor: string;
}

const ROI_METRICS: RoiMetric[] = [
  {
    stat: "34%",
    label: "Deadstock Reduction",
    subtext: "Freed capital previously locked in stagnant grey cloth & aging reactive dyes.",
    icon: TrendingDown,
    accentColor: "text-emerald-600 dark:text-emerald-400",
  },
  {
    stat: "4.2x",
    label: "Faster Order Quoting",
    subtext: "Instant multi-agent synthesis of dye formulas, fabric yield, and delivery timelines.",
    icon: Clock,
    accentColor: "text-brand",
  },
  {
    stat: "99.1%",
    label: "Color Batch Repeatability",
    subtext: "Sub-0.5 Delta E color consistency achieved with automated RAG recipe guidance.",
    icon: Award,
    accentColor: "text-indigo-600 dark:text-indigo-400",
  },
  {
    stat: "0",
    label: "Unplanned Line Halts",
    subtext: "Proactive dye buffer alerts and machine error troubleshooting prevent line shutdowns.",
    icon: CheckCircle2,
    accentColor: "text-amber-600 dark:text-amber-400",
  },
];

const COMPARISON_ROWS = [
  {
    capability: "Sales Demand Forecasting",
    traditional: "Manual Excel estimation based on gut feeling, frequent over/under-stocking.",
    gokul: "Algorithmic 90-day demand curves factoring in festive cycles and client buying habits.",
  },
  {
    capability: "Chemical Dye Inventory",
    traditional: "Periodic physical counts; dyes expire or run out mid-production shift.",
    gokul: "Automated dynamic buffer tracking with CRITICAL/HIGH priority threshold alerts.",
  },
  {
    capability: "Recipe Formulation & SOPs",
    traditional: "Paper logbooks scattered on mill floor; tribal knowledge lost when staff leaves.",
    gokul: "Instant digital search across verified color recipes and operational SOPs.",
  },
  {
    capability: "Operational Decisions",
    traditional: "Siloed communication between sales desk and shop floor leads to friction.",
    gokul: "Autonomous operational copilot aligning sales orders, warehouse stock, and machine lines.",
  },
];

export function BusinessBenefitsSection() {
  return (
    <section className="py-16 lg:py-24 bg-muted/40 border-t border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
          <Badge variant="outline" className="text-xs font-semibold px-3 py-1 text-emerald-600 dark:text-emerald-400 border-emerald-500/30">
            Measurable Mill ROI
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground">
            Proven Commercial & Operational Impact
          </h2>
          <p className="text-base sm:text-lg text-muted-foreground">
            Gokul Text Print transforms high-volume textile printing from a reactive craft into an
            optimized, predictable, and autonomous enterprise operation.
          </p>
        </div>

        {/* 4 Large ROI Stat Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {ROI_METRICS.map((metric, idx) => {
            const Icon = metric.icon;
            return (
              <Card key={idx} className="bg-card border-border shadow-xs hover:border-brand/50 transition-colors">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      KPI Metric
                    </span>
                    <Icon className="w-5 h-5 text-muted-foreground" />
                  </div>
                  <div className={`text-4xl font-extrabold tracking-tight tabular-nums ${metric.accentColor}`}>
                    {metric.stat}
                  </div>
                  <CardTitle className="text-base font-bold text-foreground mt-1">
                    {metric.label}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {metric.subtext}
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Traditional Mill vs Gokul AI Comparison Table */}
        <div className="mt-12 bg-card border border-border rounded-xl p-6 sm:p-8 shadow-xs">
          <div className="max-w-2xl mb-6">
            <h3 className="text-xl font-bold text-foreground">
              The Autonomous Mill Advantage
            </h3>
            <p className="text-sm text-muted-foreground">
              Comparing conventional textile printing operations with the Gokul Text Print Platform.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th className="py-3.5 px-4 font-semibold text-foreground w-1/4">Operational Area</th>
                  <th className="py-3.5 px-4 font-semibold text-muted-foreground w-3/8">Traditional Mill Workflow</th>
                  <th className="py-3.5 px-4 font-semibold text-brand w-3/8">Gokul Text Print Platform</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {COMPARISON_ROWS.map((row, idx) => (
                  <tr key={idx} className="hover:bg-muted/30 transition-colors">
                    <td className="py-4 px-4 font-medium text-foreground align-top">
                      {row.capability}
                    </td>
                    <td className="py-4 px-4 text-xs text-muted-foreground align-top">
                      <div className="flex items-start gap-2">
                        <XCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                        <span>{row.traditional}</span>
                      </div>
                    </td>
                    <td className="py-4 px-4 text-xs text-foreground align-top font-medium">
                      <div className="flex items-start gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{row.gokul}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Bottom CTA within card */}
          <div className="mt-8 pt-6 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-xs text-muted-foreground">
              Want a customized ROI projection for your factory's specific meter capacity?
            </p>
            <Link href="/contact">
              <Button size="sm" className="gap-1.5 text-xs font-semibold">
                <span>Calculate Your Mill Savings</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
