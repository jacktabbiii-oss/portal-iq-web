"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-[#0f1a2e] text-white">
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <Link href="/" className="inline-flex items-center gap-2 text-gray-400 hover:text-white mb-8">
          <ArrowLeft className="h-4 w-4" />
          Back to Home
        </Link>

        <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>

        <div className="prose prose-invert max-w-none space-y-6 text-gray-300">
          <p>Last updated: February 2025</p>

          <h2 className="text-2xl font-semibold text-white mt-8">1. Information We Collect</h2>
          <p>
            We collect information you provide directly to us, including your name, email address,
            and organization when you create an account.
          </p>

          <h2 className="text-2xl font-semibold text-white mt-8">2. How We Use Your Information</h2>
          <p>
            We use the information we collect to provide, maintain, and improve our services,
            process transactions, and send you technical notices and support messages.
          </p>

          <h2 className="text-2xl font-semibold text-white mt-8">3. Data Security</h2>
          <p>
            We implement appropriate security measures to protect your personal information
            against unauthorized access, alteration, disclosure, or destruction.
          </p>

          <h2 className="text-2xl font-semibold text-white mt-8">4. Data Retention</h2>
          <p>
            We retain your information for as long as your account is active or as needed
            to provide you services and comply with legal obligations.
          </p>

          <h2 className="text-2xl font-semibold text-white mt-8">5. Third-Party Services</h2>
          <p>
            We may use third-party services such as Stripe for payment processing.
            These services have their own privacy policies.
          </p>

          <h2 className="text-2xl font-semibold text-white mt-8">6. Contact</h2>
          <p>
            For questions about this Privacy Policy, please contact us at{" "}
            <a href="mailto:support@portaliq.ai" className="text-[#D4AF37] hover:underline">
              support@portaliq.ai
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
