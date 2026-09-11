"use client";

import * as React from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge, PriorityBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageTransition } from "@/components/ui/page-transition";
import {
  Check,
  HelpCircle,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Zap,
  ChevronDown,
} from "lucide-react";

interface PricingTier {
  name: string;
  badge?: string;
  featured?: boolean;
  priceMonthly: number | "Custom";
  priceAnnual: number | "Custom";
  description: string;
  idealFor: string;
  features: string[];
  ctaLabel: string;
  ctaHref: string;
}

const TIERS: PricingTier[] = [
  {
    name: "Starter Mill",
    priceMonthly: 1200,
    priceAnnual: 960,
    description: "Core sales forecasting and dye stock intelligence for single-facility printing units.",
    idealFor: "Single printing plant producing up to 2M meters/month",
    features: [
      "1 Printing plant facility",
      "Predictive sales demand forecasting",
      "Greige cloth & chemical dye inventory tracking",
      "Digital recipe & SOP library (up to 2,000 documents)",
      "Commercial & Inventory Operational Intelligence",
      "Standard business-hours email & phone support",
      "Cloud-hosted deployment",
    ],
    ctaLabel: "Start with Starter Mill",
    ctaHref: "/contact?tier=starter",
  },
  {
    name: "Enterprise Cluster",
    badge: "Most Popular",
    featured: true,
    priceMonthly: 3400,
    priceAnnual: 2720,
    description: "The complete autonomous operational intelligence suite for multi-plant textile printing groups.",
    idealFor: "Multi-facility mills producing up to 15M meters/month",
    features: [
      "Up to 5 Printing plant facilities",
      "Seasonal festive surge demand forecasting",
      "Dynamic deadstock mitigation & replenishment alerts",
      "Certified color kitchen formula assistant",
      "Autonomous Operational Copilot with cross-department alignment",
      "Real-time Priority Alert Engine with resolution playbooks",
      "Dedicated textile systems engineer",
      "Edge air-gap deployment option",
    ],
    ctaLabel: "Launch Enterprise Cluster",
    ctaHref: "/contact?tier=enterprise",
  },
  {
    name: "Global Conglomerate",
    badge: "Bespoke",
    priceMonthly: "Custom",
    priceAnnual: "Custom",
    description: "Tailored operational intelligence architecture for international textile conglomerates.",
    idealFor: "Large textile export corporations (>15M meters/month)",
    features: [
      "Unlimited global manufacturing facilities",
      "Custom domain-tuned models on proprietary recipes",
      "Sub-second on-premise air-gapped edge server cluster",
      "Bespoke SAP / Oracle / Infor ERP bi-directional sync",
      "99.99% guaranteed uptime SLA",
      "24/7 dedicated mission-control operations support",
      "On-site master chemical and software calibration",
    ],
    ctaLabel: "Request Custom Architecture",
    ctaHref: "/contact?tier=custom",
  },
];

const FAQS = [
  {
    question: "How does commercial licensing work for textile mills?",
    answer:
      "Pricing scales predictably based on the number of manufacturing facilities, monthly fabric yardage, and deployment mode (managed enterprise cloud or dedicated on-premise edge servers). Contact our mill solutions team for a tailored deployment quote.",
  },
  {
    question: "Can we test the platform before committing?",
    answer:
      "Yes! You can explore the platform immediately with our pre-configured demonstration accounts via the sign-in portal without entering payment details.",
  },
  {
    question: "How long does mill onboarding typically take?",
    answer:
      "A typical mill deployment takes 2 to 4 weeks. This includes ingesting historical sales invoices, digitizing dye kitchen formulation recipe sheets into our encrypted recipe knowledge base, and configuring factory safety buffer thresholds.",
  },
  {
    question: "Can the platform run if our mill loses internet connectivity?",
    answer:
      "Yes. Our Enterprise and Global tiers support edge deployment on local mill servers. The autonomous operational copilot and local recipe repository continue operating reliably during external ISP disruptions.",
  },
  {
    question: "How are proprietary color recipes kept confidential?",
    answer:
      "Every mill is assigned an isolated, encrypted enterprise tenant. Your proprietary chemical mixing formulations and client order contracts are strictly confidential and never used to train public models.",
  },
];

export default function PricingPage() {
  const [isAnnual, setIsAnnual] = React.useState(true);
  const [expandedFaq, setExpandedFaq] = React.useState<number | null>(0);

  return (
    <PageTransition className="py-12 lg:py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16 lg:space-y-24">
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto space-y-4">
          <Badge variant="outline" className="text-xs font-semibold px-3 py-1 text-brand border-brand/30">
            Transparent Mill Investment · Demo Tiers
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-foreground leading-tight">
            Predictable Pricing Engineered for Industrial Mill Scale
          </h1>
          <p className="text-base sm:text-lg text-muted-foreground">
            Invest in autonomous intelligence that pays for itself through deadstock reduction,
            faster quoting, and zero-defect color repeatability.
          </p>

          {/* Billing Interval Toggle */}
          <div className="pt-4 flex items-center justify-center gap-3">
            <span
              className={`text-sm font-medium cursor-pointer ${
                !isAnnual ? "text-foreground font-bold" : "text-muted-foreground"
              }`}
              onClick={() => setIsAnnual(false)}
            >
              Monthly Billing
            </span>

            <button
              type="button"
              role="switch"
              aria-checked={isAnnual}
              onClick={() => setIsAnnual(!isAnnual)}
              className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-hidden ${
                isAnnual ? "bg-brand" : "bg-muted"
              }`}
            >
              <span
                className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                  isAnnual ? "translate-x-5" : "translate-x-0"
                }`}
              />
            </button>

            <span
              className={`text-sm font-medium flex items-center gap-1.5 cursor-pointer ${
                isAnnual ? "text-foreground font-bold" : "text-muted-foreground"
              }`}
              onClick={() => setIsAnnual(true)}
            >
              <span>Annual Billing</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                Save 20%
              </span>
            </span>
          </div>
        </div>

        {/* Pricing Cards Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-stretch">
          {TIERS.map((tier, idx) => {
            const price = isAnnual ? tier.priceAnnual : tier.priceMonthly;
            return (
              <Card
                key={idx}
                className={`relative flex flex-col justify-between transition-all duration-200 ${
                  tier.featured
                    ? "border-brand bg-card shadow-lg ring-1 ring-brand/50 lg:-translate-y-2"
                    : "border-border bg-card shadow-xs hover:border-brand/40"
                }`}
              >
                {tier.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="px-3 py-0.5 rounded-full text-xs font-bold bg-brand text-brand-fg shadow-xs">
                      {tier.badge}
                    </span>
                  </div>
                )}

                <CardHeader className="space-y-3 pb-4">
                  <div>
                    <CardTitle className="text-2xl font-bold text-foreground">
                      {tier.name}
                    </CardTitle>
                    <CardDescription className="text-xs text-muted-foreground mt-1">
                      {tier.idealFor}
                    </CardDescription>
                  </div>

                  {/* Price */}
                  <div className="pt-2">
                    {typeof price === "number" ? (
                      <div className="flex items-baseline gap-1">
                        <span className="text-4xl font-extrabold text-foreground tabular-nums">
                          ${price}
                        </span>
                        <span className="text-xs text-muted-foreground">/ month</span>
                        {isAnnual && (
                          <span className="text-[10px] text-muted-foreground ml-1">
                            (billed annually)
                          </span>
                        )}
                      </div>
                    ) : (
                      <div className="text-3xl font-extrabold text-foreground">
                        Bespoke Quote
                      </div>
                    )}
                  </div>

                  <p className="text-xs text-muted-foreground leading-relaxed pt-1">
                    {tier.description}
                  </p>
                </CardHeader>

                <CardContent className="space-y-4 flex-1">
                  <div className="border-t border-border/80 pt-4 space-y-2.5">
                    <span className="text-xs font-semibold uppercase tracking-wider text-foreground block">
                      Included Capabilities:
                    </span>
                    {tier.features.map((f, fIdx) => (
                      <div key={fIdx} className="flex items-start gap-2.5 text-xs text-foreground">
                        <Check className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                        <span>{f}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>

                <CardFooter className="pt-4 border-t border-border/70">
                  <Link href={tier.ctaHref} className="w-full">
                    <Button
                      variant={tier.featured ? "default" : "outline"}
                      className="w-full font-semibold gap-2"
                    >
                      <span>{tier.ctaLabel}</span>
                      <ArrowRight className="w-4 h-4" />
                    </Button>
                  </Link>
                </CardFooter>
              </Card>
            );
          })}
        </div>

        {/* FAQ Accordion */}
        <div className="max-w-3xl mx-auto space-y-8">
          <div className="text-center space-y-2">
            <h2 className="text-3xl font-bold tracking-tight text-foreground">
              Frequently Asked Questions
            </h2>
            <p className="text-sm text-muted-foreground">
              Everything you need to know about implementation, hardware, and data security.
            </p>
          </div>

          <div className="space-y-3">
            {FAQS.map((faq, idx) => {
              const isOpen = expandedFaq === idx;
              return (
                <div
                  key={idx}
                  className="rounded-xl border border-border bg-card overflow-hidden shadow-2xs"
                >
                  <button
                    type="button"
                    onClick={() => setExpandedFaq(isOpen ? null : idx)}
                    className="w-full p-4 text-left flex items-center justify-between gap-4 font-semibold text-sm text-foreground hover:bg-muted/40 transition-colors"
                  >
                    <span>{faq.question}</span>
                    <ChevronDown
                      className={`w-4 h-4 text-muted-foreground shrink-0 transition-transform duration-200 ${
                        isOpen ? "rotate-180 text-brand" : ""
                      }`}
                    />
                  </button>
                  {isOpen && (
                    <div className="px-4 pb-4 pt-1 text-xs text-muted-foreground leading-relaxed border-t border-border/40">
                      {faq.answer}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Demo Assurance Banner */}
        <div className="p-6 rounded-xl bg-muted/40 border border-border flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
          <div className="flex items-center gap-2 text-muted-foreground">
            <ShieldCheck className="w-4 h-4 text-emerald-500 shrink-0" />
            <span>
              All tiers include evaluation sandbox access. Sign in through the secure portal to explore live mill workflows.
            </span>
          </div>
          <Link href="/login">
            <Button size="sm" variant="outline" className="text-xs shrink-0">
              Sign In to Portal
            </Button>
          </Link>
        </div>
      </div>
    </PageTransition>
  );
}
