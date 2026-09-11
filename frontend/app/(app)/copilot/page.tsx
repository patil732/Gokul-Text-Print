import type { Metadata } from "next";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SectionReveal } from "@/components/ui/page-transition";
import {
  Bot,
  Sparkles,
  Send,
  MessageSquare,
  Cpu,
  Database,
  Search,
  CheckCircle2,
  TrendingUp,
} from "lucide-react";

export const metadata: Metadata = {
  title: "AI Copilot | Gokul Text Print",
  description: "Autonomous multi-agent assistant for textile mills: sales, inventory, recipes, and dispatcher.",
};

export default function AiCopilotPage() {
  const samplePrompts = [
    "What is the forecasted demand for Cotton 60s Cambric next week?",
    "Do we have enough reactive dye chemical stock for 20,000 meters of navy print?",
    "Why was Batch #942 delayed by the dispatcher agent?",
    "Recommend grey cloth allocation to maximize printing gross margins.",
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <SectionReveal delay={0}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-md bg-purple-500/10 text-purple-600 dark:text-purple-400">
                <Bot className="w-5 h-5" />
              </span>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                AI Copilot
              </h2>
              <Badge variant="outline" className="text-[10px] font-semibold border-brand/30 text-brand">
                Step 8 Staging
              </Badge>
            </div>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Autonomous textile assistant orchestrated across RAG formulations, SQL ERP database, and consensus agents.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-card border border-border text-xs text-muted-foreground">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>4 Agents Online</span>
            </div>
            <Button size="sm" variant="outline" className="text-xs border-border">
              Reset Session
            </Button>
          </div>
        </div>
      </SectionReveal>

      {/* Swarm Agent Cards */}
      <SectionReveal delay={0.05}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="p-3 rounded-xl bg-card border border-border flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div className="truncate">
              <div className="text-xs font-bold text-foreground">Sales Agent</div>
              <div className="text-[10px] text-muted-foreground truncate">Order history & demand trend</div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-card border border-border flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">
              <Database className="w-4 h-4" />
            </div>
            <div className="truncate">
              <div className="text-xs font-bold text-foreground">Inventory Agent</div>
              <div className="text-[10px] text-muted-foreground truncate">Grey stock & buffer levels</div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-card border border-border flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
              <Search className="w-4 h-4" />
            </div>
            <div className="truncate">
              <div className="text-xs font-bold text-foreground">Knowledge RAG Agent</div>
              <div className="text-[10px] text-muted-foreground truncate">Dye formulas & chemical SOPs</div>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-card border border-border flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0">
              <Cpu className="w-4 h-4" />
            </div>
            <div className="truncate">
              <div className="text-xs font-bold text-foreground">Dispatcher Swarm</div>
              <div className="text-[10px] text-muted-foreground truncate">4/4 Consensus decision engine</div>
            </div>
          </div>
        </div>
      </SectionReveal>

      {/* Chat Preview Interface */}
      <SectionReveal delay={0.1}>
        <Card className="bg-card border-border overflow-hidden">
          <CardHeader className="border-b border-border/70 py-3.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-brand" />
                <CardTitle className="text-sm">Interactive Mill Intelligence Assistant</CardTitle>
              </div>
              <span className="text-[11px] text-muted-foreground">Connected to Flask AI Swarm</span>
            </div>
          </CardHeader>

          <CardContent className="p-4 sm:p-6 space-y-4">
            {/* Sample Assistant Message */}
            <div className="flex gap-3 max-w-2xl">
              <div className="w-8 h-8 rounded-lg bg-brand text-brand-fg flex items-center justify-center text-xs font-bold shrink-0 shadow-xs">
                <Bot className="w-4 h-4" />
              </div>
              <div className="space-y-2 p-3.5 rounded-2xl bg-muted/60 text-xs text-foreground leading-relaxed border border-border/60">
                <p className="font-semibold text-brand">Gokul Swarm Copilot:</p>
                <p>
                  Welcome to the autonomous textile intelligence console. I have access to your mill&apos;s real-time sales orders, grey cloth inventory buffers, and chemical dye formulation manuals.
                </p>
                <p className="text-muted-foreground text-[11px]">
                  How may I assist your plant operations today?
                </p>
              </div>
            </div>

            {/* Quick Prompt Chips */}
            <div className="pt-3 border-t border-border/60 space-y-2">
              <span className="text-[11px] font-semibold text-muted-foreground block">
                Suggested questions:
              </span>
              <div className="flex flex-wrap gap-2">
                {samplePrompts.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    className="px-3 py-1.5 rounded-lg text-xs bg-card hover:bg-muted border border-border text-foreground text-left transition-colors cursor-pointer"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>

            {/* Chat Input Placeholder */}
            <div className="pt-2">
              <div className="relative flex items-center">
                <input
                  type="text"
                  placeholder="Ask a question about mill operations, orders, or formulations... (Step 8 will wire live SSE streaming)"
                  className="w-full px-4 py-3 pr-12 text-sm rounded-xl border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                />
                <Button size="sm" className="absolute right-1.5 h-8 w-8 p-0 rounded-lg">
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </SectionReveal>
    </div>
  );
}
