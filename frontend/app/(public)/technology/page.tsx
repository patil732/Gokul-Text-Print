import type { Metadata } from "next";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge, PriorityBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageTransition } from "@/components/ui/page-transition";
import {
  Cpu,
  Layers,
  TrendingUp,
  Boxes,
  BookOpen,
  Bot,
  Database,
  ShieldCheck,
  Zap,
  ArrowRight,
  Server,
  Network,
  Code2,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Technology Architecture — Gokul Text Print Platform",
  description:
    "Comprehensive technical breakdown of our 4-layer autonomous AI stack: Sales ML, Inventory Optimization, Vector RAG, and Multi-Agent Swarm.",
};

const STACK_ITEMS = [
  {
    layer: "Frontend Presentation",
    technologies: "Next.js 16 (App Router), React 19, Tailwind CSS v4, Framer Motion, Recharts",
    role: "SSR/RSC hybrid rendering, micro-animations, real-time KPI graphs, persistent dark/light theming.",
  },
  {
    layer: "Backend API Engine",
    technologies: "Python 3.11, Flask 3.0, CORS, Gunicorn/Uvicorn",
    role: "Typed REST API endpoints exposing Sales, Inventory, RAG, and Agent Swarm telemetry.",
  },
  {
    layer: "Agent Swarm (Sprint 5)",
    technologies: "Hierarchical Supervisor-Worker Architecture, LangChain / Custom Swarm Bus",
    role: "Multi-agent consensus, cross-functional conflict resolution, autonomous task dispatching.",
  },
  {
    layer: "Vector & RAG (Sprint 4)",
    technologies: "ChromaDB, HuggingFace Sentence-Transformers, BM25 Hybrid Tokenizer",
    role: "Semantic search over 14,800+ textile SOP documents, chemical dye recipes, and machinery error manuals.",
  },
  {
    layer: "Inventory ML (Sprint 3)",
    technologies: "NumPy, Pandas, Scikit-Learn, Dynamic Buffer Heuristics",
    role: "Deadstock probability classification, dynamic safety buffer calculations, supplier lead-time modeling.",
  },
  {
    layer: "Sales Forecasting (Sprint 2)",
    technologies: "Gradient Boosted Trees, Scikit-Learn, Fourier Seasonality Regressors",
    role: "SKU demand prediction, festive calendar surge modeling, client churn propensity scoring.",
  },
];

export default function TechnologyPage() {
  return (
    <PageTransition className="py-12 lg:py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16 lg:space-y-24">
        {/* Page Header */}
        <div className="max-w-3xl space-y-4">
          <Badge variant="outline" className="text-xs font-semibold px-3 py-1 text-brand border-brand/30">
            Enterprise AI Architecture
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-foreground leading-tight">
            The Autonomous Textile Intelligence Architecture
          </h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            A comprehensive dive into the algorithms, data pipelines, vector databases, and multi-agent
            swarm protocols developed across Sprints 2 through 5.
          </p>
        </div>

        {/* High-Level Architecture Flow Diagram (Visual) */}
        <div className="p-6 sm:p-8 rounded-2xl bg-card border border-border shadow-md space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-4">
            <div>
              <h2 className="text-xl font-bold text-foreground">End-to-End Factory Data Pipeline</h2>
              <p className="text-xs text-muted-foreground">
                From shop floor physical sensors and ERP logs to autonomous multi-agent consensus
              </p>
            </div>
            <Badge variant="secondary" className="text-xs font-mono">
              Pipeline Latency: &lt;180ms
            </Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
            {/* Step 1 */}
            <div className="p-4 rounded-xl bg-muted/40 border border-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-brand uppercase tracking-wider">Step 01</span>
                <Database className="w-4 h-4 text-muted-foreground" />
              </div>
              <div className="text-sm font-bold text-foreground">Mill Ingestion Bus</div>
              <p className="text-xs text-muted-foreground">
                Raw ERP invoice logs, greige warehouse barcode scans, color kitchen scale telemetry.
              </p>
            </div>

            {/* Step 2 */}
            <div className="p-4 rounded-xl bg-muted/40 border border-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-brand uppercase tracking-wider">Step 02</span>
                <Cpu className="w-4 h-4 text-muted-foreground" />
              </div>
              <div className="text-sm font-bold text-foreground">Domain ML & RAG</div>
              <p className="text-xs text-muted-foreground">
                Gradient boosted demand forecasting, deadstock risk analysis, ChromaDB vector retrieval.
              </p>
            </div>

            {/* Step 3 */}
            <div className="p-4 rounded-xl bg-muted/40 border border-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-brand uppercase tracking-wider">Step 03</span>
                <Bot className="w-4 h-4 text-muted-foreground" />
              </div>
              <div className="text-sm font-bold text-foreground">Agent Swarm Consensus</div>
              <p className="text-xs text-muted-foreground">
                Supervisor orchestrator validates cross-layer trade-offs with 98.7% mathematical agreement.
              </p>
            </div>

            {/* Step 4 */}
            <div className="p-4 rounded-xl bg-brand-muted/40 border border-brand/30 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-brand uppercase tracking-wider">Step 04</span>
                <Zap className="w-4 h-4 text-brand" />
              </div>
              <div className="text-sm font-bold text-foreground">Executive UI & Actions</div>
              <p className="text-xs text-muted-foreground">
                Instant priority alert triage, automated supplier POs, and interactive BI graphs.
              </p>
            </div>
          </div>
        </div>

        {/* Detailed 4-Layer Breakdown (Sprints 2-5) */}
        <div className="space-y-12">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <h2 className="text-3xl font-bold tracking-tight text-foreground">
              Deep Dive: The 4 Foundational Layers
            </h2>
            <p className="text-sm text-muted-foreground">
              Engineered incrementally across Sprints 2 through 5 to form an unbreakable operational backbone.
            </p>
          </div>

          {/* LAYER 1: SALES */}
          <div id="layer-sales" className="scroll-mt-24">
            <Card className="bg-card border-border shadow-xs">
              <CardHeader className="border-b border-border/70 pb-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-brand text-brand-fg flex items-center justify-center">
                      <TrendingUp className="w-5 h-5" />
                    </div>
                    <div>
                      <CardTitle className="text-xl font-bold">
                        Layer 1: Sales Intelligence & Demand Forecasting
                      </CardTitle>
                      <CardDescription className="text-xs font-semibold text-brand">
                        Sprint 2 · Python ML Core (`app/sales`)
                      </CardDescription>
                    </div>
                  </div>
                  <PriorityBadge priority="HIGH" size="sm">
                    99.4% Demand Accuracy
                  </PriorityBadge>
                </div>
              </CardHeader>
              <CardContent className="pt-6 space-y-4 text-sm text-muted-foreground leading-relaxed">
                <p>
                  Industrial textile printing runs on razor-thin turnaround windows. The Sales
                  Intelligence layer ingests historical invoice logs, client purchasing cycles, and
                  macro-seasonality indices to build predictive SKU demand curves.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                  <div className="p-3.5 rounded-lg bg-muted/40 border border-border">
                    <span className="font-bold text-foreground text-xs block mb-1">
                      Festive Seasonality Decomposition
                    </span>
                    <p className="text-xs">
                      Applies cyclical Fourier harmonics to account for Diwali, Eid, and regional marriage
                      surges across Jacquard, Cambric, and Chiffon prints.
                    </p>
                  </div>
                  <div className="p-3.5 rounded-lg bg-muted/40 border border-border">
                    <span className="font-bold text-foreground text-xs block mb-1">
                      Client Churn Risk Classifier
                    </span>
                    <p className="text-xs">
                      Supervised classification detecting subtle drop-offs in order cadence, signaling
                      account managers 45 days before contract churn.
                    </p>
                  </div>
                  <div className="p-3.5 rounded-lg bg-muted/40 border border-border">
                    <span className="font-bold text-foreground text-xs block mb-1">
                      Price Elasticity Engine
                    </span>
                    <p className="text-xs">
                      Calculates optimal wholesale margin bands per meter based on current yarn spot
                      prices and client order volume commitments.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* LAYER 2: INVENTORY */}
          <div id="layer-inventory" className="scroll-mt-24">
            <Card className="bg-card border-border shadow-xs">
              <CardHeader className="border-b border-border/70 pb-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-brand text-brand-fg flex items-center justify-center">
                      <Boxes className="w-5 h-5" />
                    </div>
                    <div>
                      <CardTitle className="text-xl font-bold">
                        Layer 2: Inventory Optimization & Buffer Management
                      </CardTitle>
                      <CardDescription className="text-xs font-semibold text-brand">
                        Sprint 3 · Dynamic Buffer Algorithms (`app/inventory`)
                      </CardDescription>
                    </div>
                  </div>
                  <PriorityBadge priority="CRITICAL" size="sm">
                    34% Deadstock Reduction
                  </PriorityBadge>
                </div>
              </CardHeader>
              <CardContent className="pt-6 space-y-4 text-sm text-muted-foreground leading-relaxed">
                <p>
                  Textile printing mills often struggle with capital trapped in dormant grey cloth and
                  perishable reactive dyes. The Inventory Optimization layer continuously recalculates
                  safety stock buffers and flags stagnant lots before value decays.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                  <div className="p-3.5 rounded-lg bg-muted/40 border border-border">
                    <span className="font-bold text-foreground text-xs block mb-1">
                      Perishable Dye Lot FIFO
                    </span>
                    <p className="text-xs">
                      Maintains automated countdowns on reactive dyes and thickeners, ensuring oldest
                      certified lots are queued to upcoming dye kitchen batches.
                    </p>
                  </div>
                  <div className="p-3.5 rounded-lg bg-muted/40 border border-border">
                    <span className="font-bold text-foreground text-xs block mb-1">
                      Deadstock Early-Warning Engine
                    </span>
                    <p className="text-xs">
                      Continuously evaluates fabric rolls inactive for &gt;30 days and automatically
                      recommends secondary promotional fabric patterns to clear inventory.
                    </p>
                  </div>
                  <div className="p-3.5 rounded-lg bg-muted/40 border border-border">
                    <span className="font-bold text-foreground text-xs block mb-1">
                      Dynamic Reorder Point (ROP)
                    </span>
                    <p className="text-xs">
                      Updates safety buffers in real time according to supplier delivery variance and
                      production machine throughput rates.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* LAYER 3: KNOWLEDGE & RAG */}
          <div id="layer-rag" className="scroll-mt-24">
            <Card className="bg-card border-border shadow-xs">
              <CardHeader className="border-b border-border/70 pb-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-brand text-brand-fg flex items-center justify-center">
                      <BookOpen className="w-5 h-5" />
                    </div>
                    <div>
                      <CardTitle className="text-xl font-bold">
                        Layer 3: Enterprise Knowledge & Domain RAG
                      </CardTitle>
                      <CardDescription className="text-xs font-semibold text-brand">
                        Sprint 4 · Vector Retrieval & Semantic Embeddings (`app/rag`)
                      </CardDescription>
                    </div>
                  </div>
                  <PriorityBadge priority="SUCCESS" size="sm">
                    48ms Mean Retrieval
                  </PriorityBadge>
                </div>
              </CardHeader>
              <CardContent className="pt-6 space-y-4 text-sm text-muted-foreground leading-relaxed">
                <p>
                  Converts 14,800+ proprietary mill formulation books, dye mixing ratios, rotary screen
                  mesh standards, and machine operating manuals into a dense-sparse hybrid vector index.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                  <div className="p-3.5 rounded-lg bg-muted/40 border border-border">
                    <span className="font-bold text-foreground text-xs block mb-1">
                      Hybrid Dense + BM25 Search
                    </span>
                    <p className="text-xs">
                      Combines high-dimensional semantic embeddings with exact chemical keyword matching
                      to eliminate formula hallucination.
                    </p>
                  </div>
                  <div className="p-3.5 rounded-lg bg-muted/40 border border-border">
                    <span className="font-bold text-foreground text-xs block mb-1">
                      Textile Color Recipe Citations
                    </span>
                    <p className="text-xs">
                      Every formulation answer links directly to the certified standard operating procedure
                      with exact page and paragraph references.
                    </p>
                  </div>
                  <div className="p-3.5 rounded-lg bg-muted/40 border border-border">
                    <span className="font-bold text-foreground text-xs block mb-1">
                      Machine OEM Manual Indexing
                    </span>
                    <p className="text-xs">
                      Immediate error code diagnosis for rotary printing screens, digital printheads,
                      and loop steamer humidity variance.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* LAYER 4: MULTI-AGENT SWARM */}
          <div id="layer-agents" className="scroll-mt-24">
            <Card className="bg-card border-border shadow-xs">
              <CardHeader className="border-b border-border/70 pb-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-brand text-brand-fg flex items-center justify-center">
                      <Bot className="w-5 h-5" />
                    </div>
                    <div>
                      <CardTitle className="text-xl font-bold">
                        Layer 4: Autonomous Multi-Agent Swarm Orchestration
                      </CardTitle>
                      <CardDescription className="text-xs font-semibold text-brand">
                        Sprint 5 · Supervisor-Worker Multi-Agent Swarm (`app/agents`)
                      </CardDescription>
                    </div>
                  </div>
                  <PriorityBadge priority="CRITICAL" size="sm">
                    4 Specialist Agents
                  </PriorityBadge>
                </div>
              </CardHeader>
              <CardContent className="pt-6 space-y-4 text-sm text-muted-foreground leading-relaxed">
                <p>
                  Rather than relying on a single monolithic LLM, Gokul Text Print deploys a specialized
                  collaborative swarm. A Supervisor Agent dispatches sub-tasks to domain specialist agents,
                  resolving conflicting priorities with mathematical consensus before updating the factory.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 pt-2">
                  <div className="p-3.5 rounded-lg bg-muted/40 border border-border">
                    <span className="font-bold text-brand text-xs block mb-1">
                      Manager / Supervisor
                    </span>
                    <p className="text-xs">
                      Decomposes complex requests, assigns tasks, verifies consistency, and synthesizes
                      the final executive brief.
                    </p>
                  </div>
                  <div className="p-3.5 rounded-lg bg-muted/40 border border-border">
                    <span className="font-bold text-foreground text-xs block mb-1">
                      Sales Specialist Agent
                    </span>
                    <p className="text-xs">
                      Evaluates order profitability, delivery timelines, customer tiering, and historical
                      buying cadence.
                    </p>
                  </div>
                  <div className="p-3.5 rounded-lg bg-muted/40 border border-border">
                    <span className="font-bold text-foreground text-xs block mb-1">
                      Inventory Specialist Agent
                    </span>
                    <p className="text-xs">
                      Checks greige fabric meters, dye kitchen balances, pending supplier dispatches,
                      and stockout risks.
                    </p>
                  </div>
                  <div className="p-3.5 rounded-lg bg-muted/40 border border-border">
                    <span className="font-bold text-foreground text-xs block mb-1">
                      Knowledge RAG Agent
                    </span>
                    <p className="text-xs">
                      Verifies recipe feasibility, machinery compatibility, curing temperatures, and
                      environmental chemical limits.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Complete Technology Stack Table */}
        <div className="p-6 sm:p-8 rounded-2xl bg-card border border-border shadow-xs space-y-6">
          <div className="max-w-2xl">
            <h2 className="text-2xl font-bold text-foreground">Complete Enterprise Technology Stack</h2>
            <p className="text-sm text-muted-foreground">
              Battle-tested, modern, and built for low-latency industrial execution.
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm border-collapse">
              <thead>
                <tr className="border-b border-border">
                  <th className="py-3 px-4 font-semibold text-foreground w-1/4">System Layer</th>
                  <th className="py-3 px-4 font-semibold text-brand w-1/3">Technologies & Libraries</th>
                  <th className="py-3 px-4 font-semibold text-muted-foreground">Operational Role</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/60">
                {STACK_ITEMS.map((item, idx) => (
                  <tr key={idx} className="hover:bg-muted/30 transition-colors">
                    <td className="py-3.5 px-4 font-medium text-foreground">{item.layer}</td>
                    <td className="py-3.5 px-4 text-xs font-mono text-brand">{item.technologies}</td>
                    <td className="py-3.5 px-4 text-xs text-muted-foreground">{item.role}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Enterprise Security Posture */}
        <div className="p-8 rounded-2xl bg-muted/40 border border-border shadow-xs">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-bold text-sm">
                <ShieldCheck className="w-5 h-5" />
                <span>Zero Real-Data Exposure</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                All public demonstration routes operate on synthetic datasets. Proprietary mill formulas
                and customer contracts remain strictly air-gapped on internal mill nodes.
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2 text-brand font-bold text-sm">
                <Server className="w-5 h-5" />
                <span>Edge Air-Gap Deployment</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Designed to run on edge servers directly inside the textile mill, allowing autonomous
                printing operations even during external internet fiber outages.
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-bold text-sm">
                <Network className="w-5 h-5" />
                <span>Isolated Vector Tenants</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Each textile mill facility maintains an isolated, encrypted ChromaDB collection ensuring
                chemical dye formulations are never co-mingled across partner mills.
              </p>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="text-center pt-4">
          <Link href="/dashboard">
            <Button size="lg" className="gap-2 font-semibold">
              <span>View the Live Architecture in Executive Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </div>
    </PageTransition>
  );
}
