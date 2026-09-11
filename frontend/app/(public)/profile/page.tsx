"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge, PriorityBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageTransition } from "@/components/ui/page-transition";
import { useAuth } from "@/components/providers/auth-provider";
import { updateUserProfile, UserRole } from "@/lib/api/auth";
import {
  User,
  ShieldCheck,
  Mail,
  Lock,
  LogOut,
  ArrowRight,
  Sparkles,
  KeyRound,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  Activity,
  Check,
  Minus,
} from "lucide-react";

interface RoleMeta {
  title: string;
  badge: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "SUCCESS";
  description: string;
  scope: string;
}

const ROLE_METADATA: Record<UserRole, RoleMeta> = {
  CEO: {
    title: "Chief Executive Officer",
    badge: "CRITICAL",
    description: "Full strategic enterprise visibility, automated cross-agent supervisor briefings, and mill revenue metrics.",
    scope: "Enterprise-Wide Executive Authority",
  },
  Admin: {
    title: "System Administrator",
    badge: "HIGH",
    description: "Platform orchestration, telemetry bus configurations, vector tenant controls, and identity management.",
    scope: "Infrastructure & Platform Administration",
  },
  Manager: {
    title: "Plant & Production Manager",
    badge: "MEDIUM",
    description: "Rotary screen line throughput, machine error SOP lookups, shift scheduling, and inventory buffer approvals.",
    scope: "Mill Floor Operational Oversight",
  },
  Employee: {
    title: "Dye Kitchen & Line Specialist",
    badge: "LOW",
    description: "Chemical dye recipe formulation lookups, reactive batch mixing verification, and stock movement logging.",
    scope: "Shop Floor Formulation & Machine Execution",
  },
};

type PermissionLevel = boolean | "Read Only";

interface PermissionRow {
  feature: string;
  ceo: PermissionLevel;
  admin: PermissionLevel;
  manager: PermissionLevel;
  employee: PermissionLevel;
}

const PERMISSIONS_MATRIX: PermissionRow[] = [
  {
    feature: "Executive Decision Engine & Briefings",
    ceo: true,
    admin: true,
    manager: "Read Only",
    employee: false,
  },
  {
    feature: "Sales Forecasts & Festive Seasonality Curves",
    ceo: true,
    admin: true,
    manager: "Read Only",
    employee: false,
  },
  {
    feature: "Grey Cloth & Chemical Dye Buffer Approvals",
    ceo: true,
    admin: true,
    manager: true,
    employee: "Read Only",
  },
  {
    feature: "Domain RAG Recipe Formulation Lookup",
    ceo: true,
    admin: true,
    manager: true,
    employee: true,
  },
  {
    feature: "Rotary Printer Maintenance & Error Codes",
    ceo: "Read Only",
    admin: true,
    manager: true,
    employee: true,
  },
  {
    feature: "Telemetry Ingestion & Swarm Orchestration",
    ceo: "Read Only",
    admin: true,
    manager: false,
    employee: false,
  },
];

export default function ProfilePage() {
  const router = useRouter();
  const { user, role, isAuthenticated, isLoading, logout, refreshUser } = useAuth();

  const [email, setEmail] = React.useState("");
  const [newPassword, setNewPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [updating, setUpdating] = React.useState(false);
  const [updateMsg, setUpdateMsg] = React.useState<string | null>(null);
  const [updateError, setUpdateError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (user?.email) {
      setEmail(user.email);
    }
  }, [user]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setUpdateError(null);
    setUpdateMsg(null);

    if (newPassword && newPassword.length < 6) {
      setUpdateError("New password must be at least 6 characters.");
      return;
    }
    if (newPassword && newPassword !== confirmPassword) {
      setUpdateError("Passwords do not match.");
      return;
    }

    setUpdating(true);
    try {
      const payload: { email?: string; password?: string } = {};
      if (email !== user?.email) payload.email = email;
      if (newPassword) payload.password = newPassword;

      const res = await updateUserProfile(payload);
      if (res.success) {
        setUpdateMsg(res.message);
        setNewPassword("");
        setConfirmPassword("");
        await refreshUser();
      } else {
        setUpdateError(res.error || "Failed to update profile.");
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setUpdateError(err.message);
      } else {
        setUpdateError("Failed to update profile.");
      }
    } finally {
      setUpdating(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  if (isLoading) {
    return (
      <PageTransition className="py-20 text-center space-y-3">
        <div className="w-8 h-8 rounded-full border-2 border-brand border-t-transparent animate-spin mx-auto" />
        <p className="text-xs text-muted-foreground">Authenticating mill session...</p>
      </PageTransition>
    );
  }

  const currentRole = (role as UserRole) || "Employee";
  const roleMeta = ROLE_METADATA[currentRole] || ROLE_METADATA.Employee;

  return (
    <PageTransition className="py-12 lg:py-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        {/* Top Breadcrumb & Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-brand uppercase tracking-wider mb-1">
              <ShieldCheck className="w-4 h-4" />
              <span>RBAC Session Verified</span>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
              User Profile & Role Authorization
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/dashboard">
              <Button size="sm" className="gap-1.5 text-xs font-semibold">
                <span>Enter Dashboard</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </Link>

            <Button
              size="sm"
              variant="outline"
              onClick={handleLogout}
              className="text-xs font-semibold text-rose-500 hover:text-rose-600 border-border gap-1.5"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </Button>
          </div>
        </div>

        {/* User Identity Card */}
        <Card className="bg-card border-border shadow-md">
          <CardContent className="p-6 sm:p-8">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
              {/* Avatar + Primary Details */}
              <div className="flex items-center gap-5">
                <div className="w-16 h-16 rounded-2xl bg-brand text-brand-fg flex items-center justify-center font-extrabold text-2xl shadow-md">
                  {user?.username ? user.username.slice(0, 1).toUpperCase() : "U"}
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <h2 className="text-2xl font-bold text-foreground">
                      {user?.username || "Guest User"}
                    </h2>
                    <PriorityBadge priority={roleMeta.badge} size="default">
                      {currentRole}
                    </PriorityBadge>
                  </div>
                  <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                    <Mail className="w-3.5 h-3.5" />
                    <span>{user?.email || "No email assigned"}</span>
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    Account ID: #{user?.id || 1} · Internal Mill Directory
                  </p>
                </div>
              </div>

              {/* Status Pill */}
              <div className="p-3 rounded-xl bg-muted/50 border border-border/80 text-xs space-y-1">
                <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-semibold">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  <span>Session Active & Authenticated</span>
                </div>
                <div className="text-[11px] text-muted-foreground">
                  Scope: {roleMeta.scope}
                </div>
              </div>
            </div>

            {/* Role Definition Banner */}
            <div className="mt-6 pt-6 border-t border-border/70 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
              <div className="p-3.5 rounded-lg bg-brand-muted/30 border border-brand/20 md:col-span-2">
                <span className="font-bold text-brand block mb-1">
                  Role Authority: {roleMeta.title} ({currentRole})
                </span>
                <p className="text-muted-foreground leading-relaxed">
                  {roleMeta.description}
                </p>
              </div>

              <div className="p-3.5 rounded-lg bg-muted/40 border border-border/70 space-y-1">
                <span className="font-bold text-foreground block">
                  RBAC Model Readiness
                </span>
                <p className="text-muted-foreground text-[11px]">
                  Role field is stored in SQLite and persisted in Flask sessions. Ready for access control enforcement.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Grid: Permissions Matrix & Edit Profile Form */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* RBAC Comparison Matrix */}
          <div className="lg:col-span-7 space-y-4">
            <Card className="bg-card border-border shadow-xs">
              <CardHeader className="pb-3 border-b border-border/60">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base font-bold text-foreground">
                    RBAC Capability Matrix (Sprints 2–7)
                  </CardTitle>
                  <Badge variant="outline" className="text-[10px] font-semibold text-brand">
                    Active Role: {currentRole}
                  </Badge>
                </div>
                <CardDescription className="text-xs">
                  Readiness preview of operational capabilities mapped to the 4 roles.
                </CardDescription>
              </CardHeader>

              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-border bg-muted/30 text-muted-foreground">
                        <th className="py-2.5 px-4 font-semibold">Platform Domain</th>
                        <th className="py-2.5 px-2 font-semibold text-center">CEO</th>
                        <th className="py-2.5 px-2 font-semibold text-center">Admin</th>
                        <th className="py-2.5 px-2 font-semibold text-center">Manager</th>
                        <th className="py-2.5 px-2 font-semibold text-center">Employee</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/60">
                      {PERMISSIONS_MATRIX.map((row, idx) => (
                        <tr
                          key={idx}
                          className="hover:bg-muted/20 transition-colors"
                        >
                          <td className="py-3 px-4 font-medium text-foreground">
                            {row.feature}
                          </td>
                          <td className="py-3 px-2 text-center">
                            {row.ceo === true ? (
                              <Check className="w-4 h-4 text-emerald-500 mx-auto" />
                            ) : row.ceo === "Read Only" ? (
                              <span className="text-[10px] font-medium text-amber-500">Read</span>
                            ) : (
                              <Minus className="w-4 h-4 text-muted-foreground mx-auto" />
                            )}
                          </td>
                          <td className="py-3 px-2 text-center">
                            {row.admin === true ? (
                              <Check className="w-4 h-4 text-emerald-500 mx-auto" />
                            ) : row.admin === "Read Only" ? (
                              <span className="text-[10px] font-medium text-amber-500">Read</span>
                            ) : (
                              <Minus className="w-4 h-4 text-muted-foreground mx-auto" />
                            )}
                          </td>
                          <td className="py-3 px-2 text-center">
                            {row.manager === true ? (
                              <Check className="w-4 h-4 text-emerald-500 mx-auto" />
                            ) : row.manager === "Read Only" ? (
                              <span className="text-[10px] font-medium text-amber-500">Read</span>
                            ) : (
                              <Minus className="w-4 h-4 text-muted-foreground mx-auto" />
                            )}
                          </td>
                          <td className="py-3 px-2 text-center">
                            {row.employee === true ? (
                              <Check className="w-4 h-4 text-emerald-500 mx-auto" />
                            ) : row.employee === "Read Only" ? (
                              <span className="text-[10px] font-medium text-amber-500">Read</span>
                            ) : (
                              <Minus className="w-4 h-4 text-muted-foreground mx-auto" />
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Edit Profile / Credentials Form */}
          <div className="lg:col-span-5 space-y-6">
            <Card className="bg-card border-border shadow-xs">
              <CardHeader className="pb-3 border-b border-border/60">
                <CardTitle className="text-base font-bold text-foreground">
                  Update Account Settings
                </CardTitle>
                <CardDescription className="text-xs">
                  Modify your contact email or update your authentication password.
                </CardDescription>
              </CardHeader>

              <CardContent className="pt-6">
                {updateMsg && (
                  <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-600 dark:text-emerald-400 flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 shrink-0" />
                    <span>{updateMsg}</span>
                  </div>
                )}

                {updateError && (
                  <div className="mb-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-xs text-destructive flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{updateError}</span>
                  </div>
                )}

                <form onSubmit={handleUpdate} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-foreground">Email Address</label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-foreground">
                      New Password (Optional)
                    </label>
                    <input
                      type="password"
                      placeholder="Leave blank to keep unchanged"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                    />
                  </div>

                  {newPassword && (
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-foreground">
                        Confirm New Password
                      </label>
                      <input
                        type="password"
                        placeholder="Re-type new password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                      />
                    </div>
                  )}

                  <Button
                    type="submit"
                    disabled={updating}
                    className="w-full font-semibold gap-2 mt-2"
                  >
                    {updating ? (
                      <span>Saving Changes...</span>
                    ) : (
                      <>
                        <KeyRound className="w-4 h-4" />
                        <span>Save Profile Changes</span>
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* Session Diagnostics */}
            <Card className="bg-card border-border shadow-xs">
              <CardHeader className="pb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Session Diagnostics
                </span>
              </CardHeader>
              <CardContent className="space-y-2 text-xs text-muted-foreground">
                <div className="flex justify-between">
                  <span>Backend Auth Origin:</span>
                  <span className="font-mono text-foreground">http://localhost:5001</span>
                </div>
                <div className="flex justify-between">
                  <span>Session Cookie:</span>
                  <span className="font-mono text-foreground">session (Signed)</span>
                </div>
                <div className="flex justify-between">
                  <span>RBAC Role Schema:</span>
                  <span className="font-mono text-brand font-semibold">{currentRole}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}
