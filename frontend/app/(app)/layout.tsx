import * as React from "react";
import { AppShellProvider } from "@/components/app-shell/app-shell-provider";
import { AppSidebar } from "@/components/app-shell/app-sidebar";
import { AppTopbar } from "@/components/app-shell/app-topbar";
import { AppSearchDialog } from "@/components/app-shell/app-search-dialog";
import { AppMobileDrawer } from "@/components/app-shell/app-mobile-drawer";

export default function AuthenticatedAppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AppShellProvider>
      <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
        {/* Persistent Desktop Sidebar */}
        <AppSidebar />

        {/* Mobile / Tablet Drawer */}
        <AppMobileDrawer />

        {/* Main View Area */}
        <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
          {/* Top Navbar */}
          <AppTopbar />

          {/* Scrollable Main Content */}
          <main className="flex-1 overflow-y-auto bg-background/50">
            {children}
          </main>
        </div>

        {/* Global Search Modal */}
        <AppSearchDialog />
      </div>
    </AppShellProvider>
  );
}
