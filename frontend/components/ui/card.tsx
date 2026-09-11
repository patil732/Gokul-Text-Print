/**
 * components/ui/card.tsx
 * -----------------------
 * Multi-slot Card component for the GTP Enterprise UI Platform.
 *
 * Slots: Card · CardHeader · CardTitle · CardDescription · CardContent · CardFooter
 *
 * Variants:
 *   default  — surface-1 background, subtle border
 *   elevated — surface-2 background, stronger shadow
 *   ghost    — transparent background, no border
 *   outline  — border only, transparent background
 *
 * Usage:
 *   <Card variant="elevated">
 *     <CardHeader icon={<TrendingUp />} action={<Badge>Live</Badge>}>
 *       <CardTitle>Total Revenue</CardTitle>
 *       <CardDescription>Last 30 days</CardDescription>
 *     </CardHeader>
 *     <CardContent>...</CardContent>
 *     <CardFooter>...</CardFooter>
 *   </Card>
 */

import { type HTMLAttributes, type ReactNode } from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Card root
// ---------------------------------------------------------------------------

const cardVariants = cva(
  // Base: full-width block, rounded, transition for theme switches
  "relative flex flex-col rounded-xl transition-colors duration-200",
  {
    variants: {
      variant: {
        default:
          "bg-[var(--surface-1)] border border-[var(--surface-border)] shadow-sm",
        elevated:
          "bg-[var(--surface-2)] border border-[var(--surface-border)] shadow-md",
        ghost:
          "bg-transparent border-none shadow-none",
        outline:
          "bg-transparent border border-[var(--surface-border)] shadow-none",
      },
      padding: {
        none:   "",
        sm:     "p-3",
        default: "p-4",
        lg:     "p-6",
      },
    },
    defaultVariants: {
      variant: "default",
      padding: "none",
    },
  },
);

export interface CardProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

function Card({ className, variant, padding, ...props }: CardProps) {
  return (
    <div
      data-slot="card"
      className={cn(cardVariants({ variant, padding }), className)}
      {...props}
    />
  );
}

// ---------------------------------------------------------------------------
// CardHeader
// ---------------------------------------------------------------------------

interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  /** Leading icon rendered before the text block */
  icon?: ReactNode;
  /** Trailing content (badge, button, menu) aligned to the right */
  action?: ReactNode;
}

function CardHeader({ className, icon, action, children, ...props }: CardHeaderProps) {
  return (
    <div
      data-slot="card-header"
      className={cn(
        "flex items-start gap-3 px-4 pt-4 pb-0",
        className,
      )}
      {...props}
    >
      {icon && (
        <div className="mt-0.5 shrink-0 text-muted-foreground [&_svg]:size-4">
          {icon}
        </div>
      )}
      <div className="min-w-0 flex-1">{children}</div>
      {action && <div className="shrink-0 ml-auto">{action}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// CardTitle
// ---------------------------------------------------------------------------

function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      data-slot="card-title"
      className={cn(
        "text-sm font-semibold leading-snug text-foreground",
        className,
      )}
      {...props}
    />
  );
}

// ---------------------------------------------------------------------------
// CardDescription
// ---------------------------------------------------------------------------

function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      data-slot="card-description"
      className={cn("mt-0.5 text-xs text-muted-foreground leading-normal", className)}
      {...props}
    />
  );
}

// ---------------------------------------------------------------------------
// CardContent
// ---------------------------------------------------------------------------

function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      data-slot="card-content"
      className={cn("px-4 py-4", className)}
      {...props}
    />
  );
}

// ---------------------------------------------------------------------------
// CardFooter
// ---------------------------------------------------------------------------

function CardFooter({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      data-slot="card-footer"
      className={cn(
        "flex items-center px-4 py-3 mt-auto",
        "border-t border-[var(--surface-border)]",
        "bg-[var(--surface-2)] rounded-b-xl",
        className,
      )}
      {...props}
    />
  );
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------

export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  cardVariants,
};
