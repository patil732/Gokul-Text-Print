"use client";

import * as React from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageTransition } from "@/components/ui/page-transition";
import { requestPasswordReset, ForgotPasswordResponse } from "@/lib/api/auth";
import {
  KeyRound,
  ArrowRight,
  ArrowLeft,
  Mail,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  ShieldCheck,
} from "lucide-react";

export default function ForgotPasswordPage() {
  const [identifier, setIdentifier] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [result, setResult] = React.useState<ForgotPasswordResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim()) {
      setError("Please enter your username or registered email.");
      return;
    }

    setError(null);
    setLoading(true);
    try {
      const res = await requestPasswordReset({ username: identifier.trim() });
      if (res.success) {
        setResult(res);
      } else {
        setError(res.error || "Failed to generate reset link.");
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Network error while connecting to authorization service.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageTransition className="py-12 lg:py-20">
      <div className="max-w-md mx-auto px-4 sm:px-6 space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-brand-muted text-brand-muted-fg mb-2 shadow-2xs">
            <KeyRound className="w-6 h-6 text-brand" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Reset Mill Access
          </h1>
          <p className="text-xs text-muted-foreground">
            Enter your verified mill email or username to generate a secure recovery token.
          </p>
        </div>

        {/* Card */}
        <Card className="bg-card border-border shadow-md">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-lg font-bold text-foreground">
              Request Reset Token
            </CardTitle>
            <CardDescription className="text-xs text-muted-foreground">
              Tokens expire after 1 hour for security compliance.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {result ? (
              <div className="space-y-4">
                <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-700 dark:text-emerald-400 text-xs space-y-2">
                  <div className="flex items-center gap-2 font-semibold">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                    <span>Token Generated Successfully</span>
                  </div>
                  <p className="text-[11px] leading-relaxed opacity-90">
                    {result.message}
                  </p>
                </div>

                {result.reset_token && (
                  <div className="p-3 rounded-lg bg-muted/60 border border-border space-y-1.5">
                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <span className="font-semibold text-foreground">Reset Token</span>
                      <span className="flex items-center gap-1 text-[10px] text-amber-600 dark:text-amber-400">
                        <Clock className="w-3 h-3" />
                        <span>Valid for 1 Hour</span>
                      </span>
                    </div>
                    <div className="p-2 rounded bg-background border border-border font-mono text-xs text-brand break-all">
                      {result.reset_token}
                    </div>
                    <p className="text-[10px] text-muted-foreground">
                      For immediate testing, click below to proceed directly to the reset password form.
                    </p>
                  </div>
                )}

                <div className="pt-2 flex flex-col gap-2.5">
                  {result.reset_token ? (
                    <Link href={`/reset-password?token=${result.reset_token}`} className="w-full">
                      <Button className="w-full font-semibold gap-2">
                        <span>Proceed to Reset Password</span>
                        <ArrowRight className="w-4 h-4" />
                      </Button>
                    </Link>
                  ) : (
                    <Link href="/login" className="w-full">
                      <Button className="w-full font-semibold">
                        <span>Return to Sign In</span>
                      </Button>
                    </Link>
                  )}

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setResult(null);
                      setIdentifier("");
                    }}
                    className="text-xs text-muted-foreground"
                  >
                    Request another token
                  </Button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-xs text-destructive flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                <div className="space-y-2">
                  <label className="text-xs font-semibold text-foreground">
                    Username or Registered Email
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      required
                      placeholder="e.g. ceo, admin, manager, employee"
                      value={identifier}
                      onChange={(e) => setIdentifier(e.target.value)}
                      className="w-full px-3 py-2 pl-9 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                    />
                    <Mail className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
                  </div>
                </div>

                {/* Quick Persona Suggestions for Testing */}
                <div className="space-y-1.5 pt-1">
                  <span className="text-[11px] text-muted-foreground block">
                    Quick test suggestions:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {["admin", "ceo"].map((role) => (
                      <button
                        key={role}
                        type="button"
                        onClick={() => setIdentifier(role)}
                        className="px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-muted hover:bg-muted/80 text-foreground border border-border cursor-pointer transition-colors"
                      >
                        @{role}
                      </button>
                    ))}
                  </div>
                </div>

                <Button
                  type="submit"
                  size="lg"
                  disabled={loading}
                  className="w-full font-semibold gap-2 mt-4"
                >
                  {loading ? (
                    <span>Generating Reset Token...</span>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      <span>Send Reset Instructions</span>
                    </>
                  )}
                </Button>
              </form>
            )}
          </CardContent>

          <CardFooter className="pt-2 border-t border-border/60 justify-center">
            <Link
              href="/login"
              className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors font-medium"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Sign In</span>
            </Link>
          </CardFooter>
        </Card>

        {/* Security Note */}
        <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <ShieldCheck className="w-4 h-4 text-emerald-500" />
          <span>Tokens expire automatically after 60 minutes</span>
        </div>
      </div>
    </PageTransition>
  );
}
