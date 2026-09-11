"use client";

import * as React from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge, PriorityBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageTransition } from "@/components/ui/page-transition";
import {
  TrendingUp,
  Boxes,
  BookOpen,
  Bot,
  BellRing,
  ShieldCheck,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  Filter,
  BarChart3,
  Cpu,
} from "lucide-react";

type CategoryFilter = "all" | "sales" | "inventory" | "rag" | "swarm" | "dashboard";

interface DetailedFeature {
  id: string;
  category: CategoryFilter;
  categoryLabel: string;
  title: string;
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "SUCCESS";
  priorityLabel: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  specs: {
    operationalFocus: string;
    refreshCadence: string;
    millScope: string;
  };
  featuresList: string[];
}

const ALL_FEATURES: DetailedFeature[] = [
  {
    id: "f-1",
    category: "sales",
    categoryLabel: "Sales Intelligence",
    title: "Predictive Order & SKU Demand Engine",
    priority: "CRITICAL",
    priorityLabel: "Revenue Engine",
    icon: TrendingUp,
    description:
      "Forecasts client order quantities across 120+ fabric patterns and blends, analyzing historical invoice trends, lead-time elasticity, and festive surge timing.",
    specs: {
      operationalFocus: "Seasonal Surge Planning & Fabric Procurement",
      refreshCadence: "Daily automated updates at midnight",
      millScope: "Client order history, wholesale quoting pipelines",
    },
    featuresList: [
      "30/60/90-day rolling demand curves with 95% confidence intervals",
      "Diwali, Eid, and regional wedding fabric surge multipliers",
      "Dynamic wholesale price elasticity recommendations",
      "Customer repeat purchasing window notifications",
    ],
  },
  {
    id: "f-2",
    category: "sales",
    categoryLabel: "Sales Intelligence",
    title: "Client Risk & Churn Intelligence",
    priority: "HIGH",
    priorityLabel: "Retention",
    icon: TrendingUp,
    description:
      "Identifies declining order frequency or volume drop-offs from major garment exporters and retail fabric chains before they switch to competing mills.",
    specs: {
      operationalFocus: "Key Account Preservation & Repeat Ordering",
      refreshCadence: "Weekly automated assessment",
      millScope: "Invoicing intervals, dispatch timelines, client purchase velocity",
    },
    featuresList: [
      "Client risk scoring (Low, Moderate, At-Risk)",
      "Suggested incentive discounts tailored to client volume tiers",
      "Sales executive task auto-generation in CRM",
      "Historical order stability benchmarks",
    ],
  },
  {
    id: "f-3",
    category: "inventory",
    categoryLabel: "Inventory Intelligence",
    title: "Grey Cloth & Yarn Buffer Optimization",
    priority: "CRITICAL",
    priorityLabel: "Cost Optimizer",
    icon: Boxes,
    description:
      "Calculates optimal safety stocks for raw unprinted cotton cambric, viscose, satin, and polyester greige, matching production schedules with supplier delivery reliability.",
    specs: {
      operationalFocus: "Zero Stockouts & Working Capital Protection",
      refreshCadence: "Continuous live inventory updates",
      millScope: "Warehouse storage bays, unprinted fabric rolls, yarn reserve",
    },
    featuresList: [
      "Automatic reorder point (ROP) calculation for all greige SKUs",
      "Deadstock early-warning indicator for fabric rolls dormant >30 days",
      "Supplier fulfillment lead-time tracking and variance scoring",
      "Direct replenishment purchase order recommendations",
    ],
  },
  {
    id: "f-4",
    category: "inventory",
    categoryLabel: "Inventory Intelligence",
    title: "Chemical Dye & Auxiliary Shelf-Life Monitor",
    priority: "HIGH",
    priorityLabel: "Wastage Control",
    icon: Boxes,
    description:
      "Tracks reactive dyes, pigment dispersions, sodium alginate thickeners, and fixatives to eliminate lot expiration and prevent expensive batch contamination.",
    specs: {
      operationalFocus: "Eliminate Chemical Expirations & Batch Scrap",
      refreshCadence: "Real-time on stock movement",
      millScope: "Color kitchen dispensary, batch mixing tanks, chemical drums",
    },
    featuresList: [
      "Expiration countdown and FIFO usage prioritization",
      "Automated warning if scheduled printing lacks required dye lots",
      "Chemical consumption efficiency vs theoretical yield",
      "Inventory alerts when dye buffers drop below 48 hours of scheduled runtime",
    ],
  },
  {
    id: "f-5",
    category: "rag",
    categoryLabel: "Recipe & Knowledge",
    title: "Color Kitchen Recipe & Formulation Copilot",
    priority: "HIGH",
    priorityLabel: "Precision Quality",
    icon: BookOpen,
    description:
      "Enables colorists and printing masters to look up exact chemical mixing ratios, binder concentrations, and Delta E tolerances instantly.",
    specs: {
      operationalFocus: "Batch-to-Batch Color Consistency (<0.5 ΔE)",
      refreshCadence: "Instant response (<1 second)",
      millScope: "Certified mill recipe books, chemical formulas, GSM standards",
    },
    featuresList: [
      "Exact g/kg chemical formulation breakdown by fabric GSM",
      "Viscosity and pH adjustment recommendations",
      "Alternative dye substitute suggestions when primary color is depleted",
      "Strict quality standard citations with formulation source and SOP ID",
    ],
  },
  {
    id: "f-6",
    category: "rag",
    categoryLabel: "Recipe & Knowledge",
    title: "Machinery Troubleshooting & Error Code Assistant",
    priority: "MEDIUM",
    priorityLabel: "Maintenance",
    icon: BookOpen,
    description:
      "Indexes operating manuals and mechanical schematics for rotary screen printers, digital flatbed systems, loop steamers, and stenter finishing frames.",
    specs: {
      operationalFocus: "Minimize Unplanned Machine Downtime",
      refreshCadence: "Continuous knowledge library updates",
      millScope: "Print line OEM manuals, preventive maintenance procedures",
    },
    featuresList: [
      "Screen tension deviation error diagnosis",
      "Steamer temperature/humidity curing tolerance lookups",
      "Step-by-step preventive maintenance checklist generation",
      "Operator troubleshooting playbooks for rapid resolution",
    ],
  },
  {
    id: "f-7",
    category: "swarm",
    categoryLabel: "Operational Copilot",
    title: "Autonomous Operational Copilot",
    priority: "CRITICAL",
    priorityLabel: "Coordination",
    icon: Bot,
    description:
      "Coordinates commercial orders with warehouse inventory and production schedules, evaluating rush order feasibility and resolving multi-department bottlenecks.",
    specs: {
      operationalFocus: "Cross-Department Alignment & Fast Quoting",
      refreshCadence: "On-demand and event-driven triggers",
      millScope: "Enterprise orders, warehouse buffers, line schedules",
    },
    featuresList: [
      "Natural language order viability evaluations",
      "Cross-department trade-off analysis (Sales rush vs Inventory buffer)",
      "Clear managerial reasoning summaries",
      "Instant exception alerts and executive recommendations",
    ],
  },
  {
    id: "f-8",
    category: "dashboard",
    categoryLabel: "Executive Oversight",
    title: "Executive KPI Cockpit & Priority Alert Stream",
    priority: "SUCCESS",
    priorityLabel: "Executive BI",
    icon: BellRing,
    description:
      "Synthesizes thousands of shop floor data points into an executive overview with four priority alert levels (CRITICAL, HIGH, MEDIUM, LOW) and clear action playbooks.",
    specs: {
      operationalFocus: "Real-Time Operational Clarity for Mill Leadership",
      refreshCadence: "Continuous live updates",
      millScope: "Daily meter output, active alerts, working capital health",
    },
    featuresList: [
      "Live daily meter output vs seasonal forecast targets",
      "CRITICAL/HIGH/MEDIUM/LOW priority badge triage",
      "Dark / light mode toggle persisted to client browser",
      "Exportable shift summaries and PDF production briefs",
    ],
  },
];

export default function FeaturesPage() {
  const [filter, setFilter] = React.useState<CategoryFilter>("all");

  const filteredFeatures =
    filter === "all"
      ? ALL_FEATURES
      : ALL_FEATURES.filter((f) => f.category === filter);

  return (
    <PageTransition className="py-12 lg:py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {/* Section Header */}
        <div className="max-w-3xl space-y-4">
          <Badge variant="outline" className="text-xs font-semibold px-3 py-1 text-brand border-brand/30">
            Platform Capabilities
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-foreground leading-tight">
            Industrial Intelligence Across Every Mill Workflow
          </h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            From predictive demand forecasting and reactive dye safety stock to digital formulation
            retrieval and real-time operational coordination, explore our complete feature suite.
          </p>
        </div>

        {/* Filter Navigation Tabs */}
        <div className="flex flex-wrap items-center gap-2 border-b border-border pb-4">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mr-2 flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5" />
            Filter Solutions:
          </span>

          <Button
            size="sm"
            variant={filter === "all" ? "default" : "outline"}
            onClick={() => setFilter("all")}
            className="text-xs h-8"
          >
            All Capabilities ({ALL_FEATURES.length})
          </Button>

          <Button
            size="sm"
            variant={filter === "sales" ? "default" : "outline"}
            onClick={() => setFilter("sales")}
            className="text-xs h-8"
          >
            Sales Intelligence
          </Button>

          <Button
            size="sm"
            variant={filter === "inventory" ? "default" : "outline"}
            onClick={() => setFilter("inventory")}
            className="text-xs h-8"
          >
            Inventory &amp; Buffer
          </Button>

          <Button
            size="sm"
            variant={filter === "rag" ? "default" : "outline"}
            onClick={() => setFilter("rag")}
            className="text-xs h-8"
          >
            Recipe &amp; Knowledge
          </Button>

          <Button
            size="sm"
            variant={filter === "swarm" ? "default" : "outline"}
            onClick={() => setFilter("swarm")}
            className="text-xs h-8"
          >
            Operational Copilot
          </Button>

          <Button
            size="sm"
            variant={filter === "dashboard" ? "default" : "outline"}
            onClick={() => setFilter("dashboard")}
            className="text-xs h-8"
          >
            Executive Oversight
          </Button>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredFeatures.map((f) => {
            const Icon = f.icon;
            return (
              <Card
                key={f.id}
                className="bg-card border-border hover:border-brand/50 transition-all duration-200 shadow-xs flex flex-col justify-between"
              >
                <CardHeader className="space-y-3 pb-3">
                  <div className="flex items-center justify-between">
                    <div className="w-9 h-9 rounded-lg bg-brand-muted text-brand-muted-fg flex items-center justify-center">
                      <Icon className="w-4 h-4 text-brand" />
                    </div>
                    <PriorityBadge priority={f.priority} size="sm">
                      {f.priorityLabel}
                    </PriorityBadge>
                  </div>

                  <div>
                    <span className="text-xs font-semibold text-brand block uppercase tracking-wider">
                      {f.categoryLabel}
                    </span>
                    <CardTitle className="text-xl font-bold mt-1 text-foreground">
                      {f.title}
                    </CardTitle>
                  </div>

                  <CardDescription className="text-sm text-muted-foreground leading-relaxed">
                    {f.description}
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4 pt-2">
                  {/* Operational Specs box */}
                  <div className="p-3 rounded-lg bg-muted/50 border border-border/60 text-xs space-y-1">
                    <div>
                      <strong className="text-foreground">Operational Focus: </strong>
                      <span className="text-muted-foreground">{f.specs.operationalFocus}</span>
                    </div>
                    <div>
                      <strong className="text-foreground">Update Frequency: </strong>
                      <span className="text-muted-foreground">{f.specs.refreshCadence}</span>
                    </div>
                    <div>
                      <strong className="text-foreground">Mill Scope: </strong>
                      <span className="text-muted-foreground">{f.specs.millScope}</span>
                    </div>
                  </div>

                  {/* Checklist of sub-features */}
                  <div className="space-y-1.5 pt-1">
                    <span className="text-xs font-semibold uppercase tracking-wider text-foreground block">
                      Key Capabilities:
                    </span>
                    {f.featuresList.map((item, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs text-foreground">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Bottom CTA Card */}
        <div className="p-8 rounded-2xl bg-brand-muted/30 border border-brand/20 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="space-y-2">
            <h3 className="text-xl font-bold text-foreground">
              Ready to experience these capabilities in your mill workspace?
            </h3>
            <p className="text-sm text-muted-foreground">
              Explore the live executive dashboard with real-time KPI analytics, demand forecasting, and inventory buffers.
            </p>
          </div>

          <Link href="/dashboard" className="shrink-0">
            <Button size="lg" className="gap-2 font-semibold">
              <span>Launch Live Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </div>
    </PageTransition>
  );
}
