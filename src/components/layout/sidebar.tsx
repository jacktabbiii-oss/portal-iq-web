"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  DollarSign,
  ArrowRightLeft,
  Trophy,
  Users,
  Settings,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { useSubscriptionTier } from "@/stores/auth-store";
import { Badge } from "@/components/ui/badge";

const navigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    tier: "free" as const,
  },
  {
    name: "NIL Valuator",
    href: "/nil-valuator",
    icon: DollarSign,
    tier: "free" as const,
  },
  {
    name: "Portal Intelligence",
    href: "/portal-intelligence",
    icon: ArrowRightLeft,
    tier: "free" as const,
  },
  {
    name: "Draft Tracker",
    href: "/draft-tracker",
    icon: Trophy,
    tier: "free" as const,
  },
  {
    name: "Roster Builder",
    href: "/roster-builder",
    icon: Users,
    tier: "free" as const,
  },
  {
    name: "Settings",
    href: "/settings",
    icon: Settings,
    tier: "free" as const,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const subscriptionTier = useSubscriptionTier();

  return (
    <aside
      className={cn(
        "flex flex-col bg-sidebar border-r border-sidebar-border transition-all duration-300",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-sidebar-border">
        {!collapsed && (
          <Link href="/dashboard" className="flex items-center gap-2">
            <span className="text-2xl">🏈</span>
            <span className="text-xl font-bold text-primary">Portal IQ</span>
          </Link>
        )}
        {collapsed && (
          <Link href="/dashboard" className="mx-auto">
            <span className="text-2xl">🏈</span>
          </Link>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-primary"
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                collapsed && "justify-center"
              )}
              title={collapsed ? item.name : undefined}
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              {!collapsed && (
                <span className="truncate">{item.name}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Subscription badge */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-sidebar-border">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Plan</span>
            <Badge
              variant={subscriptionTier === "enterprise" ? "default" : "secondary"}
              className={cn(
                subscriptionTier === "enterprise" && "bg-primary text-primary-foreground",
                subscriptionTier === "pro" && "bg-purple-500 text-white"
              )}
            >
              {subscriptionTier.toUpperCase()}
            </Badge>
          </div>
          {subscriptionTier === "free" && (
            <Button
              variant="outline"
              size="sm"
              className="w-full mt-2 text-xs border-primary text-primary hover:bg-primary hover:text-primary-foreground"
              asChild
            >
              <Link href="/settings">Upgrade</Link>
            </Button>
          )}
        </div>
      )}

      {/* Collapse toggle */}
      <div className="px-2 py-3 border-t border-sidebar-border">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(!collapsed)}
          className={cn("w-full", collapsed ? "px-0" : "justify-start")}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <>
              <ChevronLeft className="h-4 w-4 mr-2" />
              <span className="text-xs">Collapse</span>
            </>
          )}
        </Button>
      </div>
    </aside>
  );
}
