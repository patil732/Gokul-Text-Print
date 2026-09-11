"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useAppShell } from "./app-shell-provider";
import {
  Search,
  X,
  LayoutDashboard,
  TrendingUp,
  Boxes,
  Bot,
  BookOpen,
  FileText,
  Bell,
  Settings,
  User,
  ArrowRight,
  Sparkles,
} from "lucide-react";

interface SearchItem {
  id: string;
  title: string;
  category: "Navigation" | "Actions" | "Textile Mill";
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
}

const SEARCH_ITEMS: SearchItem[] = [
  {
    id: "nav-dashboard",
    title: "Executive Dashboard",
    category: "Navigation",
    href: "/dashboard",
    icon: LayoutDashboard,
    description: "Main mill intelligence overview and KPI metrics",
  },
  {
    id: "nav-sales",
    title: "Sales Intelligence & Demand Forecast",
    category: "Navigation",
    href: "/sales",
    icon: TrendingUp,
    description: "30-day forecast, order volume, and fabric revenue",
  },
  {
    id: "nav-inventory",
    title: "Inventory Intelligence & Grey Cloth Stock",
    category: "Navigation",
    href: "/inventory",
    icon: Boxes,
    description: "Real-time stock meters, shortage risk, and safety buffers",
  },
  {
    id: "nav-copilot",
    title: "AI Copilot & Multi-Agent Chat",
    category: "Navigation",
    href: "/copilot",
    icon: Bot,
    description: "Ask questions on dye recipes, orders, and agent consensus",
  },
  {
    id: "nav-knowledge",
    title: "Knowledge Base & Chemical Dye SOPs",
    category: "Navigation",
    href: "/knowledge",
    icon: BookOpen,
    description: "Technical formulations, dye manuals, and defect catalogs",
  },
  {
    id: "nav-reports",
    title: "Executive Reports & Audit Logs",
    category: "Navigation",
    href: "/reports",
    icon: FileText,
    description: "Generate automated summaries, PDF reports, and CSV exports",
  },
  {
    id: "nav-alerts",
    title: "Operational Priority Alerts",
    category: "Navigation",
    href: "/alerts",
    icon: Bell,
    description: "High/Medium/Low priority mill notifications and queue",
  },
  {
    id: "nav-settings",
    title: "Mill & Agent Swarm Settings",
    category: "Navigation",
    href: "/settings",
    icon: Settings,
    description: "Consensus threshold, hyperparameters, and RBAC matrix",
  },
  {
    id: "nav-profile",
    title: "User Profile & RBAC Role",
    category: "Navigation",
    href: "/profile",
    icon: User,
    description: "View credentials, session diagnostics, and mill tenant",
  },
  {
    id: "act-forecast",
    title: "Run Real-Time Demand Forecast",
    category: "Actions",
    href: "/sales",
    icon: Sparkles,
    description: "Trigger sales order predictive pipeline",
  },
  {
    id: "act-shortage",
    title: "Review Grey Cloth Shortage Risks",
    category: "Actions",
    href: "/inventory",
    icon: Boxes,
    description: "Inspect fabric items below 5,000 meters buffer",
  },
  {
    id: "act-recipe",
    title: "Search Reactive Dye Formulations",
    category: "Actions",
    href: "/knowledge",
    icon: BookOpen,
    description: "Query RAG knowledge base for cotton recipes",
  },
];

export function AppSearchDialog() {
  const router = useRouter();
  const { searchOpen, setSearchOpen } = useAppShell();
  const [query, setQuery] = React.useState("");
  const inputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (searchOpen) {
      setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
    } else {
      setQuery("");
    }
  }, [searchOpen]);

  if (!searchOpen) return null;

  const filteredItems = SEARCH_ITEMS.filter((item) => {
    const q = query.toLowerCase().trim();
    if (!q) return true;
    return (
      item.title.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q) ||
      item.description?.toLowerCase().includes(q)
    );
  });

  const handleSelect = (href: string) => {
    setSearchOpen(false);
    router.push(href);
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-start justify-center pt-16 sm:pt-24 px-4 animate-in fade-in duration-150"
      onClick={() => setSearchOpen(false)}
    >
      <div
        className="w-full max-w-xl bg-card border border-border rounded-xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="relative border-b border-border p-3 flex items-center gap-2.5">
          <Search className="w-5 h-5 text-muted-foreground ml-1 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search pages, actions, fabrics, orders, dye recipes... (Esc to close)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-hidden"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="p-1 rounded hover:bg-muted text-muted-foreground"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <button
            type="button"
            onClick={() => setSearchOpen(false)}
            className="px-2 py-1 rounded text-xs font-medium text-muted-foreground hover:text-foreground bg-muted"
          >
            Esc
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto p-2 space-y-1">
          {filteredItems.length === 0 ? (
            <div className="py-12 text-center text-xs text-muted-foreground">
              No results found for &ldquo;{query}&rdquo;
            </div>
          ) : (
            filteredItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleSelect(item.href)}
                  className="w-full text-left flex items-center justify-between p-2.5 rounded-lg hover:bg-muted transition-colors group cursor-pointer"
                >
                  <div className="flex items-center gap-3 truncate">
                    <div className="w-8 h-8 rounded-md bg-muted group-hover:bg-brand/10 group-hover:text-brand flex items-center justify-center text-muted-foreground shrink-0 transition-colors">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="flex flex-col truncate">
                      <span className="text-sm font-semibold text-foreground truncate group-hover:text-brand transition-colors">
                        {item.title}
                      </span>
                      {item.description && (
                        <span className="text-xs text-muted-foreground truncate">
                          {item.description}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 ml-2">
                    <span className="text-[10px] uppercase font-semibold text-muted-foreground px-1.5 py-0.5 rounded bg-muted/70">
                      {item.category}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-muted-foreground group-hover:text-foreground transition-transform group-hover:translate-x-0.5" />
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Footer Hint */}
        <div className="border-t border-border/70 px-4 py-2 bg-muted/30 flex items-center justify-between text-[11px] text-muted-foreground">
          <span>Navigate with click or arrow keys</span>
          <span>Press Esc to exit</span>
        </div>
      </div>
    </div>
  );
}
