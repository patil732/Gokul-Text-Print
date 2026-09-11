"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge, PriorityBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageTransition } from "@/components/ui/page-transition";
import {
  Layers,
  ArrowRight,
  ShieldCheck,
  UserCheck,
  Factory,
  Boxes,
  Lock,
  Sparkles,
  LogIn,
} from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = React.useState("executive@gokultextprint.internal");
  const [password, setPassword] = React.useState("••••••••••••");
  const [loadingRole, setLoadingRole] = React.useState<string | null>(null);

  const handleQuickLogin = (role: string) => {
    setLoadingRole(role);
    setTimeout(() => {
      router.push("/dashboard");
    }, 400);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingRole("email");
    setTimeout(() => {
      router.push("/dashboard");
    }, 400);
  };

  return (
    <PageTransition className="py-12 lg:py-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        {/* Header */}
        <div className="text-center max-w-xl mx-auto space-y-3">
          <div className="inline-flex items-center gap-2 p-2 rounded-xl bg-brand-muted/40 text-brand font-bold text-sm">
            <Layers className="w-5 h-5 text-brand" />
            <span>Gokul Text Print Enterprise Portal</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground">
            Sign In to Mill Intelligence
          </h1>

          <p className="text-sm text-muted-foreground">
            Sprint 7 public unauthenticated demonstration mode is active. You can launch the platform
            immediately with pre-configured executive roles.
          </p>
        </div>

        {/* Quick Demo Access Roles */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-brand" />
              Instant One-Click Demo Personas:
            </span>
            <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              No Password Needed
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Role 1 */}
            <Card
              className="group bg-card border-border hover:border-brand/70 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
              onClick={() => handleQuickLogin("Executive")}
            >
              <CardHeader className="space-y-2 pb-3">
                <div className="flex items-center justify-between">
                  <div className="w-8 h-8 rounded-lg bg-brand text-brand-fg flex items-center justify-center">
                    <UserCheck className="w-4 h-4" />
                  </div>
                  <PriorityBadge priority="CRITICAL" size="sm">
                    Full Access
                  </PriorityBadge>
                </div>
                <CardTitle className="text-base font-bold text-foreground">
                  Executive Director / Mill Owner
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-muted-foreground pb-4">
                Macro factory KPIs, seasonal revenue forecasts, and autonomous supervisor agent briefings.
              </CardContent>
              <CardFooter className="pt-2 border-t border-border/60">
                <Button
                  size="sm"
                  className="w-full text-xs font-semibold gap-1.5"
                  disabled={loadingRole !== null}
                >
                  {loadingRole === "Executive" ? (
                    <span>Launching...</span>
                  ) : (
                    <>
                      <span>Enter as Executive</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </Button>
              </CardFooter>
            </Card>

            {/* Role 2 */}
            <Card
              className="group bg-card border-border hover:border-brand/70 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
              onClick={() => handleQuickLogin("Production")}
            >
              <CardHeader className="space-y-2 pb-3">
                <div className="flex items-center justify-between">
                  <div className="w-8 h-8 rounded-lg bg-muted text-foreground flex items-center justify-center">
                    <Factory className="w-4 h-4" />
                  </div>
                  <PriorityBadge priority="HIGH" size="sm">
                    Operations
                  </PriorityBadge>
                </div>
                <CardTitle className="text-base font-bold text-foreground">
                  Plant & Production Lead
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-muted-foreground pb-4">
                Shift line output, rotary screen mesh tension alerts, and formula RAG troubleshooting.
              </CardContent>
              <CardFooter className="pt-2 border-t border-border/60">
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full text-xs font-semibold gap-1.5"
                  disabled={loadingRole !== null}
                >
                  {loadingRole === "Production" ? (
                    <span>Launching...</span>
                  ) : (
                    <>
                      <span>Enter as Plant Lead</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </Button>
              </CardFooter>
            </Card>

            {/* Role 3 */}
            <Card
              className="group bg-card border-border hover:border-brand/70 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between"
              onClick={() => handleQuickLogin("Inventory")}
            >
              <CardHeader className="space-y-2 pb-3">
                <div className="flex items-center justify-between">
                  <div className="w-8 h-8 rounded-lg bg-muted text-foreground flex items-center justify-center">
                    <Boxes className="w-4 h-4" />
                  </div>
                  <PriorityBadge priority="MEDIUM" size="sm">
                    Supply Chain
                  </PriorityBadge>
                </div>
                <CardTitle className="text-base font-bold text-foreground">
                  Dye Kitchen & Stock Lead
                </CardTitle>
              </CardHeader>
              <CardContent className="text-xs text-muted-foreground pb-4">
                Reactive dye reserves, grey cloth buffer velocity, and automated supplier PO proposals.
              </CardContent>
              <CardFooter className="pt-2 border-t border-border/60">
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full text-xs font-semibold gap-1.5"
                  disabled={loadingRole !== null}
                >
                  {loadingRole === "Inventory" ? (
                    <span>Launching...</span>
                  ) : (
                    <>
                      <span>Enter as Stock Lead</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </Button>
              </CardFooter>
            </Card>
          </div>
        </div>

        {/* Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t border-border" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-background px-3 text-muted-foreground font-semibold">
              Or Sign In With Enterprise SSO
            </span>
          </div>
        </div>

        {/* Standard Demo Login Box */}
        <div className="max-w-md mx-auto">
          <Card className="bg-card border-border shadow-xs">
            <CardContent className="pt-6">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">
                    Corporate Email (Pre-filled Demo)
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background text-foreground font-mono focus:outline-hidden focus:ring-2 focus:ring-brand"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">
                    Authentication Password / Token
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background text-foreground font-mono focus:outline-hidden focus:ring-2 focus:ring-brand"
                  />
                </div>

                <Button
                  type="submit"
                  size="lg"
                  className="w-full font-semibold gap-2"
                  disabled={loadingRole !== null}
                >
                  {loadingRole === "email" ? (
                    <span>Authorizing Demo Token...</span>
                  ) : (
                    <>
                      <LogIn className="w-4 h-4" />
                      <span>Sign In & Enter Dashboard</span>
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Trust Badges */}
        <div className="pt-4 flex flex-wrap items-center justify-center gap-6 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span>Zero real business data exposed</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Lock className="w-4 h-4 text-brand" />
            <span>Air-gap mill security ready</span>
          </div>
          <div>•</div>
          <Link href="/" className="text-brand hover:underline font-medium">
            Return to Public Home
          </Link>
        </div>
      </div>
    </PageTransition>
  );
}
