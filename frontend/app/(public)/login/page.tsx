"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge, PriorityBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageTransition } from "@/components/ui/page-transition";
import { useAuth } from "@/components/providers/auth-provider";
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
  AlertCircle,
  Eye,
  EyeOff,
  Briefcase,
  Users,
} from "lucide-react";

interface DemoRole {
  role: "CEO" | "Admin" | "Manager" | "Employee";
  username: string;
  password: string;
  badge: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "SUCCESS";
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const DEMO_ROLES: DemoRole[] = [
  {
    role: "CEO",
    username: "ceo",
    password: "ceo123",
    badge: "CRITICAL",
    title: "Chief Executive Officer",
    description: "Macro mill KPIs, financial forecasts, and autonomous supervisor agent briefings.",
    icon: UserCheck,
  },
  {
    role: "Admin",
    username: "admin",
    password: "admin123",
    badge: "HIGH",
    title: "System Administrator",
    description: "Platform orchestration, telemetry bus controls, and system configuration.",
    icon: ShieldCheck,
  },
  {
    role: "Manager",
    username: "manager",
    password: "manager123",
    badge: "MEDIUM",
    title: "Plant & Production Manager",
    description: "Shift throughput, rotary screen maintenance, and factory floor operations.",
    icon: Factory,
  },
  {
    role: "Employee",
    username: "employee",
    password: "employee123",
    badge: "LOW",
    title: "Dye Kitchen & Line Specialist",
    description: "Chemical lot dispensing, color kitchen SOP lookups, and inventory logging.",
    icon: Users,
  },
];

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, user } = useAuth();

  const [username, setUsername] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [activePersona, setActivePersona] = React.useState<string | null>(null);

  // If already authenticated, allow instant navigation
  React.useEffect(() => {
    if (isAuthenticated && user) {
      // Optional: keep user on page if they want to switch accounts
    }
  }, [isAuthenticated, user]);

  const executeLogin = async (uname: string, pwd: string) => {
    setError(null);
    setLoading(true);
    try {
      await login({ username: uname, password: pwd });
      router.push("/profile");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Invalid username or password.");
      }
    } finally {
      setLoading(false);
      setActivePersona(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError("Please enter both username and password.");
      return;
    }
    await executeLogin(username, password);
  };

  const handlePersonaClick = async (demo: DemoRole) => {
    setUsername(demo.username);
    setPassword(demo.password);
    setActivePersona(demo.role);
    await executeLogin(demo.username, demo.password);
  };

  return (
    <PageTransition className="py-12 lg:py-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
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
            Wired to the Flask authentication API with RBAC session support (CEO, Admin, Manager, Employee).
          </p>
        </div>

        {/* Quick Demo Personas */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-brand" />
              One-Click RBAC Demo Personas:
            </span>
            <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              Live Flask Auth Ready
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {DEMO_ROLES.map((demo) => {
              const Icon = demo.icon;
              const isSelected = activePersona === demo.role;
              return (
                <Card
                  key={demo.role}
                  className={`group bg-card border-border hover:border-brand/70 hover:shadow-md transition-all cursor-pointer flex flex-col justify-between ${
                    isSelected ? "ring-2 ring-brand border-brand" : ""
                  }`}
                  onClick={() => handlePersonaClick(demo)}
                >
                  <CardHeader className="space-y-2 pb-3">
                    <div className="flex items-center justify-between">
                      <div className="w-8 h-8 rounded-lg bg-brand-muted text-brand-muted-fg flex items-center justify-center">
                        <Icon className="w-4 h-4 text-brand" />
                      </div>
                      <PriorityBadge priority={demo.badge} size="sm">
                        {demo.role}
                      </PriorityBadge>
                    </div>
                    <div>
                      <CardTitle className="text-sm font-bold text-foreground">
                        {demo.title}
                      </CardTitle>
                      <span className="text-[11px] font-mono text-brand block mt-0.5">
                        @{demo.username}
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="text-xs text-muted-foreground pb-4">
                    {demo.description}
                  </CardContent>
                  <CardFooter className="pt-2 border-t border-border/60">
                    <Button
                      size="sm"
                      variant={isSelected ? "default" : "outline"}
                      className="w-full text-xs font-semibold gap-1.5"
                      disabled={loading}
                    >
                      {isSelected ? (
                        <span>Authenticating...</span>
                      ) : (
                        <>
                          <span>Login as {demo.role}</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </>
                      )}
                    </Button>
                  </CardFooter>
                </Card>
              );
            })}
          </div>
        </div>

        {/* Divider */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t border-border" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-background px-3 text-muted-foreground font-semibold">
              Or Sign In With Mill Credentials
            </span>
          </div>
        </div>

        {/* Standard Credentials Form */}
        <div className="max-w-md mx-auto">
          <Card className="bg-card border-border shadow-md">
            <CardHeader className="pb-3 border-b border-border/60">
              <CardTitle className="text-base font-bold text-foreground">
                Enterprise Credentials
              </CardTitle>
              <CardDescription className="text-xs">
                Enter your registered username or email to access your RBAC workspace.
              </CardDescription>
            </CardHeader>

            <CardContent className="pt-6">
              {error && (
                <div className="mb-4 p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-xs text-destructive flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-foreground">
                    Username or Email
                  </label>
                  <input
                    type="text"
                    required
                    autoComplete="username"
                    placeholder="e.g. ceo, admin, manager"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                  />
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-foreground">Password</label>
                    <Link
                      href="/forgot-password"
                      className="text-xs text-brand hover:underline font-medium"
                    >
                      Forgot password?
                    </Link>
                  </div>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      autoComplete="current-password"
                      placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-3 py-2 pr-10 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                      aria-label={showPassword ? "Hide password" : "Show password"}
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <Button
                  type="submit"
                  size="lg"
                  disabled={loading}
                  className="w-full font-semibold gap-2 mt-2"
                >
                  {loading ? (
                    <span>Verifying Session...</span>
                  ) : (
                    <>
                      <LogIn className="w-4 h-4" />
                      <span>Sign In to Platform</span>
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Trust Badges */}
        <div className="pt-2 flex flex-wrap items-center justify-center gap-6 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span>Encrypted Session Cookie</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Lock className="w-4 h-4 text-brand" />
            <span>RBAC Role Schema Active</span>
          </div>
          <div>•</div>
          <Link href="/dashboard" className="text-brand hover:underline font-medium">
            Jump Directly to Live Dashboard
          </Link>
        </div>
      </div>
    </PageTransition>
  );
}
