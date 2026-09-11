"use client";

import * as React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  ArrowRight,
  Sparkles,
  Layers,
  Cpu,
  BarChart3,
  ShieldCheck,
  Zap,
  LogIn,
} from "lucide-react";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden pt-12 pb-16 lg:pt-20 lg:pb-24">
      {/* Background Decorative Gradients */}
      <div
        className="pointer-events-none absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[400px] bg-brand/10 dark:bg-brand/15 blur-[120px] rounded-full"
        aria-hidden="true"
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="text-center max-w-3xl mx-auto space-y-6">
          {/* Release Tag */}
          <div className="inline-flex items-center">
            <Badge
              variant="outline"
              className="py-1 px-3.5 text-xs font-semibold gap-2 border-brand/40 bg-brand-muted/40 text-brand-muted-fg dark:text-brand shadow-xs"
            >
              <Sparkles className="w-3.5 h-3.5 text-brand shrink-0" />
              <span>Enterprise Mill Intelligence · Autonomous Operational Platform</span>
            </Badge>
          </div>

          {/* Main Headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-foreground leading-[1.15]">
            Autonomous AI Intelligence for{" "}
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-brand via-indigo-500 to-violet-600 dark:from-brand dark:via-indigo-400 dark:to-violet-400">
              Industrial Textile Printing
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg sm:text-xl text-muted-foreground leading-relaxed max-w-2xl mx-auto">
            Unifying Sales Demand Forecasting, Dynamic Grey Cloth & Dye Optimization, Color
            Formulation Intelligence, and Real-Time Executive Oversight into a single workspace.
          </p>

          {/* Call-to-Action Group */}
          <div className="flex flex-wrap items-center justify-center gap-3.5 pt-2">
            <Link href="/register">
              <Button size="lg" className="h-12 px-6 text-base font-semibold shadow-md gap-2">
                <span>Register Your Mill</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>

            <Link href="/login">
              <Button
                variant="outline"
                size="lg"
                className="h-12 px-6 text-base font-medium gap-2 border-border hover:bg-muted"
              >
                <LogIn className="w-4 h-4 text-brand" />
                <span>Sign In</span>
              </Button>
            </Link>

            <Link href="/dashboard">
              <Button
                variant="ghost"
                size="lg"
                className="h-12 px-5 text-base font-medium text-muted-foreground hover:text-foreground gap-2"
              >
                <Sparkles className="w-4 h-4 text-amber-500" />
                <span>Live Demo</span>
              </Button>
            </Link>
          </div>

          {/* Trust Guarantees */}
          <div className="flex flex-wrap items-center justify-center gap-6 pt-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
              <span>Enterprise Data Isolation</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Zap className="w-4 h-4 text-amber-500" />
              <span>Continuous Factory Sync</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Cpu className="w-4 h-4 text-brand" />
              <span>Cross-Department Coordination</span>
            </div>
          </div>
        </div>

        {/* Live Metrics Ticker Grid */}
        <div className="mt-16 pt-10 border-t border-border grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          <div className="p-4 rounded-xl bg-card border border-border/70 shadow-2xs">
            <div className="text-3xl lg:text-4xl font-extrabold text-foreground tracking-tight tabular-nums">
              40+
            </div>
            <div className="text-xs font-medium text-muted-foreground mt-1">
              Textile Mills Automated
            </div>
          </div>

          <div className="p-4 rounded-xl bg-card border border-border/70 shadow-2xs">
            <div className="text-3xl lg:text-4xl font-extrabold text-brand tracking-tight tabular-nums">
              14.8M
            </div>
            <div className="text-xs font-medium text-muted-foreground mt-1">
              Fabric Meters Forecasted
            </div>
          </div>

          <div className="p-4 rounded-xl bg-card border border-border/70 shadow-2xs">
            <div className="text-3xl lg:text-4xl font-extrabold text-emerald-600 dark:text-emerald-400 tracking-tight tabular-nums">
              99.4%
            </div>
            <div className="text-xs font-medium text-muted-foreground mt-1">
              Order Demand Precision
            </div>
          </div>

          <div className="p-4 rounded-xl bg-card border border-border/70 shadow-2xs">
            <div className="text-3xl lg:text-4xl font-extrabold text-foreground tracking-tight tabular-nums">
              34%
            </div>
            <div className="text-xs font-medium text-muted-foreground mt-1">
              Average Deadstock Cut
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
