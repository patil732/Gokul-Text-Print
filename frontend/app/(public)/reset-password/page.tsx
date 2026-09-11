"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Badge, PriorityBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageTransition } from "@/components/ui/page-transition";
import { verifyResetToken, resetPassword } from "@/lib/api/auth";
import {
  Lock,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  Eye,
  EyeOff,
  ShieldCheck,
  KeyRound,
  Sparkles,
} from "lucide-react";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const urlToken = searchParams.get("token") || "";

  const [token, setToken] = React.useState(urlToken);
  const [verifying, setVerifying] = React.useState(!!urlToken);
  const [tokenValid, setTokenValid] = React.useState<boolean | null>(urlToken ? null : false);
  const [targetUser, setTargetUser] = React.useState<string | null>(null);

  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);

  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [success, setSuccess] = React.useState(false);

  // Verify token on mount if present in URL
  React.useEffect(() => {
    if (urlToken) {
      setVerifying(true);
      verifyResetToken(urlToken)
        .then((res) => {
          if (res.valid) {
            setTokenValid(true);
            setTargetUser(res.username || null);
          } else {
            setTokenValid(false);
            setError(res.error || "Reset token is invalid or expired.");
          }
        })
        .finally(() => {
          setVerifying(false);
        });
    }
  }, [urlToken]);

  // Real-time password strength calculation
  const strengthScore = React.useMemo(() => {
    let score = 0;
    if (password.length >= 6) score += 1;
    if (password.length >= 10) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;
    return score; // 0 to 5
  }, [password]);

  const strengthLabel = ["Too short", "Weak", "Fair", "Good", "Strong", "Very Strong"][strengthScore];
  const strengthColor = [
    "bg-muted",
    "bg-rose-500",
    "bg-amber-500",
    "bg-amber-400",
    "bg-emerald-500",
    "bg-emerald-600",
  ][strengthScore];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token.trim()) {
      setError("Please provide a valid reset token.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setError(null);
    setSubmitting(true);
    try {
      const res = await resetPassword({ token: token.trim(), password });
      if (res.success) {
        setSuccess(true);
      } else {
        setError(res.error || "Failed to update password.");
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Network error while connecting to Flask auth server.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card className="bg-card border-border shadow-md">
      <CardHeader className="pb-3 border-b border-border/60">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-bold text-foreground">
            {success ? "Password Reset Complete" : "Choose a New Password"}
          </CardTitle>
          {targetUser && (
            <Badge variant="secondary" className="text-xs font-mono">
              Account: @{targetUser}
            </Badge>
          )}
        </div>
        <CardDescription className="text-xs">
          {success
            ? "Your credentials have been securely updated in the mill database."
            : "Enter and confirm your new password below."}
        </CardDescription>
      </CardHeader>

      <CardContent className="pt-6">
        {success ? (
          <div className="py-6 text-center space-y-4 animate-in fade-in zoom-in-95 duration-200">
            <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 mx-auto flex items-center justify-center border border-emerald-500/20">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div className="space-y-1.5">
              <h3 className="text-lg font-bold text-foreground">
                Password Successfully Reset!
              </h3>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto leading-relaxed">
                Your new password is now active. You can now sign in to your RBAC account using your new credentials.
              </p>
            </div>

            <div className="pt-2">
              <Link href="/login" className="w-full">
                <Button size="lg" className="w-full font-semibold gap-2">
                  <span>Sign In with New Password</span>
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {verifying && (
              <div className="p-3 rounded-lg bg-muted/60 text-xs text-muted-foreground flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-brand animate-ping" />
                <span>Verifying reset token with Flask auth engine...</span>
              </div>
            )}

            {error && (
              <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-xs text-destructive flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Token field: auto-filled from URL or editable */}
            {!urlToken && (
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Reset Token</label>
                <input
                  type="text"
                  required
                  placeholder="Paste your reset token here"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  className="w-full px-3 py-2 text-xs font-mono rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                />
              </div>
            )}

            {/* New Password */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">New Password</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="At least 6 characters"
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

              {/* Password Strength Meter */}
              {password && (
                <div className="space-y-1 pt-1">
                  <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden flex">
                    <div
                      className={`h-full transition-all duration-300 ${strengthColor}`}
                      style={{ width: `${(strengthScore / 5) * 100}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] text-muted-foreground">
                    <span>Strength: {strengthLabel}</span>
                    <span>Min 6 characters</span>
                  </div>
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Confirm New Password</label>
              <input
                type={showPassword ? "text" : "password"}
                required
                placeholder="Re-type your new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={`w-full px-3 py-2 text-sm rounded-lg border bg-background text-foreground focus:outline-hidden focus:ring-2 ${
                  confirmPassword && confirmPassword !== password
                    ? "border-rose-500 focus:ring-rose-500"
                    : "border-border focus:ring-brand"
                }`}
              />
              {confirmPassword && confirmPassword !== password && (
                <span className="text-[10px] text-rose-500 block">Passwords do not match</span>
              )}
            </div>

            <Button
              type="submit"
              size="lg"
              disabled={submitting || verifying || (!!confirmPassword && confirmPassword !== password)}
              className="w-full font-semibold gap-2 mt-2"
            >
              {submitting ? (
                <span>Updating Password...</span>
              ) : (
                <>
                  <KeyRound className="w-4 h-4" />
                  <span>Update Password</span>
                </>
              )}
            </Button>
          </form>
        )}
      </CardContent>

      <CardFooter className="pt-2 border-t border-border/60 justify-center">
        <Link
          href="/login"
          className="text-xs text-muted-foreground hover:text-foreground transition-colors font-medium"
        >
          Return to Sign In
        </Link>
      </CardFooter>
    </Card>
  );
}

export default function ResetPasswordPage() {
  return (
    <PageTransition className="py-12 lg:py-20">
      <div className="max-w-md mx-auto px-4 sm:px-6 space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-brand-muted text-brand-muted-fg mb-2 shadow-2xs">
            <Lock className="w-6 h-6 text-brand" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
            Reset Your Password
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
            Create a secure new password for your Gokul Text Print account.
          </p>
        </div>

        {/* Suspense boundary for useSearchParams */}
        <React.Suspense
          fallback={
            <div className="p-8 rounded-xl border border-border bg-card text-center text-xs text-muted-foreground">
              Loading password reset parameters...
            </div>
          }
        >
          <ResetPasswordForm />
        </React.Suspense>

        {/* Security Note */}
        <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <ShieldCheck className="w-4 h-4 text-emerald-500" />
          <span>Passphrases hashed with PBKDF2:SHA256</span>
        </div>
      </div>
    </PageTransition>
  );
}
