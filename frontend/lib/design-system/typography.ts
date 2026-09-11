/**
 * lib/design-system/typography.ts
 * --------------------------------
 * Named typography scale constants.
 *
 * Instead of sprinkling raw Tailwind classes like `text-sm font-semibold`
 * everywhere, import from here so all text styles are defined once.
 *
 * Usage:
 *   import { type } from "@/lib/design-system";
 *   <h1 className={type.pageTitle}>...</h1>
 */

// ---------------------------------------------------------------------------
// Raw scale — mirrors --text-* CSS vars (values in rem)
// ---------------------------------------------------------------------------

export const fontSize = {
  "2xs":  "0.625rem",  // 10px
  xs:     "0.75rem",   // 12px
  sm:     "0.875rem",  // 14px
  base:   "1rem",      // 16px
  lg:     "1.125rem",  // 18px
  xl:     "1.25rem",   // 20px
  "2xl":  "1.5rem",    // 24px
  "3xl":  "1.875rem",  // 30px
  "4xl":  "2.25rem",   // 36px
} as const;

// ---------------------------------------------------------------------------
// Semantic Tailwind class bundles
// Use these on elements directly: <h1 className={type.pageTitle}>
// ---------------------------------------------------------------------------

export const type = {
  // Page-level headings
  pageTitle:       "text-2xl font-bold tracking-tight text-foreground",
  sectionTitle:    "text-lg font-semibold tracking-tight text-foreground",
  cardTitle:       "text-sm font-semibold text-foreground",

  // Body / supporting text
  body:            "text-sm text-foreground",
  bodyMuted:       "text-sm text-muted-foreground",
  caption:         "text-xs text-muted-foreground",
  label:           "text-xs font-medium text-muted-foreground uppercase tracking-wider",

  // Numeric / data display
  kpiValue:        "text-3xl font-bold tracking-tight tabular-nums text-foreground",
  kpiValueSm:      "text-xl font-semibold tabular-nums text-foreground",
  metricLabel:     "text-xs font-medium text-muted-foreground",

  // Code / mono
  code:            "font-mono text-xs text-foreground bg-muted px-1.5 py-0.5 rounded",
  mono:            "font-mono text-sm text-foreground",

  // Table
  tableHeader:     "text-xs font-semibold text-muted-foreground uppercase tracking-wider",
  tableCell:       "text-sm text-foreground",
  tableCellMuted:  "text-sm text-muted-foreground",
} as const;

export type TypeScale = keyof typeof type;
