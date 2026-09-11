"use client";

import * as React from "react";
import { usePathname } from "next/navigation";

interface AppShellContextType {
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  toggleSidebar: () => void;
  mobileOpen: boolean;
  setMobileOpen: (open: boolean) => void;
  toggleMobileOpen: () => void;
  searchOpen: boolean;
  setSearchOpen: (open: boolean) => void;
  notificationsOpen: boolean;
  setNotificationsOpen: (open: boolean) => void;
  toggleNotifications: () => void;
  unreadAlertsCount: number;
  markAlertsAsRead: () => void;
}

const AppShellContext = React.createContext<AppShellContextType | undefined>(undefined);

const SIDEBAR_STORAGE_KEY = "gtp-sidebar-collapsed";

export function AppShellProvider({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const [sidebarCollapsed, setSidebarCollapsedState] = React.useState(false);
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [searchOpen, setSearchOpen] = React.useState(false);
  const [notificationsOpen, setNotificationsOpen] = React.useState(false);
  const [unreadAlertsCount, setUnreadAlertsCount] = React.useState(3);

  // Restore sidebar state from localStorage on mount
  React.useEffect(() => {
    try {
      const saved = localStorage.getItem(SIDEBAR_STORAGE_KEY);
      if (saved !== null) {
        setSidebarCollapsedState(saved === "true");
      }
    } catch {
      // ignore storage errors
    }
  }, []);

  const setSidebarCollapsed = React.useCallback((collapsed: boolean) => {
    setSidebarCollapsedState(collapsed);
    try {
      localStorage.setItem(SIDEBAR_STORAGE_KEY, String(collapsed));
    } catch {
      // ignore
    }
  }, []);

  const toggleSidebar = React.useCallback(() => {
    setSidebarCollapsedState((prev) => {
      const next = !prev;
      try {
        localStorage.setItem(SIDEBAR_STORAGE_KEY, String(next));
      } catch {
        // ignore
      }
      return next;
    });
  }, []);

  const toggleMobileOpen = React.useCallback(() => {
    setMobileOpen((prev) => !prev);
  }, []);

  const toggleNotifications = React.useCallback(() => {
    setNotificationsOpen((prev) => !prev);
  }, []);

  const markAlertsAsRead = React.useCallback(() => {
    setUnreadAlertsCount(0);
  }, []);

  // Close overlays on route change
  React.useEffect(() => {
    setMobileOpen(false);
    setSearchOpen(false);
    setNotificationsOpen(false);
  }, [pathname]);

  // Global keyboard shortcuts (Cmd/Ctrl + K to search, Esc to close)
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setSearchOpen((prev) => !prev);
      } else if (e.key === "Escape") {
        setSearchOpen(false);
        setNotificationsOpen(false);
        setMobileOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <AppShellContext.Provider
      value={{
        sidebarCollapsed,
        setSidebarCollapsed,
        toggleSidebar,
        mobileOpen,
        setMobileOpen,
        toggleMobileOpen,
        searchOpen,
        setSearchOpen,
        notificationsOpen,
        setNotificationsOpen,
        toggleNotifications,
        unreadAlertsCount,
        markAlertsAsRead,
      }}
    >
      {children}
    </AppShellContext.Provider>
  );
}

export function useAppShell() {
  const context = React.useContext(AppShellContext);
  if (!context) {
    throw new Error("useAppShell must be used within an AppShellProvider");
  }
  return context;
}
