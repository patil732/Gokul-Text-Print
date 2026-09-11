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
  Layers,
  ArrowRight,
  Cpu,
  Database,
  Workflow,
  CheckCircle2,
  Sparkles,
} from "lucide-react";

interface ArchLayer {
  id: string;
  sprint: string;
  name: string;
  badge: string;
  icon: React.ComponentType<{ className?: string }>;
  tagline: string;
  description: string;
  capabilities: string[];
  algorithms: string;
  inputs: string;
  outputs: string;
  sampleTelemetry: {
    metric: string;
    value: string;
    status: "SUCCESS" | "HIGH" | "MEDIUM" | "LOW";
  }[];
}

const ARCH_LAYERS: ArchLayer[] = [
  {
    id: "layer-sales",
    sprint: "Sprint 2",
    name: "Sales Intelligence Layer",
    badge: "Demand Prediction",
    icon: TrendingUp,
    tagline: "Predictive order pipelines and seasonal fabric surges",
    description:
      "Analyzes historical client purchase cycles, regional festive surges, and fabric pattern trends to forecast upcoming SKU demand with over 99% accuracy.",
    capabilities: [
      "SKU-level 30/60/90-day order demand forecasting",
      "Festive seasonality curve modeling (Diwali, Wedding seasons)",
      "High-value client churn detection & repeat order timing",
      "Dynamic price and discount elasticity recommendations",
    ],
    algorithms: "Gradient Boosted Regressors + Seasonality Decomposition",
    inputs: "Historical order books, client CRM transactions, seasonal calendars",
    outputs: "Projected meter demands, pipeline risk scores, revenue estimates",
    sampleTelemetry: [
      { metric: "Order Forecast Accuracy", value: "99.4%", status: "SUCCESS" },
      { metric: "Festive Demand Surge (Jacquard)", value: "+38.2%", status: "HIGH" },
      { metric: "Client Churn Risk Index", value: "2.1% (Low)", status: "SUCCESS" },
    ],
  },
  {
    id: "layer-inventory",
    sprint: "Sprint 3",
    name: "Inventory Optimization Layer",
    badge: "Deadstock Prevention",
    icon: Boxes,
    tagline: "Dynamic grey cloth, yarn, and chemical dye buffer management",
    description:
      "Continuously monitors grey cloth yardage, reactive dye pigment batches, and auxiliary chemicals to minimize deadstock while preventing expensive production line stalls.",
    capabilities: [
      "Real-time stock turnover velocity tracking across warehouse bays",
      "Deadstock early-warning engine for aging dyes and unprinted cotton",
      "Dynamic safety stock recalculation based on supplier lead times",
      "Automated replenishment purchase order generation",
    ],
    algorithms: "Dynamic Buffer Inventory Modeling + Reorder Threshold Optimization",
    inputs: "WMS ledger, batch expiration dates, yarn consumption rates",
    outputs: "Reorder triggers, deadstock mitigation flags, supplier allocations",
    sampleTelemetry: [
      { metric: "Active Deadstock Cut", value: "-34.1%", status: "SUCCESS" },
      { metric: "Reactive Cyan Dye Reserve", value: "18 Days (Critical)", status: "HIGH" },
      { metric: "Stock Turnover Rate", value: "6.8x / year", status: "SUCCESS" },
    ],
  },
  {
    id: "layer-rag",
    sprint: "Sprint 4",
    name: "Knowledge & Domain RAG Layer",
    badge: "Vector Retrieval",
    icon: BookOpen,
    tagline: "Hybrid semantic search across textile formulations and mill SOPs",
    description:
      "Converts unstructured mill manuals, chemical dye mixing recipes, GSM standards, and machine operating procedures into high-dimensional vector embeddings for instant retrieval.",
    capabilities: [
      "Hybrid dense vector + BM25 keyword semantic retrieval",
      "Textile color recipe formulation lookups with exact dye ratios",
      "Rotary screen & digital printer error code troubleshooting",
      "Safety Data Sheet (MSDS) compliance and operator guidance",
    ],
    algorithms: "HuggingFace Embeddings + Vector Store + Cosine Reranking",
    inputs: "PDF recipe books, rotary printing machine manuals, textile SOPs",
    outputs: "Ground-truth cited technical answers, color adjustment formulas",
    sampleTelemetry: [
      { metric: "Vector Chunks Indexed", value: "14,820 docs", status: "SUCCESS" },
      { metric: "Mean Retrieval Latency", value: "48ms", status: "SUCCESS" },
      { metric: "Recipe Verification Rate", value: "100%", status: "SUCCESS" },
    ],
  },
  {
    id: "layer-agents",
    sprint: "Sprint 5",
    name: "Autonomous Multi-Agent Swarm",
    badge: "Supervisor Swarm",
    icon: Bot,
    tagline: "Collaborative agent consensus across sales, inventory, and knowledge",
    description:
      "A supervisor orchestrator dispatches complex mill operational decisions to domain specialist agents, synthesizing cross-functional trade-offs into actionable executive briefs.",
    capabilities: [
      "Supervisor agent orchestrating Sales, Inventory, and Knowledge agents",
      "Automated cross-agent consensus and trade-off synthesis",
      "Natural language business queries converted into multi-step tool calls",
      "Autonomous exception handling and executive escalation triggers",
    ],
    algorithms: "Hierarchical Supervisor-Worker Swarm + Multi-Turn Agent Consensus",
    inputs: "Executive inquiries, automated anomaly alerts, mill event stream",
    outputs: "Multi-agent synthesized decisions, verified action plans, alerts",
    sampleTelemetry: [
      { metric: "Active Agent Workers", value: "4 Specialists", status: "SUCCESS" },
      { metric: "Consensus Confidence", value: "98.7%", status: "SUCCESS" },
      { metric: "Mean Swarm Resolution", value: "1.4s", status: "SUCCESS" },
    ],
  },
];

export function ArchitectureSection() {
  const [activeLayerId, setActiveLayerId] = React.useState<string>("layer-agents");
  const activeLayer = ARCH_LAYERS.find((l) => l.id === activeLayerId) || ARCH_LAYERS[0];
  const ActiveIcon = activeLayer.icon;

  return (
    <section id="architecture" className="py-16 lg:py-24 bg-muted/30 border-y border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-14">
          <Badge variant="outline" className="text-xs font-semibold px-3 py-1 text-brand border-brand/30">
            System Architecture · Sprints 2–5
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground">
            A Unified 4-Layer Autonomous Intelligence Stack
          </h2>
          <p className="text-base sm:text-lg text-muted-foreground">
            Explore how data flows from predictive sales pipelines and mill floor inventory ledgers
            through domain RAG retrieval into our autonomous multi-agent consensus swarm.
          </p>
        </div>

        {/* 4 Layer Navigators */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {ARCH_LAYERS.map((layer) => {
            const Icon = layer.icon;
            const isSelected = layer.id === activeLayerId;
            return (
              <button
                key={layer.id}
                type="button"
                onClick={() => setActiveLayerId(layer.id)}
                className={`text-left p-4 rounded-xl border transition-all duration-200 cursor-pointer ${
                  isSelected
                    ? "bg-card border-brand shadow-sm ring-1 ring-brand/50"
                    : "bg-card/60 hover:bg-card border-border/80 hover:border-border"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                    {layer.sprint}
                  </span>
                  <span
                    className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      isSelected
                        ? "bg-brand text-brand-fg"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {layer.badge}
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
                    {layer.name}
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Active Layer Deep Dive Card */}
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
                      <CardTitle className="text-xl font-bold">{activeLayer.name}</CardTitle>
                      <Badge variant="secondary" className="text-xs">
                        {activeLayer.sprint}
                      </Badge>
                    </div>
                    <CardDescription className="text-sm font-medium text-brand">
                      {activeLayer.tagline}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="space-y-5 text-sm">
                <p className="text-muted-foreground leading-relaxed">
                  {activeLayer.description}
                </p>

                {/* Core Capabilities */}
                <div className="space-y-2.5">
                  <span className="text-xs font-semibold uppercase tracking-wider text-foreground">
                    Core Capabilities:
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {activeLayer.capabilities.map((cap, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs text-foreground">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{cap}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Algorithmic Pipeline Specs */}
                <div className="pt-3 border-t border-border/80 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                  <div className="p-2.5 rounded-lg bg-muted/50">
                    <span className="font-semibold text-muted-foreground block mb-0.5">Algorithm:</span>
                    <span className="text-foreground">{activeLayer.algorithms}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-muted/50">
                    <span className="font-semibold text-muted-foreground block mb-0.5">Telemetry In:</span>
                    <span className="text-foreground">{activeLayer.inputs}</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-muted/50">
                    <span className="font-semibold text-muted-foreground block mb-0.5">Direct Out:</span>
                    <span className="text-foreground">{activeLayer.outputs}</span>
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
                    <Cpu className="w-4 h-4 text-brand" />
                    Layer Telemetry Monitor
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                    Live Simulator
                  </span>
                </div>
                <CardTitle className="text-base font-semibold text-foreground">
                  Synthetic Mill Pipeline Output
                </CardTitle>
              </CardHeader>

              <CardContent className="space-y-3 flex-1">
                {activeLayer.sampleTelemetry.map((item, idx) => (
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

                {/* Pipeline Flow Visualization */}
                <div className="p-3.5 rounded-lg bg-brand-muted/30 border border-brand/20 space-y-2">
                  <div className="flex items-center justify-between text-xs font-semibold text-brand-muted-fg dark:text-brand">
                    <span>Swarm Integration Bus</span>
                    <Sparkles className="w-3.5 h-3.5" />
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    This layer publishes structured events to the multi-agent bus, allowing the
                    Supervisor Agent to perform cross-functional validation before notifying the
                    Executive Dashboard.
                  </p>
                </div>
              </CardContent>

              <div className="p-4 border-t border-border/80 bg-muted/20 flex items-center justify-between">
                <Link
                  href="/technology"
                  className="text-xs font-semibold text-brand hover:underline inline-flex items-center gap-1"
                >
                  <span>Read Full Technical Architecture</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>

                <Link href="/dashboard">
                  <Button size="sm" variant="outline" className="text-xs h-8">
                    View in Dashboard
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
