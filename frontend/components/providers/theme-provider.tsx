"use client";

/*
 * components/providers/theme-provider.tsx
 * -----------------------------------------
 * Client-side wrapper around next-themes ThemeProvider.
 * Must be "use client" -- next-themes injects a blocking script for
 * FOUC prevention that React 19 RSC renderer does not allow.
 *
 * Configuration:
 *   attribute="class"         adds/removes .dark on <html> (matches Shadcn)
 *   defaultTheme="system"     respects OS preference out of the box
 *   enableSystem              keeps OS sync active
 *   storageKey="gtp-ui-theme" localStorage key (namespaced to this app)
 *   disableTransitionOnChange prevents flash when switching themes
 */

import { ThemeProvider as NextThemesProvider } from "next-themes";
import type { ThemeProviderProps } from "next-themes";

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      storageKey="gtp-ui-theme"
      disableTransitionOnChange
      {...props}
    >
      {children}
    </NextThemesProvider>
  );
}
