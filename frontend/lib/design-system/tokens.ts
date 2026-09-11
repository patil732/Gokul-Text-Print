/**
 * lib/design-system/tokens.ts
 * ----------------------------
 * TypeScript mirror of the CSS custom properties in globals.css.
 *
 * Use these constants anywhere you need to reference design tokens in
 * JavaScript/TypeScript (e.g. Recharts color arrays, Framer Motion
 * animation colours, dynamic class generation).
 *
 * IMPORTANT: these are CSS var() references, not raw colour values.
 * They resolve at runtime using the current theme (light / dark).
 */

// ---------------------------------------------------------------------------
// Surface tokens
// ---------------------------------------------------------------------------

export const surfaces = {
  0: "var(--surface-0)",
  1: "var(--surface-1)",
  2: "var(--surface-2)",
  border: "var(--surface-border)",
} as const;

// ---------------------------------------------------------------------------
// Brand tokens
// ---------------------------------------------------------------------------

export const brand = {
  DEFAULT: "var(--brand)",
  fg: "var(--brand-fg)",
  muted: "var(--brand-muted)",
  mutedFg: "var(--brand-muted-fg)",
} as const;

// ---------------------------------------------------------------------------
// Priority tokens
// ---------------------------------------------------------------------------

export type Priority = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "SUCCESS";

export const priorityTokens = {
  CRITICAL: {
    bg:     "var(--priority-critical)",
    fg:     "var(--priority-critical-fg)",
    border: "var(--priority-critical-border)",
  },
  HIGH: {
    bg:     "var(--priority-high)",
    fg:     "var(--priority-high-fg)",
    border: "var(--priority-high-border)",
  },
  MEDIUM: {
    bg:     "var(--priority-medium)",
    fg:     "var(--priority-medium-fg)",
    border: "var(--priority-medium-border)",
  },
  LOW: {
    bg:     "var(--priority-low)",
    fg:     "var(--priority-low-fg)",
    border: "var(--priority-low-border)",
  },
  SUCCESS: {
    bg:     "var(--priority-success)",
    fg:     "var(--priority-success-fg)",
    border: "var(--priority-success-border)",
  },
} as const satisfies Record<Priority, { bg: string; fg: string; border: string }>;

// ---------------------------------------------------------------------------
// Chart colour palette (mirrors --chart-1 through --chart-5)
// Use for Recharts <Line>, <Bar>, <Pie> stroke/fill props.
// ---------------------------------------------------------------------------

export const chartColors = [
  "var(--chart-1)", // indigo
  "var(--chart-2)", // emerald
  "var(--chart-3)", // amber
  "var(--chart-4)", // rose
  "var(--chart-5)", // violet
] as const;

// Semantic chart-color aliases
export const chartPalette = {
  primary:   "var(--chart-1)",
  success:   "var(--chart-2)",
  warning:   "var(--chart-3)",
  danger:    "var(--chart-4)",
  secondary: "var(--chart-5)",
} as const;

// ---------------------------------------------------------------------------
// Semantic colour aliases
// ---------------------------------------------------------------------------

export const semanticColors = {
  background:   "var(--background)",
  foreground:   "var(--foreground)",
  muted:        "var(--muted)",
  mutedFg:      "var(--muted-foreground)",
  border:       "var(--border)",
  ring:         "var(--ring)",
  destructive:  "var(--destructive)",
} as const;

// ---------------------------------------------------------------------------
// Radius scale
// ---------------------------------------------------------------------------

export const radius = {
  sm:  "var(--radius-sm)",
  md:  "var(--radius-md)",
  lg:  "var(--radius-lg)",
  xl:  "var(--radius-xl)",
  "2xl": "var(--radius-2xl)",
} as const;
