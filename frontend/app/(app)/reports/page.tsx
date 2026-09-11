"use client";

import * as React from "react";
import {
  generateReport,
  getReportDownloadUrl,
  type ReportType,
  type ExportFormat,
} from "@/lib/api/reports";
import { ReportPreviewCard } from "./_components/report-preview-card";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DataTable, type Column } from "@/components/ui/data-table";
import { SectionReveal } from "@/components/ui/page-transition";
import {
  FileText,
  Download,
  Calendar,
  Sparkles,
  FileSpreadsheet,
  CheckCircle2,
  Clock,
  Printer,
  Loader2,
  Filter,
  ExternalLink,
  AlertCircle,
} from "lucide-react";

interface ArchivedReport {
  id: string;
  name: string;
  type: ReportType;
  format: ExportFormat;
  dateTag: string;
  fileSize: string;
  status: string;
}

const ARCHIVED_REPORTS: ArchivedReport[] = [
  {
    id: "REP-DAILY-01",
    name: "Daily Executive Operations Briefing",
    type: "daily",
    format: "pdf",
    dateTag: "Today at 06:00 AM",
    fileSize: "184 KB",
    status: "Ready",
  },
  {
    id: "REP-DAILY-02",
    name: "Daily Sales & Inventory CSV Export",
    type: "daily",
    format: "csv",
    dateTag: "Today at 06:00 AM",
    fileSize: "42 KB",
    status: "Ready",
  },
  {
    id: "REP-WEEK-36",
    name: "Weekly Plant Executive Intelligence Briefing",
    type: "weekly",
    format: "pdf",
    dateTag: "Yesterday at 06:00 PM",
    fileSize: "248 KB",
    status: "Ready",
  },
  {
    id: "REP-MONTH-08",
    name: "Monthly Financial Reconciliation & Stock Ledger",
    type: "monthly",
    format: "pdf",
    dateTag: "Sep 01, 2026",
    fileSize: "412 KB",
    status: "Ready",
  },
  {
    id: "REP-MONTH-08-CSV",
    name: "Monthly Complete Order Line Items CSV",
    type: "monthly",
    format: "csv",
    dateTag: "Sep 01, 2026",
    fileSize: "1.2 MB",
    status: "Ready",
  },
];

export default function ReportsCenterPage() {
  const [activeTab, setActiveTab] = React.useState<ReportType>("daily");
  const [startDate, setStartDate] = React.useState<string>("");
  const [endDate, setEndDate] = React.useState<string>("");

  const [downloadingFormat, setDownloadingFormat] = React.useState<ExportFormat | null>(null);
  const [downloadSuccess, setDownloadSuccess] = React.useState<string | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const handleDownload = async (format: ExportFormat) => {
    setDownloadingFormat(format);
    setError(null);
    setDownloadSuccess(null);

    try {
      const params = {
        type: activeTab,
        format,
        start: activeTab === "custom" ? startDate || undefined : undefined,
        end: activeTab === "custom" ? endDate || undefined : undefined,
      };

      const { blob, filename } = await generateReport(params);
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(blobUrl);

      setDownloadSuccess(`Successfully exported "${filename}"!`);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to generate and download report."
      );
    } finally {
      setDownloadingFormat(null);
    }
  };

  const archiveColumns: Column<ArchivedReport>[] = [
    {
      key: "name",
      header: "Report Title",
      accessor: (r) => (
        <div className="flex items-center gap-2.5 py-1">
          <div
            className={`p-1.5 rounded-lg shrink-0 ${
              r.format === "pdf"
                ? "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
            }`}
          >
            {r.format === "pdf" ? (
              <FileText className="w-4 h-4" />
            ) : (
              <FileSpreadsheet className="w-4 h-4" />
            )}
          </div>
          <div>
            <span className="font-semibold text-foreground block">{r.name}</span>
            <span className="text-[10px] text-muted-foreground font-mono">{r.id}</span>
          </div>
        </div>
      ),
      sortKey: "name",
      sortAccessor: (r) => r.name,
    },
    {
      key: "type",
      header: "Cadence",
      accessor: (r) => (
        <Badge variant="outline" className="capitalize text-[10px] font-mono">
          {r.type}
        </Badge>
      ),
      sortKey: "type",
      align: "center",
    },
    {
      key: "format",
      header: "Format",
      accessor: (r) => (
        <span
          className={`uppercase font-mono text-[10px] font-bold px-2 py-0.5 rounded ${
            r.format === "pdf"
              ? "bg-rose-500/10 text-rose-600 dark:text-rose-400"
              : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
          }`}
        >
          {r.format}
        </span>
      ),
      sortKey: "format",
      align: "center",
    },
    {
      key: "dateTag",
      header: "Generated",
      accessor: (r) => (
        <span className="text-xs text-muted-foreground font-mono">{r.dateTag}</span>
      ),
      sortKey: "dateTag",
    },
    {
      key: "fileSize",
      header: "File Size",
      accessor: (r) => (
        <span className="text-xs text-muted-foreground font-mono">{r.fileSize}</span>
      ),
      align: "right",
    },
    {
      key: "status",
      header: "Status",
      accessor: (r) => <PriorityBadge priority="SUCCESS" label={r.status} />,
      align: "center",
    },
    {
      key: "actions",
      header: "Download",
      accessor: (r) => (
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            setActiveTab(r.type);
            handleDownload(r.format);
          }}
          className="text-xs h-7 gap-1"
        >
          <Download className="w-3 h-3" />
          <span>Export</span>
        </Button>
      ),
      align: "right",
    },
  ];

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <SectionReveal delay={0}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1.5 rounded-md bg-blue-500/10 text-blue-600 dark:text-blue-400">
                <FileText className="w-5 h-5" />
              </span>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                Reports Center & Document Exports
              </h1>
              <Badge variant="outline" className="text-[10px] font-semibold border-brand/30 text-brand">
                Sprint 6 ReportLab API
              </Badge>
            </div>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Automated executive performance summaries, multi-domain audits, and binary PDF / CSV downloads.
            </p>
          </div>

          {/* Quick PDF & CSV Download Buttons */}
          <div className="flex items-center gap-2.5 flex-wrap">
            <Button
              onClick={() => handleDownload("pdf")}
              disabled={downloadingFormat !== null}
              className="text-xs font-semibold gap-1.5 shadow-sm"
            >
              {downloadingFormat === "pdf" ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Download className="w-3.5 h-3.5" />
              )}
              <span>Download PDF</span>
            </Button>

            <Button
              variant="outline"
              onClick={() => handleDownload("csv")}
              disabled={downloadingFormat !== null}
              className="text-xs font-semibold gap-1.5 border-border shadow-xs"
            >
              {downloadingFormat === "csv" ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <FileSpreadsheet className="w-3.5 h-3.5" />
              )}
              <span>Download CSV</span>
            </Button>
          </div>
        </div>
      </SectionReveal>

      {/* Report Cadence Selector Tabs & Custom Range */}
      <SectionReveal delay={0.03}>
        <div className="p-3 rounded-xl bg-card border border-border flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-2xs">
          <div className="flex items-center gap-1.5 p-1 rounded-lg bg-muted border border-border overflow-x-auto">
            {(
              [
                { id: "daily", label: "Daily Briefing" },
                { id: "weekly", label: "Weekly Summary" },
                { id: "monthly", label: "Monthly Audit" },
                { id: "custom", label: "Custom Date Range" },
              ] as const
            ).map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`px-3 py-1.5 text-xs rounded-md font-semibold transition-colors shrink-0 ${
                  activeTab === tab.id
                    ? "bg-background text-foreground shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Custom Date Inputs (only active when custom is selected) */}
          {activeTab === "custom" && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground animate-fadeIn">
              <span>From:</span>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="px-2.5 py-1 text-xs rounded-md border border-border bg-background text-foreground"
              />
              <span>To:</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="px-2.5 py-1 text-xs rounded-md border border-border bg-background text-foreground"
              />
            </div>
          )}
        </div>
      </SectionReveal>

      {/* Success Notification */}
      {downloadSuccess && (
        <SectionReveal delay={0.04}>
          <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 text-xs flex items-center justify-between gap-2 animate-fadeIn">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
              <span>{downloadSuccess}</span>
            </div>
            <button
              type="button"
              onClick={() => setDownloadSuccess(null)}
              className="text-xs underline hover:no-underline text-emerald-600 dark:text-emerald-400"
            >
              Dismiss
            </button>
          </div>
        </SectionReveal>
      )}

      {/* Error Alert */}
      {error && (
        <SectionReveal delay={0.04}>
          <div className="p-3.5 rounded-xl border border-rose-500/30 bg-rose-500/10 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2 animate-fadeIn">
            <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
            <span>{error}</span>
          </div>
        </SectionReveal>
      )}

      {/* Live Report Preview Card */}
      <SectionReveal delay={0.06}>
        <div className="space-y-2">
          <div className="flex items-center justify-between px-1">
            <span className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-1.5">
              <Printer className="w-3.5 h-3.5 text-brand" />
              <span>Live Report Preview Before Download</span>
            </span>
            <span className="text-[11px] text-muted-foreground font-mono">
              Scope: {activeTab.toUpperCase()}
            </span>
          </div>
          <ReportPreviewCard
            reportType={activeTab}
            startDate={startDate}
            endDate={endDate}
          />
        </div>
      </SectionReveal>

      {/* Past Generated Reports & Audit Archives Table */}
      <SectionReveal delay={0.09}>
        <Card className="bg-card border-border shadow-xs">
          <CardHeader className="pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="space-y-1">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-500" />
                <span>Executive Reports & Compliance Archive</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Historical executive briefs generated across all reporting periods.
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-[10px] font-mono">
              Sprint 6 Architecture
            </Badge>
          </CardHeader>
          <CardContent>
            <DataTable
              columns={archiveColumns}
              data={ARCHIVED_REPORTS}
              rowKey={(r) => r.id}
              caption="Executive BI generated reports log"
            />
          </CardContent>
        </Card>
      </SectionReveal>
    </div>
  );
}
