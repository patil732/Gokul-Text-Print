import * as React from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge, PriorityBadge } from "@/components/ui/badge";
import {
  Bot,
  TrendingUp,
  Boxes,
  BookOpen,
  BellRing,
  ShieldCheck,
  ArrowRight,
  Sparkles,
} from "lucide-react";

interface FeatureItem {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  category: string;
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "SUCCESS";
  priorityLabel: string;
  description: string;
  highlights: string[];
}

const AI_FEATURES: FeatureItem[] = [
  {
    icon: Bot,
    title: "Autonomous Supervisor Orchestrator",
    category: "Multi-Agent Swarm · Sprint 5",
    priority: "CRITICAL",
    priorityLabel: "Core AI",
    description:
      "A supervisor LLM agent decomposes complex operational goals and assigns micro-tasks to Sales, Inventory, and Knowledge specialist workers, synthesizing the results with mathematical consensus.",
    highlights: [
      "Dynamic sub-task delegation",
      "Consensus conflict resolution",
      "Explainable reasoning audit trail",
    ],
  },
  {
    icon: TrendingUp,
    title: "Predictive Seasonal Demand Engine",
    category: "Sales Intelligence · Sprint 2",
    priority: "HIGH",
    priorityLabel: "High Impact",
    description:
      "Learns from multi-year textile invoice logs to model festive fabric surges, regional marriage seasons, and customer repeat cadences with 99.4% precision.",
    highlights: [
      "SKU-level 90-day demand curves",
      "Diwali & festive surge indicators",
      "Client churn risk profiling",
    ],
  },
  {
    icon: Boxes,
    title: "Dynamic Grey Cloth & Dye Optimization",
    category: "Inventory Intelligence · Sprint 3",
    priority: "HIGH",
    priorityLabel: "Cost Saver",
    description:
      "Eliminates capital lockup by dynamically computing safety buffers for reactive dyes, pigments, and unprinted grey fabric, alerting operators weeks before shortages or deadstock accumulation.",
    highlights: [
      "Turnover velocity tracking",
      "Automated supplier PO triggers",
      "Dye chemical shelf-life alarms",
    ],
  },
  {
    icon: BookOpen,
    title: "Domain RAG & Formula Copilot",
    category: "Knowledge Engine · Sprint 4",
    priority: "MEDIUM",
    priorityLabel: "Knowledge Base",
    description:
      "An intelligent semantic copilot connected to mill manuals, GSM fabric specifications, and exact dye color mixing formulas for zero-error batch repeatability.",
    highlights: [
      "Sub-50ms hybrid vector search",
      "Color shade & liquor ratio calculators",
      "Machine error code troubleshooting",
    ],
  },
  {
    icon: BellRing,
    title: "Proactive Priority Alert Engine",
    category: "Executive BI · Sprint 6",
    priority: "CRITICAL",
    priorityLabel: "Real-Time",
    description:
      "Monitors continuous factory telemetry to classify anomalies into CRITICAL, HIGH, MEDIUM, and LOW alerts, giving managers actionable resolution steps immediately.",
    highlights: [
      "Multi-channel anomaly thresholds",
      "One-click resolution playbooks",
      "Automated shift briefings",
    ],
  },
  {
    icon: ShieldCheck,
    title: "Air-Gapped Factory Security",
    category: "Enterprise Infrastructure",
    priority: "SUCCESS",
    priorityLabel: "Certified",
    description:
      "Built for enterprise textile mills with zero-trust token authentication, edge-ready processing, and a strict guarantee that proprietary formulations never leak to external models.",
    highlights: [
      "On-premise / edge deployment ready",
      "Role-based access control (RBAC)",
      "Isolated tenant vector stores",
    ],
  },
];

export function AiFeaturesSection() {
  return (
    <section className="py-16 lg:py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4 mb-16">
          <Badge variant="outline" className="text-xs font-semibold px-3 py-1 text-brand border-brand/30">
            Intelligent Factory Automation
          </Badge>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground">
            Engineered Specifically for Industrial Textile Mills
          </h2>
          <p className="text-base sm:text-lg text-muted-foreground">
            Every feature is purpose-built to solve real mill bottlenecks: dyeing formulation variance,
            deadstock accumulation, unpredictable seasonal demand, and disparate knowledge silos.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {AI_FEATURES.map((feature, idx) => {
            const Icon = feature.icon;
            return (
              <Card
                key={idx}
                className="group hover:border-brand/60 transition-all duration-200 bg-card hover:shadow-md flex flex-col justify-between"
              >
                <CardHeader className="space-y-3 pb-3">
                  <div className="flex items-center justify-between">
                    <div className="w-10 h-10 rounded-lg bg-brand-muted text-brand-muted-fg flex items-center justify-center group-hover:scale-105 transition-transform">
                      <Icon className="w-5 h-5 text-brand" />
                    </div>
                    <PriorityBadge priority={feature.priority} size="sm">
                      {feature.priorityLabel}
                    </PriorityBadge>
                  </div>
                  <div>
                    <span className="text-[11px] font-semibold text-brand block uppercase tracking-wider">
                      {feature.category}
                    </span>
                    <CardTitle className="text-lg font-bold mt-1 text-foreground">
                      {feature.title}
                    </CardTitle>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4 text-sm flex-1 flex flex-col justify-between">
                  <CardDescription className="text-sm text-muted-foreground leading-relaxed">
                    {feature.description}
                  </CardDescription>

                  <div className="pt-3 border-t border-border/70 space-y-1.5">
                    {feature.highlights.map((h, hIdx) => (
                      <div key={hIdx} className="flex items-center gap-2 text-xs text-foreground">
                        <Sparkles className="w-3 h-3 text-brand shrink-0" />
                        <span>{h}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* View All Features Link */}
        <div className="text-center mt-12">
          <Link
            href="/features"
            className="inline-flex items-center gap-2 text-sm font-semibold text-brand hover:underline"
          >
            <span>Explore Comprehensive Feature Catalog & Specs</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}
