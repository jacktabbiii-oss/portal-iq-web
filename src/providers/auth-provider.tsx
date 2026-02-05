"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import pb from "@/lib/pocketbase/client";
import { useAuthStore } from "@/stores/auth-store";
import type { User } from "@/lib/pocketbase/client";

const publicPaths = ["/login", "/register", "/forgot-password", "/", "/pricing", "/terms", "/privacy"];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { setUser, setLoading, isLoading } = useAuthStore();

  useEffect(() => {
    // Check for existing auth on mount
    const checkAuth = async () => {
      try {
        if (pb.authStore.isValid) {
          // Refresh auth to validate token
          try {
            await pb.collection("users").authRefresh();
            setUser(pb.authStore.model as unknown as User);
          } catch {
            // Token invalid, clear store
            pb.authStore.clear();
            setUser(null);
          }
        } else {
          setUser(null);
        }
      } catch {
        setUser(null);
      }
    };

    checkAuth();

    // Listen for auth changes
    const unsubscribe = pb.authStore.onChange((token, model) => {
      if (token && model) {
        setUser(model as unknown as User);
      } else {
        setUser(null);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [setUser, setLoading]);

  // Handle route protection
  useEffect(() => {
    if (isLoading) return;

    const isPublicPath = publicPaths.some(
      (path) => pathname === path || pathname.startsWith("/api")
    );
    const isAuthenticated = pb.authStore.isValid;

    if (!isAuthenticated && !isPublicPath) {
      router.push("/login");
    } else if (isAuthenticated && (pathname === "/login" || pathname === "/register")) {
      router.push("/dashboard");
    }
  }, [pathname, isLoading, router]);

  return <>{children}</>;
}

// Auth utility functions
export async function login(email: string, password: string) {
  const authData = await pb
    .collection("users")
    .authWithPassword(email, password);
  return authData;
}

export async function register(
  email: string,
  password: string,
  data: { name: string; organization?: string }
) {
  const user = await pb.collection("users").create({
    email,
    password,
    passwordConfirm: password,
    name: data.name,
    organization: data.organization || "",
    subscription_tier: "free",
  });

  // Auto-login after registration
  await pb.collection("users").authWithPassword(email, password);

  return user;
}

export async function logout() {
  pb.authStore.clear();
  useAuthStore.getState().logout();
}

export async function requestPasswordReset(email: string) {
  await pb.collection("users").requestPasswordReset(email);
}
