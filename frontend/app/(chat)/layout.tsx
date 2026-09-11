import * as React from "react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Copilot — Multi-Agent Textile Intelligence | Gokul Text Print",
  description:
    "Dedicated ChatGPT-style executive assistant powered by Sales, Inventory, and Knowledge RAG agents.",
};

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="h-screen w-screen overflow-hidden bg-background text-foreground flex">
      {children}
    </div>
  );
}
