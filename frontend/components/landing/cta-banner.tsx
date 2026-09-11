import * as React from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Sparkles, Layers, ShieldCheck, PhoneCall } from "lucide-react";

export function CtaBanner() {
  return (
    <section className="py-16 lg:py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative rounded-3xl overflow-hidden bg-gradient-to-b from-brand/90 to-indigo-950 text-white px-6 py-12 sm:px-12 sm:py-16 shadow-xl text-center">
          {/* Subtle background glow */}
          <div
            className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-white/10 blur-[90px] rounded-full"
            aria-hidden="true"
          />

          <div className="relative max-w-3xl mx-auto space-y-6">
            <div className="inline-flex items-center">
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white/15 text-white backdrop-blur-xs border border-white/20">
                Sprint 7 Enterprise Platform · Production Ready
              </span>
            </div>

            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight leading-tight">
              Ready to Modernize Your Textile Mill with Autonomous AI?
            </h2>

            <p className="text-base sm:text-lg text-indigo-100 max-w-2xl mx-auto leading-relaxed">
              Explore the live executive dashboard now or speak directly with our engineering team
              to customize the multi-agent swarm for your factory's specific machinery and dye formulations.
            </p>

            {/* CTAs */}
            <div className="flex flex-wrap items-center justify-center gap-3.5 pt-2">
              <Link href="/dashboard">
                <Button
                  size="lg"
                  className="h-12 px-6 text-base font-semibold bg-white text-indigo-950 hover:bg-white/90 shadow-md gap-2"
                >
                  <span>Launch Live Demo</span>
                  <ArrowRight className="w-4 h-4 text-brand" />
                </Button>
              </Link>

              <Link href="/contact">
                <Button
                  size="lg"
                  variant="outline"
                  className="h-12 px-6 text-base font-semibold text-white border-white/30 hover:bg-white/10 gap-2"
                >
                  <PhoneCall className="w-4 h-4" />
                  <span>Request Factory Assessment</span>
                </Button>
              </Link>

              <Link href="/pricing">
                <Button
                  size="lg"
                  variant="ghost"
                  className="h-12 px-5 text-base font-medium text-indigo-200 hover:text-white hover:bg-white/10"
                >
                  <span>View Mill Tiers</span>
                </Button>
              </Link>
            </div>

            <div className="pt-4 flex flex-wrap items-center justify-center gap-6 text-xs text-indigo-200">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-300" />
                <span>Zero real business data exposed</span>
              </div>
              <div>•</div>
              <div>Instant unauthenticated demo access</div>
              <div>•</div>
              <div>On-premise air-gap deployable</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
