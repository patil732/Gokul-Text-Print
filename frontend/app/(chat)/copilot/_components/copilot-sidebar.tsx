"use client";

import * as React from "react";
import Link from "next/link";
import { type ChatHistoryEntry } from "@/lib/api/chat";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import {
  Plus,
  Search,
  MessageSquare,
  PanelLeftClose,
  LayoutDashboard,
  Bot,
  User,
  Sparkles,
  ArrowLeft,
  Clock,
  ExternalLink,
} from "lucide-react";

interface CopilotSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onNewChat: () => void;
  history: ChatHistoryEntry[];
  loadingHistory: boolean;
  selectedChatId: string | null;
  onSelectChat: (entry: ChatHistoryEntry) => void;
}

export function CopilotSidebar({
  isOpen,
  onClose,
  onNewChat,
  history,
  loadingHistory,
  selectedChatId,
  onSelectChat,
}: CopilotSidebarProps) {
  const [search, setSearch] = React.useState("");

  const filteredHistory = React.useMemo(() => {
    if (!search.trim()) return history;
    const q = search.toLowerCase();
    return history.filter(
      (item) =>
        item.question.toLowerCase().includes(q) ||
        item.answer.toLowerCase().includes(q)
    );
  }, [history, search]);

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 flex flex-col w-72 sm:w-80 bg-card border-r border-border transition-transform duration-300 ease-in-out md:relative md:translate-x-0 ${
        isOpen ? "translate-x-0" : "-translate-x-full md:-ml-72 md:sm:-ml-80"
      }`}
    >
      {/* Top Header */}
      <div className="flex items-center justify-between p-3.5 border-b border-border">
        <div className="flex items-center gap-2.5">
          <span className="p-1.5 rounded-lg bg-brand/10 text-brand">
            <Bot className="w-5 h-5" />
          </span>
          <div>
            <h2 className="text-sm font-bold tracking-tight text-foreground flex items-center gap-1.5">
              <span>AI Copilot</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-purple-500/10 text-purple-600 dark:text-purple-400 font-mono font-medium">
                v5.0
              </span>
            </h2>
            <p className="text-[11px] text-muted-foreground">Multi-Agent Consensus</p>
          </div>
        </div>

        <button
          type="button"
          onClick={onClose}
          title="Collapse sidebar"
          className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
        >
          <PanelLeftClose className="w-4 h-4" />
        </button>
      </div>

      {/* Action Buttons: New Chat & Search */}
      <div className="p-3 space-y-2 border-b border-border/60">
        <Button
          onClick={onNewChat}
          className="w-full justify-start gap-2 text-xs font-semibold h-9 shadow-xs"
        >
          <Plus className="w-4 h-4" />
          <span>New Conversation</span>
        </Button>

        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search past questions..."
            className="w-full pl-8 pr-2.5 py-1.5 text-xs rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>
      </div>

      {/* History List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        <div className="px-2 py-1 flex items-center justify-between text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">
          <span>Conversation History</span>
          <span className="font-mono text-[10px] text-muted-foreground/80">
            {filteredHistory.length}
          </span>
        </div>

        {loadingHistory ? (
          <div className="space-y-2 p-2">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-12 rounded-lg bg-muted/40 animate-pulse" />
            ))}
          </div>
        ) : filteredHistory.length === 0 ? (
          <div className="p-6 text-center text-xs text-muted-foreground space-y-1">
            <MessageSquare className="w-6 h-6 mx-auto text-muted-foreground/40 mb-1" />
            <p className="font-medium">No past conversations</p>
            <p className="text-[11px] text-muted-foreground/80">
              {search ? "No match for your search." : "Your question history will appear here."}
            </p>
          </div>
        ) : (
          filteredHistory.map((item) => {
            const isSelected = selectedChatId === item.chat_id;
            const timeStr = item.timestamp ? item.timestamp.split(".")[0].replace("T", " ") : "";

            return (
              <button
                key={item.chat_id}
                type="button"
                onClick={() => onSelectChat(item)}
                className={`w-full text-left p-2.5 rounded-lg text-xs transition-colors flex items-start gap-2.5 group relative ${
                  isSelected
                    ? "bg-brand/10 text-foreground border border-brand/20 font-medium"
                    : "hover:bg-muted/60 text-muted-foreground hover:text-foreground"
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5 shrink-0 mt-0.5 text-muted-foreground group-hover:text-brand" />
                <div className="flex-1 min-w-0 space-y-0.5">
                  <div className="font-medium text-foreground truncate">
                    {item.question}
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                    <span className="truncate flex items-center gap-1 font-mono">
                      <Clock className="w-2.5 h-2.5" />
                      {timeStr}
                    </span>
                    {item.is_manager && (
                      <span className="px-1 rounded bg-purple-500/10 text-purple-600 dark:text-purple-400 font-mono text-[9px]">
                        Orchestrated
                      </span>
                    )}
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>

      {/* Footer: User & Back to Dashboard */}
      <div className="p-3 border-t border-border bg-card/80 space-y-2">
        <Link
          href="/dashboard"
          className="flex items-center justify-between p-2 rounded-lg border border-border bg-background hover:bg-muted text-foreground text-xs font-medium transition-colors"
        >
          <div className="flex items-center gap-2">
            <LayoutDashboard className="w-3.5 h-3.5 text-brand" />
            <span>Exit to Dashboard</span>
          </div>
          <ExternalLink className="w-3 h-3 text-muted-foreground" />
        </Link>

        <div className="flex items-center justify-between pt-1 px-1">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-brand/15 text-brand font-bold text-xs flex items-center justify-center">
              GP
            </div>
            <div className="text-[11px] leading-tight">
              <div className="font-semibold text-foreground">Gokul Executive</div>
              <div className="text-muted-foreground">Manager Tier</div>
            </div>
          </div>
          <ThemeToggle />
        </div>
      </div>
    </aside>
  );
}
