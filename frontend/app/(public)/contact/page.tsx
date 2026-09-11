"use client";

import * as React from "react";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge, PriorityBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PageTransition } from "@/components/ui/page-transition";
import {
  Mail,
  Phone,
  MapPin,
  Clock,
  ShieldCheck,
  Send,
  CheckCircle2,
  Sparkles,
  ArrowRight,
} from "lucide-react";

export default function ContactPage() {
  const [formData, setFormData] = React.useState({
    fullName: "",
    email: "",
    company: "",
    volume: "1m-5m",
    interest: "swarm",
    message: "",
  });

  const [submitted, setSubmitted] = React.useState(false);
  const [loading, setLoading] = React.useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Simulate brief client-side network submission
    setTimeout(() => {
      setLoading(false);
      setSubmitted(true);
    }, 600);
  };

  return (
    <PageTransition className="py-12 lg:py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        {/* Header */}
        <div className="max-w-3xl space-y-4">
          <Badge variant="outline" className="text-xs font-semibold px-3 py-1 text-brand border-brand/30">
            Factory Assessment & Technical Inquiry
          </Badge>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-foreground leading-tight">
            Schedule a Custom Textile Mill Assessment
          </h1>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Speak directly with our industrial textile AI specialists to evaluate how the 4-layer
            autonomous platform can reduce deadstock and improve batch repeatability in your mill.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Contact & Demo Form */}
          <div className="lg:col-span-7">
            <Card className="bg-card border-border shadow-md">
              <CardHeader className="pb-4 border-b border-border/70">
                <CardTitle className="text-xl font-bold">Mill Assessment Request</CardTitle>
                <CardDescription className="text-xs text-muted-foreground">
                  Fill in your factory details below. In demo mode, submissions are processed locally.
                </CardDescription>
              </CardHeader>

              <CardContent className="pt-6">
                {submitted ? (
                  <div className="py-10 text-center space-y-4 animate-in fade-in zoom-in-95 duration-200">
                    <div className="w-14 h-14 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 mx-auto flex items-center justify-center border border-emerald-500/20">
                      <CheckCircle2 className="w-8 h-8" />
                    </div>
                    <div className="space-y-1.5">
                      <h3 className="text-xl font-bold text-foreground">
                        Assessment Request Received!
                      </h3>
                      <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                        Thank you, <strong>{formData.fullName || "Partner"}</strong>. Our industrial
                        engineering desk has queued a simulation profile for{" "}
                        <strong>{formData.company || "your mill"}</strong>.
                      </p>
                    </div>

                    <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
                      <Link href="/dashboard">
                        <Button className="gap-2 font-semibold">
                          <span>Explore Live Executive Dashboard</span>
                          <ArrowRight className="w-4 h-4" />
                        </Button>
                      </Link>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setSubmitted(false);
                          setFormData({
                            fullName: "",
                            email: "",
                            company: "",
                            volume: "1m-5m",
                            interest: "swarm",
                            message: "",
                          });
                        }}
                      >
                        Submit Another Inquiry
                      </Button>
                    </div>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {/* Name */}
                      <div className="space-y-1.5">
                        <label className="text-xs font-semibold text-foreground">
                          Full Name <span className="text-rose-500">*</span>
                        </label>
                        <input
                          type="text"
                          required
                          placeholder="e.g. Ramesh Patel"
                          value={formData.fullName}
                          onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                          className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                        />
                      </div>

                      {/* Email */}
                      <div className="space-y-1.5">
                        <label className="text-xs font-semibold text-foreground">
                          Work Email <span className="text-rose-500">*</span>
                        </label>
                        <input
                          type="email"
                          required
                          placeholder="e.g. ramesh@textilemill.com"
                          value={formData.email}
                          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                          className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      {/* Mill Name */}
                      <div className="space-y-1.5">
                        <label className="text-xs font-semibold text-foreground">
                          Mill / Company Name <span className="text-rose-500">*</span>
                        </label>
                        <input
                          type="text"
                          required
                          placeholder="e.g. Surat Supreme Fabrics Ltd."
                          value={formData.company}
                          onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                          className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                        />
                      </div>

                      {/* Monthly Output */}
                      <div className="space-y-1.5">
                        <label className="text-xs font-semibold text-foreground">
                          Monthly Output Volume
                        </label>
                        <select
                          value={formData.volume}
                          onChange={(e) => setFormData({ ...formData, volume: e.target.value })}
                          className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                        >
                          <option value="under-1m">&lt; 1 Million Meters / Month</option>
                          <option value="1m-5m">1M – 5M Meters / Month</option>
                          <option value="5m-15m">5M – 15M Meters / Month</option>
                          <option value="over-15m">&gt; 15 Million Meters (Enterprise)</option>
                        </select>
                      </div>
                    </div>

                    {/* Primary Interest */}
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-foreground">
                        Primary Optimization Focus
                      </label>
                      <select
                        value={formData.interest}
                        onChange={(e) => setFormData({ ...formData, interest: e.target.value })}
                        className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                      >
                        <option value="swarm">Autonomous Operational Copilot</option>
                        <option value="inventory">Grey Cloth & Chemical Dye Buffer Optimization</option>
                        <option value="sales">Sales Demand & Seasonal Festive Forecasting</option>
                        <option value="rag">Color Kitchen Formula & Recipe Assistant</option>
                        <option value="full">Complete Turnkey Mill Modernization</option>
                      </select>
                    </div>

                    {/* Message */}
                    <div className="space-y-1.5">
                      <label className="text-xs font-semibold text-foreground">
                        Additional Machinery or Workflow Details
                      </label>
                      <textarea
                        rows={4}
                        placeholder="Tell us about your print lines (e.g. 12-color rotary screen, high-speed digital reactive, reactive vs pigment ratio)..."
                        value={formData.message}
                        onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                        className="w-full px-3 py-2 text-sm rounded-lg border border-border bg-background text-foreground focus:outline-hidden focus:ring-2 focus:ring-brand"
                      />
                    </div>

                    <Button
                      type="submit"
                      disabled={loading}
                      size="lg"
                      className="w-full font-semibold gap-2"
                    >
                      {loading ? (
                        <span>Processing Simulation...</span>
                      ) : (
                        <>
                          <Send className="w-4 h-4" />
                          <span>Submit Assessment Request</span>
                        </>
                      )}
                    </Button>
                  </form>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Contact Cards & Hubs */}
          <div className="lg:col-span-5 space-y-6">
            {/* Quick Contact Cards */}
            <Card className="bg-card border-border shadow-xs">
              <CardHeader className="pb-3">
                <CardTitle className="text-base font-bold">Direct Mill Communications</CardTitle>
                <CardDescription className="text-xs">
                  Available Monday through Saturday, 09:00 to 19:00 IST
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/40 border border-border/60">
                  <Mail className="w-4 h-4 text-brand shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-foreground text-xs block">
                      Industrial Solutions Desk:
                    </span>
                    <span className="text-xs font-mono text-muted-foreground">
                      enterprise@gokultextprint.internal
                    </span>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/40 border border-border/60">
                  <Phone className="w-4 h-4 text-brand shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-foreground text-xs block">
                      Direct Mill Hotline:
                    </span>
                    <span className="text-xs font-mono text-muted-foreground">
                      +91 (261) 289-4820 (Surat Hub)
                    </span>
                  </div>
                </div>

                <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/40 border border-border/60">
                  <Clock className="w-4 h-4 text-brand shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-foreground text-xs block">
                      SLA Response Guarantee:
                    </span>
                    <span className="text-xs text-muted-foreground">
                      Under 4 business hours for technical mill assessments
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Production Hub Address */}
            <Card className="bg-card border-border shadow-xs">
              <CardHeader className="pb-2">
                <div className="flex items-center gap-2 text-brand font-bold text-sm">
                  <MapPin className="w-4 h-4" />
                  <span>Surat Mill Complex</span>
                </div>
              </CardHeader>
              <CardContent className="text-xs text-muted-foreground leading-relaxed">
                Plots 48–52, GIDC Industrial Estate, Sachin, Surat, Gujarat 394230, India.
                Equipped with visitor demonstration room and live edge telemetry terminal.
              </CardContent>
            </Card>

            {/* Trust Assurance */}
            <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-800 dark:text-emerald-300 flex items-start gap-2.5">
              <ShieldCheck className="w-4 h-4 shrink-0 mt-0.5" />
              <span>
                All mill inquiries are strictly protected under mutual confidentiality. Proprietary
                color formulas and client lists remain your exclusive property.
              </span>
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
}
