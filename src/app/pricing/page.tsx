"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, ArrowLeft, Loader2 } from "lucide-react";

// Stripe Price IDs - replace with your actual IDs from Stripe Dashboard
const STRIPE_PRICES = {
  pro_monthly: process.env.NEXT_PUBLIC_STRIPE_PRO_MONTHLY || "price_pro_monthly",
  pro_annual: process.env.NEXT_PUBLIC_STRIPE_PRO_ANNUAL || "price_pro_annual",
};

const proFeatures = [
  "Unlimited NIL valuations",
  "Transfer portal intelligence",
  "Advanced performance metrics",
  "Win impact calculator",
  "AI assistant (100 queries/mo)",
  "Player comparison tools",
  "Export to CSV/PDF",
  "Email alerts",
];

const enterpriseFeatures = [
  "Everything in Pro",
  "Unlimited AI queries",
  "API access",
  "SSO / SAML",
  "Dedicated account manager",
  "Custom integrations",
  "Priority support",
  "Training & onboarding",
];

export default function PricingPage() {
  const [loading, setLoading] = useState<string | null>(null);
  const [billingPeriod, setBillingPeriod] = useState<"monthly" | "annual">("monthly");

  const handleSubscribe = async (priceId: string | null) => {
    if (!priceId) {
      // Enterprise - redirect to contact
      window.location.href = "mailto:sales@portaliq.ai?subject=Portal%20IQ%20Enterprise%20Inquiry";
      return;
    }

    setLoading(priceId);
    try {
      const response = await fetch("/api/stripe/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ priceId }),
      });

      if (!response.ok) {
        throw new Error("Failed to create checkout session");
      }

      const { url } = await response.json();
      window.location.href = url;
    } catch (error) {
      console.error("Checkout error:", error);
      // Fallback to Streamlit app
      window.location.href = "https://portal-iq.streamlit.app";
    } finally {
      setLoading(null);
    }
  };

  const currentPriceId = billingPeriod === "monthly"
    ? STRIPE_PRICES.pro_monthly
    : STRIPE_PRICES.pro_annual;

  return (
    <div className="min-h-screen bg-[#0f1a2e]">
      {/* Header */}
      <header className="border-b border-white/10">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <Link href="/" className="flex items-center gap-3">
            <ArrowLeft className="h-4 w-4 text-gray-400" />
            <Image
              src="/logo.png"
              alt="Portal IQ"
              width={32}
              height={32}
              className="object-contain"
            />
            <span className="text-xl font-bold text-white">PORTAL IQ</span>
          </Link>
          <a href="https://portal-iq.streamlit.app">
            <Button variant="ghost" className="text-white hover:text-white/80">
              Sign In
            </Button>
          </a>
        </div>
      </header>

      {/* Pricing */}
      <section className="container mx-auto px-4 py-20">
        <div className="mb-12 text-center">
          <h1 className="mb-4 text-4xl font-bold text-white md:text-5xl">
            Simple, Transparent Pricing
          </h1>
          <p className="text-lg text-gray-400">
            Start with a 14-day free trial. No credit card required.
          </p>

          {/* Billing Toggle */}
          <div className="mt-8 flex items-center justify-center gap-4">
            <button
              onClick={() => setBillingPeriod("monthly")}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
                billingPeriod === "monthly"
                  ? "bg-[#D4AF37] text-black"
                  : "bg-white/10 text-white hover:bg-white/20"
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod("annual")}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
                billingPeriod === "annual"
                  ? "bg-[#D4AF37] text-black"
                  : "bg-white/10 text-white hover:bg-white/20"
              }`}
            >
              Annual
              <span className="ml-2 rounded bg-[#22C55E] px-2 py-0.5 text-xs text-white">
                Save $58
              </span>
            </button>
          </div>
        </div>

        <div className="mx-auto grid max-w-4xl gap-8 md:grid-cols-2">
          {/* Pro Plan */}
          <Card className="relative border-white/10 bg-[#1a2744] ring-2 ring-[#D4AF37]">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full bg-[#D4AF37] px-3 py-1 text-xs font-semibold text-black">
              Most Popular
            </div>
            <CardHeader className="text-center">
              <CardTitle className="text-2xl text-white">Pro</CardTitle>
              <CardDescription className="text-gray-400">
                For coaches and NIL collectives
              </CardDescription>
              <div className="mt-4">
                {billingPeriod === "monthly" ? (
                  <>
                    <span className="text-4xl font-bold text-white">$29</span>
                    <span className="text-gray-400">/month</span>
                  </>
                ) : (
                  <>
                    <span className="text-4xl font-bold text-white">$290</span>
                    <span className="text-gray-400">/year</span>
                    <p className="mt-1 text-sm text-[#22C55E]">
                      2 months free!
                    </p>
                  </>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {proFeatures.map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-gray-300">
                    <CheckCircle2 className="h-5 w-5 text-[#22C55E]" />
                    {feature}
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button
                className="w-full bg-[#D4AF37] text-black hover:bg-[#D4AF37]/90"
                onClick={() => handleSubscribe(currentPriceId)}
                disabled={loading === currentPriceId}
              >
                {loading === currentPriceId ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  "Start Free Trial"
                )}
              </Button>
            </CardFooter>
          </Card>

          {/* Enterprise Plan */}
          <Card className="relative border-white/10 bg-[#1a2744]">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl text-white">Enterprise</CardTitle>
              <CardDescription className="text-gray-400">
                For athletic departments & agencies
              </CardDescription>
              <div className="mt-4">
                <span className="text-4xl font-bold text-white">Custom</span>
              </div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {enterpriseFeatures.map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-gray-300">
                    <CheckCircle2 className="h-5 w-5 text-[#22C55E]" />
                    {feature}
                  </li>
                ))}
              </ul>
            </CardContent>
            <CardFooter>
              <Button
                className="w-full bg-white/10 text-white hover:bg-white/20"
                onClick={() => handleSubscribe(null)}
              >
                Contact Sales
              </Button>
            </CardFooter>
          </Card>
        </div>

        {/* FAQ */}
        <div className="mx-auto mt-20 max-w-2xl text-center">
          <h2 className="mb-8 text-2xl font-bold text-white">
            Frequently Asked Questions
          </h2>
          <div className="space-y-6 text-left">
            <div>
              <h3 className="mb-2 font-semibold text-white">
                What&apos;s included in the free trial?
              </h3>
              <p className="text-gray-400">
                Full access to all Pro features for 14 days. No credit card required.
              </p>
            </div>
            <div>
              <h3 className="mb-2 font-semibold text-white">
                Can I cancel anytime?
              </h3>
              <p className="text-gray-400">
                Yes, you can cancel your subscription at any time with no penalties.
              </p>
            </div>
            <div>
              <h3 className="mb-2 font-semibold text-white">
                Do you offer team discounts?
              </h3>
              <p className="text-gray-400">
                Yes! Contact us for volume pricing for athletic departments and agencies.
              </p>
            </div>
          </div>
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
