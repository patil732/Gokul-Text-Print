"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAppShell } from "./app-shell-provider";
import { useAuth } from "@/components/providers/auth-provider";
import { ADMIN_SIDEBAR_ITEMS, CEO_SIDEBAR_ITEMS } from "./app-sidebar";
import {
  Layers,
  X,
  Activity,
  LogOut,
  User,
  ShieldAlert,
} from "lucide-react";

export function AppMobileDrawer() {
  const router = useRouter();
  const pathname = usePathname();
  const { mobileOpen, setMobileOpen, unreadAlertsCount } = useAppShell();
  const { user, logout } = useAuth();

  if (!mobileOpen) return null;

  const isAdmin = user?.role?.toUpperCase() === "ADMIN";
  const navItems = isAdmin ? ADMIN_SIDEBAR_ITEMS : CEO_SIDEBAR_ITEMS;
  const brandHref = isAdmin ? "/admin" : "/dashboard";

  const isItemActive = (href: string) => {
    if (href === "/admin") return pathname === "/admin";
    if (href === "/dashboard") return pathname === "/dashboard";
    return pathname.startsWith(href);
  };

  const handleLogout = async () => {
    setMobileOpen(false);
    await logout();
    router.push("/login");
  };

  return (
    <div
      className="fixed inset-0 z-50 lg:hidden bg-black/60 backdrop-blur-xs flex animate-in fade-in duration-200"
      onClick={() => setMobileOpen(false)}
    >
      <div
        className="w-72 max-w-[85vw] bg-card border-r border-border h-full flex flex-col shadow-2xl animate-in slide-in-from-left duration-250"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drawer Header */}
        <div className="h-16 border-b border-border flex items-center justify-between px-4">
          <Link
            href={brandHref}
            onClick={() => setMobileOpen(false)}
            className="flex items-center gap-2.5 text-foreground"
          >
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center shadow-xs ${
                isAdmin
                  ? "bg-red-500/15 text-red-600 dark:text-red-400"
                  : "bg-brand text-brand-fg"
              }`}
            >
              {isAdmin ? <ShieldAlert className="w-4 h-4" /> : <Layers className="w-4 h-4" />}
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-sm tracking-tight leading-tight">
                Gokul Text Print
              </span>
              <span className="text-[10px] text-muted-foreground font-medium uppercase">
                {isAdmin ? "Admin Center" : "AI Mill Platform"}
              </span>
            </div>
          </Link>

          <button
            type="button"
            onClick={() => setMobileOpen(false)}
            className="p-1.5 rounded-md hover:bg-muted text-muted-foreground hover:text-foreground"
            aria-label="Close navigation drawer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
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
                onClick={() => setMobileOpen(false)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  active
                    ? "bg-brand/10 text-brand font-semibold dark:bg-brand/15"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
              >
                <Icon className={`w-5 h-5 shrink-0 ${active ? "text-brand" : "text-muted-foreground"}`} />
                <span className="flex-1 truncate">{item.label}</span>
                {badge && (
                  <span
                    className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${
                      item.badgeVariant === "rose"
                        ? "bg-rose-500/15 text-rose-600 dark:text-rose-400"
                        : "bg-brand-muted text-brand-muted-fg"
                    }`}
                  >
                    {badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Footer info & Logout */}
        <div className="p-3 border-t border-border space-y-2">
          {user && (
            <Link
              href="/profile"
              onClick={() => setMobileOpen(false)}
              className="flex items-center gap-2.5 p-2 rounded-lg bg-muted/40 hover:bg-muted transition-colors"
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
              <div className="flex flex-col truncate flex-1">
                <span className="text-xs font-bold text-foreground truncate">
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
            </Link>
          )}

          <div className="p-2.5 rounded-lg bg-muted/50 border border-border/60 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <div className="flex flex-col">
                <span className="text-xs font-semibold text-foreground leading-tight">
                  Flask AI Engine
                </span>
                <span className="text-[10px] text-muted-foreground">Port 5001 Connected</span>
              </div>
            </div>
            <Activity className="w-4 h-4 text-emerald-500 shrink-0" />
          </div>

          {user && (
            <div className="space-y-2">
              <div className="flex items-center gap-2.5 p-2 rounded-lg bg-card border border-border">
                <div className="w-8 h-8 rounded-full bg-brand text-brand-fg flex items-center justify-center text-xs font-bold shrink-0">
                  {user.username.slice(0, 1).toUpperCase()}
                </div>
                <div className="flex flex-col truncate flex-1">
                  <span className="text-xs font-bold text-foreground truncate">
                    {user.username}
                  </span>
                  <span className="text-[10px] text-brand font-semibold uppercase">
                    {user.role}
                  </span>
                </div>
              </div>

              <div className="flex gap-2">
                <Link
                  href="/profile"
                  onClick={() => setMobileOpen(false)}
                  className="flex-1 py-1.5 px-2 text-xs font-medium text-center rounded-md border border-border hover:bg-muted text-foreground flex items-center justify-center gap-1.5"
                >
                  <User className="w-3.5 h-3.5 text-muted-foreground" />
                  <span>Profile</span>
                </Link>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="py-1.5 px-3 text-xs font-medium rounded-md bg-rose-500/10 hover:bg-rose-500/20 text-rose-600 dark:text-rose-400 flex items-center justify-center gap-1 cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
