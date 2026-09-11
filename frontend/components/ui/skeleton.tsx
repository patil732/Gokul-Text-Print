/**
 * components/ui/skeleton.tsx
 * ---------------------------
 * Animated loading placeholder components.
 *
 * Components:
 *   Skeleton      — generic animated block (use className for sizing)
 *   SkeletonText  — multi-line text placeholder
 *   SkeletonCard  — pre-composed card-shaped skeleton
 *
 * Usage:
 *   // Generic block
 *   <Skeleton className="h-4 w-32" />
 *
 *   // Text placeholder (3 lines)
 *   <SkeletonText lines={3} />
 *
 *   // Full card placeholder
 *   <SkeletonCard />
 *   <SkeletonCard showFooter />
 */

import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Base Skeleton block
// ---------------------------------------------------------------------------

function Skeleton({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      role="status"
      aria-label="Loading…"
      aria-busy="true"
      className={cn(
        "animate-pulse rounded-md bg-muted",
        className,
      )}
      {...props}
    />
  );
}

// ---------------------------------------------------------------------------
// SkeletonText — multi-line text block
// ---------------------------------------------------------------------------

interface SkeletonTextProps extends HTMLAttributes<HTMLDivElement> {
  /** Number of text lines to render (1–10). Default: 3 */
  lines?: number;
  /** Last line is shorter (simulates natural text). Default: true */
  shortenLast?: boolean;
}

function SkeletonText({
  lines = 3,
  shortenLast = true,
  className,
  ...props
}: SkeletonTextProps) {
  const count = Math.min(Math.max(lines, 1), 10);
  return (
    <div
      role="status"
      aria-label="Loading text…"
      aria-busy="true"
      className={cn("space-y-2", className)}
      {...props}
    >
      {Array.from({ length: count }, (_, i) => (
        <Skeleton
          key={i}
          className={cn(
            "h-3",
            // Last line gets 60% width to look more natural
            shortenLast && i === count - 1 ? "w-3/5" : "w-full",
          )}
          aria-hidden="true"
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// SkeletonCard — pre-composed card skeleton
// ---------------------------------------------------------------------------

interface SkeletonCardProps extends HTMLAttributes<HTMLDivElement> {
  /** Render a footer row. Default: false */
  showFooter?: boolean;
  /** Lines of body text to show. Default: 3 */
  bodyLines?: number;
}

function SkeletonCard({
  showFooter = false,
  bodyLines = 3,
  className,
  ...props
}: SkeletonCardProps) {
  return (
    <div
      role="status"
      aria-label="Loading card…"
      aria-busy="true"
      className={cn(
        "rounded-xl border border-[var(--surface-border)]",
        "bg-[var(--surface-1)] p-4 space-y-4",
        className,
      )}
      {...props}
    >
      {/* Header row: icon placeholder + title + subtitle */}
      <div className="flex items-start gap-3">
        <Skeleton className="h-8 w-8 rounded-lg shrink-0" aria-hidden="true" />
        <div className="flex-1 space-y-1.5">
          <Skeleton className="h-3.5 w-40" aria-hidden="true" />
          <Skeleton className="h-2.5 w-24" aria-hidden="true" />
        </div>
        {/* Action placeholder */}
        <Skeleton className="h-6 w-16 rounded-full shrink-0" aria-hidden="true" />
      </div>

      {/* Body */}
      <SkeletonText lines={bodyLines} />

      {/* Optional footer */}
      {showFooter && (
        <div className="flex items-center justify-between pt-3 border-t border-[var(--surface-border)]">
          <Skeleton className="h-3 w-24" aria-hidden="true" />
          <Skeleton className="h-7 w-20 rounded-lg" aria-hidden="true" />
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

export { Skeleton, SkeletonText, SkeletonCard };
