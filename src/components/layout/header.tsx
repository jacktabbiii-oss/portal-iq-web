"use client";

import { useState, useEffect, useCallback, useRef } from "react";
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
import { Bell, Search, LogOut, Settings, User, Moon, Sun, Loader2, Star } from "lucide-react";
import { Input } from "@/components/ui/input";
import Link from "next/link";
import { MobileSidebar } from "./mobile-sidebar";
import { cn } from "@/lib/utils";
import { getNILLeaderboard } from "@/lib/api/nil";
import { getActivePortalPlayers, getPortalTeamRankings } from "@/lib/api/portal";
import { searchPlayers, type PlayerSearchResult, formatNILValue } from "@/lib/api/players";

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

  // Search state
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<PlayerSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchDropdown, setShowSearchDropdown] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);

  // Debounced search
  useEffect(() => {
    if (searchQuery.length < 2) {
      setSearchResults([]);
      setShowSearchDropdown(false);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const response = await searchPlayers(searchQuery, "all", 8);
        setSearchResults(response.players);
        setShowSearchDropdown(true);
      } catch {
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSearchDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handlePlayerClick = (player: PlayerSearchResult) => {
    setShowSearchDropdown(false);
    setSearchQuery("");
    router.push(`/player/${encodeURIComponent(player.name)}`);
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
        <div className="relative flex-1 max-w-xs" ref={searchRef}>
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground z-10" />
          {isSearching && (
            <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-primary z-10" />
          )}
          <Input
            type="search"
            placeholder="Search players, schools..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => searchResults.length > 0 && setShowSearchDropdown(true)}
            className="pl-10 bg-input border-border rounded-full h-9 text-sm focus-visible:ring-primary"
          />
          {showSearchDropdown && searchResults.length > 0 && (
            <div className="absolute top-full mt-2 w-[360px] right-0 bg-card border border-border rounded-xl shadow-2xl z-50 overflow-hidden">
              <div className="p-2 border-b border-border">
                <p className="text-xs text-muted-foreground px-2">
                  {searchResults.length} result{searchResults.length !== 1 ? "s" : ""} for &quot;{searchQuery}&quot;
                </p>
              </div>
              <div className="max-h-[400px] overflow-y-auto">
                {searchResults.map((player) => (
                  <button
                    key={`${player.name}-${player.school}`}
                    onClick={() => handlePlayerClick(player)}
                    className="w-full p-3 flex items-center gap-3 hover:bg-primary/10 transition-colors text-left"
                  >
                    {player.headshot_url ? (
                      <img
                        src={player.headshot_url}
                        alt={player.name}
                        className="w-9 h-9 rounded-full object-cover border border-border"
                      />
                    ) : (
                      <div className="w-9 h-9 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold text-primary">
                        {player.name.split(" ").map(n => n[0]).join("").slice(0, 2)}
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-sm truncate">{player.name}</p>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <span className="font-medium text-foreground/80">{player.position}</span>
                        <span>-</span>
                        <span className="truncate">{player.school}</span>
                        {player.stars && player.stars > 0 && (
                          <>
                            <span>-</span>
                            <span className="flex items-center text-yellow-500">
                              {player.stars}<Star className="h-3 w-3 fill-yellow-500 ml-0.5" />
                            </span>
                          </>
                        )}
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      {player.nil_value && player.nil_value > 0 ? (
                        <p className="text-sm font-bold text-primary">{formatNILValue(player.nil_value)}</p>
                      ) : null}
                      {player.pff_overall && player.pff_overall > 0 ? (
                        <p className="text-[10px] text-muted-foreground">PFF {player.pff_overall.toFixed(1)}</p>
                      ) : null}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
          {showSearchDropdown && searchQuery.length >= 2 && !isSearching && searchResults.length === 0 && (
            <div className="absolute top-full mt-2 w-[360px] right-0 bg-card border border-border rounded-xl shadow-2xl z-50 p-6 text-center">
              <p className="text-muted-foreground text-sm">No players found for &quot;{searchQuery}&quot;</p>
            </div>
          )}
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
