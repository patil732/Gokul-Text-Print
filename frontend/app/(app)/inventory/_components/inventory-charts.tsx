"use client";

import * as React from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { StockTrendPoint } from "@/lib/api/analytics";
import { Boxes, Layers } from "lucide-react";

interface InventoryChartsProps {
  stockTrend?: StockTrendPoint[];
}

function formatUnits(val: number): string {
  if (val >= 1000000) {
    return `${(val / 1000000).toFixed(1)}M m`;
  }
  if (val >= 1000) {
    return `${(val / 1000).toFixed(0)}k m`;
  }
  return `${val.toLocaleString()} m`;
}

export function InventoryCharts({ stockTrend = [] }: InventoryChartsProps) {
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const chartData = stockTrend.length > 0 ? stockTrend : [
    { date: "2025-08", stock: 2468602, production: 0, stock_ratio: 327197 },
    { date: "2025-09", stock: 2468602, production: 0, stock_ratio: 429007 },
    { date: "2025-10", stock: 2468602, production: 0, stock_ratio: 481340 },
    { date: "2025-11", stock: 2468602, production: 0, stock_ratio: 491268 },
    { date: "2025-12", stock: 2468602, production: 0, stock_ratio: 543784 },
    { date: "2026-01", stock: 2468602, production: 0, stock_ratio: 144276 },
    { date: "2026-02", stock: 2468602, production: 0, stock_ratio: 61954 },
    { date: "2026-03", stock: 2468602, production: 0, stock_ratio: 148138 },
    { date: "2026-04", stock: 2468602, production: 0, stock_ratio: 331372 },
    { date: "2026-05", stock: 2468602, production: 0, stock_ratio: 343190 },
    { date: "2026-06", stock: 2468602, production: 0, stock_ratio: 408153 },
    { date: "2026-07", stock: 2468602, production: 0, stock_ratio: 345242 },
  ];

  return (
    <Card className="bg-card border-border shadow-xs">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="space-y-1">
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <Boxes className="w-4 h-4 text-amber-500" />
              <span>Grey Cloth Stock Trajectory & Holding Curve</span>
            </CardTitle>
            <CardDescription className="text-xs">
              Aggregate fabric meters held in factory storage bins vs replenishment thresholds.
            </CardDescription>
          </div>
          <span className="text-[11px] font-semibold text-muted-foreground px-2 py-0.5 rounded bg-muted">
            Safety Buffer: 5,000m minimum
          </span>
        </div>
      </CardHeader>

      <CardContent className="pt-2">
        {!mounted ? (
          <div className="h-72 w-full bg-muted/20 animate-pulse rounded-xl" />
        ) : (
          <div className="h-72 w-full min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="stockGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.1} />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: "currentColor" }}
                  opacity={0.6}
                  tickLine={false}
                />
                <YAxis
                  tickFormatter={formatUnits}
                  tick={{ fontSize: 11, fill: "currentColor" }}
                  opacity={0.6}
                  tickLine={false}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload as StockTrendPoint;
                      return (
                        <div className="p-3 rounded-xl bg-card/95 backdrop-blur-md border border-border shadow-xl text-xs space-y-1">
                          <div className="font-bold text-foreground">{label}</div>
                          <div className="text-amber-600 dark:text-amber-400 font-semibold">
                            Total Stock: {formatUnits(d.stock)}
                          </div>
                          {d.production > 0 && (
                            <div className="text-emerald-600 dark:text-emerald-400 font-medium">
                              Production: {formatUnits(d.production)}
                            </div>
                          )}
                          <div className="text-muted-foreground">
                            Stock-to-Sales Ratio: {d.stock_ratio ? d.stock_ratio.toFixed(1) : "--"}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="stock"
                  stroke="#f59e0b"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#stockGradient)"
                  name="Stock Level"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
