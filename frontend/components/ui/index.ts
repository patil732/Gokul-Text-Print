/**
 * components/ui/index.ts
 * -----------------------
 * Barrel re-export for all GTP UI components.
 *
 * Usage:
 *   import { Card, CardHeader, CardTitle, PriorityBadge, DataTable } from "@/components/ui";
 */

// Card system
export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  cardVariants,
} from "./card";
export type { CardProps } from "./card";

// Skeleton loaders
export { Skeleton, SkeletonText, SkeletonCard } from "./skeleton";

// Badge / Priority tag
export { Badge, PriorityBadge, badgeVariants } from "./badge";
export type { BadgeProps, PriorityBadgeProps } from "./badge";

// Data table
export { DataTable } from "./data-table";
export type { Column, DataTableProps, SortDirection } from "./data-table";

// Page transitions
export { PageTransition, SectionReveal, FadeIn } from "./page-transition";
export type {
  PageTransitionProps,
  SectionRevealProps,
  FadeInProps,
} from "./page-transition";

// Theme toggle
export { ThemeToggle } from "./theme-toggle";

// Shadcn Button (already present)
export { Button, buttonVariants } from "./button";
