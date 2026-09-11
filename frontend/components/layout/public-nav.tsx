"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/providers/auth-provider";
import {
  Layers,
  Menu,
  X,
  ArrowRight,
  Sparkles,
  Cpu,
  BarChart3,
  BookOpen,
  Info,
  DollarSign,
  Mail,
  LogIn,
  User,
  LogOut,
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Home", href: "/", icon: Sparkles },
  { label: "Features", href: "/features", icon: BarChart3 },
  { label: "Solutions", href: "/technology", icon: Cpu },
  { label: "How It Works", href: "/#how-it-works", icon: Layers },
  { label: "Pricing", href: "/pricing", icon: DollarSign },
  { label: "About", href: "/about", icon: Info },
  { label: "Contact", href: "/contact", icon: Mail },
];

export function PublicNav() {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [scrolled, setScrolled] = React.useState(false);

  React.useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close mobile drawer on route change
  React.useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    if (href.startsWith("/#")) return false;
    return pathname.startsWith(href);
  };

  return (
    <header
      className={`sticky top-0 z-50 w-full transition-all duration-200 ${
        scrolled
          ? "bg-background/90 backdrop-blur-md border-b border-border shadow-xs"
          : "bg-background/70 backdrop-blur-sm border-b border-border/40"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <Link
          href="/"
          className="flex items-center gap-2.5 font-bold tracking-tight text-foreground hover:opacity-90 transition-opacity"
        >
          <div className="w-9 h-9 rounded-lg bg-brand text-brand-fg flex items-center justify-center shadow-xs">
            <Layers className="w-5 h-5" />
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="text-base font-bold text-foreground">Gokul Text Print</span>
              <span className="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-brand-muted text-brand-muted-fg uppercase tracking-wider">
                AI Enterprise
              </span>
            </div>
            <span className="text-[10px] text-muted-foreground hidden sm:block">
              Industrial Textile Intelligence
            </span>
          </div>
        </Link>

        {/* Desktop Nav Items */}
        <nav className="hidden lg:flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.label}
                href={item.href}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  active
                    ? "text-brand font-semibold bg-brand-muted/50"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Right Actions */}
        <div className="flex items-center gap-2">
          <ThemeToggle />

          {isAuthenticated && user ? (
            <div className="hidden sm:flex items-center gap-2">
              <Link
                href="/profile"
                className="inline-flex items-center gap-2 px-2.5 py-1 text-xs font-medium text-foreground bg-card hover:bg-muted border border-border rounded-full shadow-2xs transition-colors"
                title="View Profile & RBAC Role"
              >
                <div className="w-5 h-5 rounded-full bg-brand text-brand-fg flex items-center justify-center text-[10px] font-bold">
                  {user.username.slice(0, 1).toUpperCase()}
                </div>
                <span className="font-semibold max-w-[90px] truncate">{user.username}</span>
                <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-brand-muted text-brand-muted-fg uppercase tracking-wider">
                  {user.role}
                </span>
              </Link>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => logout()}
                className="h-8 px-2 text-xs text-muted-foreground hover:text-rose-500 gap-1"
                title="Sign Out"
              >
                <LogOut className="w-3.5 h-3.5" />
              </Button>
            </div>
          ) : (
            <div className="hidden sm:flex items-center gap-2">
              <Link href="/login">
                <Button variant="ghost" size="sm" className="h-9 px-3 text-sm font-medium gap-1.5">
                  <LogIn className="w-4 h-4" />
                  <span>Sign In</span>
                </Button>
              </Link>
              <Link href="/register">
                <Button size="sm" className="h-9 px-3.5 text-sm font-semibold gap-1.5 shadow-xs">
                  <span>Register</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </Link>
            </div>
          )}

          <Link
            href={user?.role?.toUpperCase() === "ADMIN" ? "/admin" : "/dashboard"}
            className="hidden md:inline-flex"
          >
            <Button
              variant="outline"
              size="sm"
              className="h-9 px-3 text-xs font-semibold text-foreground hover:bg-muted gap-1.5 border-border"
            >
              <span>{user?.role?.toUpperCase() === "ADMIN" ? "Admin Center" : "Executive Dashboard"}</span>
            </Button>
          </Link>

          {/* Mobile Menu Button */}
          <button
            type="button"
            onClick={() => setMobileOpen(!mobileOpen)}
            className="lg:hidden inline-flex items-center justify-center p-2 rounded-md text-foreground hover:bg-muted transition-colors"
            aria-label="Toggle navigation menu"
            aria-expanded={mobileOpen}
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Drawer */}
      {mobileOpen && (
        <div className="lg:hidden border-b border-border bg-background px-4 pt-3 pb-6 space-y-3 animate-in slide-in-from-top-2 duration-200">
          <div className="grid grid-cols-1 gap-1">
            {NAV_ITEMS.map((item) => {
              const active = isActive(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    active
                      ? "text-brand font-semibold bg-brand-muted/60"
                      : "text-foreground hover:bg-muted"
                  }`}
                >
                  <Icon className="w-4 h-4 text-muted-foreground" />
                  <span>{item.label}</span>
                </Link>
              );
            })}

            {isAuthenticated && (
              <Link
                href="/profile"
                className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  pathname === "/profile"
                    ? "text-brand font-semibold bg-brand-muted/60"
                    : "text-foreground hover:bg-muted"
                }`}
              >
                <User className="w-4 h-4 text-brand" />
                <span>My Profile & RBAC Role</span>
              </Link>
            )}
          </div>

          <div className="pt-3 border-t border-border flex flex-col gap-2">
            {isAuthenticated && user ? (
              <div className="space-y-2">
                <div className="p-2.5 rounded-lg bg-card border border-border flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full bg-brand text-brand-fg flex items-center justify-center text-xs font-bold">
                      {user.username.slice(0, 1).toUpperCase()}
                    </div>
                    <div>
                      <div className="text-xs font-bold text-foreground">{user.username}</div>
                      <div className="text-[10px] text-muted-foreground">{user.email}</div>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-brand-muted text-brand-muted-fg uppercase">
                    {user.role}
                  </span>
                </div>

                <div className="flex gap-2">
                  <Link href="/profile" className="flex-1">
                    <Button variant="outline" size="sm" className="w-full text-xs">
                      View Profile
                    </Button>
                  </Link>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => logout()}
                    className="text-xs text-rose-500 hover:text-rose-600 gap-1"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Sign Out</span>
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <Link href="/register" className="w-full block">
                  <Button className="w-full flex items-center justify-center gap-2 font-semibold">
                    <span>Register Account</span>
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </Link>
                <Link href="/login" className="w-full block">
                  <Button
                    variant="outline"
                    className="w-full flex items-center justify-center gap-2"
                  >
                    <LogIn className="w-4 h-4" />
                    <span>Sign In (Portal)</span>
                  </Button>
                </Link>
              </div>
            )}

            <Link
              href={user?.role?.toUpperCase() === "ADMIN" ? "/admin" : "/dashboard"}
              className="w-full block"
            >
              <Button
                variant="ghost"
                className="w-full flex items-center justify-center gap-2 text-foreground font-semibold"
              >
                <span>{user?.role?.toUpperCase() === "ADMIN" ? "Launch Admin Operations" : "Launch Executive Dashboard"}</span>
              </Button>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
