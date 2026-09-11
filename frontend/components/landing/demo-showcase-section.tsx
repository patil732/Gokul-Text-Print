"use client";

import * as React from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge, PriorityBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  LayoutDashboard,
  Bot,
  AlertTriangle,
  BookOpen,
  ArrowRight,
  TrendingUp,
  Activity,
  CheckCircle2,
  Clock,
  Sparkles,
  Search,
  Boxes,
  MessageSquare,
} from "lucide-react";

type DemoTab = "dashboard" | "swarm" | "alerts" | "rag";

export function DemoShowcaseSection() {
  const [activeTab, setActiveTab] = React.useState<DemoTab>("dashboard");

  return (
    <section className="py-16 lg:py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-12">
          <Badge variant="outline" className="text-xs font-semibold px-3 py-1 text-brand border-brand/30">
            Interactive Product Preview
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground">
            Experience the Executive Intelligence Interface
          </h2>
          <p className="text-base sm:text-lg text-muted-foreground">
            Explore live previews of the platform's four operational surfaces: Executive KPIs,
            Multi-Agent Swarm logs, Priority Anomaly Alerts, and Domain RAG Copilot.
          </p>
        </div>

        {/* Tab Controls */}
        <div className="flex flex-wrap justify-center gap-2 mb-8">
          <Button
            variant={activeTab === "dashboard" ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveTab("dashboard")}
            className="gap-2"
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Executive KPIs</span>
          </Button>

          <Button
            variant={activeTab === "swarm" ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveTab("swarm")}
            className="gap-2"
          >
            <Bot className="w-4 h-4" />
            <span>Multi-Agent Swarm</span>
          </Button>

          <Button
            variant={activeTab === "alerts" ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveTab("alerts")}
            className="gap-2"
          >
            <AlertTriangle className="w-4 h-4" />
            <span>Priority Alerts</span>
          </Button>

          <Button
            variant={activeTab === "rag" ? "default" : "outline"}
            size="sm"
            onClick={() => setActiveTab("rag")}
            className="gap-2"
          >
            <BookOpen className="w-4 h-4" />
            <span>Domain RAG Copilot</span>
          </Button>
        </div>

        {/* Showcase Frame Container */}
        <div className="rounded-2xl border border-border bg-card shadow-lg overflow-hidden">
          {/* Browser Chrome Simulation */}
          <div className="px-4 py-3 border-b border-border bg-muted/40 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-rose-500/80 inline-block" />
              <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block" />
              <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block" />
              <span className="ml-2 text-xs font-mono text-muted-foreground hidden sm:inline">
                https://gtp-platform.internal/preview/{activeTab}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                Synthetic Demo Environment
              </span>
              <Link href="/dashboard">
                <Button size="sm" variant="ghost" className="h-7 text-xs gap-1">
                  <span>Open Full Dashboard</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </Link>
            </div>
          </div>

          {/* Tab Screen Content */}
          <div className="p-6 sm:p-8 bg-background/50">
            {/* TAB 1: EXECUTIVE KPIS */}
            {activeTab === "dashboard" && (
              <div className="space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-4">
                  <div>
                    <h4 className="text-lg font-bold text-foreground">Executive Overview Dashboard</h4>
                    <p className="text-xs text-muted-foreground">
                      Real-time cross-mill telemetry synthesized by Supervisor Agent
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-xs font-mono">
                      Shift: Morning (Line A, B, C)
                    </Badge>
                  </div>
                </div>

                {/* KPI Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="p-4 rounded-xl border border-border bg-card">
                    <div className="text-xs text-muted-foreground">Active Daily Output</div>
                    <div className="text-2xl font-extrabold text-foreground mt-1 tabular-nums">
                      48,520 m
                    </div>
                    <div className="text-[11px] text-emerald-600 dark:text-emerald-400 mt-1 flex items-center gap-1">
                      <TrendingUp className="w-3 h-3" />
                      <span>+12.4% vs forecast target</span>
                    </div>
                  </div>

                  <div className="p-4 rounded-xl border border-border bg-card">
                    <div className="text-xs text-muted-foreground">Chemical Dye Stock Health</div>
                    <div className="text-2xl font-extrabold text-brand mt-1 tabular-nums">
                      94.8%
                    </div>
                    <div className="text-[11px] text-muted-foreground mt-1">
                      124 batches active in reserve
                    </div>
                  </div>

                  <div className="p-4 rounded-xl border border-border bg-card">
                    <div className="text-xs text-muted-foreground">Batch Color Variance (ΔE)</div>
                    <div className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400 mt-1 tabular-nums">
                      0.32 ΔE
                    </div>
                    <div className="text-[11px] text-emerald-600 dark:text-emerald-400 mt-1">
                      Well below 0.8 tolerance
                    </div>
                  </div>

                  <div className="p-4 rounded-xl border border-border bg-card">
                    <div className="text-xs text-muted-foreground">Open Anomaly Alerts</div>
                    <div className="text-2xl font-extrabold text-amber-600 dark:text-amber-400 mt-1 tabular-nums">
                      2 Items
                    </div>
                    <div className="text-[11px] text-muted-foreground mt-1">
                      1 High, 1 Medium priority
                    </div>
                  </div>
                </div>

                {/* Simulated Chart preview */}
                <div className="p-4 rounded-xl border border-border bg-card">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      30-Day Demand Projection vs Actual Production
                    </span>
                    <span className="text-xs text-brand font-medium">99.4% AI Match</span>
                  </div>
                  <div className="h-28 w-full flex items-end gap-2 pt-4 px-2 border-b border-border/60">
                    {[40, 55, 48, 62, 75, 80, 72, 85, 92, 88, 95, 99].map((val, i) => (
                      <div key={i} className="flex-1 flex flex-col items-center gap-1">
                        <div
                          className="w-full rounded-t bg-brand/80 hover:bg-brand transition-all"
                          style={{ height: `${val}%` }}
                        />
                      </div>
                    ))}
                  </div>
                  <div className="flex justify-between text-[10px] text-muted-foreground pt-2">
                    <span>Day 1 (Week 1)</span>
                    <span>Mid-Month Surge</span>
                    <span>Day 30 (Projected Target)</span>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: MULTI-AGENT SWARM */}
            {activeTab === "swarm" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div>
                    <h4 className="text-lg font-bold text-foreground">Multi-Agent Collaborative Reasoning Swarm</h4>
                    <p className="text-xs text-muted-foreground">
                      Autonomous consensus between Supervisor, Sales, Inventory, and Knowledge agents
                    </p>
                  </div>
                  <PriorityBadge priority="SUCCESS" size="sm">
                    Consensus Reached (1.2s)
                  </PriorityBadge>
                </div>

                <div className="space-y-3 font-mono text-xs">
                  <div className="p-3 rounded-lg bg-card border border-border space-y-1">
                    <div className="flex items-center gap-2 text-brand font-bold">
                      <Bot className="w-3.5 h-3.5" />
                      <span>[Supervisor Agent] DISPATCH QUERY</span>
                      <span className="text-[10px] text-muted-foreground">10:42:01.012</span>
                    </div>
                    <p className="text-muted-foreground">
                      "Client Shanti Textiles requesting 25,000 meters 60x60 Cotton Cambric by Friday.
                      Can our inventory and production schedule sustain this without jeopardizing Order #842?"
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-card border border-border space-y-1 ml-4 border-l-2 border-l-emerald-500">
                    <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-bold">
                      <Activity className="w-3.5 h-3.5" />
                      <span>[Sales Specialist Agent] RESPONSE</span>
                      <span className="text-[10px] text-muted-foreground">10:42:01.420</span>
                    </div>
                    <p className="text-muted-foreground">
                      "Client tier is Platinum. Projected margin is +28.4%. Order #842 delivery is
                      scheduled for next Tuesday, giving 72 hours buffer window."
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-card border border-border space-y-1 ml-4 border-l-2 border-l-amber-500">
                    <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400 font-bold">
                      <Boxes className="w-3.5 h-3.5" />
                      <span>[Inventory Specialist Agent] RESPONSE</span>
                      <span className="text-[10px] text-muted-foreground">10:42:01.810</span>
                    </div>
                    <p className="text-muted-foreground">
                      "Current unprinted Cambric greige stock: 32,400 meters. Reactive Navy Dye lot #419 has
                      sufficient buffer. Approval recommended with reorder trigger for yarn batch #88."
                    </p>
                  </div>

                  <div className="p-3 rounded-lg bg-brand-muted/40 border border-brand/30 space-y-1">
                    <div className="flex items-center gap-2 text-brand font-bold">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>[Supervisor Agent] FINAL EXECUTIVE ACTION</span>
                      <span className="text-[10px] text-muted-foreground">10:42:02.110</span>
                    </div>
                    <p className="text-foreground font-semibold">
                      "Consensus 99.1% confidence: APPROVED. Order queued to Line 2 rotary press.
                      Automated yarn supplier replenishment PO #4892 dispatched."
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: PRIORITY ANOMALY ALERTS */}
            {activeTab === "alerts" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div>
                    <h4 className="text-lg font-bold text-foreground">Live Anomaly Alert Stream</h4>
                    <p className="text-xs text-muted-foreground">
                      Continuous shop floor monitoring classified by urgency
                    </p>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    Auto-Refreshed via Flask API
                  </Badge>
                </div>

                <div className="space-y-2.5">
                  <div className="p-3.5 rounded-lg border border-border bg-card flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <PriorityBadge priority="CRITICAL" size="sm" />
                        <span className="text-xs font-bold text-foreground">
                          Reactive Cyan Pigment Low Buffer
                        </span>
                        <span className="text-[11px] text-muted-foreground font-mono">Bay 4-D</span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Projected consumption exceeds inventory within 36 hours based on scheduled chiffon runs.
                      </p>
                    </div>
                    <Button size="sm" variant="destructive" className="text-xs h-8 shrink-0">
                      Trigger Supplier PO
                    </Button>
                  </div>

                  <div className="p-3.5 rounded-lg border border-border bg-card flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <PriorityBadge priority="HIGH" size="sm" />
                        <span className="text-xs font-bold text-foreground">
                          Viscose Rayon Deadstock Threshold
                        </span>
                        <span className="text-[11px] text-muted-foreground font-mono">Lot #810</span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        4,200m dormant for 45 days. Recommendation: Bundle into upcoming ethnic print promotion.
                      </p>
                    </div>
                    <Button size="sm" variant="outline" className="text-xs h-8 shrink-0">
                      Review Promotion
                    </Button>
                  </div>

                  <div className="p-3.5 rounded-lg border border-border bg-card flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <PriorityBadge priority="MEDIUM" size="sm" />
                        <span className="text-xs font-bold text-foreground">
                          Rotary Screen Tension Calibration
                        </span>
                        <span className="text-[11px] text-muted-foreground font-mono">Machine #3</span>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        Micro-deviation in mesh tension detected after 18,000 meters. Operator recalibration advised.
                      </p>
                    </div>
                    <Button size="sm" variant="outline" className="text-xs h-8 shrink-0">
                      View Calibration SOP
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: DOMAIN RAG COPILOT */}
            {activeTab === "rag" && (
              <div className="space-y-4">
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div>
                    <h4 className="text-lg font-bold text-foreground">Domain RAG & Formula Assistant</h4>
                    <p className="text-xs text-muted-foreground">
                      Sub-second semantic lookup over 14,800+ textile SOPs and chemical dye formulations
                    </p>
                  </div>
                  <Badge variant="secondary" className="text-xs font-mono">
                    ChromaDB Vector Store · 48ms
                  </Badge>
                </div>

                <div className="space-y-3">
                  {/* User Query Mock */}
                  <div className="p-3 rounded-lg bg-muted/60 border border-border text-xs flex items-start gap-2">
                    <Search className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
                    <div>
                      <span className="font-semibold text-foreground">Operator Prompt: </span>
                      <span className="text-muted-foreground">
                        "What is the recommended sodium alginate thickener ratio for 80s Cotton Satin reactive discharge printing?"
                      </span>
                    </div>
                  </div>

                  {/* RAG Answer Mock */}
                  <div className="p-4 rounded-lg bg-card border border-border space-y-3 text-xs">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 font-bold text-brand">
                        <Sparkles className="w-4 h-4" />
                        <span>Gokul Textile Knowledge Engine</span>
                      </div>
                      <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                        99.8% Ground Truth Citation
                      </span>
                    </div>

                    <p className="text-foreground leading-relaxed">
                      For <strong>80s Cotton Satin (110 GSM)</strong> using reactive dyes via rotary printing, the certified formula standard is:
                    </p>

                    <div className="p-2.5 rounded bg-muted/50 font-mono text-[11px] text-foreground space-y-1">
                      <div>• High-Viscosity Sodium Alginate (4% stock solution): <strong>650 g/kg</strong></div>
                      <div>• Urea (moisture retention & dye dissolution): <strong>100 g/kg</strong></div>
                      <div>• Sodium Bicarbonate (alkali fixative): <strong>25 g/kg</strong></div>
                      <div>• Resist Salt (mild oxidizing agent): <strong>10 g/kg</strong></div>
                      <div>• Water / balance: <strong>215 g/kg</strong> (Liquor viscosity: 4200–4500 mPa.s)</div>
                    </div>

                    <div className="flex items-center gap-2 text-[10px] text-muted-foreground pt-1">
                      <span>Source: [SOP-PRINT-2024-V3.pdf · Page 42 · Section 4.2.1]</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
