"use client";

import { useState, useEffect, useCallback } from "react";
import { useUser } from "@/stores/auth-store";
import { logout } from "@/providers/auth-provider";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Bell, Search, LogOut, Settings, User, Moon, Sun } from "lucide-react";
import { Input } from "@/components/ui/input";
import Link from "next/link";
import { MobileSidebar } from "./mobile-sidebar";
import { cn } from "@/lib/utils";
import { getNILLeaderboard } from "@/lib/api/nil";
import { getActivePortalPlayers, getPortalTeamRankings } from "@/lib/api/portal";

interface TickerItem {
  type: string;
  text: string;
}

function formatTickerValue(value: number): string {
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `$${Math.round(value / 1000)}K`;
  return `$${value.toLocaleString()}`;
}

export function Header() {
  const user = useUser();
  const router = useRouter();
  const [isDark, setIsDark] = useState(true);
  const [currentTickerIndex, setCurrentTickerIndex] = useState(0);
  const [tickerItems, setTickerItems] = useState<TickerItem[]>([
    { type: "loading", text: "Loading live data..." },
  ]);

  // Fetch real ticker data from API
  const fetchTickerData = useCallback(async () => {
    try {
      const [nilResponse, portalResponse, rankingsResponse] = await Promise.all([
        getNILLeaderboard({ limit: 5 }).catch(() => ({ players: [], total: 0 })),
        getActivePortalPlayers({ limit: 10, status: "all" }).catch(() => ({ players: [], total: 0, total_count: 0, active_in_portal: 0, committed: 0, schools_active: 0, offset: 0, limit: 10, has_more: false, filters_applied: {} })),
        getPortalTeamRankings(3).catch(() => ({ rankings: [], total_teams: 0 })),
      ]);

      const items: TickerItem[] = [];

      // Add top NIL players
      for (const player of nilResponse.players.slice(0, 3)) {
        items.push({
          type: "nil",
          text: `${player.player_name} (${player.position}) - ${formatTickerValue(player.valuation)}`,
        });
      }

      // Add recent portal commits
      const commits = portalResponse.players
        .filter((p) => p.status === "committed" && p.destination_school)
        .slice(0, 3);
      for (const player of commits) {
        items.push({
          type: "transfer",
          text: `${player.player_name} (${player.position}) → ${player.destination_school}`,
        });
      }

      // Add top portal classes
      for (const team of rankingsResponse.rankings.slice(0, 2)) {
        items.push({
          type: "ranking",
          text: `${team.team}: ${team.grade} Portal Class (${team.breakdown.transfers_in} transfers)`,
        });
      }

      if (items.length > 0) {
        setTickerItems(items);
        setCurrentTickerIndex(0);
      }
    } catch (err) {
      console.error("Failed to fetch ticker data:", err);
    }
  }, []);

  useEffect(() => {
    fetchTickerData();
  }, [fetchTickerData]);

  // Rotate ticker every 4 seconds
  useEffect(() => {
    if (tickerItems.length <= 1) return;
    const interval = setInterval(() => {
      setCurrentTickerIndex((prev) => (prev + 1) % tickerItems.length);
    }, 4000);
    return () => clearInterval(interval);
  }, [tickerItems.length]);

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle("dark");
    document.documentElement.classList.toggle("light");
  };

  const initials = user?.name
    ? user.name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  return (
    <header className="h-16 border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-40">
      <div className="flex h-full items-center justify-between px-4 md:px-6 gap-4">
        {/* Mobile menu trigger */}
        <MobileSidebar />

        {/* Live Ticker - Desktop only */}
        <div className="hidden md:flex items-center gap-3 flex-1 overflow-hidden min-w-0">
          <Badge
            variant="destructive"
            className="animate-pulse shrink-0 font-bold text-[10px] px-2"
          >
            LIVE
          </Badge>
          <div className="flex items-center gap-2 overflow-hidden">
            <span className={cn(
              tickerItems[currentTickerIndex]?.type === "nil" && "text-primary",
              tickerItems[currentTickerIndex]?.type === "transfer" && "text-blue-400",
              tickerItems[currentTickerIndex]?.type === "ranking" && "text-purple-400",
              !["nil", "transfer", "ranking"].includes(tickerItems[currentTickerIndex]?.type) && "text-muted-foreground",
            )}>●</span>
            <span className="text-sm font-medium truncate transition-all duration-300 text-muted-foreground">
              {tickerItems[currentTickerIndex]?.text || "Loading..."}
            </span>
          </div>
        </div>

        {/* Search */}
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            type="search"
            placeholder="Search players, schools..."
            className="pl-10 bg-input border-border rounded-full h-9 text-sm focus-visible:ring-primary"
          />
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="text-muted-foreground hover:text-foreground h-9 w-9"
          >
            {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>

          {/* Notifications */}
          <Button variant="ghost" size="icon" asChild className="relative h-9 w-9">
            <Link href="/notifications">
              <Bell className="h-4 w-4 text-muted-foreground" />
            </Link>
          </Button>

          {/* User menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2 px-2 h-9">
                <Avatar className="h-8 w-8 border-2 border-primary/30">
                  <AvatarFallback className="bg-primary/20 text-primary text-sm font-semibold">
                    {initials}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden lg:block text-left">
                  <p className="text-sm font-medium leading-none">{user?.name || "User"}</p>
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    {user?.organization || "Pro Account"}
                  </p>
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">{user?.name || "User"}</p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {user?.email || "user@example.com"}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href="/settings" className="flex items-center cursor-pointer">
                  <User className="mr-2 h-4 w-4" />
                  Profile
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href="/settings" className="flex items-center cursor-pointer">
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleLogout}
                className="text-destructive focus:text-destructive cursor-pointer"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
