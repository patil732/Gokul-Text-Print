"use client";

/**
 * components/ui/data-table.tsx
 * -----------------------------
 * Generic sortable data table for the GTP Enterprise UI Platform.
 *
 * Features:
 *   - Fully generic: DataTable<TRow> — typed column accessors
 *   - Click column header to cycle: none → ASC → DESC → none
 *   - aria-sort on <th> for screen-reader accessibility
 *   - loading=true renders SkeletonCard instead of data rows
 *   - Empty state with configurable message
 *   - Optional caption
 *
 * Usage:
 *   const columns: Column<Alert>[] = [
 *     { key: "priority",   header: "Priority",   accessor: r => r.priority,   sortKey: "priority" },
 *     { key: "message",    header: "Message",    accessor: r => r.message },
 *     { key: "created_at", header: "Created",    accessor: r => r.created_at, sortKey: "created_at" },
 *   ];
 *
 *   <DataTable columns={columns} data={alerts} loading={isLoading} />
 */

import { useState, useMemo, type ReactNode } from "react";
import { ChevronUp, ChevronDown, ChevronsUpDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "./skeleton";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type SortDirection = "asc" | "desc" | null;

export interface Column<TRow> {
  /** Unique column identifier */
  key: string;
  /** Header label */
  header: string;
  /** Accessor function — can return string | number | ReactNode */
  accessor: (row: TRow) => ReactNode;
  /**
   * If provided, this column is sortable.
   * Value used for comparison (must be string | number to sort correctly).
   * Provide a separate sortAccessor if accessor returns ReactNode.
   */
  sortKey?: string;
  /** Secondary accessor used for sorting when accessor returns ReactNode */
  sortAccessor?: (row: TRow) => string | number;
  /** Tailwind classes applied to both <th> and <td> cells */
  className?: string;
  /** Alignment. Default: "left" */
  align?: "left" | "center" | "right";
}

export interface DataTableProps<TRow extends object> {
  columns: Column<TRow>[];
  data: TRow[];
  /** Key extractor for stable React keys. Defaults to row index. */
  rowKey?: (row: TRow, index: number) => string | number;
  /** Show skeleton rows instead of data */
  loading?: boolean;
  /** Number of skeleton rows to display. Default: 5 */
  skeletonRows?: number;
  /** Message when data is empty */
  emptyText?: string;
  /** Optional <caption> for the table */
  caption?: string;
  className?: string;
  /** Additional <tbody> row classes (e.g. hover effects) */
  rowClassName?: string | ((row: TRow, index: number) => string);
}

// ---------------------------------------------------------------------------
// Sort icon helper
// ---------------------------------------------------------------------------

function SortIcon({ direction }: { direction: SortDirection }) {
  if (direction === "asc")  return <ChevronUp  aria-hidden="true" className="size-3.5 shrink-0" />;
  if (direction === "desc") return <ChevronDown aria-hidden="true" className="size-3.5 shrink-0" />;
  return <ChevronsUpDown aria-hidden="true" className="size-3.5 shrink-0 opacity-40" />;
}

// ---------------------------------------------------------------------------
// DataTable
// ---------------------------------------------------------------------------

export function DataTable<TRow extends object>({
  columns,
  data,
  rowKey,
  loading = false,
  skeletonRows = 5,
  emptyText = "No data available.",
  caption,
  className,
  rowClassName,
}: DataTableProps<TRow>) {
  const [sortKey, setSortKey]   = useState<string | null>(null);
  const [sortDir, setSortDir]   = useState<SortDirection>(null);

  // Cycle: null → asc → desc → null
  function handleSort(key: string) {
    if (sortKey !== key) {
      setSortKey(key);
      setSortDir("asc");
    } else if (sortDir === "asc") {
      setSortDir("desc");
    } else if (sortDir === "desc") {
      setSortKey(null);
      setSortDir(null);
    }
  }

  // Sort data
  const sorted = useMemo<TRow[]>(() => {
    if (!sortKey || !sortDir) return data;
    const col = columns.find(c => c.sortKey === sortKey);
    if (!col) return data;

    return [...data].sort((a, b) => {
      const va = col.sortAccessor ? col.sortAccessor(a) : (col.accessor(a) as string | number) ?? "";
      const vb = col.sortAccessor ? col.sortAccessor(b) : (col.accessor(b) as string | number) ?? "";

      if (typeof va === "number" && typeof vb === "number") {
        return sortDir === "asc" ? va - vb : vb - va;
      }
      const sa = String(va).toLowerCase();
      const sb = String(vb).toLowerCase();
      if (sa < sb) return sortDir === "asc" ? -1 : 1;
      if (sa > sb) return sortDir === "asc" ? 1 : -1;
      return 0;
    });
  }, [data, sortKey, sortDir, columns]);

  const alignClass = {
    left:   "text-left",
    center: "text-center",
    right:  "text-right",
  } as const;

  return (
    <div className={cn("w-full overflow-x-auto rounded-xl border border-[var(--surface-border)] thin-scrollbar", className)}>
      <table className="w-full min-w-[640px] table-auto border-collapse text-sm">
        {caption && (
          <caption className="px-4 py-2 text-left text-xs text-muted-foreground">
            {caption}
          </caption>
        )}

        {/* ── Head ─────────────────────────────────────────────────────── */}
        <thead className="bg-[var(--surface-2)] border-b border-[var(--surface-border)]">
          <tr>
            {columns.map(col => {
              const isSortable = Boolean(col.sortKey);
              const isActive   = sortKey === col.sortKey;
              const ariaSort   = !isSortable ? undefined
                : isActive && sortDir === "asc"  ? "ascending"
                : isActive && sortDir === "desc" ? "descending"
                : "none";

              return (
                <th
                  key={col.key}
                  scope="col"
                  aria-sort={ariaSort}
                  className={cn(
                    "px-4 py-3 font-semibold text-xs text-muted-foreground uppercase tracking-wider whitespace-nowrap",
                    alignClass[col.align ?? "left"],
                    isSortable && "cursor-pointer select-none hover:text-foreground transition-colors",
                    isActive && "text-foreground",
                    col.className,
                  )}
                  onClick={isSortable ? () => handleSort(col.sortKey!) : undefined}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.header}
                    {isSortable && (
                      <SortIcon direction={isActive ? sortDir : null} />
                    )}
                  </span>
                </th>
              );
            })}
          </tr>
        </thead>

        {/* ── Body ─────────────────────────────────────────────────────── */}
        <tbody className="divide-y divide-[var(--surface-border)] bg-[var(--surface-1)]">
          {loading ? (
            // Skeleton rows
            Array.from({ length: skeletonRows }, (_, ri) => (
              <tr key={`skel-${ri}`} aria-hidden="true">
                {columns.map(col => (
                  <td key={col.key} className="px-4 py-3">
                    <Skeleton className="h-3.5 w-full max-w-[120px]" />
                  </td>
                ))}
              </tr>
            ))
          ) : sorted.length === 0 ? (
            // Empty state
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-10 text-center text-sm text-muted-foreground"
              >
                {emptyText}
              </td>
            </tr>
          ) : (
            sorted.map((row, ri) => {
              const key = rowKey ? rowKey(row, ri) : ri;
              const rClass = typeof rowClassName === "function"
                ? rowClassName(row, ri)
                : rowClassName;

              return (
                <tr
                  key={key}
                  className={cn(
                    "transition-colors hover:bg-[var(--surface-2)]",
                    rClass,
                  )}
                >
                  {columns.map(col => (
                    <td
                      key={col.key}
                      className={cn(
                        "px-4 py-3 text-sm text-foreground whitespace-nowrap",
                        alignClass[col.align ?? "left"],
                        col.className,
                      )}
                    >
                      {col.accessor(row)}
                    </td>
                  ))}
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
