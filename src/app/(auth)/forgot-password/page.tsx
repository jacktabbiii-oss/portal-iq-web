"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { ArrowLeft, Mail, CheckCircle2 } from "lucide-react";
import { requestPasswordReset } from "@/providers/auth-provider";
import { toast } from "sonner";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      await requestPasswordReset(email);
      setIsSuccess(true);
      toast.success("Password reset email sent!");
    } catch (err) {
      console.error("Password reset error:", err);
      toast.error("Failed to send reset email. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0f1a2e] flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-3 mb-6">
            <Image
              src="/logo.png"
              alt="Portal IQ"
              width={48}
              height={48}
              className="object-contain"
            />
            <span className="text-2xl font-bold text-white">PORTAL IQ</span>
          </Link>
        </div>

        <Card className="border-white/10 bg-[#1a2744]">
          <CardContent className="p-8">
            {isSuccess ? (
              <div className="text-center py-8">
                <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto mb-4" />
                <h2 className="text-2xl font-bold text-white mb-2">Check your email</h2>
                <p className="text-gray-400 mb-6">
                  We&apos;ve sent a password reset link to <span className="text-white">{email}</span>
                </p>
                <Link href="/login">
                  <Button className="bg-[#D4AF37] text-black hover:bg-[#D4AF37]/90">
                    Back to Sign In
                  </Button>
                </Link>
              </div>
            ) : (
              <>
                <div className="text-center mb-6">
                  <h1 className="text-2xl font-bold text-white mb-2">Reset your password</h1>
                  <p className="text-gray-400">
                    Enter your email and we&apos;ll send you a reset link
                  </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-gray-300">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                      <Input
                        id="email"
                        type="email"
                        placeholder="you@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        className="pl-10 bg-[#0f1a2e] border-white/10 text-white placeholder:text-gray-500"
                      />
                    </div>
                  </div>

                  <Button
                    type="submit"
                    className="w-full bg-[#D4AF37] text-black hover:bg-[#D4AF37]/90"
                    disabled={isLoading}
                  >
                    {isLoading ? "Sending..." : "Send Reset Link"}
                  </Button>
                </form>

                <div className="mt-6 text-center">
                  <Link
                    href="/login"
                    className="inline-flex items-center gap-2 text-sm text-gray-400 hover:text-white"
                  >
                    <ArrowLeft className="h-4 w-4" />
                    Back to Sign In
                  </Link>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
