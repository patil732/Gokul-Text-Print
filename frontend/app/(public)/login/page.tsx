"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PageTransition } from "@/components/ui/page-transition";
import { useAuth } from "@/components/providers/auth-provider";
import {
  Layers,
  LogIn,
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
  Lock,
  User,
  ShieldCheck,
  ArrowRight,
} from "lucide-react";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const justRegistered = searchParams.get("registered") === "true";
  const initialUser = searchParams.get("user") || "";

  const { login } = useAuth();

  const [username, setUsername] = React.useState(initialUser);
  const [password, setPassword] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError("Please enter your username and password.");
      return;
    }

    setError(null);
    setLoading(true);
    try {
      await login({ username: username.trim(), password });
      router.push("/profile");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Invalid username or password.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleQuickFill = async (uname: string, pwd: string) => {
    setUsername(uname);
    setPassword(pwd);
    setError(null);
    setLoading(true);
    try {
      await login({ username: uname, password: pwd });
      router.push("/profile");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Login failed.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="bg-card border-border shadow-md">
      <CardContent className="pt-6 space-y-4">
        {justRegistered && (
          <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-700 dark:text-emerald-300 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
            <span>Account registered successfully! Please sign in with your password.</span>
          </div>
        )}

        {error && (
          <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-xs text-destructive flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-foreground">
              Work Email or Username
            </label>
            <div className="relative">
              <input
                type="text"
                required
                autoComplete="username"
                placeholder="name@company.com or username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-3 py-2 pl-9 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
              />
              <User className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
            </div>
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
                className="w-full px-3 py-2 pl-9 pr-10 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
              />
              <Lock className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
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
              <span>Signing in...</span>
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                <span>Sign In</span>
              </>
            )}
          </Button>
        </form>

        {/* Discreet Demo Access Helper */}
        <div className="pt-3 border-t border-border/60 text-center space-y-2">
          <span className="text-[11px] text-muted-foreground block font-medium">
            Demo quick fill:
          </span>
          <div className="flex items-center justify-center gap-1.5 flex-wrap">
            <button
              type="button"
              onClick={() => handleQuickFill("ceo", "ceo123")}
              className="px-2 py-1 rounded text-[11px] font-medium bg-muted hover:bg-muted/80 text-foreground border border-border cursor-pointer transition-colors"
            >
              CEO
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill("manager", "manager123")}
              className="px-2 py-1 rounded text-[11px] font-medium bg-muted hover:bg-muted/80 text-foreground border border-border cursor-pointer transition-colors"
            >
              Manager
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill("employee", "employee123")}
              className="px-2 py-1 rounded text-[11px] font-medium bg-muted hover:bg-muted/80 text-foreground border border-border cursor-pointer transition-colors"
            >
              Employee
            </button>
            <button
              type="button"
              onClick={() => handleQuickFill("admin", "admin123")}
              className="px-2 py-1 rounded text-[11px] font-medium bg-muted hover:bg-muted/80 text-foreground border border-border cursor-pointer transition-colors"
            >
              Admin
            </button>
          </div>
        </div>
      </CardContent>

      <CardFooter className="pt-2 border-t border-border/60 justify-center">
        <p className="text-xs text-muted-foreground">
          Don&apos;t have an enterprise account?{" "}
          <Link href="/register" className="text-brand font-semibold hover:underline">
            Register your mill
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}

export default function LoginPage() {
  return (
    <PageTransition className="py-12 lg:py-20">
      <div className="max-w-md mx-auto px-4 sm:px-6 space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <Link href="/" className="inline-flex items-center gap-2 font-bold text-foreground hover:opacity-90 transition-opacity">
            <div className="w-8 h-8 rounded-lg bg-brand text-brand-fg flex items-center justify-center shadow-xs">
              <Layers className="w-4 h-4" />
            </div>
            <span className="text-base font-bold">Gokul Text Print</span>
          </Link>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
            Sign In to Mill Intelligence
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground">
            Enter your enterprise credentials to access your autonomous workspace.
          </p>
        </div>

        {/* Suspense Boundary for useSearchParams */}
        <React.Suspense
          fallback={
            <div className="p-8 rounded-xl border border-border bg-card text-center text-xs text-muted-foreground">
              Loading sign in form...
            </div>
          }
        >
          <LoginForm />
        </React.Suspense>

        {/* Security Assurance */}
        <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <ShieldCheck className="w-4 h-4 text-emerald-500" />
          <span>Secure 256-bit encrypted session</span>
        </div>
      </div>
    </PageTransition>
  );
}
