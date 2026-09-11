"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { useAuth } from "@/components/providers/auth-provider";
import {
  DashboardPreferences,
  getDashboardPreferences,
  saveDashboardPreferences,
  getLlmProviderSetting,
  setLlmProviderSetting,
} from "@/lib/api/dashboard";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Settings,
  Sun,
  Moon,
  Laptop,
  Cpu,
  KeyRound,
  Eye,
  EyeOff,
  Bell,
  User,
  Building2,
  Save,
  CheckCircle2,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { user } = useAuth();

  // Settings State
  const [selectedTheme, setSelectedTheme] = useState<string>("system");
  const [llmProvider, setLlmProvider] = useState<"gemini" | "openai">("gemini");
  const [activeModel, setActiveModel] = useState<string>("gemini-2.5-flash");

  // API Keys (masked)
  const [geminiKey, setGeminiKey] = useState<string>("");
  const [openaiKey, setOpenaiKey] = useState<string>("");
  const [showGeminiKey, setShowGeminiKey] = useState<boolean>(false);
  const [showOpenaiKey, setShowOpenaiKey] = useState<boolean>(false);

  // Notifications
  const [emailAlerts, setEmailAlerts] = useState<boolean>(true);
  const [criticalSms, setCriticalSms] = useState<boolean>(true);
  const [dailyDigest, setDailyDigest] = useState<boolean>(true);
  const [weeklyPdf, setWeeklyPdf] = useState<boolean>(false);

  // Profile — seeded from live auth user; user can override in-form
  const [fullName, setFullName] = useState<string>("");
  const [email, setEmail] = useState<string>("");
  const [phone, setPhone] = useState<string>("");
  const [role, setRole] = useState<string>("");

  // Company — generic defaults; overridden by saved preferences on load
  const [millName, setMillName] = useState<string>("Gokul Text Print Pvt. Ltd.");
  const [gstin, setGstin] = useState<string>("");
  const [address, setAddress] = useState<string>("");
  const [capacity, setCapacity] = useState<string>("");
  const [machinery, setMachinery] = useState<string>("");

  // UI status
  const [loading, setLoading] = useState<boolean>(true);
  const [saving, setSaving] = useState<boolean>(false);
  const [saveNotice, setSaveNotice] = useState<string | null>(null);

  // Hydrate settings on mount
  useEffect(() => {
    let mounted = true;

    // Seed profile from live auth session
    if (user) {
      setFullName(user.username || "");
      setEmail(user.email || "");
      setRole(user.role || "");
    }

    async function loadData() {
      try {
        const currentUser = user?.username || "ceo";
        const [prefsRes, providerRes] = await Promise.allSettled([
          getDashboardPreferences(currentUser),
          getLlmProviderSetting(),
        ]);

        if (prefsRes.status === "fulfilled" && prefsRes.value.status === "success") {
          const p = prefsRes.value.data;
          if (p.theme) setSelectedTheme(p.theme);
          if (p.llm_provider) setLlmProvider(p.llm_provider);
          if (p.api_keys) {
            if (p.api_keys.gemini) setGeminiKey(p.api_keys.gemini);
            if (p.api_keys.openai) setOpenaiKey(p.api_keys.openai);
          }
          if (p.notifications) {
            setEmailAlerts(p.notifications.email_alerts ?? true);
            setCriticalSms(p.notifications.critical_sms ?? true);
            setDailyDigest(p.notifications.daily_digest ?? true);
            setWeeklyPdf(p.notifications.weekly_pdf ?? false);
          }
          if (p.profile) {
            if (p.profile.full_name) setFullName(p.profile.full_name);
            if (p.profile.email) setEmail(p.profile.email);
            if (p.profile.phone) setPhone(p.profile.phone);
            if (p.profile.role) setRole(p.profile.role);
          }
          if (p.company) {
            if (p.company.mill_name) setMillName(p.company.mill_name);
            if (p.company.gstin) setGstin(p.company.gstin);
            if (p.company.address) setAddress(p.company.address);
            if (p.company.printing_capacity) setCapacity(p.company.printing_capacity);
            if (p.company.active_machinery) setMachinery(p.company.active_machinery);
          }
        }

        if (providerRes.status === "fulfilled" && providerRes.value.status === "success") {
          setLlmProvider(providerRes.value.provider);
          if (providerRes.value.model) setActiveModel(providerRes.value.model);
        }
      } catch (err) {
        console.error("Failed to load settings:", err);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadData();
    return () => {
      mounted = false;
    };
  }, [user]);

  const handleThemeChange = (newTheme: string) => {
    setSelectedTheme(newTheme);
    setTheme(newTheme);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // 1. Update SQLite dashboard_preferences table
      const updatedPrefs: DashboardPreferences = {
        theme: selectedTheme,
        llm_provider: llmProvider,
        api_keys: {
          gemini: geminiKey,
          openai: openaiKey,
        },
        notifications: {
          email_alerts: emailAlerts,
          critical_sms: criticalSms,
          daily_digest: dailyDigest,
          weekly_pdf: weeklyPdf,
        },
        profile: {
          full_name: fullName,
          email,
          phone,
          role,
        },
        company: {
          mill_name: millName,
          gstin,
          address,
          printing_capacity: capacity,
          active_machinery: machinery,
        },
      };

      await Promise.all([
        saveDashboardPreferences(updatedPrefs, "ceo"),
        setLlmProviderSetting(llmProvider),
      ]);

      setSaveNotice("Settings successfully saved and synced with mill backend.");
      setTimeout(() => setSaveNotice(null), 3500);
    } catch (err) {
      console.error("Error saving settings:", err);
      setSaveNotice("Failed to save settings. Please verify backend connection.");
      setTimeout(() => setSaveNotice(null), 3500);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-64 w-full rounded-xl" />
          <Skeleton className="h-64 w-full rounded-xl" />
          <Skeleton className="h-64 w-full rounded-xl" />
          <Skeleton className="h-64 w-full rounded-xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Toast Notice */}
      {saveNotice && (
        <div className="fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl shadow-lg border text-xs font-semibold flex items-center gap-2 bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-300 backdrop-blur-md animate-in fade-in slide-in-from-bottom-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
          <span>{saveNotice}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded-xl bg-brand/10 text-brand border border-brand/20">
              <Settings className="w-5 h-5" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
                  Enterprise Settings & Configuration
                </h1>
                <Badge variant="outline" className="text-[10px] font-semibold border-brand/30 text-brand">
                  Preferences
                </Badge>
              </div>
              <p className="text-xs sm:text-sm text-muted-foreground">
                Manage factory telemetry, config-driven LLM providers, masked credentials, and executive profile fields.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            onClick={handleSave}
            disabled={saving}
            size="sm"
            className="text-xs gap-1.5 font-semibold bg-brand hover:bg-brand/90 text-brand-foreground shadow-sm h-9 px-4"
          >
            <Save className={`w-3.5 h-3.5 ${saving ? "animate-spin" : ""}`} />
            <span>{saving ? "Saving Changes..." : "Save Settings"}</span>
          </Button>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 1. Theme & Appearance */}
        <Card className="bg-card border-border shadow-sm flex flex-col">
          <CardHeader className="pb-4 border-b border-border/60">
            <div className="flex items-center gap-2">
              <Sun className="w-4 h-4 text-amber-500" />
              <CardTitle className="text-base font-bold">Theme & Appearance</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Customize interface display for bright daylight factory floor vs low-light night shifts.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-5 space-y-4 flex-1">
            <div className="grid grid-cols-3 gap-3">
              {/* Light */}
              <button
                type="button"
                onClick={() => handleThemeChange("light")}
                className={`p-3.5 rounded-xl border flex flex-col items-center text-center gap-2 transition-all ${
                  selectedTheme === "light"
                    ? "border-brand bg-brand/5 shadow-sm ring-1 ring-brand"
                    : "border-border hover:bg-muted/40"
                }`}
              >
                <div className="p-2 rounded-lg bg-amber-500/10 text-amber-600">
                  <Sun className="w-5 h-5" />
                </div>
                <div className="text-xs font-bold text-foreground">Light Mode</div>
                <span className="text-[10px] text-muted-foreground leading-tight">
                  Daylight control
                </span>
              </button>

              {/* Dark */}
              <button
                type="button"
                onClick={() => handleThemeChange("dark")}
                className={`p-3.5 rounded-xl border flex flex-col items-center text-center gap-2 transition-all ${
                  selectedTheme === "dark"
                    ? "border-brand bg-brand/5 shadow-sm ring-1 ring-brand"
                    : "border-border hover:bg-muted/40"
                }`}
              >
                <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                  <Moon className="w-5 h-5" />
                </div>
                <div className="text-xs font-bold text-foreground">Dark Mode</div>
                <span className="text-[10px] text-muted-foreground leading-tight">
                  Night shift
                </span>
              </button>

              {/* System */}
              <button
                type="button"
                onClick={() => handleThemeChange("system")}
                className={`p-3.5 rounded-xl border flex flex-col items-center text-center gap-2 transition-all ${
                  selectedTheme === "system"
                    ? "border-brand bg-brand/5 shadow-sm ring-1 ring-brand"
                    : "border-border hover:bg-muted/40"
                }`}
              >
                <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-600">
                  <Laptop className="w-5 h-5" />
                </div>
                <div className="text-xs font-bold text-foreground">System Sync</div>
                <span className="text-[10px] text-muted-foreground leading-tight">
                  OS automatic
                </span>
              </button>
            </div>
            <p className="text-[11px] text-muted-foreground pt-1">
              Active mode is automatically synced with your local workstation and persisted in your user preferences.
            </p>
          </CardContent>
        </Card>

        {/* 2. AI Provider Engine */}
        <Card className="bg-card border-border shadow-sm flex flex-col">
          <CardHeader className="pb-4 border-b border-border/60">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-brand" />
                <CardTitle className="text-base font-bold">AI Provider Engine</CardTitle>
              </div>
            </div>
            <CardDescription className="text-xs">
              Switch the underlying AI model driver between providers with automatic configuration reset.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-5 space-y-3 flex-1">
            {/* Google Gemini Card */}
            <div
              onClick={() => setLlmProvider("gemini")}
              className={`p-4 rounded-xl border cursor-pointer transition-all flex items-start justify-between gap-3 ${
                llmProvider === "gemini"
                  ? "border-brand bg-brand/5 shadow-sm ring-1 ring-brand"
                  : "border-border hover:bg-muted/30"
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-foreground">Google Gemini</span>
                  <Badge variant="secondary" className="text-[10px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                    Recommended
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Default enterprise model (<code className="font-mono text-[11px]">gemini-2.5-flash</code>). Ultra-fast sub-second latency with 1M context window for textile RAG documents.
                </p>
              </div>
              <div
                className={`w-4 h-4 rounded-full border flex items-center justify-center shrink-0 mt-1 ${
                  llmProvider === "gemini" ? "border-brand bg-brand" : "border-muted-foreground/40"
                }`}
              >
                {llmProvider === "gemini" && <div className="w-1.5 h-1.5 rounded-full bg-background" />}
              </div>
            </div>

            {/* OpenAI Card */}
            <div
              onClick={() => setLlmProvider("openai")}
              className={`p-4 rounded-xl border cursor-pointer transition-all flex items-start justify-between gap-3 ${
                llmProvider === "openai"
                  ? "border-brand bg-brand/5 shadow-sm ring-1 ring-brand"
                  : "border-border hover:bg-muted/30"
              }`}
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-foreground">OpenAI GPT-4o</span>
                  <Badge variant="secondary" className="text-[10px] font-semibold bg-muted text-muted-foreground">
                    Alternative
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Structured multi-step reasoning (<code className="font-mono text-[11px]">gpt-4o-mini</code>). High precision for autonomous agent swarm coordination and sales forecasting synthesis.
                </p>
              </div>
              <div
                className={`w-4 h-4 rounded-full border flex items-center justify-center shrink-0 mt-1 ${
                  llmProvider === "openai" ? "border-brand bg-brand" : "border-muted-foreground/40"
                }`}
              >
                {llmProvider === "openai" && <div className="w-1.5 h-1.5 rounded-full bg-background" />}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 3. API Keys Management (Masked Input) */}
        <Card className="bg-card border-border shadow-sm flex flex-col">
          <CardHeader className="pb-4 border-b border-border/60">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <KeyRound className="w-4 h-4 text-purple-500" />
                <CardTitle className="text-base font-bold">API Keys Management</CardTitle>
              </div>
              <div className="flex items-center gap-1.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                <ShieldCheck className="w-3 h-3" />
                <span>Masked & Protected</span>
              </div>
            </div>
            <CardDescription className="text-xs">
              Credentials are never displayed in full plain text and are stored securely encrypted.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-5 space-y-4 flex-1">
            {/* Gemini Key */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground flex items-center justify-between">
                <span>Google Gemini API Key</span>
                <span className="text-[11px] text-muted-foreground font-normal">
                  {geminiKey ? "Key configured" : "Uses env var default"}
                </span>
              </label>
              <div className="relative">
                <input
                  type={showGeminiKey ? "text" : "password"}
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  placeholder="AIzaSy••••••••••••••••••••••••••••"
                  className="w-full pl-3 pr-10 py-2 text-xs font-mono rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-brand"
                />
                <button
                  type="button"
                  onClick={() => setShowGeminiKey(!showGeminiKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showGeminiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* OpenAI Key */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground flex items-center justify-between">
                <span>OpenAI API Key</span>
                <span className="text-[11px] text-muted-foreground font-normal">
                  {openaiKey ? "Key configured" : "Uses env var default"}
                </span>
              </label>
              <div className="relative">
                <input
                  type={showOpenaiKey ? "text" : "password"}
                  value={openaiKey}
                  onChange={(e) => setOpenaiKey(e.target.value)}
                  placeholder="sk-proj-••••••••••••••••••••••••••••"
                  className="w-full pl-3 pr-10 py-2 text-xs font-mono rounded-lg border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-brand"
                />
                <button
                  type="button"
                  onClick={() => setShowOpenaiKey(!showOpenaiKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showOpenaiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <p className="text-[11px] text-muted-foreground pt-1">
              If left blank, the backend automatically falls back to <code className="font-mono text-[10px]">GEMINI_API_KEY</code> and <code className="font-mono text-[10px]">OPENAI_API_KEY</code> from your server environment.
            </p>
          </CardContent>
        </Card>

        {/* 4. Notification Preferences */}
        <Card className="bg-card border-border shadow-sm flex flex-col">
          <CardHeader className="pb-4 border-b border-border/60">
            <div className="flex items-center gap-2">
              <Bell className="w-4 h-4 text-sky-500" />
              <CardTitle className="text-base font-bold">Notification Preferences</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Configure alert dispatch channels and scheduled executive operational briefs.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-5 space-y-4 flex-1">
            <div className="space-y-3">
              {/* Urgent SMS */}
              <label className="flex items-start justify-between gap-3 p-3 rounded-xl border border-border/60 hover:bg-muted/30 cursor-pointer transition-colors">
                <div className="space-y-0.5">
                  <div className="text-xs font-bold text-foreground">Critical Urgent SMS Alerts</div>
                  <p className="text-[11px] text-muted-foreground leading-relaxed">
                    Immediate SMS dispatch when greige cloth breaches safety buffer (&lt; 2,000m) or rotary print line halts.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={criticalSms}
                  onChange={(e) => setCriticalSms(e.target.checked)}
                  className="mt-0.5 rounded border-border text-brand focus:ring-brand accent-brand h-4 w-4 cursor-pointer"
                />
              </label>

              {/* Supervisor Email */}
              <label className="flex items-start justify-between gap-3 p-3 rounded-xl border border-border/60 hover:bg-muted/30 cursor-pointer transition-colors">
                <div className="space-y-0.5">
                  <div className="text-xs font-bold text-foreground">Supervisor Email Alerts</div>
                  <p className="text-[11px] text-muted-foreground leading-relaxed">
                    Automated email sent to plant supervisors whenever High or Critical incidents are triggered.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={emailAlerts}
                  onChange={(e) => setEmailAlerts(e.target.checked)}
                  className="mt-0.5 rounded border-border text-brand focus:ring-brand accent-brand h-4 w-4 cursor-pointer"
                />
              </label>

              {/* Daily Morning Digest */}
              <label className="flex items-start justify-between gap-3 p-3 rounded-xl border border-border/60 hover:bg-muted/30 cursor-pointer transition-colors">
                <div className="space-y-0.5">
                  <div className="text-xs font-bold text-foreground">Daily Morning Operational Digest</div>
                  <p className="text-[11px] text-muted-foreground leading-relaxed">
                    Sent every morning at 08:00 AM IST summarizing daily sales target, meter throughput, and restock actions.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={dailyDigest}
                  onChange={(e) => setDailyDigest(e.target.checked)}
                  className="mt-0.5 rounded border-border text-brand focus:ring-brand accent-brand h-4 w-4 cursor-pointer"
                />
              </label>

              {/* Weekly PDF Report */}
              <label className="flex items-start justify-between gap-3 p-3 rounded-xl border border-border/60 hover:bg-muted/30 cursor-pointer transition-colors">
                <div className="space-y-0.5">
                  <div className="text-xs font-bold text-foreground">Weekly Executive PDF Audit</div>
                  <p className="text-[11px] text-muted-foreground leading-relaxed">
                    Deliver automated multi-section PDF executive briefing every Monday morning to executive leadership.
                  </p>
                </div>
                <input
                  type="checkbox"
                  checked={weeklyPdf}
                  onChange={(e) => setWeeklyPdf(e.target.checked)}
                  className="mt-0.5 rounded border-border text-brand focus:ring-brand accent-brand h-4 w-4 cursor-pointer"
                />
              </label>
            </div>
          </CardContent>
        </Card>

        {/* 5. User Profile Fields */}
        <Card className="bg-card border-border shadow-sm flex flex-col">
          <CardHeader className="pb-4 border-b border-border/60">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-emerald-500" />
              <CardTitle className="text-base font-bold">User Profile & RBAC Role</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Executive account profile and role credentials for autonomous agent delegation.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-5 space-y-3.5 flex-1">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-brand"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Work Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-brand"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Phone Number</label>
              <input
                type="tel"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-brand"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">RBAC Role Assignment</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-brand cursor-pointer"
              >
                <option value="CEO">CEO (Chief Executive — Full Decision Autonomy)</option>
                <option value="Plant Manager">Plant Manager (Operations & Production Control)</option>
                <option value="Dispatcher">Dispatcher (Order Allocation & Logistics)</option>
                <option value="Admin">System Admin (Infrastructure & Model Maintenance)</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* 6. Company & Mill Information */}
        <Card className="bg-card border-border shadow-sm flex flex-col">
          <CardHeader className="pb-4 border-b border-border/60">
            <div className="flex items-center gap-2">
              <Building2 className="w-4 h-4 text-brand" />
              <CardTitle className="text-base font-bold">Company & Mill Information</CardTitle>
            </div>
            <CardDescription className="text-xs">
              Registered mill entity details incorporated into generated PDF/CSV reports and dispatch invoices.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-5 space-y-3.5 flex-1">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Registered Mill Name</label>
              <input
                type="text"
                value={millName}
                onChange={(e) => setMillName(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-brand"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">GSTIN Number</label>
                <input
                  type="text"
                  value={gstin}
                  onChange={(e) => setGstin(e.target.value)}
                  className="w-full px-3 py-2 text-xs font-mono uppercase rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-brand"
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground">Daily Printing Capacity</label>
                <input
                  type="text"
                  value={capacity}
                  onChange={(e) => setCapacity(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-brand"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Factory / Plant Address</label>
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-brand"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-foreground">Active Machinery Summary</label>
              <input
                type="text"
                value={machinery}
                onChange={(e) => setMachinery(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-1 focus:ring-brand"
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
