import type { Metadata } from "next";
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
  Database,
  ShieldCheck,
  Zap,
  ArrowRight,
  CheckCircle2,
  Activity,
  Layers,
  Sparkles,
  BarChart3,
  Clock,
  Award,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Platform Solutions — Gokul Text Print Platform",
  description:
    "Explore how Gokul Text Print's autonomous operational solutions empower industrial textile printing mills: sales forecasting, inventory buffer balancing, digital recipe kitchen, and operational copilot.",
};

const PILLARS = [
  {
    id: "sales",
    title: "Sales & Demand Planning",
    badge: "Commercial Intelligence",
    icon: TrendingUp,
    headline: "Eliminate stockouts and forecast seasonal order volume accurately",
    overview:
      "Automates sales order intelligence by analyzing historical client invoice cycles, regional wedding seasons, and festive surge patterns. Mill executives gain 30, 60, and 90-day visibility into SKU demand, enabling precise grey fabric procurement weeks ahead of deadlines.",
    benefits: [
      "99.4% demand prediction precision on high-volume fabric blends",
      "Festive surge alerts for Jacquard, Cambric, Rayon, and Chiffon",
      "Customer repeat purchasing window notifications to prevent churn",
      "Profitable pricing guidance based on raw material market fluctuations",
    ],
    operationalMetrics: [
      { label: "Forecast Horizon", value: "30 / 60 / 90 Days" },
      { label: "Average Precision", value: "99.4%" },
      { label: "Delivery Lead Advantage", value: "+28% Faster" },
    ],
  },
  {
    id: "inventory",
    title: "Inventory & Buffer Optimization",
    badge: "Working Capital Protection",
    icon: Boxes,
    headline: "Keep grey cloth and reactive dyes in balance without tying up working capital",
    overview:
      "Continuously monitors grey cloth yardage, yarn reserves, and reactive dye batches across warehouse bays. Automatically flags slow-moving stock before aging thresholds and dynamically recalculates safety stock buffers based on supplier delivery lead times.",
    benefits: [
      "Dynamic safety buffer calculations tailored to supplier reliability",
      "Early warning alerts for slow-moving fabric rolls and aging dye pigments",
      "Automated replenishment purchase order triggers before stockouts occur",
      "Live warehouse turnover velocity tracking across all storage locations",
    ],
    operationalMetrics: [
      { label: "Working Capital Freed", value: "34% Average" },
      { label: "Stock Turnover Rate", value: "6.8x / year" },
      { label: "Unplanned Line Halts", value: "0 Incidents" },
    ],
  },
  {
    id: "recipes",
    title: "Digital Color Kitchen & SOP Library",
    badge: "Formulation Intelligence",
    icon: BookOpen,
    headline: "Centralize certified dye recipes and standard operating procedures",
    overview:
      "Digitizes paper recipe sheets and tribal color kitchen knowledge into a single searchable repository. Print line operators and master colorists can look up exact dye ratios, auxiliary chemical concentrations, and rotary machine settings instantly to ensure sub-0.5 Delta-E color consistency.",
    benefits: [
      "Instant verified formulation lookups for all reactive, disperse, and pigment dyes",
      "Certified chemical liquor ratio guidance for GSM-specific fabric substrates",
      "Machine error code troubleshooting playbooks for rotary and digital presses",
      "100% preservation of institutional color kitchen formulations",
    ],
    operationalMetrics: [
      { label: "Color Variance (ΔE)", value: "Sub-0.5 ΔE" },
      { label: "Recipe Search Time", value: "< 1 Second" },
      { label: "Formulation Retention", value: "100%" },
    ],
  },
  {
    id: "copilot",
    title: "Executive Operational Copilot",
    badge: "Autonomous Coordination",
    icon: Bot,
    headline: "Coordinate commercial commitments with factory floor capacity in real time",
    overview:
      "Acts as an intelligent operational copilot for mill leadership. When rush orders arrive, the copilot immediately cross-references warehouse grey cloth availability, reactive dye reserves, and scheduled press runtime to provide clear feasibility assessments and actionable escalation briefs.",
    benefits: [
      "Instant commercial order feasibility checks with margin analysis",
      "Automated cross-department trade-off analysis between sales and production",
      "Priority anomaly alert classification (Critical, High, Medium, Low)",
      "Automated shift briefings and daily executive performance summaries",
    ],
    operationalMetrics: [
      { label: "Feasibility Assessment", value: "Instant" },
      { label: "Decision Confidence", value: "99.1%" },
      { label: "Quoting Turnaround", value: "4.2x Faster" },
    ],
  },
];

export default function TechnologyPage() {
  return (
    <PageTransition className="py-12 lg:py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16 lg:space-y-24">
        {/* Page Header */}
        <div className="max-w-3xl space-y-4">
          <Badge variant="outline" className="text-xs font-semibold px-3 py-1 text-brand border-brand/30">
            Enterprise Solutions
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-foreground leading-tight">
            How Autonomous AI Powers Modern Textile Mills
          </h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Designed around the real-world complexities of industrial textile printing: seasonal demand spikes,
            dye kitchen chemical balances, deadstock prevention, and cross-department decision alignment.
          </p>
        </div>

        {/* 4-Step Factory Workflow Diagram */}
        <div className="p-6 sm:p-8 rounded-2xl bg-card border border-border shadow-md space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-4">
            <div>
              <h2 className="text-xl font-bold text-foreground">Continuous Factory Intelligence Workflow</h2>
              <p className="text-xs text-muted-foreground">
                How shop floor inputs translate into clear executive decisions
              </p>
            </div>
            <Badge variant="secondary" className="text-xs font-mono">
              Real-Time Factory Floor Synchronization
            </Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-muted/40 border border-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-brand uppercase tracking-wider">Step 01</span>
                <Database className="w-4 h-4 text-muted-foreground" />
              </div>
              <h3 className="text-sm font-bold text-foreground">Data Ingestion</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Connects directly to client order books, warehouse fabric ledgers, and chemical dye receipts.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-muted/40 border border-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-brand uppercase tracking-wider">Step 02</span>
                <Activity className="w-4 h-4 text-muted-foreground" />
              </div>
              <h3 className="text-sm font-bold text-foreground">Predictive Analysis</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Forecasts 30/60/90-day demand curves, calculates safety buffer levels, and identifies aging stock.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-muted/40 border border-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-brand uppercase tracking-wider">Step 03</span>
                <BookOpen className="w-4 h-4 text-muted-foreground" />
              </div>
              <h3 className="text-sm font-bold text-foreground">Operational Alignment</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Cross-references incoming orders with fabric inventory and certified color mixing formulations.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-muted/40 border border-border space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-brand uppercase tracking-wider">Step 04</span>
                <Zap className="w-4 h-4 text-emerald-500" />
              </div>
              <h3 className="text-sm font-bold text-foreground">Executive Action</h3>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Delivers instant order feasibility, replenishment PO triggers, and prioritized anomaly alerts.
              </p>
            </div>
          </div>
        </div>

        {/* Deep Dive Pillars */}
        <div className="space-y-12">
          {PILLARS.map((pillar) => {
            const Icon = pillar.icon;
            return (
              <div
                key={pillar.id}
                id={pillar.id}
                className="p-6 sm:p-8 rounded-2xl bg-card border border-border shadow-xs space-y-6 scroll-mt-24"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border pb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-brand text-brand-fg flex items-center justify-center shadow-xs">
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-foreground">{pillar.title}</h2>
                      <p className="text-xs text-brand font-medium">{pillar.headline}</p>
                    </div>
                  </div>
                  <Badge variant="secondary" className="text-xs w-fit">
                    {pillar.badge}
                  </Badge>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                  {/* Left Description & Benefits */}
                  <div className="lg:col-span-8 space-y-4">
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {pillar.overview}
                    </p>

                    <div className="space-y-2 pt-2">
                      <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
                        Operational Capabilities:
                      </span>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        {pillar.benefits.map((benefit, idx) => (
                          <div key={idx} className="flex items-start gap-2 text-xs text-foreground">
                            <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                            <span>{benefit}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Right Metrics Cards */}
                  <div className="lg:col-span-4 flex flex-col justify-between gap-3 p-4 rounded-xl bg-muted/30 border border-border">
                    <span className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
                      Verified Mill Impact
                    </span>
                    <div className="space-y-3">
                      {pillar.operationalMetrics.map((metric, idx) => (
                        <div key={idx} className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">{metric.label}</span>
                          <span className="font-bold text-foreground tabular-nums">{metric.value}</span>
                        </div>
                      ))}
                    </div>
                    <Link href="/login" className="pt-2">
                      <Button size="sm" variant="outline" className="w-full text-xs h-8 gap-1.5">
                        <span>Sign In to Access</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Enterprise Security & Architecture Guarantees */}
        <div className="p-6 sm:p-8 rounded-2xl bg-gradient-to-br from-card via-card to-brand-muted/20 border border-border shadow-md space-y-6">
          <div className="max-w-2xl space-y-2">
            <Badge variant="outline" className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 border-emerald-500/30">
              Enterprise Governance
            </Badge>
            <h2 className="text-2xl font-bold text-foreground">
              Industrial-Grade Security &amp; Data Privacy
            </h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Designed from the ground up for proprietary manufacturing operations. Your formulation recipes,
              client volume commitments, and financial invoices remain strictly confidential and isolated.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-card border border-border space-y-2">
              <div className="flex items-center gap-2 text-brand font-semibold text-xs">
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                <span>Role-Based Access Control</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Strict separation between Admin infrastructure controls and CEO executive workspaces.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-card border border-border space-y-2">
              <div className="flex items-center gap-2 text-brand font-semibold text-xs">
                <Database className="w-4 h-4 text-brand" />
                <span>Isolated Tenant Data</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Encrypted storage ensuring proprietary chemical dye formulas and customer pricing never cross boundaries.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-card border border-border space-y-2">
              <div className="flex items-center gap-2 text-brand font-semibold text-xs">
                <Zap className="w-4 h-4 text-amber-500" />
                <span>Flexible Deployment</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Deployable in managed enterprise cloud or completely air-gapped on-premise edge servers for continuous reliability.
              </p>
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}
