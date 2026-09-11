import type { Metadata } from "next";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SectionReveal } from "@/components/ui/page-transition";
import {
  Settings,
  Sliders,
  Shield,
  Cpu,
  Database,
  Save,
  CheckCircle2,
  Lock,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Settings | Gokul Text Print",
  description: "Mill configuration, multi-agent hyperparameters, and RBAC matrix.",
};

export default function SettingsPage() {
  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <SectionReveal delay={0}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-md bg-muted text-foreground">
                <Settings className="w-5 h-5" />
              </span>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                Platform & Agent Settings
              </h2>
              <Badge variant="outline" className="text-[10px] font-semibold border-brand/30 text-brand">
                Step 11 Staging
              </Badge>
            </div>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Configure factory parameters, agent swarm consensus sensitivity, and role-based permissions.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <Button size="sm" className="text-xs gap-1.5 font-semibold">
              <Save className="w-3.5 h-3.5" />
              <span>Save Changes</span>
            </Button>
          </div>
        </div>
      </SectionReveal>

      {/* Settings Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Agent Consensus Parameters */}
        <SectionReveal delay={0.05}>
          <Card className="bg-card border-border h-full flex flex-col">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-brand" />
                <CardTitle className="text-base">Autonomous Swarm Consensus</CardTitle>
              </div>
              <CardDescription>
                Control threshold sensitivity required before agents can auto-dispatch production changes.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 flex-1">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-foreground">Minimum Agent Agreement Threshold</span>
                  <span className="font-bold text-brand tabular-nums">75% (3 of 4 Agents)</span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="100"
                  defaultValue="75"
                  className="w-full accent-brand cursor-pointer"
                />
                <p className="text-[11px] text-muted-foreground">
                  Sales, Inventory, Chemical RAG, and Dispatcher must agree to trigger automatic rescheduling.
                </p>
              </div>

              <div className="space-y-2 pt-2 border-t border-border/60">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-foreground">Grey Cloth Safety Buffer</span>
                  <span className="font-bold text-foreground tabular-nums">5,000 meters</span>
                </div>
                <input
                  type="range"
                  min="2000"
                  max="10000"
                  step="500"
                  defaultValue="5000"
                  className="w-full accent-brand cursor-pointer"
                />
                <p className="text-[11px] text-muted-foreground">
                  Automatic warning dispatched if any fabric type falls below this meter threshold.
                </p>
              </div>

              <div className="space-y-2 pt-2 border-t border-border/60">
                <label className="flex items-center gap-2.5 text-xs text-foreground cursor-pointer">
                  <input type="checkbox" defaultChecked className="rounded border-border accent-brand" />
                  <span className="font-medium">Enable real-time Slack/WhatsApp emergency dispatch</span>
                </label>
                <label className="flex items-center gap-2.5 text-xs text-foreground cursor-pointer">
                  <input type="checkbox" defaultChecked className="rounded border-border accent-brand" />
                  <span className="font-medium">Require CEO / Plant Manager sign-off for orders &gt; ₹10,00,000</span>
                </label>
              </div>
            </CardContent>
          </Card>
        </SectionReveal>

        {/* Mill Profile & Database */}
        <SectionReveal delay={0.1}>
          <Card className="bg-card border-border h-full flex flex-col">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-emerald-500" />
                <CardTitle className="text-base">Mill Connection & ERP Integration</CardTitle>
              </div>
              <CardDescription>
                Active data synchronization with factory machinery and SQLite ERP database.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 flex-1">
              <div className="p-3 rounded-lg bg-muted/40 border border-border/60 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Database Engine:</span>
                  <span className="font-semibold text-foreground">SQLite (ai_decision.db)</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Backend API Host:</span>
                  <span className="font-semibold text-foreground">http://localhost:5001</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">ERP Sales Orders Ingested:</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">3,493 Orders</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">ERP Inventory Bins Ingested:</span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">2,000 Bins</span>
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-border/60">
                <div className="text-xs font-semibold text-foreground">Active Mill Organization</div>
                <input
                  type="text"
                  defaultValue="Gokul Text Print Mills Ltd."
                  className="w-full px-3 py-2 text-xs rounded-lg border border-border bg-background text-foreground"
                />
              </div>

              <div className="space-y-2">
                <div className="text-xs font-semibold text-foreground">Factory Location</div>
                <input
                  type="text"
                  defaultValue="Surat Industrial Textile Zone, Gujarat, India"
                  className="w-full px-3 py-2 text-xs rounded-lg border border-border bg-background text-foreground"
                />
              </div>
            </CardContent>
          </Card>
        </SectionReveal>
      </div>
    </div>
  );
}
