"use client";

import * as React from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge, PriorityBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  TrendingUp,
  Boxes,
  BookOpen,
  Bot,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  Activity,
} from "lucide-react";

interface MillSolution {
  id: string;
  name: string;
  badge: string;
  icon: React.ComponentType<{ className?: string }>;
  tagline: string;
  description: string;
  capabilities: string[];
  businessChallenge: string;
  operationalApproach: string;
  measurableImpact: string;
  sampleMetrics: {
    metric: string;
    value: string;
    status: "SUCCESS" | "HIGH" | "MEDIUM" | "LOW";
  }[];
}

const MILL_SOLUTIONS: MillSolution[] = [
  {
    id: "solution-sales",
    name: "Sales & Demand Planning",
    badge: "Predictive Growth",
    icon: TrendingUp,
    tagline: "Forecast seasonal fabric demand and prevent lost order opportunities",
    description:
      "Replaces spreadsheet guesswork with automated demand intelligence. Analyzes multi-year client buying cadences, regional wedding seasons, and festive surge patterns so your mill knows exactly what fabric blends to prepare weeks in advance.",
    capabilities: [
      "30/60/90-day SKU-level demand forecasting",
      "Festive and wedding season fabric surge projections",
      "Client repeat ordering cycle indicators & churn detection",
      "Profitable order pricing and volume discount recommendations",
    ],
    businessChallenge: "Unpredictable order volumes causing stockouts and missed delivery dates",
    operationalApproach: "Proactive demand visibility across all active wholesale accounts",
    measurableImpact: "99.4% Order Demand Precision · +28% Timely Delivery Rate",
    sampleMetrics: [
      { metric: "Order Forecast Precision", value: "99.4%", status: "SUCCESS" },
      { metric: "Festive Demand Surge (Jacquard)", value: "+38.2%", status: "HIGH" },
      { metric: "Client Retention Rate", value: "97.9%", status: "SUCCESS" },
    ],
  },
  {
    id: "solution-inventory",
    name: "Inventory & Buffer Optimization",
    badge: "Working Capital Protection",
    icon: Boxes,
    tagline: "Keep grey cloth and reactive dyes in balance without tying up capital",
    description:
      "Maintains live visibility across unprinted greige fabric rolls, yarn reserve, reactive dyes, and auxiliary chemicals. Automatically flags aging batches before they degrade and alerts purchasing managers when safety buffers run low.",
    capabilities: [
      "Real-time stock turnover tracking across warehouse bays",
      "Early warning alerts for slow-moving fabric and aging dyes",
      "Dynamic safety stock buffers adjusted for supplier lead times",
      "One-click automated replenishment recommendations",
    ],
    businessChallenge: "Capital locked in stagnant fabric while urgent jobs halt for dye",
    operationalApproach: "Continuous automated balance between floor usage and lead times",
    measurableImpact: "34% Average Working Capital Freed · 0 Unplanned Halts",
    sampleMetrics: [
      { metric: "Working Capital Freed", value: "34.1%", status: "SUCCESS" },
      { metric: "Stock Turnover Velocity", value: "6.8x / year", status: "SUCCESS" },
      { metric: "Active Chemical Buffer Health", value: "Optimal", status: "SUCCESS" },
    ],
  },
  {
    id: "solution-recipes",
    name: "Color Kitchen & SOP Intelligence",
    badge: "Color Repeatability",
    icon: BookOpen,
    tagline: "Certified dye recipes and operating procedures at operator fingertips",
    description:
      "Brings all mill knowledge—textile color mixing formulations, exact dye ratios, GSM fabric standards, and machine error troubleshooting—into an instant, searchable knowledge base for zero-error color consistency.",
    capabilities: [
      "Instant formula lookups with certified dye and chemical ratios",
      "Sub-0.5 Delta-E color repeatability across repeated print runs",
      "Rotary screen and digital printer troubleshooting playbooks",
      "Standard operating procedure (SOP) compliance and operator guidance",
    ],
    businessChallenge: "Tribal knowledge lost with staff turnover; high batch color variance",
    operationalApproach: "Centralized verified digital formulations and step-by-step SOPs",
    measurableImpact: "Sub-0.5 Delta-E Precision · 100% Formulation Retention",
    sampleMetrics: [
      { metric: "Batch Color Variance (ΔE)", value: "0.32 ΔE", status: "SUCCESS" },
      { metric: "Recipe Lookup Speed", value: "Instant", status: "SUCCESS" },
      { metric: "Formulation Retention", value: "100%", status: "SUCCESS" },
    ],
  },
  {
    id: "solution-copilot",
    name: "Executive Operational Copilot",
    badge: "Autonomous Coordination",
    icon: Bot,
    tagline: "Instant cross-department coordination for high-stakes mill decisions",
    description:
      "Acts as an executive co-pilot that instantly checks sales commitments against floor inventory and machine schedules. Get clear feasibility assessments, order confirmations, and urgent anomaly alerts without chasing supervisors.",
    capabilities: [
      "Instant feasibility checks for rush wholesale fabric orders",
      "Cross-department trade-off analysis between sales and production",
      "Executive summaries and automated daily shift briefings",
      "One-click escalation and priority anomaly alert management",
    ],
    businessChallenge: "Communication gaps between sales team and mill production managers",
    operationalApproach: "Unified operational intelligence evaluating order feasibility instantly",
    measurableImpact: "4.2x Faster Order Quoting · Automated Shift Oversight",
    sampleMetrics: [
      { metric: "Order Quoting Turnaround", value: "4.2x Faster", status: "SUCCESS" },
      { metric: "Feasibility Assessment Confidence", value: "99.1%", status: "SUCCESS" },
      { metric: "Cross-Department Alignment", value: "Real-Time", status: "SUCCESS" },
    ],
  },
];

export function ArchitectureSection() {
  const [activeSolutionId, setActiveSolutionId] = React.useState<string>("solution-sales");
  const activeSolution = MILL_SOLUTIONS.find((s) => s.id === activeSolutionId) || MILL_SOLUTIONS[0];
  const ActiveIcon = activeSolution.icon;

  return (
    <section id="how-it-works" className="py-16 lg:py-24 bg-muted/30 border-y border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-14">
          <Badge variant="outline" className="text-xs font-semibold px-3 py-1 text-brand border-brand/30">
            Operational Excellence · Core Pillars
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground">
            How Autonomous AI Powers Your Mill Operations
          </h2>
          <p className="text-base sm:text-lg text-muted-foreground">
            Designed specifically around the daily reality of industrial textile printing: from sales pipeline
            commitments and warehouse inventory balance to color kitchen formulations and executive decision making.
          </p>
        </div>

        {/* 4 Solution Navigators */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {MILL_SOLUTIONS.map((solution) => {
            const Icon = solution.icon;
            const isSelected = solution.id === activeSolutionId;
            return (
              <button
                key={solution.id}
                type="button"
                onClick={() => setActiveSolutionId(solution.id)}
                className={`text-left p-4 rounded-xl border transition-all duration-200 cursor-pointer ${
                  isSelected
                    ? "bg-card border-brand shadow-sm ring-1 ring-brand/50"
                    : "bg-card/60 hover:bg-card border-border/80 hover:border-border"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      isSelected
                        ? "bg-brand text-brand-fg"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {solution.badge}
                  </span>
                </div>
                <div className="flex items-center gap-2.5">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      isSelected ? "bg-brand-muted text-brand-muted-fg" : "bg-muted text-foreground"
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="text-sm font-bold text-foreground truncate">
                    {solution.name}
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Active Solution Deep Dive Card */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          {/* Main Description */}
          <div className="lg:col-span-7">
            <Card className="h-full border-border bg-card shadow-xs">
              <CardHeader className="space-y-2 pb-4">
                <div className="flex items-center gap-2">
                  <div className="w-9 h-9 rounded-lg bg-brand text-brand-fg flex items-center justify-center">
                    <ActiveIcon className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-xl font-bold">{activeSolution.name}</CardTitle>
                      <Badge variant="secondary" className="text-xs">
                        {activeSolution.badge}
                      </Badge>
                    </div>
                    <CardDescription className="text-sm font-medium text-brand">
                      {activeSolution.tagline}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-5 text-sm">
                <p className="text-muted-foreground leading-relaxed">
                  {activeSolution.description}
                </p>

                {/* Core Capabilities */}
                <div className="space-y-2.5">
                  <span className="text-xs font-semibold uppercase tracking-wider text-foreground">
                    Key Operational Capabilities:
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {activeSolution.capabilities.map((cap, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs text-foreground">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{cap}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Business Value Breakdown */}
                <div className="pt-3 border-t border-border/80 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                  <div className="p-2.5 rounded-lg bg-muted/50 space-y-1">
                    <span className="font-semibold text-muted-foreground block text-[11px] uppercase tracking-wider">
                      Business Challenge:
                    </span>
                    <span className="text-foreground leading-snug">{activeSolution.businessChallenge}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-muted/50 space-y-1">
                    <span className="font-semibold text-muted-foreground block text-[11px] uppercase tracking-wider">
                      Operational Approach:
                    </span>
                    <span className="text-foreground leading-snug">{activeSolution.operationalApproach}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-muted/50 space-y-1">
                    <span className="font-semibold text-emerald-600 dark:text-emerald-400 block text-[11px] uppercase tracking-wider">
                      Measurable Impact:
                    </span>
                    <span className="text-foreground font-medium leading-snug">{activeSolution.measurableImpact}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Real-time Telemetry & Dataflow Simulator */}
          <div className="lg:col-span-5">
            <Card className="h-full border-border bg-card/80 shadow-xs flex flex-col justify-between">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                    <Activity className="w-4 h-4 text-brand" />
                    Operational Impact Summary
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                    Live Verified
                  </span>
                </div>
                <CardTitle className="text-base font-semibold text-foreground">
                  Expected Factory Performance
                </CardTitle>
              </CardHeader>

              <CardContent className="space-y-3 flex-1">
                {activeSolution.sampleMetrics.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg border border-border/70 bg-background/80 flex items-center justify-between"
                  >
                    <div>
                      <div className="text-xs text-muted-foreground">{item.metric}</div>
                      <div className="text-base font-bold text-foreground tabular-nums">
                        {item.value}
                      </div>
                    </div>
                    <PriorityBadge priority={item.status} size="sm" />
                  </div>
                ))}

                {/* Workflow Integration Card */}
                <div className="p-3.5 rounded-lg bg-brand-muted/30 border border-brand/20 space-y-2">
                  <div className="flex items-center justify-between text-xs font-semibold text-brand-muted-fg dark:text-brand">
                    <span>Executive Decision Synchronization</span>
                    <Sparkles className="w-3.5 h-3.5" />
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    This pillar continuously updates executive dashboards and mobile alerts, giving factory leadership
                    real-time clarity over order deadlines, inventory safety buffers, and color kitchen standards.
                  </p>
                </div>
              </CardContent>

              <div className="p-4 border-t border-border/80 bg-muted/20 flex items-center justify-between">
                <Link
                  href="/features"
                  className="text-xs font-semibold text-brand hover:underline inline-flex items-center gap-1"
                >
                  <span>Explore All Platform Features</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>

                <Link href="/dashboard">
                  <Button size="sm" variant="outline" className="text-xs h-8">
                    View Live Workspace
                  </Button>
                </Link>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
}
