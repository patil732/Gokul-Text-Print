"use client";

import * as React from "react";
import { predictInventory, type InventoryPredictResponse } from "@/lib/api/inventory";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sparkles, Bot, ArrowRight, CheckCircle2, AlertTriangle, Play, RefreshCw } from "lucide-react";

interface InventoryPredictionCardProps {
  onPredictionCompleted?: () => void;
}

export function InventoryPredictionCard({ onPredictionCompleted }: InventoryPredictionCardProps) {
  const [stockInput, setStockInput] = React.useState<number>(18500);
  const [warehouseCount, setWarehouseCount] = React.useState<number>(24);
  const [productionGap, setProductionGap] = React.useState<number>(4500);
  const [safetyBuffer, setSafetyBuffer] = React.useState<number>(5000);

  const [loading, setLoading] = React.useState(false);
  const [result, setResult] = React.useState<InventoryPredictResponse | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload = {
        total_stock: Number(stockInput),
        warehouse_count: Number(warehouseCount),
        production_gap: Number(productionGap),
        safety_stock: Number(safetyBuffer),
        fulfillment_rate: 0.92,
        has_open_orders: 1,
        stock_turnover: 4.8,
        days_in_inventory: 28.5,
        fast_moving: 1,
        slow_moving: 0,
        dead_stock: 0,
        reorder_level: Number(safetyBuffer),
      };

      const res = await predictInventory(payload);
      setResult(res);
      if (onPredictionCompleted) {
        onPredictionCompleted();
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Inference execution failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="bg-card border-border shadow-xs">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="space-y-1">
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <Bot className="w-4 h-4 text-purple-500" />
              <span>Inventory Reorder ML Inference Simulator</span>
              <Badge variant="outline" className="text-[10px] font-mono">
                Sprint 3 XGBoost
              </Badge>
            </CardTitle>
            <CardDescription className="text-xs">
              Simulate stock scenarios against the production ML model to predict replenishment necessity.
            </CardDescription>
          </div>
          <span className="text-[11px] font-mono text-muted-foreground px-2 py-0.5 rounded bg-muted">
            POST /api/ml/inventory/predict
          </span>
        </div>
      </CardHeader>

      <CardContent>
        <form onSubmit={handlePredict} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-muted-foreground">
              Current Stock (meters)
            </label>
            <input
              type="number"
              value={stockInput}
              onChange={(e) => setStockInput(Number(e.target.value))}
              className="w-full px-3 py-1.5 text-xs rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-brand font-mono"
              placeholder="e.g. 18500"
              required
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-muted-foreground">
              Active Factory Bins
            </label>
            <input
              type="number"
              value={warehouseCount}
              onChange={(e) => setWarehouseCount(Number(e.target.value))}
              className="w-full px-3 py-1.5 text-xs rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-brand font-mono"
              placeholder="24"
              required
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-muted-foreground">
              Planned Production Gap (m)
            </label>
            <input
              type="number"
              value={productionGap}
              onChange={(e) => setProductionGap(Number(e.target.value))}
              className="w-full px-3 py-1.5 text-xs rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-brand font-mono"
              placeholder="4500"
              required
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-semibold text-muted-foreground">
              Safety Stock Buffer (m)
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                value={safetyBuffer}
                onChange={(e) => setSafetyBuffer(Number(e.target.value))}
                className="w-full px-3 py-1.5 text-xs rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-brand font-mono"
                placeholder="5000"
                required
              />
              <Button
                type="submit"
                size="sm"
                disabled={loading}
                className="text-xs font-semibold gap-1.5 h-8 px-3 shrink-0"
              >
                {loading ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Play className="w-3.5 h-3.5 fill-current" />
                )}
                <span>{loading ? "Running..." : "Test"}</span>
              </Button>
            </div>
          </div>
        </form>

        {error && (
          <div className="mt-4 p-3 rounded-lg border border-rose-500/20 bg-rose-500/5 text-rose-600 dark:text-rose-400 text-xs flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {result && (
          <div
            className={`mt-4 p-4 rounded-xl border transition-all text-xs space-y-2 ${
              String(result.decision).toLowerCase().includes("reorder")
                ? "bg-amber-500/10 border-amber-500/30"
                : "bg-emerald-500/10 border-emerald-500/30"
            }`}
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <CheckCircle2
                  className={`w-4 h-4 ${
                    String(result.decision).toLowerCase().includes("reorder")
                      ? "text-amber-600 dark:text-amber-400"
                      : "text-emerald-600 dark:text-emerald-400"
                  }`}
                />
                <span className="font-bold text-foreground text-sm">
                  Prediction: {String(result.decision)}
                </span>
                <PriorityBadge
                  priority={
                    String(result.decision).toLowerCase().includes("reorder") ? "HIGH" : "SUCCESS"
                  }
                  label={String(result.decision)}
                />
              </div>

              <div className="flex items-center gap-3 text-muted-foreground text-[11px] font-mono">
                <span>Confidence: <strong className="text-foreground">{String(result.confidence || "High")}</strong></span>
                {typeof result.probability === "number" && (
                  <span>Probability: <strong className="text-foreground">{(result.probability * 100).toFixed(1)}%</strong></span>
                )}
                <span>Model: <strong className="text-foreground">{String(result.version || "v1.0")}</strong></span>
              </div>
            </div>

            <p className="text-muted-foreground text-xs leading-relaxed">
              {String(result.decision).toLowerCase().includes("reorder")
                ? "The XGBoost model determined that current storage levels are nearing critical threshold relative to planned production requirements. Recommendation: Dispatch purchase order for grey cloth."
                : "Storage levels across all 24 bins comfortably exceed required safety buffers. No immediate replenishment orders needed for the current production cycle."}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
