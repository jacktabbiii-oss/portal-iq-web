"use client";

import Link from "next/link";
import Image from "next/image";
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
  CheckCircle2,
  Target,
  Brain,
  DollarSign,
  Star,
  ChevronRight,
  Quote,
  Flame,
  Medal,
  Crosshair,
} from "lucide-react";

const stats = [
  { value: "21,200+", label: "NIL Valuations", description: "Live data updated daily" },
  { value: "4,500+", label: "Portal Players", description: "2025-26 cycle tracking" },
  { value: "134", label: "FBS Programs", description: "Complete coverage" },
  { value: "24/7", label: "Live Updates", description: "Never miss a move" },
];

const features = [
  {
    icon: DollarSign,
    title: "NIL Valuations",
    description: "Know exactly what a player is worth before you make an offer. Our AI analyzes performance, social following, market size, and 40+ factors.",
    highlight: "AI-powered predictions",
  },
  {
    icon: Target,
    title: "Portal Tracker",
    description: "Real-time alerts when players enter the portal. Filter by position, conference, star rating, and more. Never miss a prospect.",
    highlight: "4,500+ players tracked",
  },
  {
    icon: BarChart3,
    title: "Advanced Analytics",
    description: "Deep performance metrics, historical stats, and trend analysis to evaluate players beyond the highlight reel.",
    highlight: "Data-driven scouting",
  },
  {
    icon: Zap,
    title: "Win Impact Calculator",
    description: "Quantify exactly how many wins a transfer adds to your roster based on historical transfer outcomes.",
    highlight: "Project roster impact",
  },
  {
    icon: Shield,
    title: "Risk Assessment",
    description: "Evaluate injury history, academic standing, and fit scores. Make informed decisions, not gut calls.",
    highlight: "Reduce transfer busts",
  },
  {
    icon: Brain,
    title: "AI Assistant",
    description: "Ask questions in plain English: \"Who are the best available QBs under $500K NIL?\" Get instant answers.",
    highlight: "Powered by AI",
  },
];

const useCases = [
  {
    title: "Coaches & Staff",
    description: "Build championship rosters with data-driven transfer decisions",
    benefits: ["Identify undervalued talent", "Compare players objectively", "Project roster fit"],
    icon: Trophy,
  },
  {
    title: "NIL Collectives",
    description: "Maximize ROI on every NIL dollar you invest",
    benefits: ["Fair market valuations", "Track deal performance", "Avoid overpaying"],
    icon: DollarSign,
  },
  {
    title: "Agents & Advisors",
    description: "Negotiate better deals with market intelligence",
    benefits: ["Comparable player data", "Market rate benchmarks", "Value projections"],
    icon: Users,
  },
  {
    title: "Media & Analysts",
    description: "Break stories with exclusive data and insights",
    benefits: ["Portal movement alerts", "NIL deal analysis", "Advanced statistics"],
    icon: BarChart3,
  },
];

const testimonials = [
  {
    quote: "Finally, a platform that brings real data to NIL discussions. This is exactly what the industry needed.",
    author: "Director of Operations",
    org: "FBS Program",
    rating: 5,
  },
  {
    quote: "The AI-powered valuations give us confidence when making offers. No more guessing games.",
    author: "Collective Manager",
    org: "Power 4 School",
    rating: 5,
  },
  {
    quote: "Having all the portal data in one place saves hours of research. Essential tool for recruiting season.",
    author: "Recruiting Analyst",
    org: "Group of 5 Program",
    rating: 5,
  },
];

const comparisonPoints = [
  { feature: "Real-time portal alerts", us: true, them: false },
  { feature: "AI-powered NIL valuations", us: true, them: false },
  { feature: "Win impact projections", us: true, them: false },
  { feature: "Natural language AI queries", us: true, them: false },
  { feature: "Player comparison tools", us: true, them: true },
  { feature: "Advanced performance metrics", us: true, them: false },
  { feature: "Export to CSV/PDF", us: true, them: true },
];

const faqs = [
  {
    q: "How accurate are the NIL valuations?",
    a: "Our AI model analyzes 40+ factors including performance, social following, and market size to provide data-driven valuations that help you negotiate smarter.",
  },
  {
    q: "Where does the data come from?",
    a: "We aggregate data from multiple public sources including recruiting databases, social media, and historical transfer outcomes. Data is refreshed daily during portal season.",
  },
  {
    q: "Is there a free trial?",
    a: "Yes! Every subscription includes a 14-day free trial with full access to all features. No credit card required to start.",
  },
  {
    q: "Can I cancel anytime?",
    a: "Absolutely. Cancel your subscription at any time with no penalties or hidden fees.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0f1a2e]">
      {/* Header */}
      <header className="fixed top-0 z-50 w-full border-b border-white/10 bg-[#0f1a2e]/95 backdrop-blur">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-3">
            <Image
              src="/logo.png"
              alt="Portal IQ"
              width={36}
              height={36}
              className="object-contain"
            />
            <span className="text-xl font-bold text-white">PORTAL IQ</span>
          </Link>
          <nav className="hidden items-center gap-8 md:flex">
            <a href="#features" className="text-sm text-gray-400 hover:text-white transition">Features</a>
            <a href="#how-it-works" className="text-sm text-gray-400 hover:text-white transition">How It Works</a>
            <a href="#testimonials" className="text-sm text-gray-400 hover:text-white transition">Testimonials</a>
            <Link href="/pricing" className="text-sm text-gray-400 hover:text-white transition">Pricing</Link>
          </nav>
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost" className="text-white hover:text-white/80">
                Sign In
              </Button>
            </Link>
            <Link href="/pricing">
              <Button className="bg-[#D4AF37] text-black hover:bg-[#D4AF37]/90">
                Start Free Trial
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden pt-32 pb-20">
        {/* Background with field lines effect */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#D4AF37]/5 to-transparent" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-[#D4AF37]/5 rounded-full blur-3xl" />
        {/* Yard line accents */}
        <div className="absolute left-0 top-1/4 w-24 h-1 bg-gradient-to-r from-[#D4AF37]/20 to-transparent" />
        <div className="absolute right-0 top-1/3 w-32 h-1 bg-gradient-to-l from-[#D4AF37]/20 to-transparent" />
        <div className="absolute left-0 bottom-1/4 w-16 h-1 bg-gradient-to-r from-[#D4AF37]/20 to-transparent" />

        <div className="container relative mx-auto px-4 text-center">
          <div className="mx-auto max-w-4xl">
            {/* Trust badge */}
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-[#D4AF37]/30 bg-[#D4AF37]/10 px-4 py-2">
              <Trophy className="h-4 w-4 text-[#D4AF37]" />
              <span className="text-sm font-medium text-[#D4AF37]">Trusted by 50+ College Programs</span>
            </div>

            <h1 className="mb-6 text-5xl font-black tracking-tight text-white md:text-7xl uppercase">
              Dominate
              <br />
              <span className="text-[#D4AF37]">The Portal</span>
            </h1>

            <p className="mb-8 text-xl text-gray-400 md:text-2xl max-w-3xl mx-auto">
              The <span className="text-white font-semibold">AI-powered intelligence platform</span> that gives you
              the edge in NIL valuations, transfer tracking, and roster building.
            </p>

            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row mb-8">
              <Link href="/pricing">
                <Button size="lg" className="bg-[#D4AF37] text-black hover:bg-[#D4AF37]/90 text-lg px-8 py-6 h-auto font-bold uppercase tracking-wide">
                  Start Free Trial
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline" className="border-white/20 text-white hover:bg-white/10 text-lg px-8 py-6 h-auto font-semibold">
                  Sign In
                </Button>
              </Link>
            </div>

            <p className="text-sm text-gray-500">
              14-day free trial • No credit card required • Cancel anytime
            </p>
          </div>
        </div>
      </section>

      {/* Stats - Scoreboard Style */}
      <section className="border-y-4 border-[#D4AF37]/30 bg-[#1a2744] relative">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAwIDEwIEwgNDAgMTAgTSAxMCAwIEwgMTAgNDAgTSAwIDIwIEwgNDAgMjAgTSAyMCAwIEwgMjAgNDAgTSAwIDMwIEwgNDAgMzAgTSAzMCAwIEwgMzAgNDAiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzMzMyIgc3Ryb2tlLXdpZHRoPSIwLjUiLz48L3BhdHRlcm4+PC9kZWZzPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9InVybCgjZ3JpZCkiLz48L3N2Zz4=')] opacity-10" />
        <div className="container relative mx-auto grid grid-cols-2 gap-8 px-4 py-16 md:grid-cols-4">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-5xl font-black text-[#D4AF37] md:text-6xl tracking-tight" style={{ fontFamily: 'system-ui' }}>
                {stat.value}
              </div>
              <div className="mt-2 text-lg font-bold text-white uppercase tracking-wider">{stat.label}</div>
              <div className="mt-1 text-sm text-gray-500">{stat.description}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Problem Section */}
      <section className="container mx-auto px-4 py-24">
        <div className="mx-auto max-w-4xl text-center">
          <div className="inline-flex items-center gap-2 mb-6 text-red-400 uppercase tracking-wider text-sm font-bold">
            <Flame className="h-4 w-4" />
            The Competition Is Fierce
          </div>
          <h2 className="mb-6 text-3xl font-black text-white md:text-5xl uppercase">
            Don&apos;t Get Left Behind
          </h2>
          <p className="text-xl text-gray-400 mb-12">
            While you&apos;re crunching spreadsheets, your rivals are closing deals with AI-powered intel.
          </p>

          <div className="grid gap-6 md:grid-cols-3 text-left">
            <Card className="border-red-500/30 bg-gradient-to-br from-red-500/10 to-transparent">
              <CardContent className="p-6">
                <div className="text-red-400 text-5xl font-black mb-2">68%</div>
                <p className="text-gray-400">of transfers don&apos;t meet expectations at their new school</p>
              </CardContent>
            </Card>
            <Card className="border-red-500/30 bg-gradient-to-br from-red-500/10 to-transparent">
              <CardContent className="p-6">
                <div className="text-red-400 text-5xl font-black mb-2">$2.1M</div>
                <p className="text-gray-400">average NIL overpayment per program annually</p>
              </CardContent>
            </Card>
            <Card className="border-red-500/30 bg-gradient-to-br from-red-500/10 to-transparent">
              <CardContent className="p-6">
                <div className="text-red-400 text-5xl font-black mb-2">72hrs</div>
                <p className="text-gray-400">average time to evaluate a portal entry manually</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="container mx-auto px-4 py-24">
        <div className="mb-16 text-center">
          <div className="inline-flex items-center gap-2 mb-4 text-[#D4AF37] uppercase tracking-wider text-sm font-bold">
            <Medal className="h-4 w-4" />
            Your Competitive Edge
          </div>
          <h2 className="mb-4 text-3xl font-black text-white md:text-5xl uppercase">
            Built to Win
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Every tool you need to dominate recruiting and roster building.
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <Card key={feature.title} className="border-white/10 bg-[#1a2744] hover:border-[#D4AF37]/50 transition-colors group">
              <CardContent className="p-8">
                <div className="mb-6 inline-flex h-14 w-14 items-center justify-center rounded-xl bg-[#D4AF37]/10 group-hover:bg-[#D4AF37]/20 transition-colors">
                  <feature.icon className="h-7 w-7 text-[#D4AF37]" />
                </div>
                <h3 className="mb-3 text-xl font-semibold text-white">
                  {feature.title}
                </h3>
                <p className="text-gray-400 mb-4">{feature.description}</p>
                <div className="inline-flex items-center text-sm font-medium text-[#D4AF37]">
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                  {feature.highlight}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="border-y-4 border-[#D4AF37]/30 bg-[#1a2744] py-24">
        <div className="container mx-auto px-4">
          <div className="mb-16 text-center">
            <div className="inline-flex items-center gap-2 mb-4 text-[#D4AF37] uppercase tracking-wider text-sm font-bold">
              <Crosshair className="h-4 w-4" />
              Your Game Plan
            </div>
            <h2 className="mb-4 text-3xl font-black text-white md:text-5xl uppercase">
              Scout. Evaluate. Sign.
            </h2>
            <p className="text-xl text-gray-400">
              From portal entry to commitment in four simple steps
            </p>
          </div>

          <div className="mx-auto max-w-5xl">
            <div className="grid gap-8 md:grid-cols-4">
              {[
                { step: "1", title: "Scout", desc: "Get instant alerts when players enter the portal matching your needs" },
                { step: "2", title: "Evaluate", desc: "AI analyzes stats, NIL value, and fit score in seconds" },
                { step: "3", title: "Compare", desc: "Stack candidates side-by-side with objective data" },
                { step: "4", title: "Execute", desc: "Make confident offers backed by data, not guesswork" },
              ].map((item, i) => (
                <div key={item.step} className="relative text-center">
                  <div className="mb-4 mx-auto h-16 w-16 rounded-full bg-[#D4AF37] flex items-center justify-center text-2xl font-black text-black">
                    {item.step}
                  </div>
                  {i < 3 && (
                    <ChevronRight className="absolute top-8 -right-4 h-6 w-6 text-[#D4AF37]/50 hidden md:block" />
                  )}
                  <h3 className="mb-2 text-lg font-bold text-white uppercase">{item.title}</h3>
                  <p className="text-sm text-gray-400">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="container mx-auto px-4 py-24">
        <div className="mb-16 text-center">
          <div className="inline-flex items-center gap-2 mb-4 text-[#D4AF37] uppercase tracking-wider text-sm font-bold">
            <Users className="h-4 w-4" />
            Built For Winners
          </div>
          <h2 className="mb-4 text-3xl font-black text-white md:text-5xl uppercase">
            Your Role. Your Edge.
          </h2>
          <p className="text-xl text-gray-400">
            Portal IQ adapts to how you compete
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          {useCases.map((useCase) => (
            <Card key={useCase.title} className="border-white/10 bg-[#1a2744]">
              <CardContent className="p-6">
                <useCase.icon className="mb-4 h-10 w-10 text-[#D4AF37]" />
                <h3 className="mb-2 text-lg font-semibold text-white">{useCase.title}</h3>
                <p className="text-sm text-gray-400 mb-4">{useCase.description}</p>
                <ul className="space-y-2">
                  {useCase.benefits.map((benefit) => (
                    <li key={benefit} className="flex items-center text-sm text-gray-300">
                      <CheckCircle2 className="mr-2 h-4 w-4 text-[#22C55E]" />
                      {benefit}
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="border-y border-white/10 bg-[#1a2744] py-24">
        <div className="container mx-auto px-4">
          <div className="mb-16 text-center">
            <div className="inline-flex items-center gap-2 mb-4 text-[#D4AF37] uppercase tracking-wider text-sm font-bold">
              <Star className="h-4 w-4 fill-[#D4AF37]" />
              From The Field
            </div>
            <h2 className="mb-4 text-3xl font-black text-white md:text-5xl uppercase">
              What Users Say
            </h2>
          </div>

          <div className="grid gap-8 md:grid-cols-3">
            {testimonials.map((testimonial, i) => (
              <Card key={i} className="border-white/10 bg-[#0f1a2e]">
                <CardContent className="p-8">
                  <div className="flex mb-4">
                    {[...Array(testimonial.rating)].map((_, j) => (
                      <Star key={j} className="h-5 w-5 fill-[#D4AF37] text-[#D4AF37]" />
                    ))}
                  </div>
                  <Quote className="h-8 w-8 text-[#D4AF37]/30 mb-4" />
                  <p className="text-gray-300 mb-6 italic">&quot;{testimonial.quote}&quot;</p>
                  <div>
                    <div className="font-medium text-white">{testimonial.author}</div>
                    <div className="text-sm text-gray-500">{testimonial.org}</div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison */}
      <section className="container mx-auto px-4 py-24">
        <div className="mb-16 text-center">
          <div className="inline-flex items-center gap-2 mb-4 text-[#D4AF37] uppercase tracking-wider text-sm font-bold">
            <Zap className="h-4 w-4" />
            Level Up
          </div>
          <h2 className="mb-4 text-3xl font-black text-white md:text-5xl uppercase">
            Ditch The Spreadsheets
          </h2>
        </div>

        <div className="mx-auto max-w-3xl">
          <Card className="border-white/10 bg-[#1a2744] overflow-hidden">
            <div className="grid grid-cols-3 border-b border-white/10 bg-[#0f1a2e] p-4">
              <div className="text-gray-400">Feature</div>
              <div className="text-center text-[#D4AF37] font-semibold">Portal IQ</div>
              <div className="text-center text-gray-500">Spreadsheets</div>
            </div>
            {comparisonPoints.map((point, i) => (
              <div key={i} className="grid grid-cols-3 border-b border-white/10 p-4 last:border-0">
                <div className="text-gray-300">{point.feature}</div>
                <div className="text-center">
                  {point.us ? (
                    <CheckCircle2 className="inline h-5 w-5 text-[#22C55E]" />
                  ) : (
                    <span className="text-gray-600">—</span>
                  )}
                </div>
                <div className="text-center">
                  {point.them ? (
                    <CheckCircle2 className="inline h-5 w-5 text-gray-500" />
                  ) : (
                    <span className="text-gray-600">—</span>
                  )}
                </div>
              </div>
            ))}
          </Card>
        </div>
      </section>

      {/* FAQ */}
      <section className="border-t border-white/10 bg-[#1a2744] py-24">
        <div className="container mx-auto px-4">
          <div className="mb-16 text-center">
            <h2 className="mb-4 text-3xl font-bold text-white md:text-4xl">
              Frequently Asked Questions
            </h2>
          </div>

          <div className="mx-auto max-w-3xl space-y-6">
            {faqs.map((faq, i) => (
              <Card key={i} className="border-white/10 bg-[#0f1a2e]">
                <CardContent className="p-6">
                  <h3 className="mb-2 text-lg font-semibold text-white">{faq.q}</h3>
                  <p className="text-gray-400">{faq.a}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="relative overflow-hidden py-24">
        <div className="absolute inset-0 bg-gradient-to-t from-[#D4AF37]/10 to-transparent" />
        {/* Field accent lines */}
        <div className="absolute left-0 top-1/3 w-32 h-1 bg-gradient-to-r from-[#D4AF37]/30 to-transparent" />
        <div className="absolute right-0 top-1/2 w-24 h-1 bg-gradient-to-l from-[#D4AF37]/30 to-transparent" />
        <div className="container relative mx-auto px-4 text-center">
          <h2 className="mb-4 text-4xl font-black text-white md:text-6xl uppercase">
            Ready to Dominate?
          </h2>
          <p className="mb-8 text-xl text-gray-400 max-w-2xl mx-auto">
            Get the edge you need to build a championship roster.
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link href="/pricing">
              <Button size="lg" className="bg-[#D4AF37] text-black hover:bg-[#D4AF37]/90 text-lg px-8 py-6 h-auto font-bold uppercase tracking-wide">
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
          <p className="mt-6 text-sm text-gray-500">
            14-day free trial • No credit card required • Cancel anytime
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 bg-[#0f1a2e]">
        <div className="container mx-auto px-4 py-12">
          <div className="grid gap-8 md:grid-cols-4 mb-8">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <Image
                  src="/logo.png"
                  alt="Portal IQ"
                  width={48}
                  height={48}
                  className="object-contain"
                />
                <span className="text-xl font-bold text-white">PORTAL IQ</span>
              </div>
              <p className="text-sm text-gray-500">
                AI-powered transfer portal intelligence for college football.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#features" className="hover:text-white transition">Features</a></li>
                <li><Link href="/pricing" className="hover:text-white transition">Pricing</Link></li>
                <li><a href="#testimonials" className="hover:text-white transition">Testimonials</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="mailto:support@portaliq.ai" className="hover:text-white transition">Contact</a></li>
                <li><Link href="/privacy" className="hover:text-white transition">Privacy Policy</Link></li>
                <li><Link href="/terms" className="hover:text-white transition">Terms of Service</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Get Started</h4>
              <Link href="/pricing">
                <Button className="w-full bg-[#D4AF37] text-black hover:bg-[#D4AF37]/90">
                  Start Free Trial
                </Button>
              </Link>
            </div>
          </div>
          <div className="border-t border-white/10 pt-8 flex flex-col items-center justify-between gap-4 md:flex-row">
            <p className="text-sm text-gray-500">
              © 2026 Portal IQ by Elite Sports Solutions. All rights reserved.
            </p>
            <div className="flex gap-6 text-sm text-gray-500">
              <a href="https://twitter.com/portaliq" className="hover:text-white transition">Twitter</a>
              <a href="https://linkedin.com/company/portaliq" className="hover:text-white transition">LinkedIn</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
