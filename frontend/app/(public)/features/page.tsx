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
  sprint: string;
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "SUCCESS";
  priorityLabel: string;
  icon: React.ComponentType<{ className?: string }>;
  description: string;
  specs: {
    algorithm: string;
    refreshCadence: string;
    telemetrySource: string;
  };
  featuresList: string[];
}

const ALL_FEATURES: DetailedFeature[] = [
  {
    id: "f-1",
    category: "sales",
    categoryLabel: "Sales Intelligence",
    title: "Predictive Order & SKU Demand Engine",
    sprint: "Sprint 2",
    priority: "CRITICAL",
    priorityLabel: "Revenue Engine",
    icon: TrendingUp,
    description:
      "Forecasts client order quantities across 120+ fabric patterns and blends, analyzing historical invoice trends, lead-time elasticity, and festive surge timing.",
    specs: {
      algorithm: "Gradient Boosted Trees + Fourier Seasonality",
      refreshCadence: "Daily sync at 00:00 IST",
      telemetrySource: "ERP sales ledgers, client quotation pipeline",
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
    sprint: "Sprint 2",
    priority: "HIGH",
    priorityLabel: "Retention",
    icon: TrendingUp,
    description:
      "Identifies declining order frequency or volume drop-offs from major garment exporters and retail fabric chains before they switch to competing mills.",
    specs: {
      algorithm: "Multi-factor Churn Classifier",
      refreshCadence: "Weekly automated assessment",
      telemetrySource: "Invoicing intervals, dispatch delay metrics",
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
    sprint: "Sprint 3",
    priority: "CRITICAL",
    priorityLabel: "Cost Optimizer",
    icon: Boxes,
    description:
      "Calculates optimal safety stocks for raw unprinted cotton cambric, viscose, satin, and polyester greige, matching production schedules with supplier delivery reliability.",
    specs: {
      algorithm: "Dynamic Safety Buffer Optimization",
      refreshCadence: "Hourly live ledger polling",
      telemetrySource: "WMS bay sensors, barcode dispatch logs",
    },
    featuresList: [
      "Automatic reorder point (ROP) calculation for all greige SKUs",
      "Deadstock early-warning indicator for fabric rolls dormant >30 days",
      "Supplier fulfillment lead-time tracking and variance scoring",
      "Direct PO generation for cotton spinning mills",
    ],
  },
  {
    id: "f-4",
    category: "inventory",
    categoryLabel: "Inventory Intelligence",
    title: "Chemical Dye & Auxiliary Shelf-Life Monitor",
    sprint: "Sprint 3",
    priority: "HIGH",
    priorityLabel: "Wastage Control",
    icon: Boxes,
    description:
      "Tracks reactive dyes, pigment dispersions, sodium alginate thickeners, and fixatives to eliminate lot expiration and prevent expensive batch contamination.",
    specs: {
      algorithm: "Perishable Inventory Tracking Model",
      refreshCadence: "Real-time on stock movement",
      telemetrySource: "Color kitchen digital dispensing scales",
    },
    featuresList: [
      "Expiration countdown and FIFO usage prioritization",
      "Automated warning if scheduled printing lacks required dye lots",
      "Chemical consumption efficiency vs theoretical yield",
      "Regulatory environmental compliance reporting for hazardous lots",
    ],
  },
  {
    id: "f-5",
    category: "rag",
    categoryLabel: "Knowledge & RAG",
    title: "Color Kitchen Recipe & Formula Copilot",
    sprint: "Sprint 4",
    priority: "HIGH",
    priorityLabel: "Precision RAG",
    icon: BookOpen,
    description:
      "Enables colorists and printing masters to ask natural language questions regarding exact chemical mixing ratios, binder concentrations, and Delta E tolerances.",
    specs: {
      algorithm: "ChromaDB Dense Vectors + BM25 Hybrid Retrieval",
      refreshCadence: "Instant on query (<50ms)",
      telemetrySource: "14,800+ indexed mill recipe sheets & SOPs",
    },
    featuresList: [
      "Exact g/kg chemical formulation breakdown by fabric GSM",
      "Viscosity and pH adjustment recommendations",
      "Alternative dye substitute suggestions when primary color is depleted",
      "Strict provenance citation with document name and page number",
    ],
  },
  {
    id: "f-6",
    category: "rag",
    categoryLabel: "Knowledge & RAG",
    title: "Machinery Troubleshooting & Error Code Assistant",
    sprint: "Sprint 4",
    priority: "MEDIUM",
    priorityLabel: "Maintenance",
    icon: BookOpen,
    description:
      "Indexes operating manuals and mechanical schematics for rotary screen printers, digital flatbed systems, loop steamers, and stenter finishing frames.",
    specs: {
      algorithm: "Hierarchical Document Chunking + Vector Search",
      refreshCadence: "Updated with each maintenance ticket",
      telemetrySource: "OEM machinery service handbooks",
    },
    featuresList: [
      "Screen tension deviation error diagnosis",
      "Steamer temperature/humidity curing tolerance lookups",
      "Step-by-step preventive maintenance checklist generation",
      "Audio/text notes indexing from master machine operators",
    ],
  },
  {
    id: "f-7",
    category: "swarm",
    categoryLabel: "Multi-Agent Swarm",
    title: "Hierarchical Supervisor Swarm Orchestrator",
    sprint: "Sprint 5",
    priority: "CRITICAL",
    priorityLabel: "Agent Swarm",
    icon: Bot,
    description:
      "An autonomous supervisor LLM coordinates specialist workers (Sales Agent, Inventory Agent, Knowledge Agent), synthesizing complex cross-departmental factory operations.",
    specs: {
      algorithm: "Supervisor-Worker Swarm with Multi-Turn Consensus",
      refreshCadence: "Event-driven & scheduled cron triggers",
      telemetrySource: "Internal Flask business logic & API layer",
    },
    featuresList: [
      "Natural language order viability evaluations",
      "Cross-agent conflict resolution (e.g. Sales wanting rush vs Inventory buffer)",
      "Comprehensive multi-step reasoning audit logs",
      "Autonomous exception escalation to plant management",
    ],
  },
  {
    id: "f-8",
    category: "dashboard",
    categoryLabel: "Executive BI & Alerts",
    title: "Executive KPI Cockpit & Alert Stream",
    sprint: "Sprint 6",
    priority: "SUCCESS",
    priorityLabel: "Executive BI",
    icon: BellRing,
    description:
      "Synthesizes thousands of shop floor data points into an executive overview with four priority alert levels (CRITICAL, HIGH, MEDIUM, LOW) and one-click playbooks.",
    specs: {
      algorithm: "Real-time Telemetry Aggregator + Rule Engine",
      refreshCadence: "Live auto-refresh via CORS Flask API",
      telemetrySource: "Integrated platform databases",
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
            Platform Capabilities Catalog
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-foreground leading-tight">
            Industrial-Grade Intelligence Across Every Mill Workflow
          </h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            From predictive demand forecasting and reactive dye safety stock to RAG formulation
            retrieval and autonomous multi-agent consensus, explore our complete feature suite.
          </p>
        </div>

        {/* Filter Navigation Tabs */}
        <div className="flex flex-wrap items-center gap-2 border-b border-border pb-4">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mr-2 flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5" />
            Filter By Layer:
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
            Sales (Sprint 2)
          </Button>

          <Button
            size="sm"
            variant={filter === "inventory" ? "default" : "outline"}
            onClick={() => setFilter("inventory")}
            className="text-xs h-8"
          >
            Inventory (Sprint 3)
          </Button>

          <Button
            size="sm"
            variant={filter === "rag" ? "default" : "outline"}
            onClick={() => setFilter("rag")}
            className="text-xs h-8"
          >
            Knowledge & RAG (Sprint 4)
          </Button>

          <Button
            size="sm"
            variant={filter === "swarm" ? "default" : "outline"}
            onClick={() => setFilter("swarm")}
            className="text-xs h-8"
          >
            Agent Swarm (Sprint 5)
          </Button>

          <Button
            size="sm"
            variant={filter === "dashboard" ? "default" : "outline"}
            onClick={() => setFilter("dashboard")}
            className="text-xs h-8"
          >
            Executive BI (Sprint 6)
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
                    <div className="flex items-center gap-2">
                      <div className="w-9 h-9 rounded-lg bg-brand-muted text-brand-muted-fg flex items-center justify-center">
                        <Icon className="w-4 h-4 text-brand" />
                      </div>
                      <Badge variant="secondary" className="text-[11px] font-mono">
                        {f.sprint}
                      </Badge>
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
                  {/* Technical Specs box */}
                  <div className="p-3 rounded-lg bg-muted/50 border border-border/60 text-xs space-y-1">
                    <div>
                      <strong className="text-foreground">Model/Algorithm: </strong>
                      <span className="text-muted-foreground">{f.specs.algorithm}</span>
                    </div>
                    <div>
                      <strong className="text-foreground">Refresh Cadence: </strong>
                      <span className="text-muted-foreground">{f.specs.refreshCadence}</span>
                    </div>
                    <div>
                      <strong className="text-foreground">Data Ingestion: </strong>
                      <span className="text-muted-foreground">{f.specs.telemetrySource}</span>
                    </div>
                  </div>

                  {/* Checklist of sub-features */}
                  <div className="space-y-1.5 pt-1">
                    <span className="text-xs font-semibold uppercase tracking-wider text-foreground block">
                      Key Highlights:
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
              Ready to test these capabilities on live synthetic factory data?
            </h3>
            <p className="text-sm text-muted-foreground">
              Our executive dashboard runs the full agent swarm and KPI analytics with unauthenticated demo access.
            </p>
          </div>

          <Link href="/dashboard" className="shrink-0">
            <Button size="lg" className="gap-2 font-semibold">
              <span>Launch Live Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </div>
    </PageTransition>
  );
}
