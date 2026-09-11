/**
 * components/ui/badge.tsx
 * ------------------------
 * Badge and PriorityBadge components for the GTP Enterprise UI Platform.
 *
 * Standard variants: default · secondary · outline · destructive · brand
 * Priority variants: critical · high · medium · low · success
 *
 * PriorityBadge is a convenience wrapper that accepts a priority string
 * directly from the Flask API response (`"CRITICAL" | "HIGH" | "MEDIUM" | "LOW"`)
 * and maps it to the correct variant automatically.
 *
 * Usage:
 *   <Badge variant="brand">Live</Badge>
 *   <Badge variant="high">HIGH</Badge>
 *
 *   // From Flask alert: { priority: "CRITICAL" }
 *   <PriorityBadge priority="CRITICAL" />
 *   <PriorityBadge priority="HIGH" label="Revenue Drop" />
 */

import { type HTMLAttributes } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import type { Priority } from "@/lib/design-system/tokens";

// ---------------------------------------------------------------------------
// Badge CVA
// ---------------------------------------------------------------------------

const badgeVariants = cva(
  // Base: inline pill
  [
    "inline-flex items-center gap-1 rounded-full px-2 py-0.5",
    "text-xs font-semibold leading-none whitespace-nowrap select-none",
    "border transition-colors duration-150",
    "ring-0 outline-none",
  ].join(" "),
  {
    variants: {
      variant: {
        // ── Standard variants ──────────────────────────────────────────────
        default:
          "bg-foreground text-background border-transparent",
        secondary:
          "bg-secondary text-secondary-foreground border-transparent",
        outline:
          "bg-transparent text-foreground border-border",
        destructive:
          "bg-destructive/15 text-destructive border-destructive/20",
        brand:
          "bg-[var(--brand-muted)] text-[var(--brand-muted-fg)] border-[var(--brand)]/20",

        // ── Priority variants (maps to --priority-* tokens) ────────────────
        critical:
          "bg-[var(--priority-critical)] text-[var(--priority-critical-fg)] border-[var(--priority-critical-border)]",
        high:
          "bg-[var(--priority-high)] text-[var(--priority-high-fg)] border-[var(--priority-high-border)]",
        medium:
          "bg-[var(--priority-medium)] text-[var(--priority-medium-fg)] border-[var(--priority-medium-border)]",
        low:
          "bg-[var(--priority-low)] text-[var(--priority-low-fg)] border-[var(--priority-low-border)]",
        success:
          "bg-[var(--priority-success)] text-[var(--priority-success-fg)] border-[var(--priority-success-border)]",
      },
      size: {
        sm:      "px-1.5 py-px text-[10px]",
        default: "px-2 py-0.5 text-xs",
        lg:      "px-2.5 py-1 text-sm",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, size, ...props }: BadgeProps) {
  return (
    <span
      data-slot="badge"
      className={cn(badgeVariants({ variant, size }), className)}
      {...props}
    />
  );
}

// ---------------------------------------------------------------------------
// Priority dot icons (●)
// ---------------------------------------------------------------------------

const priorityDotColor: Record<Priority, string> = {
  CRITICAL: "text-[var(--priority-critical-fg)]",
  HIGH:     "text-[var(--priority-high-fg)]",
  MEDIUM:   "text-[var(--priority-medium-fg)]",
  LOW:      "text-[var(--priority-low-fg)]",
  SUCCESS:  "text-[var(--priority-success-fg)]",
};

const priorityVariant: Record<Priority, VariantProps<typeof badgeVariants>["variant"]> = {
  CRITICAL: "critical",
  HIGH:     "high",
  MEDIUM:   "medium",
  LOW:      "low",
  SUCCESS:  "success",
};

const priorityLabels: Record<Priority, string> = {
  CRITICAL: "Critical",
  HIGH:     "High",
  MEDIUM:   "Medium",
  LOW:      "Low",
  SUCCESS:  "Success",
};

// ---------------------------------------------------------------------------
// PriorityBadge convenience wrapper
// ---------------------------------------------------------------------------

export interface PriorityBadgeProps extends Omit<BadgeProps, "variant"> {
  /**
   * Priority string from the Flask API.
   * Accepts either uppercase ("CRITICAL") or lowercase ("critical").
   */
  priority: Priority | Lowercase<Priority>;
  /** Override the displayed label. Defaults to title-cased priority. */
  label?: string;
  /** Show a coloured dot before the label. Default: true */
  showDot?: boolean;
}

function PriorityBadge({
  priority,
  label,
  showDot = true,
  className,
  ...props
}: PriorityBadgeProps) {
  const normalized = priority.toUpperCase() as Priority;
  const variant = priorityVariant[normalized] ?? "outline";
  const displayLabel = label ?? priorityLabels[normalized] ?? normalized;

  return (
    <Badge
      variant={variant}
      className={cn("gap-1", className)}
      aria-label={`Priority: ${displayLabel}`}
      {...props}
    >
      {showDot && (
        <span
          aria-hidden="true"
          className={cn("inline-block size-1.5 rounded-full bg-current", priorityDotColor[normalized])}
        />
      )}
      {displayLabel}
    </Badge>
  );
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

export { Badge, PriorityBadge, badgeVariants };
export type { Priority };
