import * as React from "react";
import Link from "next/link";
import { Layers, ShieldCheck, Activity, ArrowUpRight } from "lucide-react";

export function PublicFooter() {
  return (
    <footer className="w-full border-t border-border bg-card/60 backdrop-blur-xs text-foreground mt-auto">
      {/* Upper Footer Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8 lg:gap-12">
          {/* Brand & Overview */}
          <div className="lg:col-span-2 space-y-4">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-brand text-brand-fg flex items-center justify-center shadow-xs">
                <Layers className="w-4 h-4" />
              </div>
              <span className="text-lg font-bold tracking-tight text-foreground">
                Gokul Text Print
              </span>
            </Link>

            <p className="text-sm text-muted-foreground leading-relaxed max-w-sm">
              The autonomous enterprise operating system for industrial textile printing mills.
              Unifying sales forecasting, grey cloth inventory optimization, chemical dye RAG
              retrieval, and multi-agent supervisory intelligence.
            </p>

            {/* Live System Status Indicator */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-background text-xs text-muted-foreground shadow-2xs">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className="font-medium text-foreground">Enterprise Platform Active</span>
              <span className="text-border">|</span>
              <span>Autonomous AI Engine</span>
            </div>
          </div>

          {/* Solutions Column */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-foreground">
              Core Solutions
            </p>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <Link href="/technology#sales" className="hover:text-foreground transition-colors">
                  Sales Demand Intelligence
                </Link>
              </li>
              <li>
                <Link href="/technology#inventory" className="hover:text-foreground transition-colors">
                  Warehouse &amp; Dye Optimization
                </Link>
              </li>
              <li>
                <Link href="/technology#recipes" className="hover:text-foreground transition-colors">
                  Color Kitchen &amp; SOPs
                </Link>
              </li>
              <li>
                <Link href="/technology#copilot" className="hover:text-foreground transition-colors">
                  Operational Copilot
                </Link>
              </li>
              <li>
                <Link href="/login" className="hover:text-foreground transition-colors">
                  Enterprise Portal Sign In
                </Link>
              </li>
            </ul>
          </div>

          {/* Platform Navigation */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-foreground">
              Platform Navigation
            </p>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li>
                <Link href="/features" className="hover:text-foreground transition-colors">
                  Platform Features
                </Link>
              </li>
              <li>
                <Link href="/technology" className="hover:text-foreground transition-colors">
                  Platform Solutions
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="hover:text-foreground transition-colors">
                  Pricing & Mill Tiers
                </Link>
              </li>
              <li>
                <Link href="/about" className="hover:text-foreground transition-colors">
                  Company Heritage
                </Link>
              </li>
              <li>
                <Link href="/contact" className="hover:text-foreground transition-colors">
                  Request Mill Assessment
                </Link>
              </li>
              <li>
                <Link href="/login" className="hover:text-foreground transition-colors">
                  Sign In / Quick Demo
                </Link>
              </li>
            </ul>
          </div>

          {/* Official Factory & Sales Offices */}
          <div className="space-y-3">
            <p className="text-xs font-semibold uppercase tracking-wider text-foreground">
              Official Mill Locations
            </p>
            <div className="space-y-2.5 text-xs text-muted-foreground">
              <div>
                <span className="font-semibold text-foreground block">Head Office &amp; Factory:</span>
                <span>B-74-77, Central Park, Pandesara, GIDC, Surat - 394221, Gujarat, India</span>
              </div>
              <div>
                <span className="font-semibold text-foreground block">Millennium Sales Office:</span>
                <span>A-I Hall, Wing-A, Upper Ground, Millennium Textile Market, Ring Road, Surat - 395002</span>
              </div>
              <div className="pt-1 space-y-1">
                <p>
                  <strong className="text-foreground">Email: </strong>
                  <a href="mailto:info@gokulprint.com" className="hover:text-brand underline">info@gokulprint.com</a>
                </p>
                <p>
                  <strong className="text-foreground">Phone / WhatsApp: </strong>
                  <a href="tel:+919081433354" className="hover:text-brand underline">+91 90814 33354</a>
                </p>
                <p>
                  <strong className="text-foreground">Official Store: </strong>
                  <a href="https://gokulprint.com" target="_blank" rel="noopener noreferrer" className="hover:text-brand inline-flex items-center gap-1">
                    <span>gokulprint.com</span>
                    <ArrowUpRight className="w-3 h-3" />
                  </a>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Lower Copyright Bar */}
      <div className="border-t border-border/70 py-6 bg-background/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-muted-foreground">
          <p>
            &copy; {new Date().getFullYear()} Gokul Text Print Ltd. All rights reserved. Public demonstration portal.
          </p>
          <div className="flex items-center gap-6">
            <Link href="/about" className="hover:text-foreground transition-colors">
              Privacy Policy (Demo)
            </Link>
            <Link href="/technology" className="hover:text-foreground transition-colors">
              Architecture Security
            </Link>
            <Link href="/contact" className="hover:text-foreground transition-colors">
              Support Desk
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
