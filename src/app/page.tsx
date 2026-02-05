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
  CheckCircle2,
  Target,
  Brain,
  Clock,
  DollarSign,
  Star,
  ChevronRight,
  Play,
  Quote,
} from "lucide-react";

const stats = [
  { value: "17,500+", label: "NIL Valuations", description: "Continuously updated" },
  { value: "4,000+", label: "Portal Players", description: "Real-time tracking" },
  { value: "71,000+", label: "PFF Records", description: "Advanced metrics" },
  { value: "94%", label: "Accuracy", description: "Valuation predictions" },
];

const features = [
  {
    icon: DollarSign,
    title: "NIL Valuations",
    description: "Know exactly what a player is worth before you make an offer. Our AI model analyzes performance, social following, market size, and 40+ other factors.",
    highlight: "94% prediction accuracy",
  },
  {
    icon: Target,
    title: "Transfer Portal Tracker",
    description: "Real-time alerts when players enter the portal. Filter by position, conference, star rating, and more. Never miss a prospect again.",
    highlight: "4,000+ players tracked",
  },
  {
    icon: BarChart3,
    title: "PFF Grade Integration",
    description: "Access 71,000+ PFF grades and advanced metrics. See passing charts, run blocking grades, coverage stats, and more.",
    highlight: "Deep performance data",
  },
  {
    icon: Zap,
    title: "Win Impact Calculator",
    description: "Quantify exactly how many wins a transfer adds to your roster. Based on historical data from 500+ successful transfers.",
    highlight: "Data-driven decisions",
  },
  {
    icon: Shield,
    title: "Risk Assessment",
    description: "Evaluate injury history, academic standing, culture fit, and character concerns. Make informed decisions, not gut calls.",
    highlight: "Reduce transfer busts",
  },
  {
    icon: Brain,
    title: "AI Assistant",
    description: "Ask questions in plain English: \"Who are the best available QBs under $500K NIL?\" Get instant, data-backed answers.",
    highlight: "Powered by Claude AI",
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
    quote: "Portal IQ completely changed how we approach the transfer portal. We signed three impact players last cycle that other programs overlooked.",
    author: "Director of Player Personnel",
    org: "Power 4 Program",
    rating: 5,
  },
  {
    quote: "The NIL valuations are scary accurate. We've saved over $200K by knowing the fair market value before negotiations.",
    author: "NIL Collective Director",
    org: "SEC School",
    rating: 5,
  },
  {
    quote: "I can't imagine going back to spreadsheets. The AI assistant alone saves me 10+ hours per week during portal season.",
    author: "Recruiting Coordinator",
    org: "Big Ten Program",
    rating: 5,
  },
];

const comparisonPoints = [
  { feature: "Real-time portal alerts", us: true, them: false },
  { feature: "AI-powered NIL valuations", us: true, them: false },
  { feature: "PFF grade integration", us: true, them: false },
  { feature: "Win impact projections", us: true, them: false },
  { feature: "Natural language AI queries", us: true, them: false },
  { feature: "Player comparison tools", us: true, them: true },
  { feature: "Export to CSV/PDF", us: true, them: true },
];

const faqs = [
  {
    q: "How accurate are the NIL valuations?",
    a: "Our model achieves 94% accuracy when compared to actual NIL deal values. We continuously train on new data to improve predictions.",
  },
  {
    q: "Where does the data come from?",
    a: "We aggregate data from PFF, On3, 247Sports, ESPN, and proprietary sources. All data is refreshed daily during portal season.",
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
          <div className="flex items-center gap-2">
            <span className="text-2xl">🏈</span>
            <span className="text-xl font-bold text-white">Portal IQ</span>
          </div>
          <nav className="hidden items-center gap-8 md:flex">
            <a href="#features" className="text-sm text-gray-400 hover:text-white transition">Features</a>
            <a href="#how-it-works" className="text-sm text-gray-400 hover:text-white transition">How It Works</a>
            <a href="#testimonials" className="text-sm text-gray-400 hover:text-white transition">Testimonials</a>
            <Link href="/pricing" className="text-sm text-gray-400 hover:text-white transition">Pricing</Link>
          </nav>
          <div className="flex items-center gap-4">
            <a href="https://portal-iq.streamlit.app">
              <Button variant="ghost" className="text-white hover:text-white/80">
                Sign In
              </Button>
            </a>
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
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#D4AF37]/5 to-transparent" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-[#D4AF37]/5 rounded-full blur-3xl" />

        <div className="container relative mx-auto px-4 text-center">
          <div className="mx-auto max-w-4xl">
            {/* Trust badge */}
            <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-[#D4AF37]/30 bg-[#D4AF37]/10 px-4 py-2">
              <div className="flex -space-x-2">
                {[1,2,3,4].map(i => (
                  <div key={i} className="h-6 w-6 rounded-full bg-gradient-to-br from-[#D4AF37] to-[#B8962E] ring-2 ring-[#0f1a2e]" />
                ))}
              </div>
              <span className="text-sm text-[#D4AF37]">Trusted by 50+ college programs</span>
            </div>

            <h1 className="mb-6 text-5xl font-bold tracking-tight text-white md:text-7xl">
              Stop Guessing.
              <br />
              <span className="text-[#D4AF37]">Start Winning.</span>
            </h1>

            <p className="mb-8 text-xl text-gray-400 md:text-2xl max-w-3xl mx-auto">
              The only platform that combines <span className="text-white">AI-powered NIL valuations</span>,
              {" "}<span className="text-white">real-time portal tracking</span>, and{" "}
              <span className="text-white">PFF analytics</span> to help you build championship rosters.
            </p>

            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row mb-12">
              <Link href="/pricing">
                <Button size="lg" className="bg-[#D4AF37] text-black hover:bg-[#D4AF37]/90 text-lg px-8 py-6 h-auto">
                  Start 14-Day Free Trial
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="border-white/20 text-white hover:bg-white/10 text-lg px-8 py-6 h-auto">
                <Play className="mr-2 h-5 w-5" />
                Watch Demo
              </Button>
            </div>

            <p className="text-sm text-gray-500">
              No credit card required • Cancel anytime • Setup in 2 minutes
            </p>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="border-y border-white/10 bg-[#1a2744]">
        <div className="container mx-auto grid grid-cols-2 gap-8 px-4 py-16 md:grid-cols-4">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-4xl font-bold text-[#D4AF37] md:text-5xl">
                {stat.value}
              </div>
              <div className="mt-2 text-lg font-medium text-white">{stat.label}</div>
              <div className="mt-1 text-sm text-gray-500">{stat.description}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Problem Section */}
      <section className="container mx-auto px-4 py-24">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="mb-6 text-3xl font-bold text-white md:text-5xl">
            The Transfer Portal Changed Everything.
            <br />
            <span className="text-gray-500">Your Tools Didn&apos;t.</span>
          </h2>
          <p className="text-xl text-gray-400 mb-12">
            You&apos;re still using spreadsheets, gut feelings, and outdated recruiting services
            while competitors are making data-driven decisions in real-time.
          </p>

          <div className="grid gap-6 md:grid-cols-3 text-left">
            <Card className="border-red-500/20 bg-red-500/5">
              <CardContent className="p-6">
                <div className="text-red-400 text-4xl font-bold mb-2">68%</div>
                <p className="text-gray-400">of transfers don&apos;t meet expectations at their new school</p>
              </CardContent>
            </Card>
            <Card className="border-red-500/20 bg-red-500/5">
              <CardContent className="p-6">
                <div className="text-red-400 text-4xl font-bold mb-2">$2.1M</div>
                <p className="text-gray-400">average NIL overpayment per program annually</p>
              </CardContent>
            </Card>
            <Card className="border-red-500/20 bg-red-500/5">
              <CardContent className="p-6">
                <div className="text-red-400 text-4xl font-bold mb-2">72hrs</div>
                <p className="text-gray-400">average time to evaluate a portal entry manually</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="container mx-auto px-4 py-24">
        <div className="mb-16 text-center">
          <div className="mb-4 text-sm font-medium uppercase tracking-wider text-[#D4AF37]">
            Platform Features
          </div>
          <h2 className="mb-4 text-3xl font-bold text-white md:text-5xl">
            Everything You Need to Win
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Built by former coaches, data scientists, and NIL experts who understand what it takes to compete.
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
      <section id="how-it-works" className="border-y border-white/10 bg-[#1a2744] py-24">
        <div className="container mx-auto px-4">
          <div className="mb-16 text-center">
            <div className="mb-4 text-sm font-medium uppercase tracking-wider text-[#D4AF37]">
              How It Works
            </div>
            <h2 className="mb-4 text-3xl font-bold text-white md:text-5xl">
              From Portal Entry to Signed LOI
            </h2>
            <p className="text-xl text-gray-400">
              Portal IQ streamlines your entire transfer evaluation workflow
            </p>
          </div>

          <div className="mx-auto max-w-5xl">
            <div className="grid gap-8 md:grid-cols-4">
              {[
                { step: "1", title: "Get Alerted", desc: "Instant notifications when players enter the portal matching your criteria" },
                { step: "2", title: "Evaluate", desc: "AI analyzes PFF grades, NIL value, and fit score in seconds" },
                { step: "3", title: "Compare", desc: "Stack candidates side-by-side with objective data" },
                { step: "4", title: "Decide", desc: "Make confident offers backed by data, not guesswork" },
              ].map((item, i) => (
                <div key={item.step} className="relative text-center">
                  <div className="mb-4 mx-auto h-16 w-16 rounded-full bg-[#D4AF37] flex items-center justify-center text-2xl font-bold text-black">
                    {item.step}
                  </div>
                  {i < 3 && (
                    <ChevronRight className="absolute top-8 -right-4 h-6 w-6 text-[#D4AF37]/50 hidden md:block" />
                  )}
                  <h3 className="mb-2 text-lg font-semibold text-white">{item.title}</h3>
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
          <div className="mb-4 text-sm font-medium uppercase tracking-wider text-[#D4AF37]">
            Built For
          </div>
          <h2 className="mb-4 text-3xl font-bold text-white md:text-5xl">
            Whether You&apos;re a Coach, Collective, or Agent
          </h2>
          <p className="text-xl text-gray-400">
            Portal IQ adapts to how you work
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
            <div className="mb-4 text-sm font-medium uppercase tracking-wider text-[#D4AF37]">
              Testimonials
            </div>
            <h2 className="mb-4 text-3xl font-bold text-white md:text-5xl">
              Trusted by Winning Programs
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
          <div className="mb-4 text-sm font-medium uppercase tracking-wider text-[#D4AF37]">
            Why Portal IQ
          </div>
          <h2 className="mb-4 text-3xl font-bold text-white md:text-5xl">
            Stop Settling for Spreadsheets
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
        <div className="container relative mx-auto px-4 text-center">
          <h2 className="mb-4 text-4xl font-bold text-white md:text-6xl">
            Ready to Win the Portal?
          </h2>
          <p className="mb-8 text-xl text-gray-400 max-w-2xl mx-auto">
            Join the coaches, collectives, and analysts who are already using Portal IQ
            to gain a competitive edge.
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link href="/pricing">
              <Button size="lg" className="bg-[#D4AF37] text-black hover:bg-[#D4AF37]/90 text-lg px-8 py-6 h-auto">
                Start Your Free Trial
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
              <div className="flex items-center gap-2 mb-4">
                <span className="text-2xl">🏈</span>
                <span className="text-xl font-bold text-white">Portal IQ</span>
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
              © 2025 Portal IQ by Playmaker VC. All rights reserved.
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
