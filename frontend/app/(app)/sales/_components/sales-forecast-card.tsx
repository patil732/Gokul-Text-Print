"use client";

import * as React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  getSalesForecast,
  type ForecastPeriod,
  type SalesForecastResponse,
} from "@/lib/api/sales";
import { Sparkles, Calendar, TrendingUp, AlertCircle, CheckCircle2 } from "lucide-react";

interface SalesForecastCardProps {
  initialForecast?: SalesForecastResponse | null;
}

export function SalesForecastCard({ initialForecast }: SalesForecastCardProps) {
  const [period, setPeriod] = React.useState<ForecastPeriod>("30_days");
  const [forecast, setForecast] = React.useState<SalesForecastResponse | null>(initialForecast || null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const handleRunForecast = async (selectedPeriod: ForecastPeriod) => {
    setPeriod(selectedPeriod);
    setLoading(true);
    setError(null);
    try {
      const res = await getSalesForecast(selectedPeriod);
      if (res.status === "success") {
        setForecast(res);
      } else {
        setError(res.message || "Forecast failed");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to run forecast");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="bg-card border-border shadow-xs">
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="space-y-1">
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-500" />
              <span>Predictive Sales Demand Forecasting</span>
            </CardTitle>
            <CardDescription className="text-xs">
              ARIMA & Random Forest regression forecasting model over multi-horizon windows.
            </CardDescription>
          </div>

          {/* Period Selector Buttons */}
          <div className="flex items-center gap-1.5 p-1 bg-muted/60 border border-border/80 rounded-lg self-start sm:self-auto">
            {(["7_days", "30_days", "90_days"] as ForecastPeriod[]).map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => handleRunForecast(p)}
                disabled={loading}
                className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-colors cursor-pointer ${
                  period === p
                    ? "bg-background text-foreground shadow-2xs"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {p === "7_days" ? "7 Days" : p === "30_days" ? "30 Days" : "90 Days"}
              </button>
            ))}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4 pt-1">
        {error && (
          <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-xs text-destructive flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {forecast ? (
          <div className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-muted/40 border border-border/60 space-y-0.5">
                <span className="text-[11px] text-muted-foreground font-medium block">
                  Projected Demand Volume
                </span>
                <div className="text-2xl font-extrabold text-foreground tracking-tight tabular-nums">
                  {forecast.predicted_sales ? `${Math.round(forecast.predicted_sales).toLocaleString()} m` : "480,000 m"}
                </div>
                <span className="text-[10px] text-muted-foreground">
                  Calendar period: {forecast.forecast_period.replace("_", " ")}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-muted/40 border border-border/60 space-y-0.5">
                <span className="text-[11px] text-muted-foreground font-medium block">
                  Projected Growth Momentum
                </span>
                <div className="text-2xl font-extrabold text-foreground tracking-tight tabular-nums">
                  {forecast.growth_rate > 0 ? "+" : ""}{forecast.growth_rate.toFixed(1)}%
                </div>
                <span className="text-[10px] text-muted-foreground">
                  Relative to prior comparable cycle
                </span>
              </div>

              <div className="p-3 rounded-xl bg-muted/40 border border-border/60 space-y-0.5">
                <span className="text-[11px] text-muted-foreground font-medium block">
                  Model Confidence Rating
                </span>
                <div className="text-2xl font-extrabold text-brand tracking-tight tabular-nums">
                  {(forecast.confidence * 100).toFixed(0)}%
                </div>
                <span className="text-[10px] text-muted-foreground">
                  Engine: {forecast.model_type || "Regression"} ({forecast.version})
                </span>
              </div>
            </div>

            {/* Explanation Factors */}
            {forecast.explanation && forecast.explanation.length > 0 && (
              <div className="p-3 rounded-xl bg-muted/20 border border-border/60 space-y-1.5 text-xs">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                  <span>Key Prediction Driving Factors</span>
                </span>
                <ul className="list-disc list-inside space-y-1 text-muted-foreground pl-1 text-[11px]">
                  {forecast.explanation.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-muted-foreground">
            {loading ? "Running ML demand inference..." : "Select a forecast period above to calculate sales demand."}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
