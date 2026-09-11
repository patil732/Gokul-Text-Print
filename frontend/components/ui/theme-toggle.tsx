"use client";

/**
 * components/ui/theme-toggle.tsx
 * --------------------------------
 * Icon-only button that cycles: system → light → dark → system.
 * Persists to localStorage via next-themes (key: gtp-ui-theme).
 *
 * Usage:
 *   <ThemeToggle />                          — icon button
 *   <ThemeToggle showLabel />                — icon + text label
 *   <ThemeToggle className="ml-auto" />      — with extra classes
 */

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Monitor, Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";

const CYCLE: Array<"system" | "light" | "dark"> = ["system", "light", "dark"];

const icons = {
  system: Monitor,
  light:  Sun,
  dark:   Moon,
} as const;

const labels = {
  system: "System theme",
  light:  "Light mode",
  dark:   "Dark mode",
} as const;

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
}

export function ThemeToggle({ className, showLabel = false }: ThemeToggleProps) {
  const { theme, setTheme } = useTheme();
  // Avoid hydration mismatch: render neutral icon on server
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const current = (mounted ? (theme as "system" | "light" | "dark") : "system") ?? "system";
  const Icon = icons[current];
  const label = labels[current];

  function cycleTheme() {
    const idx = CYCLE.indexOf(current);
    const next = CYCLE[(idx + 1) % CYCLE.length];
    setTheme(next);
  }

  return (
    <button
      id="theme-toggle"
      type="button"
      aria-label={`Toggle theme — currently ${label}`}
      title={label}
      onClick={cycleTheme}
      className={cn(
        // Base: icon-button sizing
        "inline-flex items-center justify-center gap-1.5 rounded-lg",
        "h-8 w-8 shrink-0 text-sm font-medium",
        // Colours: muted text, hover to foreground
        "text-muted-foreground hover:text-foreground",
        "hover:bg-muted",
        // Transition
        "transition-colors duration-150",
        // Focus ring
        "outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
        // Icon sizing
        "[&_svg]:size-4 [&_svg]:shrink-0",
        // Label variant
        showLabel && "w-auto px-2.5",
        className,
      )}
    >
      {mounted ? (
        <Icon aria-hidden="true" />
      ) : (
        /* Prevent layout shift during SSR */
        <span className="size-4" />
      )}
      {showLabel && <span className="text-xs">{label}</span>}
    </button>
  );
}
