"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  TrendingUp,
  Users,
  Zap,
  BarChart3,
  Shield,
  Trophy,
  ArrowRight,
} from "lucide-react";

const features = [
  {
    icon: TrendingUp,
    title: "AI-Powered NIL Valuations",
    description: "Proprietary model trained on 17,500+ valuations predicts NIL value with 94% accuracy",
  },
  {
    icon: Users,
    title: "Transfer Portal Intelligence",
    description: "Real-time tracking of 4,000+ portal entries with commitment predictions",
  },
  {
    icon: BarChart3,
    title: "PFF Integration",
    description: "71,000+ PFF grades and advanced metrics for comprehensive player analysis",
  },
  {
    icon: Zap,
    title: "Win Impact Calculator",
    description: "Quantify exactly how many wins a transfer adds to your roster",
  },
  {
    icon: Shield,
    title: "Risk Assessment",
    description: "Evaluate transfer risk with injury history, fit scores, and culture analysis",
  },
  {
    icon: Trophy,
    title: "AI Assistant",
    description: "Ask questions in natural language - get instant insights powered by Claude",
  },
];

const stats = [
  { value: "17,500+", label: "NIL Valuations" },
  { value: "4,000+", label: "Portal Players" },
  { value: "71,000+", label: "PFF Records" },
  { value: "94%", label: "Prediction Accuracy" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0f1a2e]">
      {/* Header */}
      <header className="border-b border-white/10">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🏈</span>
            <span className="text-xl font-bold text-white">Portal IQ</span>
          </div>
          <div className="flex items-center gap-4">
            <a href="https://portal-iq.streamlit.app">
              <Button variant="ghost" className="text-white hover:text-white/80">
                Sign In
              </Button>
            </a>
            <Link href="/pricing">
              <Button className="bg-[#D4AF37] text-black hover:bg-[#D4AF37]/90">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="mx-auto max-w-4xl">
          <div className="mb-6 inline-block rounded-full bg-[#D4AF37]/20 px-4 py-2 text-sm text-[#D4AF37]">
            Trusted by 50+ College Programs
          </div>
          <h1 className="mb-6 text-5xl font-bold tracking-tight text-white md:text-6xl">
            Win the Transfer Portal with{" "}
            <span className="text-[#D4AF37]">AI-Powered Intelligence</span>
          </h1>
          <p className="mb-8 text-xl text-gray-400">
            The most comprehensive NIL valuation and transfer portal analytics platform
            for college football. Make data-driven decisions that win championships.
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link href="/pricing">
              <Button size="lg" className="bg-[#D4AF37] text-black hover:bg-[#D4AF37]/90">
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <a href="https://portal-iq.streamlit.app">
              <Button size="lg" variant="outline" className="border-white/20 text-white hover:bg-white/10">
                Sign In
              </Button>
            </a>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-y border-white/10 bg-[#1a2744]">
        <div className="container mx-auto grid grid-cols-2 gap-8 px-4 py-12 md:grid-cols-4">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-3xl font-bold text-[#D4AF37] md:text-4xl">
                {stat.value}
              </div>
              <div className="mt-1 text-sm text-gray-400">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="container mx-auto px-4 py-20">
        <div className="mb-12 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white md:text-4xl">
            Everything You Need to Dominate Recruiting
          </h2>
          <p className="text-lg text-gray-400">
            Built by former college coaches and data scientists
          </p>
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <Card key={feature.title} className="border-white/10 bg-[#1a2744]">
              <CardContent className="p-6">
                <feature.icon className="mb-4 h-10 w-10 text-[#D4AF37]" />
                <h3 className="mb-2 text-lg font-semibold text-white">
                  {feature.title}
                </h3>
                <p className="text-gray-400">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-white/10 bg-[#1a2744]">
        <div className="container mx-auto px-4 py-20 text-center">
          <h2 className="mb-4 text-3xl font-bold text-white md:text-4xl">
            Ready to Get Started?
          </h2>
          <p className="mb-8 text-lg text-gray-400">
            Join the programs already using Portal IQ to win the transfer portal
          </p>
          <Link href="/pricing">
            <Button size="lg" className="bg-[#D4AF37] text-black hover:bg-[#D4AF37]/90">
              View Pricing
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-[#0f1a2e]">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col items-center justify-between gap-4 md:flex-row">
            <div className="flex items-center gap-2">
              <span className="text-xl">🏈</span>
              <span className="font-bold text-white">Portal IQ</span>
              <span className="text-gray-500">by Elite Sports Solutions</span>
            </div>
            <div className="flex gap-6 text-sm text-gray-400">
              <Link href="/privacy" className="hover:text-white">Privacy</Link>
              <Link href="/terms" className="hover:text-white">Terms</Link>
              <a href="mailto:support@portaliq.ai" className="hover:text-white">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
