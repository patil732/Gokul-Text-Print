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
} from "recharts";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { SalesTrendPoint, ProductPerformanceItem } from "@/lib/api/analytics";
import { TrendingUp, BarChart3 } from "lucide-react";

interface SalesChartsProps {
  trend?: SalesTrendPoint[];
  products?: ProductPerformanceItem[];
}

function formatCurrency(val: number): string {
  if (val >= 10000000) {
    return `₹${(val / 10000000).toFixed(1)} Cr`;
  }
  if (val >= 100000) {
    return `₹${(val / 100000).toFixed(1)} L`;
  }
  return `₹${val.toLocaleString("en-IN")}`;
}

export function SalesCharts({ trend = [], products = [] }: SalesChartsProps) {
  const [activeTab, setActiveTab] = React.useState<"trend" | "products">("trend");
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const chartData = trend.length > 0 ? trend : [
    { date: "2025-08", revenue: 135197301, volume: 7302 },
    { date: "2025-09", revenue: 105452609, volume: 5922 },
    { date: "2025-10", revenue: 53186908, volume: 3559 },
    { date: "2025-11", revenue: 106532146, volume: 5079 },
    { date: "2025-12", revenue: 118487296, volume: 4698 },
    { date: "2026-01", revenue: 156986403, volume: 4733 },
    { date: "2026-02", revenue: 205071845, volume: 5776 },
    { date: "2026-03", revenue: 93601952, volume: 3867 },
    { date: "2026-04", revenue: 92923331, volume: 6211 },
    { date: "2026-05", revenue: 92496394, volume: 3185 },
    { date: "2026-06", revenue: 97209846, volume: 4439 },
    { date: "2026-07", revenue: 94663456, volume: 2736 },
  ];

  const productData = products.length > 0 ? products.slice(0, 8) : [
    { product: "Cotton 60s Cambric", revenue: 336073887, share_pct: 9.66, volume: 10127 },
    { product: "Rayon 14kg Twill", revenue: 218119622, share_pct: 6.27, volume: 29785 },
    { product: "Modal Satin 80s", revenue: 68177648, share_pct: 1.96, volume: 8122 },
    { product: "Pure Silk Crepe", revenue: 61616247, share_pct: 1.77, volume: 1494 },
    { product: "Georgette 60g", revenue: 60362372, share_pct: 1.73, volume: 1024 },
  ];

  return (
    <Card className="bg-card border-border shadow-xs">
      <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3">
        <div className="space-y-1">
          <CardTitle className="text-base font-bold flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-brand" />
            <span>Sales & Order Revenue Dynamics</span>
          </CardTitle>
          <CardDescription className="text-xs">
            Historical sales volume and revenue generation across filtered timeframe.
          </CardDescription>
        </div>

        <div className="flex items-center gap-1.5 p-1 bg-muted/60 border border-border/80 rounded-lg self-start sm:self-auto">
          <button
            type="button"
            onClick={() => setActiveTab("trend")}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors cursor-pointer ${
              activeTab === "trend"
                ? "bg-background text-foreground shadow-2xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Revenue & Volume
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("products")}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors cursor-pointer ${
              activeTab === "products"
                ? "bg-background text-foreground shadow-2xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Product Breakdown
          </button>
        </div>
      </CardHeader>

      <CardContent className="pt-2">
        {!mounted ? (
          <div className="h-72 w-full bg-muted/20 animate-pulse rounded-xl" />
        ) : activeTab === "trend" ? (
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="salesRevGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.0} />
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
                  tickFormatter={formatCurrency}
                  tick={{ fontSize: 11, fill: "currentColor" }}
                  opacity={0.6}
                  tickLine={false}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload as SalesTrendPoint;
                      return (
                        <div className="p-3 rounded-xl bg-card/95 backdrop-blur-md border border-border shadow-xl text-xs space-y-1">
                          <div className="font-bold text-foreground">{label}</div>
                          <div className="text-brand font-semibold">
                            Revenue: {formatCurrency(d.revenue)}
                          </div>
                          <div className="text-muted-foreground">
                            Order Units: {d.volume.toLocaleString()}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  stroke="#4f46e5"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#salesRevGradient)"
                  name="Revenue"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={productData} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.1} />
                <XAxis
                  dataKey="product"
                  tick={{ fontSize: 10, fill: "currentColor" }}
                  opacity={0.7}
                  angle={-15}
                  textAnchor="end"
                  interval={0}
                  tickLine={false}
                />
                <YAxis
                  tickFormatter={formatCurrency}
                  tick={{ fontSize: 11, fill: "currentColor" }}
                  opacity={0.6}
                  tickLine={false}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload as ProductPerformanceItem;
                      return (
                        <div className="p-3 rounded-xl bg-card/95 backdrop-blur-md border border-border shadow-xl text-xs space-y-1">
                          <div className="font-bold text-foreground">{d.product}</div>
                          <div className="text-brand font-semibold">
                            Revenue: {formatCurrency(d.revenue)}
                          </div>
                          <div className="text-emerald-600 dark:text-emerald-400 font-medium">
                            Share: {d.share_pct}%
                          </div>
                          <div className="text-muted-foreground">
                            Order Volume: {d.volume.toLocaleString()} units
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="revenue" fill="#6366f1" radius={[6, 6, 0, 0]} name="Product Revenue" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
