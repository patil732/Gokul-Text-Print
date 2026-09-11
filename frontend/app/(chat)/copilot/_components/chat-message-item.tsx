"use client";

import * as React from "react";
import { type ManagerOrchestrationResponse } from "@/lib/api/agents";
import { type ChatSource } from "@/lib/api/chat";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import {
  Bot,
  User,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  TrendingUp,
  Boxes,
  BookOpen,
  FileText,
  Sparkles,
  ShieldCheck,
  Layers,
  Cpu,
  Clock,
  ExternalLink,
} from "lucide-react";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agents_used?: string[];
  agent_details?: ManagerOrchestrationResponse["agent_details"];
  confidence?: number;
  sources?: ChatSource[];
  timestamp?: string;
  isStreaming?: boolean;
}

interface ChatMessageItemProps {
  message: ChatMessage;
}

export function ChatMessageItem({ message }: ChatMessageItemProps) {
  const [copied, setCopied] = React.useState(false);
  const [reasoningExpanded, setReasoningExpanded] = React.useState(true);
  const [sourcesExpanded, setSourcesExpanded] = React.useState(true);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore
    }
  };

  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end gap-3 max-w-3xl ml-auto">
        <div className="space-y-1 text-right">
          <div className="inline-block p-3.5 sm:p-4 rounded-2xl rounded-tr-xs bg-brand text-brand-fg text-xs sm:text-sm font-medium shadow-xs text-left max-w-2xl leading-relaxed whitespace-pre-wrap">
            {message.content}
          </div>
          {message.timestamp && (
            <div className="text-[10px] text-muted-foreground font-mono pr-1">
              {message.timestamp.split(".")[0].replace("T", " ")}
            </div>
          )}
        </div>
        <div className="w-8 h-8 rounded-full bg-muted border border-border flex items-center justify-center shrink-0 text-muted-foreground mt-0.5">
          <User className="w-4 h-4" />
        </div>
      </div>
    );
  }

  // Assistant Message
  const hasAgents = message.agents_used && message.agents_used.length > 0;
  const hasSources = message.sources && message.sources.length > 0;
  const confidencePct = message.confidence ? Math.round(message.confidence * 100) : 0;

  // Extract source list from knowledge agent or fallback
  const knowledgeSources: ChatSource[] =
    message.sources && message.sources.length > 0
      ? message.sources
      : message.agent_details?.knowledge?.data?.source_details
        ? message.agent_details.knowledge.data.source_details.map((s) => ({
            document: s.document,
            page: s.page,
            score: s.score,
          }))
        : message.agent_details?.knowledge?.data?.sources
          ? message.agent_details.knowledge.data.sources.map((s) => ({
              document: s,
              score: 0.9,
            }))
          : [];

  return (
    <div className="flex items-start gap-3 sm:gap-4 max-w-4xl mx-auto w-full group">
      {/* Bot Avatar */}
      <div className="w-8 h-8 rounded-full bg-purple-500/15 border border-purple-500/30 flex items-center justify-center shrink-0 text-purple-600 dark:text-purple-400 mt-1 shadow-xs">
        <Bot className="w-4 h-4" />
      </div>

      <div className="flex-1 min-w-0 space-y-4">
        {/* Main Answer Card / Text */}
        <div className="p-4 sm:p-5 rounded-2xl bg-card border border-border text-foreground shadow-xs relative">
          <div className="flex items-center justify-between gap-2 pb-2 mb-2 border-b border-border/60">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold tracking-tight text-foreground flex items-center gap-1.5">
                <span>Executive Copilot</span>
                {hasAgents && (
                  <Badge variant="outline" className="text-[10px] font-mono border-purple-500/30 text-purple-600 dark:text-purple-400">
                    Consensus Synthesized
                  </Badge>
                )}
              </span>
            </div>

            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={handleCopy}
                title="Copy answer"
                className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors text-xs flex items-center gap-1"
              >
                {copied ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-500" />
                    <span className="text-[10px] text-emerald-500 font-medium">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span className="text-[10px]">Copy</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Render Answer Text */}
          <div className="text-xs sm:text-sm text-foreground leading-relaxed whitespace-pre-wrap font-sans space-y-2">
            {message.content}
          </div>

          {message.timestamp && (
            <div className="pt-2 text-[10px] text-muted-foreground font-mono text-right">
              {message.timestamp.split(".")[0].replace("T", " ")}
            </div>
          )}
        </div>

        {/* 1. Reasoning Section (Specialist Agents + Consensus Metrics) */}
        {hasAgents && (
          <div className="rounded-xl border border-purple-500/20 bg-purple-500/5 overflow-hidden text-xs transition-all shadow-2xs">
            {/* Header / Toggle Button */}
            <button
              type="button"
              onClick={() => setReasoningExpanded(!reasoningExpanded)}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-purple-500/10 transition-colors"
            >
              <div className="flex items-center gap-2 flex-wrap">
                <Cpu className="w-4 h-4 text-purple-500" />
                <span className="font-bold text-foreground">Multi-Agent Reasoning & Orchestration</span>
                <span className="text-[11px] text-muted-foreground font-mono">
                  ({message.agents_used?.length} Specialist Agents)
                </span>
                {confidencePct > 0 && (
                  <Badge variant="outline" className="text-[10px] border-emerald-500/30 text-emerald-600 dark:text-emerald-400 font-mono font-semibold">
                    {confidencePct}% Confidence
                  </Badge>
                )}
              </div>

              <div className="flex items-center gap-1 text-muted-foreground">
                <span className="text-[11px] hidden sm:inline">
                  {reasoningExpanded ? "Collapse" : "Expand"}
                </span>
                {reasoningExpanded ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </div>
            </button>

            {/* Accordion Content */}
            {reasoningExpanded && (
              <div className="p-3.5 pt-0 space-y-3.5 border-t border-purple-500/15">
                {/* Agent Badges Used */}
                <div className="flex items-center gap-2 flex-wrap pt-2">
                  <span className="text-[11px] font-semibold text-muted-foreground">
                    Active Specialized Sub-Agents:
                  </span>
                  {message.agents_used?.map((name) => {
                    const norm = name.toLowerCase();
                    const isSales = norm.includes("sales");
                    const isInv = norm.includes("inventory");
                    const isKnow = norm.includes("knowledge");

                    return (
                      <span
                        key={name}
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold border ${
                          isSales
                            ? "bg-blue-500/10 border-blue-500/30 text-blue-600 dark:text-blue-400"
                            : isInv
                              ? "bg-amber-500/10 border-amber-500/30 text-amber-600 dark:text-amber-400"
                              : isKnow
                                ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400"
                                : "bg-purple-500/10 border-purple-500/30 text-purple-600 dark:text-purple-400"
                        }`}
                      >
                        {isSales && <TrendingUp className="w-3.5 h-3.5" />}
                        {isInv && <Boxes className="w-3.5 h-3.5" />}
                        {isKnow && <BookOpen className="w-3.5 h-3.5" />}
                        <span className="capitalize">{name} Agent</span>
                      </span>
                    );
                  })}
                </div>

                {/* Sub-Agent Data Points Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5">
                  {/* Sales Agent Details */}
                  {message.agent_details?.sales && (
                    <div className="p-3 rounded-lg border border-border bg-card/60 space-y-1.5">
                      <div className="flex items-center justify-between text-xs font-bold text-foreground">
                        <span className="flex items-center gap-1.5 text-blue-600 dark:text-blue-400">
                          <TrendingUp className="w-3.5 h-3.5" />
                          <span>Sales Agent</span>
                        </span>
                        <span className="font-mono text-[10px] text-muted-foreground">
                          {(message.agent_details.sales.confidence * 100).toFixed(0)}% conf
                        </span>
                      </div>
                      <div className="space-y-1 text-[11px] text-muted-foreground">
                        {message.agent_details.sales.data?.sales_growth !== undefined && (
                          <div className="flex justify-between">
                            <span>Growth Rate:</span>
                            <span className="font-semibold text-foreground">
                              {message.agent_details.sales.data.sales_growth > 0 ? "+" : ""}
                              {message.agent_details.sales.data.sales_growth.toFixed(1)}%
                            </span>
                          </div>
                        )}
                        {message.agent_details.sales.data?.forecast !== undefined && (
                          <div className="flex justify-between">
                            <span>Projected Demand:</span>
                            <span className="font-semibold text-foreground font-mono">
                              {Math.round(message.agent_details.sales.data.forecast).toLocaleString()} m
                            </span>
                          </div>
                        )}
                        {message.agent_details.sales.data?.top_product && (
                          <div className="flex justify-between">
                            <span>Leading Fabric:</span>
                            <span className="font-semibold text-foreground truncate max-w-[120px]">
                              {message.agent_details.sales.data.top_product}
                            </span>
                          </div>
                        )}
                        {message.agent_details.sales.data?.recommendation && (
                          <div className="pt-1 text-[10px] text-foreground font-medium border-t border-border/40">
                            Strategy: {message.agent_details.sales.data.recommendation}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Inventory Agent Details */}
                  {message.agent_details?.inventory && (
                    <div className="p-3 rounded-lg border border-border bg-card/60 space-y-1.5">
                      <div className="flex items-center justify-between text-xs font-bold text-foreground">
                        <span className="flex items-center gap-1.5 text-amber-600 dark:text-amber-400">
                          <Boxes className="w-3.5 h-3.5" />
                          <span>Inventory Agent</span>
                        </span>
                        <span className="font-mono text-[10px] text-muted-foreground">
                          {(message.agent_details.inventory.confidence * 100).toFixed(0)}% conf
                        </span>
                      </div>
                      <div className="space-y-1 text-[11px] text-muted-foreground">
                        {message.agent_details.inventory.data?.stock_health && (
                          <div className="flex justify-between">
                            <span>Stock Buffer:</span>
                            <span className="font-semibold text-foreground">
                              {message.agent_details.inventory.data.stock_health}
                            </span>
                          </div>
                        )}
                        {message.agent_details.inventory.data?.remaining_days !== undefined && (
                          <div className="flex justify-between">
                            <span>Buffer Horizon:</span>
                            <span className="font-semibold text-foreground font-mono">
                              {message.agent_details.inventory.data.remaining_days} days
                            </span>
                          </div>
                        )}
                        {message.agent_details.inventory.data?.decision && (
                          <div className="flex justify-between">
                            <span>Reorder Recommendation:</span>
                            <span className="font-semibold text-foreground">
                              {message.agent_details.inventory.data.decision}
                            </span>
                          </div>
                        )}
                        {message.agent_details.inventory.data?.model_accuracy !== undefined && (
                          <div className="pt-1 text-[10px] text-muted-foreground border-t border-border/40">
                            Engine: {message.agent_details.inventory.data.model_type || "Supply Optimizer"} (
                            {(message.agent_details.inventory.data.model_accuracy * 100).toFixed(1)}% acc)
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Knowledge Agent Details */}
                  {message.agent_details?.knowledge && (
                    <div className="p-3 rounded-lg border border-border bg-card/60 space-y-1.5">
                      <div className="flex items-center justify-between text-xs font-bold text-foreground">
                        <span className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
                          <BookOpen className="w-3.5 h-3.5" />
                          <span>Knowledge Agent</span>
                        </span>
                        <span className="font-mono text-[10px] text-muted-foreground">
                          {(message.agent_details.knowledge.confidence * 100).toFixed(0)}% conf
                        </span>
                      </div>
                      <div className="space-y-1 text-[11px] text-muted-foreground">
                        {message.agent_details.knowledge.data?.relevant_chunks !== undefined && (
                          <div className="flex justify-between">
                            <span>RAG Chunks Analyzed:</span>
                            <span className="font-semibold text-foreground font-mono">
                              {message.agent_details.knowledge.data.relevant_chunks} chunks
                            </span>
                          </div>
                        )}
                        {message.agent_details.knowledge.data?.query_used && (
                          <div className="flex justify-between">
                            <span>Vector Query:</span>
                            <span className="font-mono text-[10px] text-foreground truncate max-w-[120px]">
                              {message.agent_details.knowledge.data.query_used}
                            </span>
                          </div>
                        )}
                        {message.agent_details.knowledge.data?.policy && (
                          <div className="pt-1 text-[10px] text-foreground font-medium line-clamp-2 border-t border-border/40">
                            Policy: {message.agent_details.knowledge.data.policy}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Final Confidence Meter */}
                {confidencePct > 0 && (
                  <div className="p-2.5 rounded-lg bg-background border border-border/60 flex items-center justify-between gap-3 text-xs">
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-500" />
                      <span className="font-semibold text-foreground">Consensus Confidence Score:</span>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="w-32 sm:w-48 bg-muted h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-emerald-500 h-full rounded-full transition-all"
                          style={{ width: `${confidencePct}%` }}
                        />
                      </div>
                      <span className="font-mono font-bold text-foreground tabular-nums">
                        {confidencePct}%
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* 2. Sources Section (Document citations) */}
        {knowledgeSources.length > 0 && (
          <div className="rounded-xl border border-border bg-muted/20 overflow-hidden text-xs transition-all shadow-2xs">
            <button
              type="button"
              onClick={() => setSourcesExpanded(!sourcesExpanded)}
              className="w-full flex items-center justify-between p-3 text-left hover:bg-muted/40 transition-colors"
            >
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-emerald-500" />
                <span className="font-bold text-foreground">Knowledge Base Citations & Sources</span>
                <span className="text-[11px] text-muted-foreground font-mono">
                  ({knowledgeSources.length} Citations)
                </span>
              </div>

              <div className="flex items-center gap-1 text-muted-foreground">
                <span className="text-[11px] hidden sm:inline">
                  {sourcesExpanded ? "Collapse" : "Expand"}
                </span>
                {sourcesExpanded ? (
                  <ChevronDown className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </div>
            </button>

            {sourcesExpanded && (
              <div className="p-3 pt-0 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 border-t border-border/40">
                {knowledgeSources.map((src, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg border border-border bg-card flex items-start gap-2 text-xs"
                  >
                    <FileText className="w-4 h-4 text-brand shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0 space-y-0.5">
                      <div className="font-semibold text-foreground truncate" title={src.document}>
                        {src.document}
                      </div>
                      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                        {src.page ? <span>Page {src.page}</span> : <span>Technical Doc</span>}
                        {src.score !== undefined && (
                          <span className="font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
                            {(src.score * 100).toFixed(0)}% Match
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
