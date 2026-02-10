"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  DollarSign,
  ArrowRightLeft,
  TrendingUp,
  Bot,
  Settings,
  ChevronLeft,
  ChevronRight,
  Users,
  School,
  Bell,
  FileText,
  GitCompareArrows,
  AlertTriangle,
  Trophy,
  GitCompare,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { useSubscriptionTier } from "@/stores/auth-store";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const mainNavigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    description: "Overview & stats",
  },
  {
    name: "NIL Valuator",
    href: "/nil-valuator",
    icon: DollarSign,
    description: "Player valuations",
  },
  {
    name: "Portal Intelligence",
    href: "/portal-intelligence",
    icon: ArrowRightLeft,
    description: "Transfer tracker",
  },
  {
    name: "Win Impact",
    href: "/win-impact",
    icon: TrendingUp,
    description: "Player impact analysis",
  },
  {
    name: "AI Assistant",
    href: "/ai-assistant",
    icon: Bot,
    description: "Ask anything",
  },
];

const secondaryNavigation = [
  {
    name: "Schools",
    href: "/schools",
    icon: School,
    description: "Program profiles",
  },
  {
    name: "Power Rankings",
    href: "/power-rankings",
    icon: Trophy,
    description: "Team rankings",
  },
  {
    name: "Team Compare",
    href: "/team-compare",
    icon: GitCompare,
    description: "Compare teams",
  },
  {
    name: "Player Comparison",
    href: "/player-comparison",
    icon: GitCompareArrows,
    description: "Compare players",
  },
  {
    name: "Watchlist",
    href: "/watchlist",
    icon: Users,
    description: "Your targets",
  },
  {
    name: "Reports",
    href: "/reports",
    icon: FileText,
    description: "Scouting reports",
  },
];

const bottomNavigation = [
  {
    name: "Notifications",
    href: "/notifications",
    icon: Bell,
  },
  {
    name: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const subscriptionTier = useSubscriptionTier();

  return (
    <aside
      className={cn(
        "flex h-screen flex-col bg-sidebar border-r border-sidebar-border transition-all duration-300",
        collapsed ? "w-[72px]" : "w-64"
      )}
    >
      {/* Logo Section */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-sidebar-border">
        {!collapsed ? (
          <Link href="/dashboard" className="flex items-center gap-3">
            <div className="relative w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center overflow-hidden">
              <Image
                src="/logo.png"
                alt="Portal IQ"
                width={32}
                height={32}
                className="object-contain"
              />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-bold text-white tracking-tight">
                PORTAL <span className="text-primary">IQ</span>
              </span>
            </div>
          </Link>
        ) : (
          <Link href="/dashboard" className="mx-auto">
            <div className="relative w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center">
              <Image
                src="/logo.png"
                alt="Portal IQ"
                width={28}
                height={28}
                className="object-contain"
              />
            </div>
          </Link>
        )}
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-thin">
        {!collapsed && (
          <p className="px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
            Main Menu
          </p>
        )}
        {mainNavigation.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-primary text-primary-foreground shadow-lg glow-gold"
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-white",
                collapsed && "justify-center px-2"
              )}
              title={collapsed ? item.name : undefined}
            >
              <Icon className={cn("h-5 w-5 flex-shrink-0", isActive && "text-primary-foreground")} />
              {!collapsed && (
                <div className="flex flex-col">
                  <span className="truncate">{item.name}</span>
                </div>
              )}
            </Link>
          );
        })}

        {!collapsed && <Separator className="my-4 bg-sidebar-border" />}

        {!collapsed && (
          <p className="px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
            Tools
          </p>
        )}
        {secondaryNavigation.map((item) => {
          const isActive =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-primary text-primary-foreground shadow-lg glow-gold"
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-white",
                collapsed && "justify-center px-2"
              )}
              title={collapsed ? item.name : undefined}
            >
              <Icon className={cn("h-5 w-5 flex-shrink-0", isActive && "text-primary-foreground")} />
              {!collapsed && <span className="truncate">{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Season Selector */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-sidebar-border">
          <div className="p-3 rounded-xl bg-sidebar-accent">
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold mb-1">
              Season
            </p>
            <div className="flex items-center justify-between">
              <span className="font-semibold text-sm text-white">
                {new Date().getMonth() >= 6
                  ? `${new Date().getFullYear()}-${(new Date().getFullYear() + 1).toString().slice(2)}`
                  : `${new Date().getFullYear() - 1}-${new Date().getFullYear().toString().slice(2)}`}
              </span>
              <Badge variant="outline" className="text-[10px] border-primary/50 text-primary">
                Current
              </Badge>
            </div>
          </div>
          <div className="mt-3 text-[10px] text-muted-foreground space-y-0.5">
            <p>Updated: {new Date().toLocaleDateString()}</p>
          </div>
        </div>
      )}

      {/* Subscription Badge */}
      {!collapsed && (
        <div className="px-4 py-3 border-t border-sidebar-border">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Plan</span>
            <Badge
              className={cn(
                "font-semibold",
                subscriptionTier === "enterprise" && "bg-primary text-primary-foreground",
                subscriptionTier === "pro" && "bg-purple-500 text-white",
                subscriptionTier === "free" && "bg-slate-600"
              )}
            >
              {subscriptionTier.toUpperCase()}
            </Badge>
          </div>
          {(subscriptionTier === "free" || subscriptionTier === "pro") && (
            <Button
              variant="outline"
              size="sm"
              className="w-full mt-2 text-xs border-primary text-primary hover:bg-primary hover:text-primary-foreground transition-all"
              asChild
            >
              <Link href="/settings">Upgrade Plan</Link>
            </Button>
          )}
        </div>
      )}

      {/* Bottom Navigation */}
      <div className="px-3 py-3 border-t border-sidebar-border space-y-1">
        {bottomNavigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-primary"
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-white",
                collapsed && "justify-center px-2"
              )}
              title={collapsed ? item.name : undefined}
            >
              <Icon className="h-5 w-5 flex-shrink-0" />
              {!collapsed && <span>{item.name}</span>}
            </Link>
          );
        })}
      </div>

      {/* Collapse Toggle */}
      <div className="px-3 py-3 border-t border-sidebar-border">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            "w-full text-muted-foreground hover:text-white",
            collapsed ? "px-0" : "justify-start"
          )}
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

      {/* Powered By Footer */}
      {!collapsed && (
        <div className="px-4 py-2 border-t border-sidebar-border">
          <p className="text-[10px] text-center text-muted-foreground">
            Powered by{" "}
            <span className="text-primary font-medium">Elite Sports Solutions</span>
          </p>
        </div>
      )}
    </aside>
  );
}
