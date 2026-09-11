"use client";

import * as React from "react";
import Link from "next/link";
import { orchestrateManager, type ManagerOrchestrationResponse } from "@/lib/api/agents";
import { getChatHistory, type ChatHistoryEntry } from "@/lib/api/chat";
import { CopilotSidebar } from "./_components/copilot-sidebar";
import { ChatMessageItem, type ChatMessage } from "./_components/chat-message-item";
import { CopilotInput } from "./_components/copilot-input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import {
  Bot,
  PanelLeft,
  LayoutDashboard,
  Plus,
  Sparkles,
  TrendingUp,
  Boxes,
  BookOpen,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  ExternalLink,
} from "lucide-react";

export default function FullPageCopilot() {
  const [sidebarOpen, setSidebarOpen] = React.useState(true);
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [history, setHistory] = React.useState<ChatHistoryEntry[]>([]);
  const [loadingHistory, setLoadingHistory] = React.useState(true);
  const [selectedChatId, setSelectedChatId] = React.useState<string | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Load chat history from GET /api/chat/history
  const loadHistory = React.useCallback(async () => {
    setLoadingHistory(true);
    try {
      const res = await getChatHistory({ limit: 50 });
      if (res.status === "success" && Array.isArray(res.history)) {
        setHistory(res.history);
      }
    } catch {
      // ignore
    } finally {
      setLoadingHistory(false);
    }
  }, []);

  React.useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  // Handle Send Message
  const handleSendMessage = async (question: string) => {
    if (!question.trim() || isLoading) return;

    setError(null);
    const userMsgId = `user-${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMsgId,
      role: "user",
      content: question,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const res = await orchestrateManager(question);

      if (res.status === "success") {
        const assistantMsg: ChatMessage = {
          id: `bot-${Date.now()}`,
          role: "assistant",
          content: res.answer,
          agents_used: res.agents_used,
          agent_details: res.agent_details,
          confidence: res.confidence,
          timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, assistantMsg]);
        // Refresh history to include new turn
        loadHistory();
      } else {
        setError(res.message || "Executive Copilot returned an error.");
      }
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to connect to Multi-Agent Orchestrator (POST /api/agents/manager)."
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Handle selecting a chat from history
  const handleSelectChat = (entry: ChatHistoryEntry) => {
    setSelectedChatId(entry.chat_id);
    const userMsg: ChatMessage = {
      id: `hist-user-${entry.chat_id}`,
      role: "user",
      content: entry.question,
      timestamp: entry.timestamp,
    };
    const botMsg: ChatMessage = {
      id: `hist-bot-${entry.chat_id}`,
      role: "assistant",
      content: entry.answer,
      sources: entry.retrieved_documents,
      agents_used: entry.is_manager ? ["sales", "inventory", "knowledge"] : ["knowledge"],
      timestamp: entry.timestamp,
    };
    setMessages([userMsg, botMsg]);

    // Close on mobile screens
    if (window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  };

  // Handle New Chat
  const handleNewChat = () => {
    setMessages([]);
    setSelectedChatId(null);
    setError(null);
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      {/* 1. Collapsible Conversation History Sidebar */}
      <CopilotSidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewChat={handleNewChat}
        history={history}
        loadingHistory={loadingHistory}
        selectedChatId={selectedChatId}
        onSelectChat={handleSelectChat}
      />

      {/* 2. Main Chat Surface */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden bg-background">
        {/* Top Minimal Navigation Bar */}
        <header className="h-14 shrink-0 px-3 sm:px-5 border-b border-border flex items-center justify-between gap-3 bg-card/60 backdrop-blur-md z-10">
          <div className="flex items-center gap-2">
            {!sidebarOpen && (
              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                title="Open conversation history"
              >
                <PanelLeft className="w-5 h-5" />
              </button>
            )}

            <div className="flex items-center gap-2">
              <span className="p-1 rounded-md bg-purple-500/10 text-purple-600 dark:text-purple-400">
                <Bot className="w-4 h-4" />
              </span>
              <span className="font-bold text-sm tracking-tight text-foreground hidden sm:inline">
                Executive AI Copilot
              </span>
              <Badge
                variant="outline"
                className="text-[10px] font-mono border-emerald-500/30 text-emerald-600 dark:text-emerald-400 bg-emerald-500/5"
              >
                Manager Agent Online
              </Badge>
            </div>
          </div>

          {/* Quick Actions Right */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleNewChat}
              className="text-xs h-8 gap-1.5 border-border"
            >
              <Plus className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">New Chat</span>
            </Button>

            <Link href="/dashboard">
              <Button
                variant="ghost"
                size="sm"
                className="text-xs h-8 gap-1.5 text-muted-foreground hover:text-foreground"
              >
                <LayoutDashboard className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Exit to Dashboard</span>
              </Button>
            </Link>

            <ThemeToggle />
          </div>
        </header>

        {/* Scrollable Conversation Stream */}
        <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 space-y-6">
          {messages.length === 0 ? (
            /* Empty State Hero */
            <div className="max-w-2xl mx-auto py-12 text-center space-y-6 animate-fadeIn">
              <div className="w-14 h-14 mx-auto rounded-2xl bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-600 dark:text-purple-400 shadow-lg">
                <Bot className="w-7 h-7" />
              </div>

              <div className="space-y-2">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                  Gokul Text Print — Executive Copilot
                </h1>
                <p className="text-xs sm:text-sm text-muted-foreground max-w-lg mx-auto">
                  Ask cross-functional questions combining live ERP sales demand forecasts, warehouse grey cloth safety buffers, and technical SOP documentation.
                </p>
              </div>

              {/* Feature Highlights Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2 text-left">
                <div className="p-3.5 rounded-xl border border-border bg-card/60 space-y-1">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-blue-600 dark:text-blue-400">
                    <TrendingUp className="w-4 h-4" />
                    <span>Sales Intelligence</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    Multi-horizon meter forecasting, client orders, and volume trends.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl border border-border bg-card/60 space-y-1">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-amber-600 dark:text-amber-400">
                    <Boxes className="w-4 h-4" />
                    <span>Inventory Logistics</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    24 factory storage bins, shortage risks, and buffer depletion warnings.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl border border-border bg-card/60 space-y-1">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-600 dark:text-emerald-400">
                    <BookOpen className="w-4 h-4" />
                    <span>Knowledge RAG</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    Mill formulations, reactive dye SOPs, and compliance guidelines.
                  </p>
                </div>
              </div>
            </div>
          ) : (
            /* Message Thread */
            messages.map((msg) => <ChatMessageItem key={msg.id} message={msg} />)
          )}

          {/* Thinking / Orchestrating Indicator */}
          {isLoading && (
            <div className="flex items-center gap-3 max-w-4xl mx-auto text-xs text-muted-foreground p-3 rounded-xl border border-purple-500/20 bg-purple-500/5 animate-pulse">
              <div className="w-7 h-7 rounded-full bg-purple-500/20 text-purple-600 dark:text-purple-400 flex items-center justify-center shrink-0">
                <Sparkles className="w-3.5 h-3.5 animate-spin" />
              </div>
              <div className="space-y-0.5">
                <div className="font-semibold text-foreground">
                  Manager Agent orchestrating multi-agent consensus...
                </div>
                <div className="text-[11px] text-muted-foreground">
                  Querying Sales, Inventory, and Knowledge specialist agents in parallel.
                </div>
              </div>
            </div>
          )}

          {/* Error Banner */}
          {error && (
            <div className="max-w-4xl mx-auto p-3.5 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-600 dark:text-rose-400 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <div className="flex-1 font-medium">{error}</div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* 3. Bottom Auto-Resizing Input Dock */}
        <footer className="shrink-0 border-t border-border bg-card/60 backdrop-blur-md">
          <CopilotInput
            onSend={handleSendMessage}
            isLoading={isLoading}
            disabled={isLoading}
          />
        </footer>
      </div>
    </div>
  );
}
