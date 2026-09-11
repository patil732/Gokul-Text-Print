"use client";

import * as React from "react";
import { uploadDocument, type DocumentRecord } from "@/lib/api/documents";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  Loader2,
  X,
  FileUp,
} from "lucide-react";

interface DocumentUploadCardProps {
  onUploadSuccess?: (doc: DocumentRecord) => void;
}

export function DocumentUploadCard({ onUploadSuccess }: DocumentUploadCardProps) {
  const [file, setFile] = React.useState<File | null>(null);
  const [dragOver, setDragOver] = React.useState(false);
  const [uploading, setUploading] = React.useState(false);
  const [successMsg, setSuccessMsg] = React.useState<string | null>(null);
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      validateAndSetFile(selected);
    }
  };

  const validateAndSetFile = (selected: File) => {
    setErrorMsg(null);
    setSuccessMsg(null);

    if (!selected.name.toLowerCase().endsWith(".pdf")) {
      setErrorMsg("Only PDF documents (.pdf) are supported for technical document indexing.");
      return;
    }

    // Limit to 25MB
    if (selected.size > 25 * 1024 * 1024) {
      setErrorMsg("Document size exceeds maximum 25 MB limit.");
      return;
    }

    setFile(selected);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleUpload = async () => {
    if (!file || uploading) return;

    setUploading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const res = await uploadDocument(file, "manager");
      if (res.status === "success") {
        setSuccessMsg(`"${file.name}" uploaded successfully and queued for embedding!`);
        setFile(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
        if (onUploadSuccess) {
          onUploadSuccess(res.document);
        }
      } else {
        setErrorMsg(res.message || "Failed to process document upload.");
      }
    } catch (err: unknown) {
      setErrorMsg(
        err instanceof Error
          ? err.message
          : "Upload request failed. Please check network connection."
      );
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes >= 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    }
    return `${Math.round(bytes / 1024)} KB`;
  };

  return (
    <Card className="bg-card border-border shadow-xs">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <FileUp className="w-4 h-4 text-brand" />
              <span>Upload Enterprise Technical Document</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Upload PDF manuals, chemical SOPs, dye formulations, and price sheets for automated text chunking and FAISS indexing.
            </CardDescription>
          </div>
          <Badge variant="outline" className="text-[10px] font-mono">
            Max 25 MB • PDF Only
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Drag & Drop Surface */}
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer flex flex-col items-center justify-center gap-2 ${
            dragOver
              ? "border-brand bg-brand/5 scale-[0.99]"
              : "border-border hover:border-brand/50 hover:bg-muted/30"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="hidden"
          />

          <div className="w-10 h-10 rounded-full bg-brand/10 text-brand flex items-center justify-center">
            <UploadCloud className="w-5 h-5" />
          </div>

          <div className="space-y-0.5">
            <div className="text-xs sm:text-sm font-semibold text-foreground">
              Click to browse or drag & drop factory PDF file here
            </div>
            <p className="text-[11px] text-muted-foreground">
              Supports Standard Operating Procedures, Dye Recipes, and Quality Protocols
            </p>
          </div>
        </div>

        {/* Selected File Card */}
        {file && (
          <div className="p-3 rounded-lg border border-brand/30 bg-brand/5 flex items-center justify-between gap-3 text-xs animate-fadeIn">
            <div className="flex items-center gap-2.5 min-w-0">
              <FileText className="w-4 h-4 text-brand shrink-0" />
              <div className="min-w-0">
                <div className="font-semibold text-foreground truncate">{file.name}</div>
                <div className="text-[11px] text-muted-foreground font-mono">
                  {formatFileSize(file.size)} • application/pdf
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <Button
                size="sm"
                onClick={handleUpload}
                disabled={uploading}
                className="text-xs h-8 font-semibold gap-1.5"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Indexing...</span>
                  </>
                ) : (
                  <>
                    <UploadCloud className="w-3.5 h-3.5" />
                    <span>Upload Document</span>
                  </>
                )}
              </Button>

              <button
                type="button"
                disabled={uploading}
                onClick={(e) => {
                  e.stopPropagation();
                  setFile(null);
                  if (fileInputRef.current) fileInputRef.current.value = "";
                }}
                className="p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                title="Cancel selection"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Success Alert */}
        {successMsg && (
          <div className="p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 text-xs flex items-center gap-2 animate-fadeIn">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-500" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Error Alert */}
        {errorMsg && (
          <div className="p-3 rounded-lg border border-rose-500/30 bg-rose-500/10 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2 animate-fadeIn">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
            <span>{errorMsg}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
