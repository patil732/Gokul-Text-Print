import type { Metadata } from "next";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SectionReveal } from "@/components/ui/page-transition";
import {
  Bell,
  AlertTriangle,
  CheckCircle2,
  Filter,
  Check,
  RotateCcw,
  SlidersHorizontal,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Operational Alerts | Gokul Text Print",
  description: "Real-time High, Medium, and Low operational priority incidents and resolution queue.",
};

export default function AlertsPage() {
  const alerts = [
    {
      id: "ALT-904",
      title: "Grey Cloth Shortage: Cotton 60s Cambric",
      category: "Inventory",
      description: "Bin #14 balance dropped to 3,200m (minimum buffer: 5,000m). Recommended action: dispatch replenishment order.",
      priority: "CRITICAL" as const,
      time: "12m ago",
      source: "Inventory Agent",
      status: "Active",
    },
    {
      id: "ALT-902",
      title: "Print Machine #3 Rotary Screen Calibration Drift",
      category: "Production Line",
      description: "Registration tolerance exceeded ±0.2mm on continuous georgette run. Recommended action: halt and realign head.",
      priority: "HIGH" as const,
      time: "48m ago",
      source: "Quality Vision Swarm",
      status: "Investigating",
    },
    {
      id: "ALT-899",
      title: "Agent Swarm Consensus Reached: Batch #942",
      category: "Dispatcher Swarm",
      description: "4 of 4 agents approved shifting reactive navy batch to night shift to balance boiler steam load.",
      priority: "SUCCESS" as const,
      time: "2h ago",
      source: "Multi-Agent Consensus",
      status: "Resolved",
    },
    {
      id: "ALT-895",
      title: "Sodium Hydrosulfite Reorder Reminder",
      category: "Chemical Kitchen",
      description: "Remaining discharge printing chemical stock projected to exhaust within 6 working days.",
      priority: "MEDIUM" as const,
      time: "4h ago",
      source: "RAG Recipe Agent",
      status: "Active",
    },
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <SectionReveal delay={0}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-md bg-rose-500/10 text-rose-600 dark:text-rose-400">
                <Bell className="w-5 h-5" />
              </span>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                Operational Alerts & Incident Queue
              </h2>
              <Badge variant="outline" className="text-[10px] font-semibold border-brand/30 text-brand">
                Step 11 Staging
              </Badge>
            </div>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Prioritized queue of real-time mill notifications, sensor alarms, and autonomous swarm consensus flags.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <Button variant="outline" size="sm" className="text-xs gap-1.5 border-border">
              <Filter className="w-3.5 h-3.5" />
              <span>Filter Priority</span>
            </Button>
            <Button size="sm" className="text-xs gap-1.5 font-semibold">
              <Check className="w-3.5 h-3.5" />
              <span>Acknowledge All</span>
            </Button>
          </div>
        </div>
      </SectionReveal>

      {/* Priority Summary Cards */}
      <SectionReveal delay={0.05}>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-card border border-border flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-xs text-muted-foreground">Critical Shortages</span>
              <div className="text-2xl font-bold text-rose-500">1 Item</div>
            </div>
            <PriorityBadge priority="CRITICAL" label="High Urgency" />
          </div>

          <div className="p-4 rounded-xl bg-card border border-border flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-xs text-muted-foreground">Active Line Warnings</span>
              <div className="text-2xl font-bold text-amber-500">2 Warnings</div>
            </div>
            <PriorityBadge priority="HIGH" label="Warning" />
          </div>

          <div className="p-4 rounded-xl bg-card border border-border flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="text-xs text-muted-foreground">Swarm Resolutions Today</span>
              <div className="text-2xl font-bold text-emerald-500">14 Resolved</div>
            </div>
            <PriorityBadge priority="SUCCESS" label="Healthy" />
          </div>
        </div>
      </SectionReveal>

      {/* Alerts Feed */}
      <SectionReveal delay={0.1}>
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-base">Real-Time Operational Incident Queue</CardTitle>
            <CardDescription>
              Sorted by operational impact and required supervisor intervention.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y divide-border">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-muted/30 px-3 rounded-xl transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">
                      <PriorityBadge priority={alert.priority} />
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-bold text-foreground">
                          {alert.title}
                        </span>
                        <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-muted text-muted-foreground">
                          {alert.category}
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        {alert.description}
                      </p>
                      <div className="flex items-center gap-2 text-[11px] text-muted-foreground pt-0.5">
                        <span className="font-mono">{alert.id}</span>
                        <span>•</span>
                        <span>Source: {alert.source}</span>
                        <span>•</span>
                        <span>{alert.time}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end md:self-center shrink-0">
                    <Button size="sm" variant="outline" className="text-xs h-8 px-3 border-border">
                      Dismiss
                    </Button>
                    <Button size="sm" className="text-xs h-8 px-3 font-semibold">
                      Take Action
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </SectionReveal>
    </div>
  );
}
