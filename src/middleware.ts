import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// Routes that don't require authentication
const publicRoutes = [
  "/",
  "/login",
  "/pricing",
  "/register",
  "/forgot-password",
  "/terms",
  "/privacy",
];

// Routes that require authentication
const protectedRoutes = [
  "/dashboard",
  "/nil-valuator",
  "/portal-intelligence",
  "/win-impact",
  "/ai-assistant",
  "/watchlist",
  "/settings",
  "/schools",
  "/reports",
  "/notifications",
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip middleware for API routes and static files
  if (
    pathname.startsWith("/api") ||
    pathname.startsWith("/_next") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // Note: PocketBase stores auth in localStorage (client-side), not cookies
  // So we can't check auth in middleware. Client-side AuthProvider handles
  // route protection instead. This middleware just allows all routes through.

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\..*|api).*)",
  ],
};
