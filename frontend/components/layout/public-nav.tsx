"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Button } from "@/components/ui/button";
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
} from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Home", href: "/", icon: Sparkles },
  { label: "Features", href: "/features", icon: BarChart3 },
  { label: "Technology", href: "/technology", icon: Cpu },
  { label: "Architecture", href: "/#architecture", icon: Layers },
  { label: "Pricing", href: "/pricing", icon: DollarSign },
  { label: "About", href: "/about", icon: Info },
  { label: "Contact", href: "/contact", icon: Mail },
];

export function PublicNav() {
  const pathname = usePathname();
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
        <div className="flex items-center gap-2.5">
          <ThemeToggle />

          <Link
            href="/login"
            className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors"
          >
            <LogIn className="w-4 h-4" />
            <span>Sign In</span>
          </Link>

          <Link href="/dashboard">
            <Button size="sm" className="hidden sm:inline-flex items-center gap-1.5 font-medium">
              <span>Launch Demo</span>
              <ArrowRight className="w-4 h-4" />
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
          </div>

          <div className="pt-3 border-t border-border flex flex-col gap-2">
            <Link
              href="/login"
              className="flex items-center justify-center gap-2 w-full py-2 text-sm font-medium rounded-md border border-border hover:bg-muted text-foreground"
            >
              <LogIn className="w-4 h-4" />
              <span>Sign In (Demo Portal)</span>
            </Link>

            <Link href="/dashboard" className="w-full">
              <Button className="w-full flex items-center justify-center gap-2">
                <span>Launch Executive Demo</span>
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
