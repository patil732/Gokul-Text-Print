"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAppShell } from "./app-shell-provider";
import { useAuth } from "@/components/providers/auth-provider";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import {
  Menu,
  Search,
  Bell,
  Check,
  User,
  Settings,
  LogOut,
  ChevronDown,
  AlertTriangle,
  Info,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";

interface NotificationItem {
  id: string;
  title: string;
  description: string;
  time: string;
  type: "critical" | "warning" | "info" | "success";
}

const SAMPLE_NOTIFICATIONS: NotificationItem[] = [
  {
    id: "notif-1",
    title: "Grey Cloth Shortage Alert",
    description: "Cotton 60s inventory is at 3,200m (minimum safety buffer is 5,000m).",
    time: "10m ago",
    type: "critical",
  },
  {
    id: "notif-2",
    title: "Multi-Agent Consensus Reached",
    description: "Production Dispatcher and Sales Agent approved Batch #942 scheduling.",
    time: "42m ago",
    type: "success",
  },
  {
    id: "notif-3",
    title: "Daily Forecast Updated",
    description: "Sales forecasting model ingested 3,493 historical orders for Q3 demand.",
    time: "2h ago",
    type: "info",
  },
];

export function AppTopbar() {
  const router = useRouter();
  const pathname = usePathname();
  const {
    toggleMobileOpen,
    setSearchOpen,
    notificationsOpen,
    setNotificationsOpen,
    toggleNotifications,
    unreadAlertsCount,
    markAlertsAsRead,
  } = useAppShell();
  const { user, logout } = useAuth();

  const [profileOpen, setProfileOpen] = React.useState(false);

  const notificationsRef = React.useRef<HTMLDivElement>(null);
  const profileRef = React.useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        notificationsRef.current &&
        !notificationsRef.current.contains(e.target as Node)
      ) {
        setNotificationsOpen(false);
      }
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [setNotificationsOpen]);

  // Derive dynamic breadcrumbs & title
  const pageMeta = React.useMemo(() => {
    switch (pathname) {
      case "/dashboard":
        return { section: "Overview", title: "Executive Dashboard" };
      case "/sales":
        return { section: "Sales Intelligence", title: "Demand Forecasting & Orders" };
      case "/inventory":
        return { section: "Inventory Intelligence", title: "Grey Cloth Stocks & Shortage Risk" };
      case "/copilot":
        return { section: "AI Copilot", title: "Autonomous Multi-Agent Assistant" };
      case "/knowledge":
        return { section: "Knowledge Base", title: "Chemical Dye SOPs & Formulations" };
      case "/reports":
        return { section: "Executive Reports", title: "Intelligence Summaries & Audit Logs" };
      case "/alerts":
        return { section: "Priority Alerts", title: "Operational Incident Queue" };
      case "/settings":
        return { section: "Settings", title: "Mill & Model Configuration" };
      case "/profile":
        return { section: "User Account", title: "My Profile & RBAC Roles" };
      default:
        return { section: "Mill Intelligence", title: "Industrial AI Platform" };
    }
  }, [pathname]);

  const handleLogout = async () => {
    setProfileOpen(false);
    await logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-40 h-16 w-full border-b border-border bg-card/85 backdrop-blur-md flex items-center justify-between px-4 sm:px-6">
      {/* Left: Mobile Drawer Trigger + Breadcrumb */}
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={toggleMobileOpen}
          className="lg:hidden p-2 rounded-md hover:bg-muted text-foreground transition-colors"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex flex-col">
          <div className="hidden sm:flex items-center gap-1.5 text-xs text-muted-foreground">
            <Link href="/dashboard" className="hover:text-foreground transition-colors">
              Mill Hub
            </Link>
            <span>/</span>
            <span className="font-medium text-foreground">{pageMeta.section}</span>
          </div>
          <h1 className="text-base sm:text-lg font-bold text-foreground leading-tight truncate">
            {pageMeta.title}
          </h1>
        </div>
      </div>

      {/* Right: Search + Notifications + Theme + Profile */}
      <div className="flex items-center gap-2 sm:gap-2.5">
        {/* Global Search Button */}
        <button
          type="button"
          onClick={() => setSearchOpen(true)}
          className="flex items-center gap-2 px-2.5 py-1.5 sm:px-3 text-xs sm:text-sm font-medium text-muted-foreground bg-muted/60 hover:bg-muted border border-border/80 rounded-lg shadow-2xs transition-colors cursor-pointer"
          title="Search anything (Ctrl+K)"
        >
          <Search className="w-4 h-4 shrink-0" />
          <span className="hidden md:inline-block">Search mill intelligence...</span>
          <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono font-medium rounded bg-background border border-border text-muted-foreground">
            ⌘K
          </kbd>
        </button>

        {/* Notifications Popover */}
        <div className="relative" ref={notificationsRef}>
          <button
            type="button"
            onClick={toggleNotifications}
            className="relative p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            title="Notifications & Alerts"
            aria-label="Notifications"
          >
            <Bell className="w-5 h-5" />
            {unreadAlertsCount > 0 && (
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-card animate-pulse" />
            )}
          </button>

          {notificationsOpen && (
            <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-xl bg-card border border-border shadow-xl p-3 space-y-3 animate-in fade-in zoom-in-95 duration-150 z-50">
              <div className="flex items-center justify-between border-b border-border/70 pb-2.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-foreground">Operational Alerts</span>
                  {unreadAlertsCount > 0 && (
                    <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-rose-500/15 text-rose-600 dark:text-rose-400">
                      {unreadAlertsCount} new
                    </span>
                  )}
                </div>
                {unreadAlertsCount > 0 && (
                  <button
                    type="button"
                    onClick={markAlertsAsRead}
                    className="text-[11px] text-brand hover:underline font-medium flex items-center gap-1"
                  >
                    <Check className="w-3 h-3" />
                    <span>Mark all read</span>
                  </button>
                )}
              </div>

              <div className="space-y-2 max-h-72 overflow-y-auto">
                {SAMPLE_NOTIFICATIONS.map((notif) => (
                  <div
                    key={notif.id}
                    className="p-2.5 rounded-lg bg-muted/40 hover:bg-muted/70 transition-colors border border-border/40 text-left space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        {notif.type === "critical" && (
                          <AlertTriangle className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                        )}
                        {notif.type === "success" && (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                        )}
                        {notif.type === "info" && (
                          <Info className="w-3.5 h-3.5 text-sky-500 shrink-0" />
                        )}
                        <span className="text-xs font-bold text-foreground leading-tight">
                          {notif.title}
                        </span>
                      </div>
                      <span className="text-[10px] text-muted-foreground">{notif.time}</span>
                    </div>
                    <p className="text-xs text-muted-foreground leading-snug">
                      {notif.description}
                    </p>
                  </div>
                ))}
              </div>

              <div className="pt-2 border-t border-border/70 flex items-center justify-between">
                <Link
                  href="/alerts"
                  onClick={() => setNotificationsOpen(false)}
                  className="text-xs font-semibold text-brand hover:underline flex items-center gap-1"
                >
                  <span>View full alert queue</span>
                  <ExternalLink className="w-3 h-3" />
                </Link>
                <span className="text-[10px] text-muted-foreground">Updated real-time</span>
              </div>
            </div>
          )}
        </div>

        {/* Theme Toggle */}
        <ThemeToggle />

        {/* Profile Dropdown */}
        <div className="relative" ref={profileRef}>
          <button
            type="button"
            onClick={() => setProfileOpen(!profileOpen)}
            className="flex items-center gap-2 p-1 pl-1.5 pr-2 rounded-full border border-border hover:bg-muted transition-colors cursor-pointer"
            aria-label="User profile menu"
          >
            <div className="w-7 h-7 rounded-full bg-brand text-brand-fg flex items-center justify-center text-xs font-bold shrink-0 shadow-2xs">
              {user ? user.username.slice(0, 1).toUpperCase() : "U"}
            </div>
            {user && (
              <span className="hidden md:inline-block text-xs font-semibold text-foreground max-w-[100px] truncate">
                {user.username}
              </span>
            )}
            <ChevronDown className="w-3.5 h-3.5 text-muted-foreground" />
          </button>

          {profileOpen && (
            <div className="absolute right-0 mt-2 w-64 rounded-xl bg-card border border-border shadow-xl p-2.5 space-y-2 animate-in fade-in zoom-in-95 duration-150 z-50">
              {user ? (
                <div className="p-2 rounded-lg bg-muted/50 border border-border/60">
                  <div className="text-xs font-bold text-foreground truncate">{user.username}</div>
                  <div className="text-[11px] text-muted-foreground truncate">{user.email}</div>
                  <div className="mt-1.5 flex items-center justify-between">
                    <span className="text-[10px] text-muted-foreground">RBAC Role</span>
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-brand-muted text-brand-muted-fg uppercase tracking-wider">
                      {user.role}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="p-2 text-xs text-muted-foreground">Demo Session</div>
              )}

              <div className="space-y-1 pt-1">
                <Link
                  href="/profile"
                  onClick={() => setProfileOpen(false)}
                  className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium text-foreground hover:bg-muted transition-colors"
                >
                  <User className="w-4 h-4 text-muted-foreground" />
                  <span>My Profile & Capabilities</span>
                </Link>
                <Link
                  href="/settings"
                  onClick={() => setProfileOpen(false)}
                  className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium text-foreground hover:bg-muted transition-colors"
                >
                  <Settings className="w-4 h-4 text-muted-foreground" />
                  <span>Mill & Agent Settings</span>
                </Link>
              </div>

              <div className="pt-2 border-t border-border/70">
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-500/10 transition-colors text-left cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
