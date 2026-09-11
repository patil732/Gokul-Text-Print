import type { Metadata } from "next";
import { HeroSection } from "@/components/landing/hero-section";
import { ArchitectureSection } from "@/components/landing/architecture-section";
import { AiFeaturesSection } from "@/components/landing/ai-features-section";
import { BusinessBenefitsSection } from "@/components/landing/business-benefits-section";
import { DemoShowcaseSection } from "@/components/landing/demo-showcase-section";
import { CtaBanner } from "@/components/landing/cta-banner";
import { PageTransition } from "@/components/ui/page-transition";

export const metadata: Metadata = {
  title: "Gokul Text Print — Autonomous Enterprise AI Platform",
  description:
    "Executive intelligence platform for industrial textile printing mills: sales forecasting, grey cloth inventory optimization, chemical dye RAG, and autonomous multi-agent swarm.",
};

export default function HomePage() {
  return (
    <PageTransition>
      <HeroSection />
      <ArchitectureSection />
      <AiFeaturesSection />
      <BusinessBenefitsSection />
      <DemoShowcaseSection />
      <CtaBanner />
    </PageTransition>
  );
}
