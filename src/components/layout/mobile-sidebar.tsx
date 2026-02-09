"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  DollarSign,
  ArrowRightLeft,
  TrendingUp,
  Bot,
  GitCompareArrows,
  Users,
  School,
  Settings,
  Menu,
  Bell,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useSubscriptionTier } from "@/stores/auth-store";
import { Badge } from "@/components/ui/badge";
import { useState } from "react";

const mainNavigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "NIL Valuator",
    href: "/nil-valuator",
    icon: DollarSign,
  },
  {
    name: "Portal Intelligence",
    href: "/portal-intelligence",
    icon: ArrowRightLeft,
  },
  {
    name: "Win Impact",
    href: "/win-impact",
    icon: TrendingUp,
  },
  {
    name: "Flight Risk",
    href: "/flight-risk",
    icon: AlertTriangle,
  },
  {
    name: "AI Assistant",
    href: "/ai-assistant",
    icon: Bot,
  },
];

const toolsNavigation = [
  {
    name: "Player Comparison",
    href: "/player-comparison",
    icon: GitCompareArrows,
  },
  {
    name: "Watchlist",
    href: "/watchlist",
    icon: Users,
  },
  {
    name: "Schools",
    href: "/schools",
    icon: School,
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

export function MobileSidebar() {
  const pathname = usePathname();
  const subscriptionTier = useSubscriptionTier();
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="md:hidden">
          <Menu className="h-5 w-5" />
          <span className="sr-only">Toggle menu</span>
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-72 p-0 bg-sidebar">
        <SheetHeader className="h-16 flex flex-row items-center justify-start px-4 border-b border-sidebar-border">
          <Link
            href="/dashboard"
            className="flex items-center gap-2"
            onClick={() => setOpen(false)}
          >
            <span className="text-2xl">🏈</span>
            <SheetTitle className="text-xl font-bold text-primary">
              Portal IQ
            </SheetTitle>
          </Link>
        </SheetHeader>

        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          <p className="px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
            Main Menu
          </p>
          {mainNavigation.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            const Icon = item.icon;

            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-white"
                )}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                <span className="truncate">{item.name}</span>
              </Link>
            );
          })}

          <div className="my-3 border-t border-sidebar-border" />

          <p className="px-3 py-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
            Tools
          </p>
          {toolsNavigation.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(`${item.href}/`);
            const Icon = item.icon;

            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-white"
                )}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                <span className="truncate">{item.name}</span>
              </Link>
            );
          })}

          <div className="my-3 border-t border-sidebar-border" />

          {bottomNavigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-primary"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-white"
                )}
              >
                <Icon className="h-5 w-5 flex-shrink-0" />
                <span className="truncate">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="px-4 py-3 border-t border-sidebar-border">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">Plan</span>
            <Badge
              variant={
                subscriptionTier === "enterprise" ? "default" : "secondary"
              }
              className={cn(
                subscriptionTier === "enterprise" &&
                  "bg-primary text-primary-foreground",
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
              <Link href="/settings" onClick={() => setOpen(false)}>
                Upgrade
              </Link>
            </Button>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}
