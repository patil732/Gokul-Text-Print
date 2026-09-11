"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PageTransition } from "@/components/ui/page-transition";
import { registerUser, UserRole } from "@/lib/api/auth";
import {
  Layers,
  ArrowRight,
  ShieldCheck,
  Lock,
  Mail,
  Building,
  User,
  Eye,
  EyeOff,
  AlertCircle,
  CheckCircle2,
} from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();

  const [username, setUsername] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [company, setCompany] = React.useState("");
  const [role, setRole] = React.useState<UserRole>("CEO");
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);

  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [success, setSuccess] = React.useState(false);

  // Real-time password strength calculation (min 8 chars)
  const strengthScore = React.useMemo(() => {
    let score = 0;
    if (password.length >= 8) score += 1;
    if (password.length >= 12) score += 1;
    if (/[A-Z]/.test(password)) score += 1;
    if (/[0-9]/.test(password)) score += 1;
    if (/[^A-Za-z0-9]/.test(password)) score += 1;
    return score;
  }, [password]);

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
    setError(null);

    if (!username.trim()) {
      setError("Please enter your name or username.");
      return;
    }
    if (!email.trim() || !email.includes("@")) {
      setError("Please enter a valid work email address.");
      return;
    }
    if (!company.trim()) {
      setError("Please enter your mill or company name.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters long for enterprise security.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      const res = await registerUser({
        username: username.trim(),
        email: email.trim(),
        password,
        company: company.trim(),
        role,
      });

      if (res.success) {
        setSuccess(true);
        setTimeout(() => {
          router.push(`/login?registered=true&user=${encodeURIComponent(username.trim())}`);
        }, 1200);
      } else {
        setError(res.error || "Registration failed. Please try again.");
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Network error connecting to auth server.");
      }
    } finally {
      setLoading(false);
    }
  };

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
            Create Enterprise Account
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground">
            Register your textile mill to deploy autonomous sales, inventory, and RAG intelligence.
          </p>
        </div>

        {/* Form Card */}
        <Card className="bg-card border-border shadow-md">
          <CardContent className="pt-6">
            {success ? (
              <div className="py-8 text-center space-y-3 animate-in fade-in zoom-in-95 duration-200">
                <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 mx-auto flex items-center justify-center border border-emerald-500/20">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-foreground">Registration Successful!</h3>
                <p className="text-xs text-muted-foreground">
                  Your enterprise account has been created. Redirecting to sign in...
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-3.5">
                {error && (
                  <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-xs text-destructive flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{error}</span>
                  </div>
                )}

                {/* Username */}
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Full Name or Username</label>
                  <div className="relative">
                    <input
                      type="text"
                      required
                      placeholder="e.g. Sunil Sharma"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="w-full px-3 py-2 pl-9 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                    />
                    <User className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
                  </div>
                </div>

                {/* Work Email */}
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Corporate Work Email</label>
                  <div className="relative">
                    <input
                      type="email"
                      required
                      placeholder="e.g. sunil@sharmaprints.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full px-3 py-2 pl-9 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                    />
                    <Mail className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
                  </div>
                </div>

                {/* Company / Mill */}
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Mill / Company Name</label>
                  <div className="relative">
                    <input
                      type="text"
                      required
                      placeholder="e.g. Sharma Modern Prints Ltd."
                      value={company}
                      onChange={(e) => setCompany(e.target.value)}
                      className="w-full px-3 py-2 pl-9 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                    />
                    <Building className="w-4 h-4 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
                  </div>
                </div>

                {/* RBAC Role Selector */}
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Organization Role</label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value as UserRole)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand font-medium"
                  >
                    <option value="CEO">CEO (Executive Admin — Strategic Suite)</option>
                    <option value="Admin">Admin (System Administrator — Ops Suite)</option>
                  </select>
                </div>

                {/* Password */}
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Password (min 8 characters)</label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      placeholder="At least 8 characters"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full px-3 py-2 pr-10 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {password && (
                    <div className="h-1 w-full bg-muted rounded-full overflow-hidden mt-1">
                      <div
                        className={`h-full transition-all duration-300 ${strengthColor}`}
                        style={{ width: `${(strengthScore / 5) * 100}%` }}
                      />
                    </div>
                  )}
                </div>

                {/* Confirm Password */}
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-foreground">Confirm Password</label>
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    placeholder="Re-type your password"
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
                  disabled={loading || (!!confirmPassword && confirmPassword !== password)}
                  className="w-full font-semibold gap-2 mt-3"
                >
                  {loading ? (
                    <span>Creating Enterprise Account...</span>
                  ) : (
                    <>
                      <span>Register Account</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </Button>
              </form>
            )}
          </CardContent>

          <CardFooter className="pt-2 border-t border-border/60 justify-center">
            <p className="text-xs text-muted-foreground">
              Already have an enterprise account?{" "}
              <Link href="/login" className="text-brand font-semibold hover:underline">
                Sign in
              </Link>
            </p>
          </CardFooter>
        </Card>

        {/* Security Assurance */}
        <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
          <ShieldCheck className="w-4 h-4 text-emerald-500" />
          <span>Secure 256-bit encrypted enterprise authentication</span>
        </div>
      </div>
    </PageTransition>
  );
}
