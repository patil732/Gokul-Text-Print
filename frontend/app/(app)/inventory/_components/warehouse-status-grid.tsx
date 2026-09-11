"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { Warehouse, Search, AlertCircle, CheckCircle2, ShieldAlert, Layers } from "lucide-react";

export interface WarehouseBin {
  id: string;
  name: string;
  shed: "Shed 1" | "Shed 2";
  fabric: string;
  capacityMeters: number;
  currentMeters: number;
  status: "Healthy" | "Low Buffer" | "Critical" | "Reserved";
  safetyThreshold: number;
}

const FACTORY_BINS: WarehouseBin[] = [
  // Shed 1: Pure Cotton & Cambric Bins
  { id: "BIN-A01", name: "Bin A-01", shed: "Shed 1", fabric: "Pure Cotton 60s", capacityMeters: 25000, currentMeters: 21450, status: "Healthy", safetyThreshold: 5000 },
  { id: "BIN-A02", name: "Bin A-02", shed: "Shed 1", fabric: "Cotton Cambric 50s", capacityMeters: 25000, currentMeters: 19800, status: "Healthy", safetyThreshold: 5000 },
  { id: "BIN-A03", name: "Bin A-03", shed: "Shed 1", fabric: "Organic Cotton Poplin", capacityMeters: 25000, currentMeters: 16200, status: "Healthy", safetyThreshold: 5000 },
  { id: "BIN-A04", name: "Bin A-04", shed: "Shed 1", fabric: "Cotton Slub 40s", capacityMeters: 25000, currentMeters: 4120, status: "Critical", safetyThreshold: 5000 },
  { id: "BIN-A05", name: "Bin A-05", shed: "Shed 1", fabric: "Cotton Voile Premium", capacityMeters: 20000, currentMeters: 18900, status: "Healthy", safetyThreshold: 4000 },
  { id: "BIN-A06", name: "Bin A-06", shed: "Shed 1", fabric: "Grey Mull Cotton", capacityMeters: 20000, currentMeters: 6200, status: "Low Buffer", safetyThreshold: 5000 },

  { id: "BIN-B01", name: "Bin B-01", shed: "Shed 1", fabric: "Cotton Satin 80s", capacityMeters: 30000, currentMeters: 26500, status: "Healthy", safetyThreshold: 6000 },
  { id: "BIN-B02", name: "Bin B-02", shed: "Shed 1", fabric: "Combed Cotton 40s", capacityMeters: 25000, currentMeters: 22100, status: "Healthy", safetyThreshold: 5000 },
  { id: "BIN-B03", name: "Bin B-03", shed: "Shed 1", fabric: "Heavy Cotton Canvas", capacityMeters: 30000, currentMeters: 24800, status: "Healthy", safetyThreshold: 5000 },
  { id: "BIN-B04", name: "Bin B-04", shed: "Shed 1", fabric: "Cotton Dobby Stripe", capacityMeters: 20000, currentMeters: 3400, status: "Critical", safetyThreshold: 5000 },
  { id: "BIN-B05", name: "Bin B-05", shed: "Shed 1", fabric: "Cotton Flex Twill", capacityMeters: 20000, currentMeters: 14500, status: "Healthy", safetyThreshold: 4000 },
  { id: "BIN-B06", name: "Bin B-06", shed: "Shed 1", fabric: "Cotton Gauze Double", capacityMeters: 20000, currentMeters: 15800, status: "Reserved", safetyThreshold: 4000 },

  // Shed 2: Rayon, Viscose & Poly-Georgette Blends
  { id: "BIN-C01", name: "Bin C-01", shed: "Shed 2", fabric: "Liva Rayon 30s", capacityMeters: 30000, currentMeters: 28400, status: "Healthy", safetyThreshold: 6000 },
  { id: "BIN-C02", name: "Bin C-02", shed: "Shed 2", fabric: "Rayon Slub 2/40", capacityMeters: 25000, currentMeters: 21900, status: "Healthy", safetyThreshold: 5000 },
  { id: "BIN-C03", name: "Bin C-03", shed: "Shed 2", fabric: "Rayon Twill Print Base", capacityMeters: 25000, currentMeters: 17800, status: "Healthy", safetyThreshold: 5000 },
  { id: "BIN-C04", name: "Bin C-04", shed: "Shed 2", fabric: "Modal Viscose 40s", capacityMeters: 20000, currentMeters: 6900, status: "Low Buffer", safetyThreshold: 5000 },
  { id: "BIN-C05", name: "Bin C-05", shed: "Shed 2", fabric: "Viscose Chiffon", capacityMeters: 20000, currentMeters: 18200, status: "Healthy", safetyThreshold: 4000 },
  { id: "BIN-C06", name: "Bin C-06", shed: "Shed 2", fabric: "Rayon Crepe Jacquard", capacityMeters: 20000, currentMeters: 19100, status: "Healthy", safetyThreshold: 4000 },

  { id: "BIN-D01", name: "Bin D-01", shed: "Shed 2", fabric: "Poly Georgette 60g", capacityMeters: 30000, currentMeters: 25400, status: "Healthy", safetyThreshold: 6000 },
  { id: "BIN-D02", name: "Bin D-02", shed: "Shed 2", fabric: "Poly Crepe Smooth", capacityMeters: 25000, currentMeters: 23100, status: "Healthy", safetyThreshold: 5000 },
  { id: "BIN-D03", name: "Bin D-03", shed: "Shed 2", fabric: "Satin Silk Blend", capacityMeters: 20000, currentMeters: 16500, status: "Reserved", safetyThreshold: 4000 },
  { id: "BIN-D04", name: "Bin D-04", shed: "Shed 2", fabric: "Micro Poly Twill", capacityMeters: 25000, currentMeters: 22400, status: "Healthy", safetyThreshold: 5000 },
  { id: "BIN-D05", name: "Bin D-05", shed: "Shed 2", fabric: "Linen Viscose Blend", capacityMeters: 20000, currentMeters: 15300, status: "Healthy", safetyThreshold: 4000 },
  { id: "BIN-D06", name: "Bin D-06", shed: "Shed 2", fabric: "Poly Organza Sheer", capacityMeters: 20000, currentMeters: 17200, status: "Healthy", safetyThreshold: 4000 },
];

export function WarehouseStatusGrid() {
  const [filterShed, setFilterShed] = React.useState<"ALL" | "Shed 1" | "Shed 2" | "ATTENTION">("ALL");
  const [searchQuery, setSearchQuery] = React.useState("");
  const [selectedBin, setSelectedBin] = React.useState<WarehouseBin | null>(null);

  const filteredBins = React.useMemo(() => {
    return FACTORY_BINS.filter((bin) => {
      if (filterShed === "Shed 1" && bin.shed !== "Shed 1") return false;
      if (filterShed === "Shed 2" && bin.shed !== "Shed 2") return false;
      if (filterShed === "ATTENTION" && bin.status !== "Critical" && bin.status !== "Low Buffer") return false;

      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return (
          bin.id.toLowerCase().includes(q) ||
          bin.name.toLowerCase().includes(q) ||
          bin.fabric.toLowerCase().includes(q)
        );
      }
      return true;
    });
  }, [filterShed, searchQuery]);

  return (
    <Card className="bg-card border-border shadow-xs">
      <CardHeader className="pb-3">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="space-y-1">
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <Warehouse className="w-4 h-4 text-brand" />
              <span>Warehouse & Factory Storage Bin Status</span>
              <Badge variant="outline" className="text-[10px] font-mono font-semibold">
                24 Factory Bins
              </Badge>
            </CardTitle>
            <CardDescription className="text-xs">
              Live capacity monitoring, safety stock buffers, and batch reservations across Sheds 1 & 2.
            </CardDescription>
          </div>

          {/* Filter tabs & search */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search bin or fabric..."
                className="pl-8 pr-2.5 py-1 text-xs rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground w-40 sm:w-48 focus:outline-none focus:ring-1 focus:ring-brand"
              />
            </div>

            <div className="flex items-center gap-1 p-0.5 rounded-lg bg-muted border border-border">
              {(
                [
                  { id: "ALL", label: "All Bins (24)" },
                  { id: "Shed 1", label: "Shed 1 (12)" },
                  { id: "Shed 2", label: "Shed 2 (12)" },
                  { id: "ATTENTION", label: "Attention (4)" },
                ] as const
              ).map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setFilterShed(tab.id)}
                  className={`px-2.5 py-1 text-xs rounded font-medium transition-colors ${
                    filterShed === tab.id
                      ? "bg-background text-foreground shadow-2xs font-semibold"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Bin Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {filteredBins.map((bin) => {
            const fillPct = Math.min(100, Math.round((bin.currentMeters / bin.capacityMeters) * 100));
            const isSelected = selectedBin?.id === bin.id;

            return (
              <div
                key={bin.id}
                onClick={() => setSelectedBin(isSelected ? null : bin)}
                className={`p-3 rounded-xl border transition-all cursor-pointer text-xs space-y-2 relative ${
                  isSelected
                    ? "border-brand bg-brand/5 shadow-sm ring-1 ring-brand/30"
                    : bin.status === "Critical"
                      ? "border-rose-500/30 bg-rose-500/5 hover:border-rose-500/50"
                      : bin.status === "Low Buffer"
                        ? "border-amber-500/30 bg-amber-500/5 hover:border-amber-500/50"
                        : "border-border bg-card/60 hover:bg-muted/40 hover:border-border/80"
                }`}
              >
                <div className="flex items-start justify-between gap-1">
                  <div>
                    <span className="font-mono font-bold text-foreground">{bin.name}</span>
                    <span className="text-[10px] text-muted-foreground ml-1.5 font-medium">({bin.shed})</span>
                  </div>
                  <PriorityBadge
                    priority={
                      bin.status === "Critical"
                        ? "CRITICAL"
                        : bin.status === "Low Buffer"
                          ? "HIGH"
                          : bin.status === "Reserved"
                            ? "MEDIUM"
                            : "SUCCESS"
                    }
                    label={bin.status}
                  />
                </div>

                <div className="space-y-0.5">
                  <div className="font-medium text-foreground truncate" title={bin.fabric}>
                    {bin.fabric}
                  </div>
                  <div className="flex items-baseline justify-between text-muted-foreground">
                    <span className="font-mono tabular-nums text-foreground font-semibold">
                      {bin.currentMeters.toLocaleString()} m
                    </span>
                    <span className="text-[10px]">Max {bin.capacityMeters.toLocaleString()} m</span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="space-y-1">
                  <div className="w-full bg-muted h-1.5 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        bin.status === "Critical"
                          ? "bg-rose-500"
                          : bin.status === "Low Buffer"
                            ? "bg-amber-500"
                            : bin.status === "Reserved"
                              ? "bg-blue-500"
                              : "bg-emerald-500"
                      }`}
                      style={{ width: `${fillPct}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                    <span>{fillPct}% full</span>
                    <span>Buffer: {bin.safetyThreshold.toLocaleString()}m</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Bin Detail Modal / Expand Bar */}
        {selectedBin && (
          <div className="mt-4 p-3.5 rounded-xl border border-brand/30 bg-brand/5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs animate-fadeIn">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="font-bold font-mono text-foreground text-sm">{selectedBin.name}:</span>
                <span className="font-semibold text-foreground">{selectedBin.fabric}</span>
                <Badge variant="outline" className="text-[10px]">
                  {selectedBin.shed}
                </Badge>
              </div>
              <p className="text-muted-foreground">
                Currently holding <strong className="text-foreground font-mono">{selectedBin.currentMeters.toLocaleString()} meters</strong> of grey cloth.
                Safety minimum is <strong className="text-foreground font-mono">{selectedBin.safetyThreshold.toLocaleString()} meters</strong>.
                {selectedBin.currentMeters < selectedBin.safetyThreshold && (
                  <span className="text-rose-600 dark:text-rose-400 font-semibold ml-1">
                    Deficit: {(selectedBin.safetyThreshold - selectedBin.currentMeters).toLocaleString()} meters below buffer!
                  </span>
                )}
              </p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => setSelectedBin(null)}
                className="px-2.5 py-1 text-xs rounded-md border border-border bg-background hover:bg-muted text-foreground"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
