import type { Metadata } from "next";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SectionReveal } from "@/components/ui/page-transition";
import {
  FileText,
  Download,
  Calendar,
  Sparkles,
  FileSpreadsheet,
  CheckCircle2,
  Clock,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Executive Reports | Gokul Text Print",
  description: "Automated executive intelligence summaries and downloadable mill audits.",
};

export default function ReportsPage() {
  const sampleReports = [
    {
      id: "REP-2026-W36",
      name: "Weekly Plant Executive Intelligence Briefing",
      type: "PDF Audit",
      period: "Sep 04 - Sep 10, 2026",
      generated: "Yesterday at 6:00 PM",
      status: "Ready",
    },
    {
      id: "REP-2026-M08",
      name: "Monthly Grey Cloth Inventory & Shortage Variance",
      type: "CSV / Excel",
      period: "August 2026",
      generated: "Sep 01, 2026",
      status: "Ready",
    },
    {
      id: "REP-2026-REC",
      name: "AI Agent Swarm Intervention & Consensus Log",
      type: "PDF Report",
      period: "Q3 Cumulative",
      generated: "Aug 28, 2026",
      status: "Archived",
    },
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <SectionReveal delay={0}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-md bg-sky-500/10 text-sky-600 dark:text-sky-400">
                <FileText className="w-5 h-5" />
              </span>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                Executive Reports
              </h2>
              <Badge variant="outline" className="text-[10px] font-semibold border-brand/30 text-brand">
                Step 10 Staging
              </Badge>
            </div>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Automated executive intelligence summaries, compliance audit logs, and one-click PDF/CSV exports.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <Button size="sm" className="text-xs gap-1.5 font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Generate New Report</span>
            </Button>
          </div>
        </div>
      </SectionReveal>

      {/* Report Generator Cards */}
      <SectionReveal delay={0.05}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-card border-border hover:border-brand/40 transition-colors cursor-pointer">
            <CardHeader className="pb-2">
              <div className="w-8 h-8 rounded-lg bg-red-500/10 text-red-600 dark:text-red-400 flex items-center justify-center mb-1">
                <FileText className="w-4 h-4" />
              </div>
              <CardTitle className="text-sm">Executive PDF Summary</CardTitle>
              <CardDescription className="text-xs">
                Comprehensive 5-page board summary of sales, production capacity, and stock risk.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-2">
              <Button variant="outline" size="sm" className="w-full text-xs gap-1.5 border-border">
                <Download className="w-3.5 h-3.5" />
                <span>Export PDF</span>
              </Button>
            </CardContent>
          </Card>

          <Card className="bg-card border-border hover:border-brand/40 transition-colors cursor-pointer">
            <CardHeader className="pb-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-1">
                <FileSpreadsheet className="w-4 h-4" />
              </div>
              <CardTitle className="text-sm">Inventory Ledger CSV</CardTitle>
              <CardDescription className="text-xs">
                Raw data dump of all 2,000 ERP bin records with discrepancy markers.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-2">
              <Button variant="outline" size="sm" className="w-full text-xs gap-1.5 border-border">
                <Download className="w-3.5 h-3.5" />
                <span>Download CSV</span>
              </Button>
            </CardContent>
          </Card>

          <Card className="bg-card border-border hover:border-brand/40 transition-colors cursor-pointer">
            <CardHeader className="pb-2">
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400 flex items-center justify-center mb-1">
                <Clock className="w-4 h-4" />
              </div>
              <CardTitle className="text-sm">Scheduled Cron Dispatch</CardTitle>
              <CardDescription className="text-xs">
                Auto-generate Monday 8:00 AM briefing for plant managers and leadership.
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-2">
              <Button variant="outline" size="sm" className="w-full text-xs gap-1.5 border-border">
                <Calendar className="w-3.5 h-3.5" />
                <span>Configure Cron</span>
              </Button>
            </CardContent>
          </Card>
        </div>
      </SectionReveal>

      {/* Generated Reports List */}
      <SectionReveal delay={0.1}>
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-base">Recent Executive Reports</CardTitle>
            <CardDescription>
              Previously compiled reports ready for instantaneous download.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="divide-y divide-border">
              {sampleReports.map((report) => (
                <div
                  key={report.id}
                  className="py-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-muted/30 px-2 rounded-lg transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-lg bg-sky-500/10 text-sky-600 dark:text-sky-400 flex items-center justify-center shrink-0 mt-0.5">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-sm font-semibold text-foreground">
                        {report.name}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
                        <span className="font-mono text-[11px] font-medium text-foreground/80">{report.id}</span>
                        <span>•</span>
                        <span>{report.type}</span>
                        <span>•</span>
                        <span>{report.period}</span>
                        <span>•</span>
                        <span>Generated {report.generated}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                    <Badge variant="outline" className="text-[10px] font-semibold border-emerald-500/30 text-emerald-500">
                      {report.status}
                    </Badge>
                    <Button size="sm" variant="outline" className="h-8 px-3 text-xs gap-1.5 border-border">
                      <Download className="w-3.5 h-3.5" />
                      <span>Download</span>
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
