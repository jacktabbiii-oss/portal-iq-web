"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-[#0f1a2e] text-white">
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <Link href="/" className="inline-flex items-center gap-2 text-gray-400 hover:text-white mb-8">
          <ArrowLeft className="h-4 w-4" />
          Back to Home
        </Link>

        <h1 className="text-4xl font-bold mb-2">Terms of Service</h1>
        <p className="text-gray-500 mb-8">Portal IQ by Elite Sports Solutions</p>

        <div className="prose prose-invert max-w-none space-y-6 text-gray-300">
          <p>Last updated: February 2026</p>

          <h2 className="text-2xl font-semibold text-white mt-8">1. Acceptance of Terms</h2>
          <p>
            By accessing or using Portal IQ, you agree to be bound by these Terms of Service.
            If you do not agree to these terms, please do not use our service.
          </p>

          <h2 className="text-2xl font-semibold text-white mt-8">2. Description of Service</h2>
          <p>
            Portal IQ provides AI-powered analytics for college football, including NIL valuations,
            transfer portal tracking, and roster optimization tools.
          </p>

          <h2 className="text-2xl font-semibold text-white mt-8">3. User Accounts</h2>
          <p>
            You are responsible for maintaining the confidentiality of your account credentials
            and for all activities that occur under your account.
          </p>

          <h2 className="text-2xl font-semibold text-white mt-8">4. Subscription and Billing</h2>
          <p>
            Paid subscriptions are billed in advance on a monthly or annual basis.
            You may cancel your subscription at any time.
          </p>

          <h2 className="text-2xl font-semibold text-white mt-8">5. Data and Privacy</h2>
          <p>
            Your use of Portal IQ is also governed by our Privacy Policy.
            Please review our Privacy Policy for information on how we collect and use your data.
          </p>

          <h2 className="text-2xl font-semibold text-white mt-8">6. Contact</h2>
          <p>
            For questions about these Terms, please contact us at{" "}
            <a href="mailto:support@portaliq.ai" className="text-[#D4AF37] hover:underline">
              support@portaliq.ai
            </a>
          </p>
        </div>

        <div className="mt-12 pt-8 border-t border-white/10 text-center text-sm text-gray-500">
          © 2026 Portal IQ by Elite Sports Solutions. All rights reserved.
        </div>
      </div>
    </div>
  );
}
