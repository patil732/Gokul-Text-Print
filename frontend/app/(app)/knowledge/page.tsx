import type { Metadata } from "next";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SectionReveal } from "@/components/ui/page-transition";
import {
  BookOpen,
  Search,
  FileText,
  Filter,
  FlaskConical,
  ShieldCheck,
  Download,
  Plus,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Knowledge Base | Gokul Text Print",
  description: "Chemical dye formulations, technical mill SOPs, and defect mitigation guides.",
};

export default function KnowledgeBasePage() {
  const sampleDocuments = [
    {
      title: "Reactive Dye Fixing SOP for Cotton 60s",
      category: "Formulation",
      code: "SOP-DYE-402",
      updated: "3 days ago",
      status: "Verified",
    },
    {
      title: "Disperse Dye Temperature Curve on Rotary Screen #4",
      category: "Machinery",
      code: "SOP-MCH-118",
      updated: "1 week ago",
      status: "Active",
    },
    {
      title: "Pilling & GSM Drop Defect Prevention Protocol",
      category: "Quality Control",
      code: "SOP-QC-205",
      updated: "2 weeks ago",
      status: "Verified",
    },
    {
      title: "Effluent Treatment & Sodium Silicate pH Neutralization",
      category: "Compliance",
      code: "SOP-ENV-310",
      updated: "1 month ago",
      status: "Mandatory",
    },
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <SectionReveal delay={0}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                <BookOpen className="w-5 h-5" />
              </span>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                Knowledge Base
              </h2>
              <Badge variant="outline" className="text-[10px] font-semibold border-brand/30 text-brand">
                Step 9 Staging
              </Badge>
            </div>
            <p className="text-xs sm:text-sm text-muted-foreground">
              RAG-indexed technical repository of chemical dye recipes, standard operating procedures, and print defect mitigation.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <Button variant="outline" size="sm" className="text-xs gap-1.5 border-border">
              <Filter className="w-3.5 h-3.5" />
              <span>All Categories</span>
            </Button>
            <Button size="sm" className="text-xs gap-1.5 font-semibold">
              <Plus className="w-3.5 h-3.5" />
              <span>Upload Mill SOP</span>
            </Button>
          </div>
        </div>
      </SectionReveal>

      {/* Search Bar */}
      <SectionReveal delay={0.05}>
        <div className="relative">
          <Search className="w-4 h-4 text-muted-foreground absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search 142 technical manuals, dye formulas, or defect troubleshooting guides..."
            className="w-full pl-10 pr-4 py-2.5 text-sm rounded-xl border border-border bg-card text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand shadow-2xs"
          />
        </div>
      </SectionReveal>

      {/* Formulation & SOP List */}
      <SectionReveal delay={0.1}>
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-base">Indexed Technical Documentation</CardTitle>
            <CardDescription>
              Embedded into vector database for instantaneous retrieval by the AI Copilot.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y divide-border">
              {sampleDocuments.map((doc) => (
                <div
                  key={doc.code}
                  className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-muted/30 px-2 rounded-lg transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0 mt-0.5">
                      <FlaskConical className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-foreground hover:text-brand transition-colors cursor-pointer">
                        {doc.title}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                        <span className="font-mono text-[11px] font-medium text-foreground/80">{doc.code}</span>
                        <span>•</span>
                        <span>{doc.category}</span>
                        <span>•</span>
                        <span>Updated {doc.updated}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                    <Badge variant="outline" className="text-[10px] font-semibold border-emerald-500/30 text-emerald-500">
                      {doc.status}
                    </Badge>
                    <Button variant="ghost" size="sm" className="h-8 px-2 text-xs text-muted-foreground hover:text-foreground">
                      <Download className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </SectionReveal>
    </div>
  );
}
