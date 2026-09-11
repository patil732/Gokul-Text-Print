"use client";

import { useEffect, useState, useMemo } from "react";
import {
  Alert,
  getAlerts,
  resolveAlert,
  isCriticalAlert,
  isLowStockAlert,
  isSalesDropAlert,
  isModelErrorAlert,
} from "@/lib/api/alerts";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { PriorityBadge, Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Bell,
  AlertTriangle,
  AlertOctagon,
  ShieldAlert,
  CheckCircle2,
  Clock,
  Filter,
  Check,
  RefreshCw,
  Search,
  TrendingDown,
  Boxes,
  Cpu,
  RotateCcw,
  Sparkles,
  ExternalLink,
} from "lucide-react";

type FilterStatus = "ALL" | "PENDING" | "RESOLVED";

interface SectionConfig {
  id: string;
  title: string;
  description: string;
  icon: React.ElementType;
  iconColor: string;
  bgColor: string;
  filterFn: (a: Alert) => boolean;
}

const SECTIONS: SectionConfig[] = [
  {
    id: "critical",
    title: "Critical Priority Incidents",
    description: "Emergency operational breaches requiring immediate factory supervisor or executive sign-off.",
    icon: AlertOctagon,
    iconColor: "text-rose-600 dark:text-rose-400",
    bgColor: "bg-rose-500/10 border-rose-500/20",
    filterFn: isCriticalAlert,
  },
  {
    id: "low_stock",
    title: "Low Stock & Fabric Buffers",
    description: "Greige fabric safety buffer alerts (< 2,000m), chemical catalyst depletion, and stagnant dead stock.",
    icon: Boxes,
    iconColor: "text-amber-600 dark:text-amber-400",
    bgColor: "bg-amber-500/10 border-amber-500/20",
    filterFn: isLowStockAlert,
  },
  {
    id: "sales_drop",
    title: "Sales Drop & Corridor Anomalies",
    description: "Regional wholesale contractions, client reorder latency, and unexpected commercial volume surges.",
    icon: TrendingDown,
    iconColor: "text-purple-600 dark:text-purple-400",
    bgColor: "bg-purple-500/10 border-purple-500/20",
    filterFn: isSalesDropAlert,
  },
  {
    id: "model_errors",
    title: "Model Errors & ETL Integrity",
    description: "ARIMA forecast accuracy breaches, multi-agent consensus drift, and missing machine telemetry.",
    icon: Cpu,
    iconColor: "text-sky-600 dark:text-sky-400",
    bgColor: "bg-sky-500/10 border-sky-500/20",
    filterFn: isModelErrorAlert,
  },
];

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [resolvingId, setResolvingId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<FilterStatus>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [actionNotice, setActionNotice] = useState<{ message: string; type: "success" | "info" } | null>(null);

  const fetchAlerts = async (silent = false) => {
    if (!silent) setLoading(true);
    else setRefreshing(true);
    try {
      const res = await getAlerts({ status: "ALL", limit: 100 });
      if (res.status === "success") {
        setAlerts(res.data);
      }
    } catch (err) {
      console.error("Failed to fetch alerts:", err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, []);

  const handleToggleResolve = async (alertId: string, currentStatus: string) => {
    const isCurrentlyResolved = currentStatus.toUpperCase() === "RESOLVED";
    const newStatus = isCurrentlyResolved ? "ACTIVE" : "RESOLVED";
    setResolvingId(alertId);

    // Optimistic UI update
    setAlerts((prev) =>
      prev.map((a) => (a.alert_id === alertId ? { ...a, status: newStatus } : a))
    );

    try {
      const res = await resolveAlert(alertId, newStatus);
      if (res.status === "success") {
        setActionNotice({
          message: isCurrentlyResolved
            ? `Alert reopened to Active queue.`
            : `Incident marked as Resolved.`,
          type: "success",
        });
        setTimeout(() => setActionNotice(null), 3500);
      }
    } catch (err) {
      console.error("Failed to update alert status:", err);
      // Revert optimistic update
      setAlerts((prev) =>
        prev.map((a) => (a.alert_id === alertId ? { ...a, status: currentStatus } : a))
      );
      setActionNotice({
        message: "Failed to update alert status. Please check backend connection.",
        type: "info",
      });
      setTimeout(() => setActionNotice(null), 3500);
    } finally {
      setResolvingId(null);
    }
  };

  // Filtered dataset based on search
  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      const matchesSearch =
        searchQuery === "" ||
        alert.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
        alert.alert_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
        alert.alert_id.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesSearch;
    });
  }, [alerts, searchQuery]);

  // High-level statistics
  const stats = useMemo(() => {
    const total = alerts.length;
    const pending = alerts.filter((a) => a.status.toUpperCase() !== "RESOLVED").length;
    const resolved = alerts.filter((a) => a.status.toUpperCase() === "RESOLVED").length;
    const criticalPending = alerts.filter(
      (a) => a.priority === "CRITICAL" && a.status.toUpperCase() !== "RESOLVED"
    ).length;
    return { total, pending, resolved, criticalPending };
  }, [alerts]);

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Toast Notice */}
      {actionNotice && (
        <div
          className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl shadow-lg border text-xs font-semibold flex items-center gap-2 animate-in fade-in slide-in-from-bottom-2 ${
            actionNotice.type === "success"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-300 backdrop-blur-md"
              : "bg-rose-500/10 border-rose-500/30 text-rose-700 dark:text-rose-300 backdrop-blur-md"
          }`}
        >
          <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span>{actionNotice.message}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
              <Bell className="w-5 h-5" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                  Alert Center & Incident Command
                </h1>
                <Badge variant="outline" className="text-[10px] font-semibold border-brand/30 text-brand">
                  Live Engine
                </Badge>
              </div>
              <p className="text-xs sm:text-sm text-muted-foreground">
                Real-time operational threshold alarms across production lines, fabric buffers, sales corridors, and ML models.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchAlerts(true)}
            disabled={refreshing || loading}
            className="text-xs gap-1.5 border-border"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin text-brand" : ""}`} />
            <span>{refreshing ? "Refreshing..." : "Refresh"}</span>
          </Button>
        </div>
      </div>

      {/* Top Stat Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="p-4 rounded-xl bg-card border border-border flex items-center justify-between">
          <div className="space-y-0.5">
            <span className="text-xs text-muted-foreground font-medium">Pending Actions</span>
            <div className="text-2xl font-bold text-foreground">
              {loading ? <Skeleton className="h-8 w-12" /> : stats.pending}
            </div>
          </div>
          <span className="p-2.5 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <AlertTriangle className="w-5 h-5" />
          </span>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border flex items-center justify-between">
          <div className="space-y-0.5">
            <span className="text-xs text-muted-foreground font-medium">Critical Breaches</span>
            <div className="text-2xl font-bold text-rose-600 dark:text-rose-400">
              {loading ? <Skeleton className="h-8 w-12" /> : stats.criticalPending}
            </div>
          </div>
          <span className="p-2.5 rounded-xl bg-rose-500/10 text-rose-600 dark:text-rose-400">
            <AlertOctagon className="w-5 h-5" />
          </span>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border flex items-center justify-between">
          <div className="space-y-0.5">
            <span className="text-xs text-muted-foreground font-medium">Resolved Incidents</span>
            <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
              {loading ? <Skeleton className="h-8 w-12" /> : stats.resolved}
            </div>
          </div>
          <span className="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="w-5 h-5" />
          </span>
        </div>

        <div className="p-4 rounded-xl bg-card border border-border flex items-center justify-between">
          <div className="space-y-0.5">
            <span className="text-xs text-muted-foreground font-medium">Total Tracked Alarms</span>
            <div className="text-2xl font-bold text-foreground">
              {loading ? <Skeleton className="h-8 w-12" /> : stats.total}
            </div>
          </div>
          <span className="p-2.5 rounded-xl bg-brand/10 text-brand">
            <ShieldAlert className="w-5 h-5" />
          </span>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-xl bg-card border border-border">
        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1.5 p-1 rounded-lg bg-muted/60 border border-border/50 text-xs font-semibold">
          <button
            onClick={() => setStatusFilter("ALL")}
            className={`px-3 py-1.5 rounded-md transition-all ${
              statusFilter === "ALL"
                ? "bg-background text-foreground shadow-sm font-bold"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            All Alarms ({stats.total})
          </button>
          <button
            onClick={() => setStatusFilter("PENDING")}
            className={`px-3 py-1.5 rounded-md transition-all ${
              statusFilter === "PENDING"
                ? "bg-background text-amber-600 dark:text-amber-400 shadow-sm font-bold"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Pending Only ({stats.pending})
          </button>
          <button
            onClick={() => setStatusFilter("RESOLVED")}
            className={`px-3 py-1.5 rounded-md transition-all ${
              statusFilter === "RESOLVED"
                ? "bg-background text-emerald-600 dark:text-emerald-400 shadow-sm font-bold"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Resolved ({stats.resolved})
          </button>
        </div>

        {/* Search Box */}
        <div className="relative w-full sm:w-72">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search alerts, fabrics, or codes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>
      </div>

      {/* 4 Dedicated Operational Sections */}
      <div className="space-y-8">
        {SECTIONS.map((section) => {
          const sectionAlerts = filteredAlerts.filter(section.filterFn);
          const pendingSectionAlerts = sectionAlerts.filter(
            (a) => a.status.toUpperCase() !== "RESOLVED"
          );
          const resolvedSectionAlerts = sectionAlerts.filter(
            (a) => a.status.toUpperCase() === "RESOLVED"
          );

          // Visible alerts based on active status filter
          const visibleAlerts =
            statusFilter === "PENDING"
              ? pendingSectionAlerts
              : statusFilter === "RESOLVED"
              ? resolvedSectionAlerts
              : sectionAlerts;

          const SectionIcon = section.icon;

          return (
            <Card key={section.id} className="bg-card border-border overflow-hidden shadow-sm">
              <CardHeader className="border-b border-border/70 pb-4 bg-muted/20">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className={`p-2 rounded-xl border ${section.bgColor} ${section.iconColor}`}>
                      <SectionIcon className="w-5 h-5" />
                    </span>
                    <div>
                      <div className="flex items-center gap-2">
                        <CardTitle className="text-base font-bold text-foreground">
                          {section.title}
                        </CardTitle>
                        <Badge
                          variant="outline"
                          className={`text-[10px] uppercase font-bold tracking-wider ${
                            pendingSectionAlerts.length > 0
                              ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30"
                              : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                          }`}
                        >
                          {pendingSectionAlerts.length > 0
                            ? `${pendingSectionAlerts.length} Pending`
                            : "All Clear"}
                        </Badge>
                      </div>
                      <CardDescription className="text-xs text-muted-foreground mt-0.5">
                        {section.description}
                      </CardDescription>
                    </div>
                  </div>

                  {/* Pending vs Resolved Ratio Meter */}
                  <div className="flex items-center gap-2 text-xs self-start sm:self-center">
                    <span className="px-2.5 py-1 rounded-md bg-amber-500/10 text-amber-700 dark:text-amber-300 font-semibold border border-amber-500/20">
                      Pending: {pendingSectionAlerts.length}
                    </span>
                    <span className="px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 font-semibold border border-emerald-500/20">
                      Resolved: {resolvedSectionAlerts.length}
                    </span>
                  </div>
                </div>
              </CardHeader>

              <CardContent className="p-0">
                {loading ? (
                  <div className="p-6 space-y-3">
                    <Skeleton className="h-16 w-full rounded-xl" />
                    <Skeleton className="h-16 w-full rounded-xl" />
                  </div>
                ) : visibleAlerts.length === 0 ? (
                  <div className="p-8 text-center space-y-2">
                    <div className="inline-flex p-3 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                      <CheckCircle2 className="w-6 h-6" />
                    </div>
                    <div className="text-sm font-semibold text-foreground">
                      No {statusFilter !== "ALL" ? statusFilter.toLowerCase() : ""} alerts in this section
                    </div>
                    <p className="text-xs text-muted-foreground max-w-md mx-auto">
                      All alarms in {section.title.toLowerCase()} are currently operating within nominal safety thresholds.
                    </p>
                  </div>
                ) : (
                  <div className="divide-y divide-border/60">
                    {visibleAlerts.map((alert) => {
                      const isResolved = alert.status.toUpperCase() === "RESOLVED";
                      const isResolving = resolvingId === alert.alert_id;

                      return (
                        <div
                          key={alert.alert_id}
                          className={`p-4 sm:px-6 transition-colors flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                            isResolved
                              ? "bg-muted/10 opacity-75 hover:opacity-100"
                              : "hover:bg-muted/30"
                          }`}
                        >
                          <div className="flex items-start gap-3.5">
                            <div className="mt-1 shrink-0">
                              {isResolved ? (
                                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                                  <Check className="w-3.5 h-3.5 stroke-[3]" />
                                </span>
                              ) : (
                                <PriorityBadge priority={alert.priority} />
                              )}
                            </div>

                            <div className="space-y-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-muted text-muted-foreground">
                                  {alert.alert_id.slice(0, 8)}
                                </span>
                                <Badge
                                  variant="secondary"
                                  className="text-[10px] font-semibold uppercase tracking-wider bg-muted/80 text-foreground"
                                >
                                  {alert.alert_type.replace(/_/g, " ")}
                                </Badge>
                                <span
                                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                                    isResolved
                                      ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                                      : "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20"
                                  }`}
                                >
                                  {isResolved ? "RESOLVED" : "PENDING"}
                                </span>
                              </div>

                              <p
                                className={`text-xs sm:text-sm leading-relaxed ${
                                  isResolved
                                    ? "text-muted-foreground line-through decoration-muted-foreground/50"
                                    : "text-foreground font-medium"
                                }`}
                              >
                                {alert.message}
                              </p>

                              <div className="flex items-center gap-2 text-[11px] text-muted-foreground pt-0.5">
                                <Clock className="w-3 h-3" />
                                <span>Created: {alert.created_at}</span>
                                <span>•</span>
                                <span>Priority: {alert.priority}</span>
                              </div>
                            </div>
                          </div>

                          {/* Action Button: Mark Resolved / Reopen */}
                          <div className="flex items-center gap-2 self-end md:self-center shrink-0">
                            {isResolved ? (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleToggleResolve(alert.alert_id, alert.status)}
                                disabled={isResolving}
                                className="text-xs h-8 px-3 gap-1.5 border-border hover:bg-muted"
                              >
                                <RotateCcw className={`w-3.5 h-3.5 ${isResolving ? "animate-spin" : ""}`} />
                                <span>Reopen Alert</span>
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                onClick={() => handleToggleResolve(alert.alert_id, alert.status)}
                                disabled={isResolving}
                                className="text-xs h-8 px-3 gap-1.5 font-semibold bg-brand hover:bg-brand/90 text-brand-foreground shadow-sm"
                              >
                                <Check className={`w-3.5 h-3.5 ${isResolving ? "animate-spin" : ""}`} />
                                <span>{isResolving ? "Resolving..." : "Mark as Resolved"}</span>
                              </Button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
