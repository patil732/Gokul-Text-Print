"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAppShell } from "./app-shell-provider";
import { useAuth } from "@/components/providers/auth-provider";
import {
  Layers,
  LayoutDashboard,
  TrendingUp,
  Boxes,
  Bot,
  BookOpen,
  FileText,
  Bell,
  Settings,
  ChevronLeft,
  ChevronRight,
  Activity,
  ShieldAlert,
  Server,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
  badgeVariant?: "default" | "brand" | "amber" | "rose";
}

export const ADMIN_SIDEBAR_ITEMS: NavItem[] = [
  {
    label: "Admin Center",
    href: "/admin",
    icon: ShieldAlert,
    badge: "SYS",
    badgeVariant: "rose",
  },
  {
    label: "CEO Executive View",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Alerts",
    href: "/alerts",
    icon: Bell,
    badgeVariant: "rose",
  },
  {
    label: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

export const CEO_SIDEBAR_ITEMS: NavItem[] = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Sales Intelligence",
    href: "/sales",
    icon: TrendingUp,
  },
  {
    label: "Inventory Intelligence",
    href: "/inventory",
    icon: Boxes,
  },
  {
    label: "AI Copilot",
    href: "/copilot",
    icon: Bot,
    badge: "AI",
    badgeVariant: "brand",
  },
  {
    label: "Knowledge Base",
    href: "/knowledge",
    icon: BookOpen,
  },
  {
    label: "Reports",
    href: "/reports",
    icon: FileText,
  },
  {
    label: "Alerts",
    href: "/alerts",
    icon: Bell,
    badgeVariant: "rose",
  },
  {
    label: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

export const SIDEBAR_ITEMS = CEO_SIDEBAR_ITEMS;

export function AppSidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar, unreadAlertsCount } = useAppShell();
  const { user } = useAuth();

  const isAdmin = user?.role?.toUpperCase() === "ADMIN";
  const navItems = isAdmin ? ADMIN_SIDEBAR_ITEMS : CEO_SIDEBAR_ITEMS;
  const brandHref = isAdmin ? "/admin" : "/dashboard";

  const isItemActive = (href: string) => {
    if (href === "/admin") return pathname === "/admin";
    if (href === "/dashboard") return pathname === "/dashboard";
    return pathname.startsWith(href);
  };

  return (
    <aside
      className={`hidden lg:flex flex-col bg-card border-r border-border transition-all duration-300 select-none z-30 shrink-0 ${
        sidebarCollapsed ? "w-[72px]" : "w-64"
      }`}
      aria-label="Application Sidebar"
    >
      {/* Brand & Toggle Header */}
      <div className="h-16 border-b border-border flex items-center justify-between px-3.5">
        <Link
          href={brandHref}
          className="flex items-center gap-3 overflow-hidden text-foreground hover:opacity-90 transition-opacity"
          title={`Gokul Text Print — ${isAdmin ? "Admin Operations" : "Executive Intelligence"}`}
        >
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 shadow-xs ${
              isAdmin
                ? "bg-red-500/15 text-red-600 dark:text-red-400"
                : "bg-brand text-brand-fg"
            }`}
          >
            {isAdmin ? <ShieldAlert className="w-5 h-5" /> : <Layers className="w-5 h-5" />}
          </div>
          {!sidebarCollapsed && (
            <div className="flex flex-col truncate">
              <span className="font-bold text-sm tracking-tight truncate leading-tight">
                Gokul Text Print
              </span>
              <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">
                {isAdmin ? "Admin Center" : "Industrial AI Mill"}
              </span>
            </div>
          )}
        </Link>

        {/* Desktop Collapse Toggle */}
        <button
          type="button"
          onClick={toggleSidebar}
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          className="p-1.5 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-1">
        {navItems.map((item) => {
          const active = isItemActive(item.href);
          const Icon = item.icon;
          const badge =
            item.href === "/alerts" && unreadAlertsCount > 0
              ? String(unreadAlertsCount)
              : item.badge;

          return (
            <Link
              key={item.href}
              href={item.href}
              title={sidebarCollapsed ? item.label : undefined}
              className={`group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all relative ${
                active
                  ? "bg-brand/10 text-brand font-semibold shadow-2xs dark:bg-brand/15"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/70"
              }`}
            >
              {/* Active left highlight indicator */}
              {active && (
                <div className="absolute left-0 top-1.5 bottom-1.5 w-1 bg-brand rounded-r-full" />
              )}

              <Icon
                className={`w-5 h-5 shrink-0 transition-colors ${
                  active ? "text-brand" : "text-muted-foreground group-hover:text-foreground"
                }`}
              />

              {!sidebarCollapsed && (
                <div className="flex-1 flex items-center justify-between truncate">
                  <span className="truncate">{item.label}</span>
                  {badge && (
                    <span
                      className={`ml-2 px-1.5 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase ${
                        item.badgeVariant === "rose"
                          ? "bg-rose-500/15 text-rose-600 dark:text-rose-400"
                          : "bg-brand-muted text-brand-muted-fg"
                      }`}
                    >
                      {badge}
                    </span>
                  )}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Mill Engine Connectivity & User Pill */}
      <div className="p-3 border-t border-border space-y-2">
        {!sidebarCollapsed ? (
          <div className="p-2.5 rounded-lg bg-muted/50 border border-border/60 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <div className="flex flex-col">
                <span className="text-[11px] font-semibold text-foreground leading-tight">
                  Flask AI Engine
                </span>
                <span className="text-[9px] text-muted-foreground">Port 5001 · Connected</span>
              </div>
            </div>
            <Activity className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
          </div>
        ) : (
          <div
            className="w-full flex items-center justify-center p-2 rounded-md hover:bg-muted"
            title="Flask AI Engine · Connected"
          >
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          </div>
        )}

        {/* User Mini Card */}
        {user && (
          <Link
            href="/profile"
            className={`flex items-center gap-2.5 p-2 rounded-lg hover:bg-muted transition-colors ${
              sidebarCollapsed ? "justify-center" : ""
            }`}
            title="Manage Profile & RBAC Role"
          >
            <div
              className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                isAdmin
                  ? "bg-red-500/15 text-red-600 dark:text-red-400"
                  : "bg-brand text-brand-fg"
              }`}
            >
              {user.username.slice(0, 1).toUpperCase()}
            </div>
            {!sidebarCollapsed && (
              <div className="flex flex-col truncate flex-1">
                <span className="text-xs font-bold text-foreground truncate leading-tight">
                  {user.username}
                </span>
                <span
                  className={`text-[10px] font-bold uppercase tracking-wider ${
                    isAdmin ? "text-red-600 dark:text-red-400" : "text-brand"
                  }`}
                >
                  {user.role} {isAdmin ? "· System Root" : "· Executive"}
                </span>
              </div>
            )}
          </Link>
        )}
      </div>
    </aside>
  );
}
