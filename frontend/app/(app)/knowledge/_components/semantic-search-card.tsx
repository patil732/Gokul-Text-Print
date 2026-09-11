"use client";

import * as React from "react";
import { searchRag, type RagSearchResponse, type RagSearchChunk } from "@/lib/api/documents";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Search,
  Sparkles,
  FileText,
  Clock,
  Loader2,
  CheckCircle2,
  BookOpen,
  ArrowRight,
  SlidersHorizontal,
} from "lucide-react";

const SAMPLE_QUERIES = [
  "reactive dye printing temperature and fixation protocol",
  "inventory safety stock replenishment buffer guidelines",
  "rotary screen printing speed and viscosity requirements",
  "fabric quality grading and GSM drop defect tolerance",
];

export function SemanticSearchCard() {
  const [query, setQuery] = React.useState("");
  const [topK, setTopK] = React.useState<number>(5);
  const [loading, setLoading] = React.useState(false);
  const [results, setResults] = React.useState<RagSearchResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!query.trim() || loading) return;

    setLoading(true);
    setError(null);

    try {
      const res = await searchRag(query.trim(), topK);
      if (res.status === "success") {
        setResults(res);
      } else {
        setError(res.message || "Search query returned an error.");
      }
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to execute semantic search."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleSelectQuery = (sample: string) => {
    setQuery(sample);
  };

  return (
    <Card className="bg-card border-border shadow-xs">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="space-y-1">
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <Search className="w-4 h-4 text-emerald-500" />
              <span>Semantic Similarity Knowledge Search</span>
              <Badge variant="outline" className="text-[10px] font-mono">
                FAISS Vector Index
              </Badge>
            </CardTitle>
            <CardDescription className="text-xs">
              Natural language search over all chunked SOPs, machine guidelines, and factory operating procedures.
            </CardDescription>
          </div>
          <span className="text-[11px] font-mono text-muted-foreground px-2 py-0.5 rounded bg-muted">
            POST /api/rag/search
          </span>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Sample queries */}
        <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar text-xs">
          <span className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1 shrink-0">
            <Sparkles className="w-3 h-3 text-brand" />
            <span>Try:</span>
          </span>
          {SAMPLE_QUERIES.map((sample, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSelectQuery(sample)}
              className="px-2.5 py-1 rounded-full bg-muted/60 hover:bg-muted border border-border text-muted-foreground hover:text-foreground text-[11px] shrink-0 transition-colors truncate max-w-[260px]"
              title={sample}
            >
              {sample}
            </button>
          ))}
        </div>

        {/* Search Input and Top K Controls */}
        <form onSubmit={handleSearch} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search across factory SOPs, chemical recipes, safety thresholds..."
              className="w-full pl-9 pr-3 py-2 text-xs sm:text-sm rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-brand"
            />
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-border bg-muted/40 text-xs text-muted-foreground">
              <SlidersHorizontal className="w-3 h-3" />
              <span>Top:</span>
              <select
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="bg-transparent text-foreground font-semibold focus:outline-none cursor-pointer"
              >
                <option value={3}>3 Chunks</option>
                <option value={5}>5 Chunks</option>
                <option value={8}>8 Chunks</option>
              </select>
            </div>

            <Button
              type="submit"
              disabled={!query.trim() || loading}
              className="text-xs h-9 px-4 font-semibold gap-1.5 shrink-0"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Search className="w-3.5 h-3.5" />
                  <span>Vector Search</span>
                </>
              )}
            </Button>
          </div>
        </form>

        {error && (
          <div className="p-3 rounded-lg border border-rose-500/30 bg-rose-500/10 text-rose-700 dark:text-rose-300 text-xs">
            {error}
          </div>
        )}

        {/* Results Stream */}
        {results && (
          <div className="space-y-3 pt-2 animate-fadeIn">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs border-b border-border/60 pb-2">
              <div className="font-semibold text-foreground flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                <span>Found {results.chunks.length} Relevant Knowledge Chunks</span>
                <span className="text-[11px] text-muted-foreground font-mono">
                  ({results.elapsed_ms.toFixed(1)}ms)
                </span>
              </div>

              {results.sources.length > 0 && (
                <div className="flex items-center gap-1 text-[11px] text-muted-foreground overflow-x-auto">
                  <span>Sources cited:</span>
                  {results.sources.map((src, i) => (
                    <span
                      key={i}
                      className="px-1.5 py-0.5 rounded bg-muted font-mono text-[10px] text-foreground shrink-0"
                    >
                      {src}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {results.chunks.map((chunk, idx) => {
                const matchPct = Math.round(chunk.score * 100);
                return (
                  <div
                    key={chunk.chunk_id || idx}
                    className="p-3.5 rounded-xl border border-border bg-card/60 hover:bg-muted/30 transition-colors text-xs space-y-2 flex flex-col justify-between"
                  >
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between gap-2 text-[11px]">
                        <div className="flex items-center gap-1.5 font-semibold text-foreground truncate" title={chunk.source_document}>
                          <FileText className="w-3.5 h-3.5 text-brand shrink-0" />
                          <span className="truncate">{chunk.source_document}</span>
                        </div>
                        <span className="font-mono px-1.5 py-0.5 rounded bg-muted text-[10px] shrink-0">
                          Page {chunk.page_number}
                        </span>
                      </div>

                      <p className="text-muted-foreground leading-relaxed line-clamp-4 font-sans whitespace-pre-wrap">
                        {chunk.chunk_text}
                      </p>
                    </div>

                    <div className="pt-2 border-t border-border/40 flex items-center justify-between text-[11px]">
                      <span className="text-muted-foreground">Cosine Similarity</span>
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-muted h-1.5 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              matchPct >= 80
                                ? "bg-emerald-500"
                                : matchPct >= 50
                                  ? "bg-blue-500"
                                  : "bg-amber-500"
                            }`}
                            style={{ width: `${Math.min(100, matchPct)}%` }}
                          />
                        </div>
                        <span className="font-mono font-bold text-foreground">
                          {matchPct}% Match
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
