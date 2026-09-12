import type { Metadata } from "next";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge, PriorityBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageTransition } from "@/components/ui/page-transition";
import {
  Layers,
  Sparkles,
  Award,
  Factory,
  Leaf,
  Users,
  ShieldCheck,
  ArrowRight,
  MapPin,
  Clock,
} from "lucide-react";

export const metadata: Metadata = {
  title: "About Us — Gokul Text Print Enterprise Platform",
  description:
    "Decades of textile printing craftsmanship merged with bleeding-edge autonomous AI, sales intelligence, and sustainable dye optimization.",
};

const PILLARS = [
  {
    icon: Factory,
    title: "Industrial Precision at Scale",
    description:
      "Combining high-speed rotary screen and digital pigment printing with real-time neural quality inspection to eliminate fabric flaws before curing.",
  },
  {
    icon: Leaf,
    title: "Ecological Dye Sustainability",
    description:
      "Dynamic liquor ratio optimization and proactive shelf-life alerts reduce dye wastewater by 28% and eliminate stagnant chemical disposal.",
  },
  {
    icon: Sparkles,
    title: "Autonomous Agent Intelligence",
    description:
      "A supervisor-directed swarm of AI agents that connects sales desks, inventory warehouses, and mill color kitchens in sub-second harmony.",
  },
  {
    icon: Users,
    title: "Empowering Mill Operators",
    description:
      "Replacing chaotic paper logbooks with instant voice and natural language RAG lookups, giving line masters answers in seconds.",
  },
];

const LEADERSHIP = [
  {
    name: "Rajesh Patel",
    role: "Managing Director & Founder",
    bio: "Over 32 years steering textile manufacturing operations across Western India's premier printing mills.",
  },
  {
    name: "Dr. Priya Sharma",
    role: "Head of AI & Industrial Systems",
    bio: "Ph.D. in Computational Optimization; previously architected predictive supply chains for global industrial manufacturers.",
  },
  {
    name: "Vikram Desai",
    role: "Chief Production & Color Formulation Officer",
    bio: "Master textile chemist with 20+ years specializing in reactive dye chemistry, pigment binders, and digital fabric printing.",
  },
  {
    name: "Ananya Mehta",
    role: "VP of Supply Chain & Inventory Operations",
    bio: "Ex-logistics director optimizing multi-site cotton sourcing, grey fabric warehousing, and just-in-time delivery networks.",
  },
];

export default function AboutPage() {
  return (
    <PageTransition className="py-12 lg:py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16 lg:space-y-24">
        {/* Header Hero */}
        <div className="max-w-3xl space-y-4">
          <Badge variant="outline" className="text-xs font-semibold px-3 py-1 text-brand border-brand/30">
            Heritage & Innovation
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-foreground leading-tight">
            Where Textile Craftsmanship Meets Autonomous AI
          </h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Gokul Text Print was founded on a simple conviction: the world's most intricate textile
            printing traditions deserve the world's most sophisticated computational intelligence.
          </p>
        </div>

        {/* Origin Story Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          <div className="lg:col-span-7 space-y-4 text-base text-muted-foreground leading-relaxed">
            <h2 className="text-2xl font-bold text-foreground">
              From Surat's Textile Hub to an Autonomous Intelligent Mill
            </h2>
            <p>
              Headquartered in Surat, Gujarat—the textile epicenter of India—<strong>Gokul Tex Print</strong> has
              grown into India's leading natural fabric supplier and wholesale manufacturer. We specialize in
              100% pure natural fabrics including Viscose, Cotton Cambric, Silk, Chiffon, Velvet, and fine embroidery.
            </p>
            <p>
              Gokul Print proudly partners with <strong>Aditya Birla Group</strong> (Indian Rayon, Birla Century,
              and accredited partners of <strong>Liva</strong>) and serves as a nationwide dealer of
              <strong>Asahi Kasei Cupro Fabric, Japan</strong>. Our in-house design studio features over 30
              textile designers who have delivered more than <strong>800+ collections to 250+ private labels globally</strong>.
            </p>
            <p>
              To maintain our zero-defect quality standards across high-speed rotary printing, digital pigment printing,
              and discharge color chemistry, we developed the <strong>Enterprise Mill Intelligence Platform</strong>:
              harmonizing live sales demand, dynamic raw material buffers, certified dye formulations, and autonomous
              line optimization across our Pandesara manufacturing complex.
            </p>
          </div>

          <div className="lg:col-span-5 space-y-4">
            <Card className="bg-card border-border shadow-md">
              <CardHeader className="pb-3">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg bg-brand text-brand-fg flex items-center justify-center">
                    <Award className="w-4 h-4" />
                  </div>
                  <CardTitle className="text-base font-bold">Official Mill Credentials</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div className="flex items-center justify-between py-2 border-b border-border/60">
                  <span className="text-muted-foreground">Global Deliveries</span>
                  <span className="font-bold text-foreground">800+ Collections · 250+ Labels</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-border/60">
                  <span className="text-muted-foreground">In-House Design Studio</span>
                  <span className="font-bold text-foreground">30+ Textile Designers</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-border/60">
                  <span className="text-muted-foreground">Strategic Alliances</span>
                  <span className="font-bold text-foreground">Aditya Birla (Liva) &amp; Asahi Kasei</span>
                </div>
                <div className="flex items-center justify-between py-2 border-b border-border/60">
                  <span className="text-muted-foreground">Core Specialization</span>
                  <span className="font-bold text-brand">100% Pure Natural Fabrics</span>
                </div>
                <div className="flex items-center justify-between py-2">
                  <span className="text-muted-foreground">Printing Technologies</span>
                  <span className="font-bold text-foreground text-xs">Digital, Screen, Discharge, Block</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Four Core Pillars */}
        <div className="space-y-8">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <h2 className="text-3xl font-bold tracking-tight text-foreground">
              Our Core Operating Principles
            </h2>
            <p className="text-sm text-muted-foreground">
              Built on deep respect for manufacturing reality, worker safety, and ecological responsibility.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {PILLARS.map((pillar, idx) => {
              const Icon = pillar.icon;
              return (
                <Card key={idx} className="bg-card border-border shadow-xs hover:border-brand/40 transition-colors">
                  <CardHeader className="space-y-3 pb-3">
                    <div className="w-10 h-10 rounded-lg bg-brand-muted text-brand-muted-fg flex items-center justify-center">
                      <Icon className="w-5 h-5 text-brand" />
                    </div>
                    <CardTitle className="text-base font-bold text-foreground">
                      {pillar.title}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {pillar.description}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Leadership Team */}
        <div className="space-y-8">
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <h2 className="text-3xl font-bold tracking-tight text-foreground">
              Executive & AI Engineering Leadership
            </h2>
            <p className="text-sm text-muted-foreground">
              Bridging decades of shop floor textile mastery with modern computational intelligence.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {LEADERSHIP.map((leader, idx) => (
              <Card key={idx} className="bg-card border-border shadow-xs">
                <CardHeader className="pb-2">
                  <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center font-bold text-lg text-brand mb-2">
                    {leader.name.split(" ").map((n) => n[0]).join("")}
                  </div>
                  <CardTitle className="text-base font-bold text-foreground">
                    {leader.name}
                  </CardTitle>
                  <CardDescription className="text-xs font-semibold text-brand">
                    {leader.role}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {leader.bio}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Official Mill Locations */}
        <div className="p-8 rounded-2xl bg-card border border-border shadow-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-brand font-bold">
                <MapPin className="w-5 h-5" />
                <span className="text-base">Head Office &amp; Factory (Pandesara GIDC)</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                B-74-77, Central Park, Pandesara GIDC, Surat - 394221, Gujarat, India.<br />
                Housing state-of-the-art digital textile printing lines, rotary screen presses, natural fabric
                dye kitchen, and automated AI edge operational monitoring.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-2 text-brand font-bold">
                <MapPin className="w-5 h-5" />
                <span className="text-base">Millennium Market Commercial Hub</span>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                A-I Hall, Wing-A, Upper Ground, Millennium Textile Market, Ring Road, Surat - 395002, Gujarat, India.<br />
                Wholesale showroom, client sample sourcing, private label consultations, and global logistics hub.
              </p>
            </div>
          </div>
        </div>

        {/* Page CTA */}
        <div className="text-center pt-4">
          <Link href="/technology">
            <Button size="lg" className="gap-2 font-semibold">
              <span>Inspect Our 4-Layer Architecture</span>
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </div>
    </PageTransition>
  );
}
