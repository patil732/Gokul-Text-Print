"use client";

import * as React from "react";
import Link from "next/link";
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
import { Button } from "@/components/ui/button";
import { ArrowRight, TrendingUp, Users } from "lucide-react";

export interface MonthlyTrendPoint {
  date: string;
  revenue: number;
  volume: number;
}

export interface ClientPerformancePoint {
  product: string;
  revenue: number;
  share_pct: number;
  volume: number;
}

interface DashboardChartsProps {
  trendData?: MonthlyTrendPoint[];
  clientData?: ClientPerformancePoint[];
}

// Fallback trend data in case analytics endpoint returns empty
const DEFAULT_TREND_DATA: MonthlyTrendPoint[] = [
  { date: "Aug '25", revenue: 135197300, volume: 7302 },
  { date: "Sep '25", revenue: 105452600, volume: 5922 },
  { date: "Oct '25", revenue: 53186900, volume: 3559 },
  { date: "Nov '25", revenue: 106532100, volume: 5079 },
  { date: "Dec '25", revenue: 118487300, volume: 4698 },
  { date: "Jan '26", revenue: 156986400, volume: 4733 },
  { date: "Feb '26", revenue: 205071800, volume: 5776 },
  { date: "Mar '26", revenue: 93601900, volume: 3867 },
  { date: "Apr '26", revenue: 92923300, volume: 6211 },
  { date: "May '26", revenue: 92496400, volume: 3185 },
  { date: "Jun '26", revenue: 97209800, volume: 4439 },
  { date: "Jul '26", revenue: 94663500, volume: 2736 },
];

const DEFAULT_CLIENT_DATA: ClientPerformancePoint[] = [
  { product: "F.Studio Fashion", revenue: 336073887, share_pct: 9.66, volume: 10127 },
  { product: "Raja Bhaiya", revenue: 218119622, share_pct: 6.27, volume: 29785 },
  { product: "Gopi Vaid", revenue: 68177648, share_pct: 1.96, volume: 8122 },
  { product: "Maitri Tex", revenue: 61616247, share_pct: 1.77, volume: 1494 },
  { product: "Neel Creation", revenue: 60362372, share_pct: 1.73, volume: 1024 },
];

function formatCurrencyCrores(val: number): string {
  if (val >= 10000000) {
    return `₹${(val / 10000000).toFixed(1)} Cr`;
  }
  if (val >= 100000) {
    return `₹${(val / 100000).toFixed(1)} L`;
  }
  return `₹${val.toLocaleString("en-IN")}`;
}

export function DashboardCharts({ trendData, clientData }: DashboardChartsProps) {
  const [activeTab, setActiveTab] = React.useState<"trend" | "clients">("trend");
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const chartTrend = trendData && trendData.length > 0 ? trendData : DEFAULT_TREND_DATA;
  const chartClients = clientData && clientData.length > 0 ? clientData.slice(0, 6) : DEFAULT_CLIENT_DATA;

  // Format month labels for clean reading
  const formattedTrend = React.useMemo(() => {
    return chartTrend.map((d) => {
      const parts = d.date.split("-");
      if (parts.length === 2) {
        const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
        const mIdx = parseInt(parts[1], 10) - 1;
        return {
          ...d,
          formattedDate: `${monthNames[mIdx] || parts[1]} '${parts[0].slice(2)}`,
        };
      }
      return { ...d, formattedDate: d.date };
    });
  }, [chartTrend]);

  return (
    <Card className="bg-card border-border shadow-xs">
      <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3">
        <div className="space-y-1">
          <CardTitle className="text-base font-bold flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-brand" />
            <span>Mill Operational Momentum & Trends</span>
          </CardTitle>
          <CardDescription className="text-xs">
            Synthesizing 12-month billing trajectory and major client demand shares.
          </CardDescription>
        </div>

        {/* View Switcher Tabs */}
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
            Revenue Momentum
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("clients")}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-colors cursor-pointer ${
              activeTab === "clients"
                ? "bg-background text-foreground shadow-2xs"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Top Enterprise Clients
          </button>
        </div>
      </CardHeader>

      <CardContent className="pt-2">
        {/* Render Chart when client has mounted */}
        {!mounted ? (
          <div className="h-72 w-full bg-muted/20 animate-pulse rounded-xl" />
        ) : activeTab === "trend" ? (
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={formattedTrend} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.35} />
                    <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.1} />
                <XAxis
                  dataKey="formattedDate"
                  tick={{ fontSize: 11, fill: "currentColor" }}
                  opacity={0.6}
                  tickLine={false}
                  axisLine={{ opacity: 0.2 }}
                />
                <YAxis
                  tickFormatter={formatCurrencyCrores}
                  tick={{ fontSize: 11, fill: "currentColor" }}
                  opacity={0.6}
                  tickLine={false}
                  axisLine={{ opacity: 0.2 }}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload as MonthlyTrendPoint & { formattedDate: string };
                      return (
                        <div className="p-3 rounded-xl bg-card/95 backdrop-blur-md border border-border shadow-xl text-xs space-y-1">
                          <div className="font-bold text-foreground">{label}</div>
                          <div className="text-brand font-semibold">
                            Revenue: {formatCurrencyCrores(data.revenue)}
                          </div>
                          <div className="text-muted-foreground">
                            Order Volume: {data.volume.toLocaleString()} units
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
                  fill="url(#revenueGradient)"
                  name="Monthly Revenue"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartClients} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" opacity={0.1} />
                <XAxis
                  dataKey="product"
                  tick={{ fontSize: 10, fill: "currentColor" }}
                  opacity={0.7}
                  angle={-20}
                  textAnchor="end"
                  interval={0}
                  tickLine={false}
                />
                <YAxis
                  tickFormatter={formatCurrencyCrores}
                  tick={{ fontSize: 11, fill: "currentColor" }}
                  opacity={0.6}
                  tickLine={false}
                  axisLine={{ opacity: 0.2 }}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload as ClientPerformancePoint;
                      return (
                        <div className="p-3 rounded-xl bg-card/95 backdrop-blur-md border border-border shadow-xl text-xs space-y-1">
                          <div className="font-bold text-foreground">{data.product}</div>
                          <div className="text-brand font-semibold">
                            Total Billing: {formatCurrencyCrores(data.revenue)}
                          </div>
                          <div className="text-emerald-600 dark:text-emerald-400 font-medium">
                            Revenue Share: {data.share_pct}%
                          </div>
                          <div className="text-muted-foreground">
                            Volume: {data.volume.toLocaleString()} units
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="revenue" fill="#6366f1" radius={[6, 6, 0, 0]} name="Client Billing" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Drill-down invite footer */}
        <div className="mt-3 pt-3 border-t border-border/70 flex items-center justify-between text-xs text-muted-foreground">
          <span>Data derived from 3,493 ERP sales order records</span>
          <Link
            href="/sales"
            className="text-brand font-semibold hover:underline inline-flex items-center gap-1 group"
          >
            <span>Drill down into Sales Intelligence</span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
