"use client";

import * as React from "react";
import {
  listDocuments,
  deleteDocument,
  type DocumentRecord,
} from "@/lib/api/documents";
import { DocumentUploadCard } from "./_components/document-upload-card";
import { SemanticSearchCard } from "./_components/semantic-search-card";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { DataTable, type Column } from "@/components/ui/data-table";
import { SectionReveal } from "@/components/ui/page-transition";
import {
  BookOpen,
  FileText,
  Trash2,
  RefreshCw,
  Layers,
  Database,
  Search,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ShieldCheck,
  Cpu,
} from "lucide-react";

export default function KnowledgeCenterPage() {
  const [documents, setDocuments] = React.useState<DocumentRecord[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  // Deletion modal / state
  const [deleteTarget, setDeleteTarget] = React.useState<DocumentRecord | null>(null);
  const [deleting, setDeleting] = React.useState(false);
  const [actionNotice, setActionNotice] = React.useState<string | null>(null);

  const loadDocs = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listDocuments();
      if (res.status === "success") {
        setDocuments(res.documents);
      } else {
        setError(res.message || "Failed to load document catalog.");
      }
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Error connecting to document catalog API."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadDocs();
  }, [loadDocs]);

  const confirmDelete = async () => {
    if (!deleteTarget) return;

    setDeleting(true);
    setActionNotice(null);

    try {
      const res = await deleteDocument(deleteTarget.document_id);
      if (res.status === "success") {
        setActionNotice(`Document "${deleteTarget.document_name}" was successfully removed.`);
        setDeleteTarget(null);
        loadDocs();
      } else {
        setError(res.message || "Failed to delete document.");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Document deletion failed.");
    } finally {
      setDeleting(false);
    }
  };

  const columns: Column<DocumentRecord>[] = [
    {
      key: "document_name",
      header: "Document Name",
      accessor: (r) => (
        <div className="flex items-center gap-2.5 py-1">
          <div className="p-1.5 rounded-lg bg-brand/10 text-brand shrink-0">
            <FileText className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <span className="font-semibold text-foreground truncate block max-w-xs sm:max-w-md">
              {r.document_name}
            </span>
            <span className="text-[10px] text-muted-foreground font-mono">
              ID: {r.document_id.slice(0, 8)}...
            </span>
          </div>
        </div>
      ),
      sortKey: "document_name",
      sortAccessor: (r) => r.document_name,
    },
    {
      key: "document_type",
      header: "Type",
      accessor: (r) => (
        <Badge variant="outline" className="uppercase text-[10px] font-mono">
          {r.document_type || "pdf"}
        </Badge>
      ),
      sortKey: "document_type",
      align: "center",
    },
    {
      key: "upload_date",
      header: "Indexed Date",
      accessor: (r) => (
        <span className="text-xs text-muted-foreground font-mono">
          {r.upload_date ? r.upload_date.split(".")[0].replace("T", " ") : "--"}
        </span>
      ),
      sortKey: "upload_date",
      sortAccessor: (r) => r.upload_date,
    },
    {
      key: "uploaded_by",
      header: "Uploader",
      accessor: (r) => (
        <span className="text-xs font-medium text-foreground capitalize">
          {r.uploaded_by || "System"}
        </span>
      ),
      sortKey: "uploaded_by",
      align: "center",
    },
    {
      key: "status",
      header: "Processing Status",
      accessor: (r) => {
        const norm = (r.status || "processed").toLowerCase();
        return (
          <PriorityBadge
            priority={
              norm === "processed" || norm === "active"
                ? "SUCCESS"
                : norm === "processing"
                  ? "MEDIUM"
                  : "CRITICAL"
            }
            label={norm === "processed" ? "Indexed" : norm}
          />
        );
      },
      sortKey: "status",
      align: "center",
    },
    {
      key: "actions",
      header: "Action",
      accessor: (r) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setDeleteTarget(r)}
          className="h-8 w-8 p-0 text-muted-foreground hover:text-rose-600 hover:bg-rose-500/10"
          title="Delete document"
        >
          <Trash2 className="w-3.5 h-3.5" />
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
              <span className="p-1.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                <BookOpen className="w-5 h-5" />
              </span>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                Knowledge Center & Document Library
              </h1>
              <Badge variant="outline" className="text-[10px] font-semibold border-brand/30 text-brand">
                Sprint 4 RAG API
              </Badge>
            </div>
            <p className="text-xs sm:text-sm text-muted-foreground">
              Technical operating procedures, chemical recipes, machine manuals, and vector similarity search.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadDocs}
              disabled={loading}
              className="text-xs gap-1.5 border-border"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-brand" : ""}`} />
              <span>Refresh Catalog</span>
            </Button>
          </div>
        </div>
      </SectionReveal>

      {/* KPI Overview Cards */}
      <SectionReveal delay={0.03}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="bg-card border-border shadow-xs">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-semibold text-muted-foreground uppercase">
                Active Documents
              </CardDescription>
              <div className="text-2xl font-bold tracking-tight text-foreground mt-1 tabular-nums">
                {documents.length} Files
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Available for AI Copilot grounding</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border shadow-xs">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription className="text-xs font-semibold text-muted-foreground uppercase">
                  Vector Engine
                </CardDescription>
                <PriorityBadge priority="SUCCESS" label="FAISS Ready" />
              </div>
              <div className="text-2xl font-bold tracking-tight text-brand mt-1">
                Dense RAG
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">L2 normalized cosine similarity</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border shadow-xs">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-semibold text-muted-foreground uppercase">
                Chunk Granularity
              </CardDescription>
              <div className="text-2xl font-bold tracking-tight text-foreground mt-1">
                500 Chunks
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">50-character sliding overlap buffer</p>
            </CardContent>
          </Card>

          <Card className="bg-card border-border shadow-xs">
            <CardHeader className="pb-2">
              <CardDescription className="text-xs font-semibold text-muted-foreground uppercase">
                Search Latency
              </CardDescription>
              <div className="text-2xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400 mt-1">
                &lt; 15 ms
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground">Real-time embedded retrieval</p>
            </CardContent>
          </Card>
        </div>
      </SectionReveal>

      {/* Action Notification */}
      {actionNotice && (
        <SectionReveal delay={0.04}>
          <div className="p-3.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 text-xs flex items-center justify-between gap-2 animate-fadeIn">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
              <span>{actionNotice}</span>
            </div>
            <button
              type="button"
              onClick={() => setActionNotice(null)}
              className="text-xs underline hover:no-underline text-emerald-600 dark:text-emerald-400"
            >
              Dismiss
            </button>
          </div>
        </SectionReveal>
      )}

      {/* Semantic Search Box */}
      <SectionReveal delay={0.06}>
        <SemanticSearchCard />
      </SectionReveal>

      {/* Document Upload Form */}
      <SectionReveal delay={0.09}>
        <DocumentUploadCard onUploadSuccess={loadDocs} />
      </SectionReveal>

      {/* Document Catalog Table */}
      <SectionReveal delay={0.12}>
        <Card className="bg-card border-border shadow-xs">
          <CardHeader className="pb-3 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div className="space-y-1">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Database className="w-4 h-4 text-brand" />
                <span>Uploaded Technical Documents Catalog</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Synchronized with Flask document repository and SQLite documents table.
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-[10px] font-mono">
              Total: {documents.length} PDF Documents
            </Badge>
          </CardHeader>

          <CardContent>
            {error && (
              <div className="mb-4 p-3 rounded-lg border border-rose-500/30 bg-rose-500/10 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <DataTable
              columns={columns}
              data={documents}
              rowKey={(r) => r.document_id}
              caption="Live document repository from /api/documents"
            />
          </CardContent>
        </Card>
      </SectionReveal>

      {/* Delete Confirmation Dialog */}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xs animate-fadeIn">
          <div className="w-full max-w-md p-5 rounded-2xl border border-border bg-card shadow-xl space-y-4">
            <div className="flex items-center gap-3 text-rose-600 dark:text-rose-400">
              <div className="p-2 rounded-xl bg-rose-500/10">
                <Trash2 className="w-5 h-5" />
              </div>
              <h3 className="text-base font-bold text-foreground">Confirm Document Deletion</h3>
            </div>

            <p className="text-xs text-muted-foreground leading-relaxed">
              Are you sure you want to delete <strong className="text-foreground">{deleteTarget.document_name}</strong>?
              This will remove the file from storage and clear its text chunks from the FAISS vector index.
            </p>

            <div className="flex items-center justify-end gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                disabled={deleting}
                onClick={() => setDeleteTarget(null)}
                className="text-xs"
              >
                Cancel
              </Button>

              <Button
                size="sm"
                disabled={deleting}
                onClick={confirmDelete}
                className="text-xs bg-rose-600 hover:bg-rose-700 text-white font-semibold"
              >
                {deleting ? "Deleting..." : "Delete Document"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
