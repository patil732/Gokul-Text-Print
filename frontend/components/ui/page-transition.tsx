"use client";

/*
 * components/ui/page-transition.tsx
 * -----------------------------------
 * Framer Motion page and section animation wrappers.
 *
 * Components:
 *   PageTransition - wraps an entire page/route; fades + slides up on mount
 *   SectionReveal  - animates a section when it enters the viewport (once)
 *   FadeIn         - simple opacity fade for overlays / modals
 *
 * Design rules:
 *   - Duration: 350ms enter, 200ms exit (fast but not jarring)
 *   - Easing: cubic-bezier(0.4, 0, 0.2, 1) -- Material Design "standard" curve
 *   - Y offset: 10px enter (subtle, not dramatic)
 *   - viewport.once: true -- sections do NOT re-animate on scroll back up
 *   - Delay prop for staggering multiple sections: 0, 0.1, 0.2 ...
 *
 * Usage:
 *   // Wrap full page content
 *   <PageTransition>
 *     <h1>Dashboard</h1>
 *   </PageTransition>
 *
 *   // Stagger individual sections
 *   <SectionReveal delay={0}>   <KpiRow />       </SectionReveal>
 *   <SectionReveal delay={0.1}> <AlertsTable />  </SectionReveal>
 *   <SectionReveal delay={0.2}> <Charts />       </SectionReveal>
 */

import { type ReactNode, type HTMLAttributes } from "react";
import { motion, type Variants } from "framer-motion";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Shared animation config
// ---------------------------------------------------------------------------

// Framer Motion v13 requires a typed 4-element tuple for cubic-bezier easing.
type BezierTuple = [number, number, number, number];
const EASE: BezierTuple = [0.4, 0, 0.2, 1];

const pageVariants: Variants = {
  hidden:  { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: EASE } },
  exit:    { opacity: 0, y: -6, transition: { duration: 0.2, ease: EASE } },
};

const sectionVariants: Variants = {
  hidden:  { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: EASE } },
};

// ---------------------------------------------------------------------------
// PageTransition
// ---------------------------------------------------------------------------

export interface PageTransitionProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  /** Framer Motion layout ID for shared-element transitions (optional) */
  layoutId?: string;
}

export function PageTransition({
  children,
  className,
  layoutId,
  ...rest
}: PageTransitionProps) {
  return (
    <motion.div
      layoutId={layoutId}
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
      className={cn("w-full", className)}
      {...(rest as Record<string, unknown>)}
    >
      {children}
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// SectionReveal
// ---------------------------------------------------------------------------

export interface SectionRevealProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  /**
   * Delay in seconds before this section starts animating.
   * Use to stagger: 0, 0.1, 0.2 ...
   */
  delay?: number;
  /**
   * Fraction of the element that must be in view before triggering.
   * Range: 0-1. Default: 0.1 (10% visible)
   */
  amount?: number;
}

export function SectionReveal({
  children,
  className,
  delay = 0,
  amount = 0.1,
  ...rest
}: SectionRevealProps) {
  return (
    <motion.div
      variants={sectionVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount }}
      transition={{ delay, duration: 0.4, ease: EASE }}
      className={cn(className)}
      {...(rest as Record<string, unknown>)}
    >
      {children}
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// FadeIn -- simple opacity fade (no y offset)
// Use for overlays, modals, tooltips
// ---------------------------------------------------------------------------

export interface FadeInProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode;
  delay?: number;
  duration?: number;
}

export function FadeIn({
  children,
  className,
  delay = 0,
  duration = 0.25,
  ...rest
}: FadeInProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ delay, duration, ease: EASE }}
      className={cn(className)}
      {...(rest as Record<string, unknown>)}
    >
      {children}
    </motion.div>
  );
}
