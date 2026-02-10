"use client";

import { useState, useEffect, useCallback } from "react";
import Image from "next/image";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Search,
  TrendingUp,
  DollarSign,
  Star,
  Filter,
  Download,
  RefreshCw,
  Info,
  ChevronRight,
  Sparkles,
  Loader2,
  AlertCircle,
  Ruler,
  Weight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useRouter } from "next/navigation";
import { getNILLeaderboard, predictNIL, type NILLeaderboardPlayer, type PlayerInput } from "@/lib/api/nil";
import { searchPlayers, type PlayerSearchResult } from "@/lib/api/players";
import { SocialGrowthSimulator } from "@/components/charts/nil-growth-chart";
import { TransferValueChart } from "@/components/charts/transfer-value-chart";
import { HEIGHT_PRESETS, formatHeight } from "@/lib/constants/presets";

const positions = ["All", "QB", "RB", "WR", "TE", "OL", "DL", "LB", "CB", "S"];
const conferences = ["All", "SEC", "Big Ten", "Big 12", "ACC", "Pac-12", "AAC", "MWC", "Sun Belt", "C-USA"];
const starFilters = ["All", "5", "4+", "3+", "2+"];
const heightFilters = ["All", "6'4\"+", "6'2\"+", "6'0\"+", "5'10\"+"];
const weightFilters = ["All", "300+", "250+", "220+", "200+", "180+"];

// Player type alias (all measurables now on NILLeaderboardPlayer)
type NILPlayerWithMeasurables = NILLeaderboardPlayer;

// Helper to parse height filter string to inches
function parseHeightFilter(filter: string): number | null {
  if (filter === "All") return null;
  const match = filter.match(/(\d+)'(\d+)/);
  if (match) {
    return parseInt(match[1]) * 12 + parseInt(match[2]);
  }
  return null;
}

// Helper to parse weight filter string
function parseWeightFilter(filter: string): number | null {
  if (filter === "All") return null;
  const match = filter.match(/(\d+)/);
  return match ? parseInt(match[1]) : null;
}

function formatCurrency(value: number | undefined | null): string {
  if (value == null || isNaN(value)) return "$0";
  if (value >= 1000000000) {
    return `$${(value / 1000000000).toFixed(1)}B`;
  } else if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}K`;
  }
  return `$${value.toLocaleString()}`;
}

function getTierBadge(tier: string) {
  const styles: Record<string, string> = {
    mega: "tier-mega",
    premium: "tier-premium",
    solid: "tier-solid",
    moderate: "tier-moderate",
    entry: "tier-entry",
  };
  return styles[tier] || "tier-entry";
}

export default function NILValuatorPage() {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPosition, setSelectedPosition] = useState("All");
  const [selectedConference, setSelectedConference] = useState("All");
  const [selectedStars, setSelectedStars] = useState("All");
  const [selectedHeight, setSelectedHeight] = useState("All");
  const [selectedWeight, setSelectedWeight] = useState("All");
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [activeTab, setActiveTab] = useState("search");

  // API state
  const [players, setPlayers] = useState<NILPlayerWithMeasurables[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalPlayers, setTotalPlayers] = useState(0);
  const [isCustomLoading, setIsCustomLoading] = useState(false);

  // Selected player for Social Growth and Transfer Value tabs
  const [selectedPlayer, setSelectedPlayer] = useState<NILPlayerWithMeasurables | null>(null);

  // Tab-specific player search (for Social Growth and Transfer Value tabs)
  const [tabSearchQuery, setTabSearchQuery] = useState("");
  const [tabSearchResults, setTabSearchResults] = useState<PlayerSearchResult[]>([]);
  const [isTabSearching, setIsTabSearching] = useState(false);

  // Debounced search for Social Growth / Transfer Value tabs
  useEffect(() => {
    if (tabSearchQuery.length < 2) {
      setTabSearchResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsTabSearching(true);
      try {
        const response = await searchPlayers(tabSearchQuery, "nil", 10);
        setTabSearchResults(response.players);
      } catch (err) {
        console.error("Tab search failed:", err);
        setTabSearchResults([]);
      } finally {
        setIsTabSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [tabSearchQuery]);

  // Custom valuation form state
  const [customForm, setCustomForm] = useState({
    name: "",
    school: "",
    position: "",
    stars: "",
    instagram: "",
    twitter: "",
    pffGrade: "",
  });
  const [customResult, setCustomResult] = useState<{
    value: number;
    tier: string;
    breakdown: Record<string, number>;
  } | null>(null);

  // State for pagination
  const [totalInDatabase, setTotalInDatabase] = useState<number>(0);
  const [hasMore, setHasMore] = useState<boolean>(false);
  const [currentPage, setCurrentPage] = useState<number>(0);
  const pageSize = 50; // Show 50 players per page for readability

  // Market stats from API (calculated across ALL matching players, not just loaded ones)
  const [avgValue, setAvgValue] = useState<number>(0);
  const [marketCap, setMarketCap] = useState<number>(0);

  // Fetch NIL leaderboard data - now with pagination support
  const fetchPlayers = useCallback(async (loadMore = false) => {
    setIsLoading(true);
    setError(null);

    try {
      const params: {
        position?: string;
        conference?: string;
        search?: string;
        limit: number;
        offset: number;
      } = {
        limit: pageSize,
        offset: loadMore ? (currentPage + 1) * pageSize : 0,
      };

      if (selectedPosition !== "All") {
        params.position = selectedPosition;
      }
      if (selectedConference !== "All") {
        params.conference = selectedConference;
      }
      // Use server-side search for better performance
      if (searchQuery && searchQuery.length >= 2) {
        params.search = searchQuery;
      }

      const response = await getNILLeaderboard(params);

      if (loadMore) {
        // Append to existing players
        setPlayers(prev => [...prev, ...response.players]);
        setCurrentPage(prev => prev + 1);
      } else {
        // Replace players (new search/filter)
        setPlayers(response.players);
        setCurrentPage(0);
      }

      setTotalPlayers(response.total);
      setTotalInDatabase(response.total_count || response.total);
      setHasMore(response.has_more || false);
      // Set market stats from API (calculated across ALL matching players)
      setAvgValue(response.avg_value || 0);
      setMarketCap(response.market_cap || 0);
    } catch (err) {
      console.error("Failed to fetch NIL leaderboard:", err);
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setIsLoading(false);
    }
  }, [selectedPosition, selectedConference, searchQuery, currentPage, pageSize]);

  // Initial load and refetch on filter changes
  useEffect(() => {
    fetchPlayers(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPosition, selectedConference]);

  // Debounced search - waits 300ms after user stops typing
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery.length >= 2 || searchQuery.length === 0) {
        fetchPlayers(false);
      }
    }, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery]);

  // Client-side filtering (search + measurables + stars)
  const filteredPlayers = players.filter((player) => {
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const matchesSearch =
        player.player_name.toLowerCase().includes(query) ||
        player.school.toLowerCase().includes(query);
      if (!matchesSearch) return false;
    }

    // Stars filter (client-side)
    if (selectedStars !== "All") {
      const minStars = parseInt(selectedStars.replace("+", ""));
      if (!player.stars || player.stars < minStars) return false;
    }

    // Height filter (client-side)
    const minHeight = parseHeightFilter(selectedHeight);
    if (minHeight !== null && player.height) {
      if (player.height < minHeight) return false;
    }

    // Weight filter (client-side)
    const minWeight = parseWeightFilter(selectedWeight);
    if (minWeight !== null && player.weight) {
      if (player.weight < minWeight) return false;
    }

    return true;
  });

  // Handle custom valuation - calls the actual API
  const handleCustomValuation = async () => {
    if (!customForm.name || !customForm.school || !customForm.position) {
      return;
    }

    setIsCustomLoading(true);

    try {
      const playerInput: PlayerInput = {
        name: customForm.name,
        school: customForm.school,
        position: customForm.position,
        recruiting: customForm.stars ? { stars: parseInt(customForm.stars) } : undefined,
        social_media: {
          instagram_followers: customForm.instagram ? parseInt(customForm.instagram) : undefined,
          twitter_followers: customForm.twitter ? parseInt(customForm.twitter) : undefined,
        },
      };

      const result = await predictNIL(playerInput);

      setCustomResult({
        value: result.predicted_value,
        tier: result.value_tier,
        breakdown: {
          base_position_value: result.value_breakdown?.base_value || 0,
          social_media_value: result.value_breakdown?.social_media_premium || 0,
          school_brand_factor: result.value_breakdown?.school_brand_factor || 0,
          performance_bonus: result.value_breakdown?.position_market_factor || 0,
        },
      });
    } catch (err) {
      console.error("NIL prediction error:", err);
      // Fallback to client-side calculation
      const baseValue = 50000;
      const posMultiplier: Record<string, number> = {
        QB: 2.5, WR: 1.5, RB: 1.2, TE: 1.0, OL: 0.8, DL: 1.1, LB: 1.0, CB: 1.3, S: 1.1,
      };
      const starMultiplier: Record<string, number> = {
        "5": 4.0, "4": 2.0, "3": 1.0, "2": 0.5, "1": 0.25,
      };

      const posMult = posMultiplier[customForm.position] || 1.0;
      const starMult = starMultiplier[customForm.stars] || 1.0;
      const socialValue = (parseInt(customForm.instagram || "0") + parseInt(customForm.twitter || "0")) * 0.5;
      const pffBonus = customForm.pffGrade ? (parseFloat(customForm.pffGrade) / 100) * 100000 : 0;

      const value = Math.round(baseValue * posMult * starMult + socialValue + pffBonus);
      const tier = value >= 2000000 ? "mega" : value >= 500000 ? "premium" : value >= 100000 ? "solid" : value >= 25000 ? "moderate" : "entry";

      setCustomResult({
        value,
        tier,
        breakdown: {
          base_position_value: Math.round(baseValue * posMult),
          social_media_value: Math.round(socialValue),
          school_brand_factor: 0,
          performance_bonus: Math.round(pffBonus),
        },
      });
    } finally {
      setIsCustomLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <DollarSign className="h-8 w-8 text-primary" />
            NIL Valuator
          </h1>
          <p className="text-muted-foreground mt-1">
            AI-powered NIL valuations for {totalInDatabase > 0 ? `${totalInDatabase.toLocaleString()}+` : ""} college athletes
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" size="sm" onClick={() => fetchPlayers(false)} disabled={isLoading}>
            <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-card border border-border flex-wrap">
          <TabsTrigger
            value="search"
            className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
          >
            <Search className="h-4 w-4 mr-2" />
            Search Players
          </TabsTrigger>
          <TabsTrigger
            value="custom"
            className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
          >
            <Sparkles className="h-4 w-4 mr-2" />
            Custom Valuation
          </TabsTrigger>
          <TabsTrigger
            value="growth"
            className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
          >
            <TrendingUp className="h-4 w-4 mr-2" />
            Social Growth
          </TabsTrigger>
          <TabsTrigger
            value="transfer"
            className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
          >
            <DollarSign className="h-4 w-4 mr-2" />
            Transfer Value
          </TabsTrigger>
        </TabsList>

        {/* Search Tab */}
        <TabsContent value="search" className="space-y-6">
          {/* Search & Filters */}
          <Card className="glass">
            <CardContent className="p-6">
              <div className="flex flex-col lg:flex-row gap-4">
                {/* Search Input */}
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search by player name or school..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-input border-border h-11"
                    />
                  </div>
                </div>

                {/* Position Filter */}
                <Select value={selectedPosition} onValueChange={setSelectedPosition}>
                  <SelectTrigger className="w-full lg:w-40 h-11">
                    <SelectValue placeholder="Position" />
                  </SelectTrigger>
                  <SelectContent>
                    {positions.map((pos) => (
                      <SelectItem key={pos} value={pos}>
                        {pos}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {/* Conference Filter */}
                <Select value={selectedConference} onValueChange={setSelectedConference}>
                  <SelectTrigger className="w-full lg:w-40 h-11">
                    <SelectValue placeholder="Conference" />
                  </SelectTrigger>
                  <SelectContent>
                    {conferences.map((conf) => (
                      <SelectItem key={conf} value={conf}>
                        {conf}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                {/* Star Filter */}
                <Select value={selectedStars} onValueChange={setSelectedStars}>
                  <SelectTrigger className="w-full lg:w-28 h-11">
                    <Star className="h-4 w-4 mr-1 text-yellow-500" />
                    <SelectValue placeholder="Stars" />
                  </SelectTrigger>
                  <SelectContent>
                    {starFilters.map((stars) => (
                      <SelectItem key={stars} value={stars}>
                        {stars === "All" ? "All Stars" : `${stars} Stars`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>

                <Button
                  variant="outline"
                  className="h-11"
                  onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                >
                  <Ruler className="h-4 w-4 mr-2" />
                  {showAdvancedFilters ? "Less" : "More"}
                </Button>

                <Button
                  className="h-11 bg-primary text-primary-foreground hover:bg-primary/90"
                  onClick={() => fetchPlayers(false)}
                  disabled={isLoading}
                >
                  <Filter className="h-4 w-4 mr-2" />
                  Apply
                </Button>
              </div>

              {/* Advanced Filters (Height/Weight) */}
              {showAdvancedFilters && (
                <div className="flex flex-col lg:flex-row gap-4 pt-4 border-t border-border">
                  <div className="flex items-center gap-2">
                    <Ruler className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Height:</span>
                    <Select value={selectedHeight} onValueChange={setSelectedHeight}>
                      <SelectTrigger className="w-32 h-9">
                        <SelectValue placeholder="Min Height" />
                      </SelectTrigger>
                      <SelectContent>
                        {heightFilters.map((h) => (
                          <SelectItem key={h} value={h}>
                            {h}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center gap-2">
                    <Weight className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Weight:</span>
                    <Select value={selectedWeight} onValueChange={setSelectedWeight}>
                      <SelectTrigger className="w-32 h-9">
                        <SelectValue placeholder="Min Weight" />
                      </SelectTrigger>
                      <SelectContent>
                        {weightFilters.map((w) => (
                          <SelectItem key={w} value={w}>
                            {w === "All" ? "All" : `${w} lbs`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  {selectedPosition !== "All" && HEIGHT_PRESETS[selectedPosition] && (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground bg-card px-3 py-1 rounded-lg">
                      <span>Ideal for {selectedPosition}:</span>
                      <span className="text-foreground">
                        {HEIGHT_PRESETS[selectedPosition].label}
                      </span>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Market Stats Summary */}
          {!isLoading && !error && totalInDatabase > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card className="glass p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <TrendingUp className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider">Total Players</p>
                    <p className="text-lg font-bold">{totalInDatabase.toLocaleString()}</p>
                  </div>
                </div>
              </Card>
              <Card className="glass p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <DollarSign className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider">Avg NIL Value</p>
                    <p className="text-lg font-bold">{formatCurrency(avgValue)}</p>
                  </div>
                </div>
              </Card>
              <Card className="glass p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <Star className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wider">Total Market Cap</p>
                    <p className="text-lg font-bold">{formatCurrency(marketCap)}</p>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {/* Error State */}
          {error && (
            <Card className="glass border-red-500/50">
              <CardContent className="p-6 flex items-center gap-4 text-red-500">
                <AlertCircle className="h-6 w-6" />
                <div>
                  <p className="font-semibold">Failed to load data</p>
                  <p className="text-sm text-muted-foreground">{error}</p>
                </div>
                <Button variant="outline" size="sm" onClick={() => fetchPlayers(false)} className="ml-auto">
                  Retry
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Loading State */}
          {isLoading && (
            <Card className="glass">
              <CardContent className="p-12 flex flex-col items-center justify-center gap-4">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
                <p className="text-muted-foreground">Loading NIL valuations...</p>
              </CardContent>
            </Card>
          )}

          {/* Results Table */}
          {!isLoading && !error && (
            <Card className="glass overflow-hidden">
              <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
                <CardTitle className="text-sm font-bold uppercase tracking-wider flex items-center justify-between">
                  <span>Top NIL Valuations</span>
                  <Badge variant="secondary">{filteredPlayers.length} players</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {/* Player Cards - Better UX than cramped table */}
                <div className="divide-y divide-border">
                  {filteredPlayers.length === 0 ? (
                    <div className="text-center py-12 text-muted-foreground">
                      No players found matching your criteria
                    </div>
                  ) : (
                    filteredPlayers.map((player) => (
                      <div
                        key={player.player_id}
                        className="p-4 hover:bg-card/50 cursor-pointer transition-colors flex items-center gap-4"
                        onClick={() => router.push(`/player/${encodeURIComponent(player.player_name)}`)}
                      >
                        {/* Rank */}
                        <div className="w-10 text-center">
                          <span className="text-lg font-bold text-muted-foreground">
                            #{player.rank}
                          </span>
                        </div>

                        {/* Player Photo - BIGGER */}
                        {player.headshot_url ? (
                          <Image
                            src={player.headshot_url}
                            alt={player.player_name}
                            width={64}
                            height={64}
                            className="rounded-full object-cover border-2 border-border flex-shrink-0"
                            unoptimized
                          />
                        ) : (
                          <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center border-2 border-border flex-shrink-0">
                            <span className="text-lg font-bold text-primary">
                              {player.player_name?.split(" ").map(n => n[0]).join("").slice(0, 2)}
                            </span>
                          </div>
                        )}

                        {/* Player Info - BIGGER NAME */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="text-lg font-bold truncate">{player.player_name}</h3>
                            <Badge variant="outline" className="font-mono text-xs flex-shrink-0">
                              {player.position}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-3 text-sm text-muted-foreground flex-wrap">
                            <span>{player.school}</span>
                            {player.stars && player.stars > 0 && (
                              <div className="flex text-yellow-500">
                                {Array.from({ length: Math.min(player.stars, 5) }).map((_, i) => (
                                  <Star key={i} className="h-3.5 w-3.5 fill-yellow-500" />
                                ))}
                              </div>
                            )}
                            {player.pff_overall && player.pff_overall > 0 && (
                              <Badge
                                variant="outline"
                                className={cn(
                                  "text-xs font-mono py-0 h-5",
                                  player.pff_overall >= 80 && "border-green-500/50 text-green-500",
                                  player.pff_overall >= 70 && player.pff_overall < 80 && "border-yellow-500/50 text-yellow-500",
                                  player.pff_overall < 70 && "border-orange-500/50 text-orange-500"
                                )}
                              >
                                {player.pff_overall.toFixed(1)}
                              </Badge>
                            )}
                            {showAdvancedFilters && player.height && player.weight && (
                              <span className="text-xs">
                                {formatHeight(player.height)} / {player.weight} lbs
                              </span>
                            )}
                          </div>
                        </div>

                        {/* NIL Values - RIGHT SIDE */}
                        <div className="text-right flex-shrink-0 min-w-[120px]">
                          <p className="text-xl font-bold text-primary">
                            {formatCurrency(player.valuation)}
                          </p>
                          <Badge
                            className={cn(
                              "font-semibold text-xs uppercase mt-1",
                              getTierBadge(player.nil_tier)
                            )}
                          >
                            {player.nil_tier}
                          </Badge>
                          <div className="flex flex-col gap-0.5 mt-1">
                            {player.performance_value && player.performance_value > 0 && (
                              <p className="text-xs text-emerald-400">
                                Perf: {formatCurrency(player.performance_value)}
                              </p>
                            )}
                            {player.on3_value && player.on3_value > 0 && (
                              <p className="text-xs text-muted-foreground">
                                On3: {formatCurrency(player.on3_value)}
                              </p>
                            )}
                          </div>
                        </div>

                        {/* Arrow */}
                        <ChevronRight className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                      </div>
                    ))
                  )}
                </div>

                {/* Load More / Pagination Info */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border-t border-border bg-card/30">
                  <div className="text-sm text-muted-foreground">
                    Showing <span className="font-semibold text-foreground">{filteredPlayers.length.toLocaleString()}</span> of{" "}
                    <span className="font-semibold text-foreground">{totalInDatabase.toLocaleString()}</span> players
                    {searchQuery && <span className="text-primary"> matching &quot;{searchQuery}&quot;</span>}
                  </div>
                  {hasMore && (
                    <Button
                      variant="default"
                      onClick={() => fetchPlayers(true)}
                      disabled={isLoading}
                      className="gap-2 bg-primary text-primary-foreground"
                    >
                      {isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                      Load More Players
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Custom Valuation Tab */}
        <TabsContent value="custom" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Form */}
            <Card className="glass">
              <CardHeader className="border-b border-border">
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  Custom NIL Valuation
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Player Name</Label>
                    <Input
                      placeholder="Enter player name"
                      className="bg-input"
                      value={customForm.name}
                      onChange={(e) => setCustomForm({ ...customForm, name: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>School</Label>
                    <Input
                      placeholder="Enter school"
                      className="bg-input"
                      value={customForm.school}
                      onChange={(e) => setCustomForm({ ...customForm, school: e.target.value })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Position</Label>
                    <Select
                      value={customForm.position}
                      onValueChange={(v) => setCustomForm({ ...customForm, position: v })}
                    >
                      <SelectTrigger className="bg-input">
                        <SelectValue placeholder="Select position" />
                      </SelectTrigger>
                      <SelectContent>
                        {positions.slice(1).map((pos) => (
                          <SelectItem key={pos} value={pos}>
                            {pos}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Stars (1-5)</Label>
                    <Select
                      value={customForm.stars}
                      onValueChange={(v) => setCustomForm({ ...customForm, stars: v })}
                    >
                      <SelectTrigger className="bg-input">
                        <SelectValue placeholder="Select rating" />
                      </SelectTrigger>
                      <SelectContent>
                        {[5, 4, 3, 2, 1].map((star) => (
                          <SelectItem key={star} value={star.toString()}>
                            {star} Star{star > 1 ? "s" : ""}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Instagram Followers</Label>
                    <Input
                      type="number"
                      placeholder="e.g., 50000"
                      className="bg-input"
                      value={customForm.instagram}
                      onChange={(e) => setCustomForm({ ...customForm, instagram: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Twitter/X Followers</Label>
                    <Input
                      type="number"
                      placeholder="e.g., 25000"
                      className="bg-input"
                      value={customForm.twitter}
                      onChange={(e) => setCustomForm({ ...customForm, twitter: e.target.value })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Performance Grade (Optional)</Label>
                  <Input
                    type="number"
                    placeholder="e.g., 85.5"
                    className="bg-input"
                    value={customForm.pffGrade}
                    onChange={(e) => setCustomForm({ ...customForm, pffGrade: e.target.value })}
                  />
                </div>

                <Button
                  className="w-full bg-primary text-primary-foreground hover:bg-primary/90 mt-4"
                  onClick={handleCustomValuation}
                  disabled={isCustomLoading || !customForm.name || !customForm.school || !customForm.position}
                >
                  {isCustomLoading ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Sparkles className="h-4 w-4 mr-2" />
                  )}
                  {isCustomLoading ? "Calculating..." : "Calculate NIL Value"}
                </Button>
              </CardContent>
            </Card>

            {/* Results Card */}
            <Card className="glass">
              <CardHeader className="border-b border-border">
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-primary" />
                  Valuation Result
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                {customResult ? (
                  <div className="space-y-6">
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground mb-2">Estimated NIL Value</p>
                      <p className="text-4xl font-bold text-primary">
                        {formatCurrency(customResult.value)}
                      </p>
                      <Badge className={cn("mt-2 uppercase", getTierBadge(customResult.tier))}>
                        {customResult.tier} Tier
                      </Badge>
                    </div>

                    <div className="space-y-3">
                      <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
                        Breakdown
                      </p>
                      {Object.entries(customResult.breakdown).map(([key, value]) => (
                        <div key={key} className="flex justify-between items-center text-sm">
                          <span className="text-muted-foreground capitalize">
                            {key.replace(/_/g, " ")}
                          </span>
                          <span className="font-semibold">
                            {key.includes("multiplier")
                              ? `${value}x`
                              : formatCurrency(value as number)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
                      <Info className="h-8 w-8 text-primary" />
                    </div>
                    <h3 className="text-lg font-semibold mb-2">Enter Player Details</h3>
                    <p className="text-muted-foreground text-sm">
                      Fill out the form to get an AI-powered NIL valuation estimate based on
                      performance, social media, and market factors.
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Social Growth Tab */}
        <TabsContent value="growth" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Player Selection */}
            <Card className="glass">
              <CardHeader className="border-b border-border">
                <CardTitle className="flex items-center gap-2">
                  <Search className="h-5 w-5 text-primary" />
                  Select a Player
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                {/* API-powered search for player selection */}
                <div className="relative mb-4">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search any player..."
                    className="pl-10 bg-input border-border"
                    value={tabSearchQuery}
                    onChange={(e) => setTabSearchQuery(e.target.value)}
                  />
                  {isTabSearching && (
                    <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
                  )}
                  {/* Search Results Dropdown */}
                  {tabSearchResults.length > 0 && tabSearchQuery.length >= 2 && (
                    <div className="absolute z-50 w-full mt-1 bg-card border border-border rounded-lg shadow-lg max-h-64 overflow-y-auto">
                      {tabSearchResults.map((result) => (
                        <div
                          key={result.name}
                          className="p-3 hover:bg-primary/10 cursor-pointer flex items-center gap-3"
                          onClick={() => {
                            setSelectedPlayer({
                              player_id: result.name,
                              player_name: result.name,
                              position: result.position,
                              school: result.school,
                              valuation: result.nil_value || 0,
                              nil_tier: "entry",
                              headshot_url: result.headshot_url,
                              stars: result.stars,
                              rank: 0,
                            });
                            setTabSearchQuery("");
                            setTabSearchResults([]);
                          }}
                        >
                          {result.headshot_url ? (
                            <Image src={result.headshot_url} alt={result.name} width={32} height={32} className="rounded-full" unoptimized />
                          ) : (
                            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold">
                              {result.name.split(" ").map(n => n[0]).join("").slice(0, 2)}
                            </div>
                          )}
                          <div className="flex-1">
                            <p className="font-semibold text-sm">{result.name}</p>
                            <p className="text-xs text-muted-foreground">{result.position} • {result.school}</p>
                          </div>
                          {result.nil_value && (
                            <span className="text-sm font-bold text-primary">{formatCurrency(result.nil_value)}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                {selectedPlayer ? (
                  <div className="flex items-center gap-4 p-4 bg-card rounded-lg border border-border">
                    {selectedPlayer.headshot_url ? (
                      <Image
                        src={selectedPlayer.headshot_url}
                        alt={selectedPlayer.player_name}
                        width={50}
                        height={50}
                        className="rounded-full object-cover"
                        unoptimized
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                        <span className="text-sm font-bold text-primary">
                          {selectedPlayer.player_name?.split(" ").map(n => n[0]).join("").slice(0, 2)}
                        </span>
                      </div>
                    )}
                    <div className="flex-1">
                      <p className="font-bold">{selectedPlayer.player_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {selectedPlayer.position} • {selectedPlayer.school}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-primary">{formatCurrency(selectedPlayer.valuation)}</p>
                      <Badge className={cn("uppercase", getTierBadge(selectedPlayer.nil_tier))}>
                        {selectedPlayer.nil_tier}
                      </Badge>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4 text-muted-foreground">
                    <TrendingUp className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Search above or select from the Search Players tab</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Growth Simulator */}
            {selectedPlayer && (
              <SocialGrowthSimulator
                currentNILValue={selectedPlayer.valuation}
                currentFollowers={50000}
                playerName={selectedPlayer.player_name}
              />
            )}
          </div>
        </TabsContent>

        {/* Transfer Value Tab */}
        <TabsContent value="transfer" className="space-y-6">
          <div className="grid grid-cols-1 gap-6">
            {/* Player Selection */}
            <Card className="glass">
              <CardHeader className="border-b border-border">
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-primary" />
                  Transfer Value Analysis
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                {/* API-powered search for player selection */}
                <div className="relative mb-4">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search any player..."
                    className="pl-10 bg-input border-border"
                    value={tabSearchQuery}
                    onChange={(e) => setTabSearchQuery(e.target.value)}
                  />
                  {isTabSearching && (
                    <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
                  )}
                  {/* Search Results Dropdown */}
                  {tabSearchResults.length > 0 && tabSearchQuery.length >= 2 && (
                    <div className="absolute z-50 w-full mt-1 bg-card border border-border rounded-lg shadow-lg max-h-64 overflow-y-auto">
                      {tabSearchResults.map((result) => (
                        <div
                          key={result.name}
                          className="p-3 hover:bg-primary/10 cursor-pointer flex items-center gap-3"
                          onClick={() => {
                            setSelectedPlayer({
                              player_id: result.name,
                              player_name: result.name,
                              position: result.position,
                              school: result.school,
                              valuation: result.nil_value || 0,
                              nil_tier: "entry",
                              headshot_url: result.headshot_url,
                              stars: result.stars,
                              rank: 0,
                            });
                            setTabSearchQuery("");
                            setTabSearchResults([]);
                          }}
                        >
                          {result.headshot_url ? (
                            <Image src={result.headshot_url} alt={result.name} width={32} height={32} className="rounded-full" unoptimized />
                          ) : (
                            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-xs font-bold">
                              {result.name.split(" ").map(n => n[0]).join("").slice(0, 2)}
                            </div>
                          )}
                          <div className="flex-1">
                            <p className="font-semibold text-sm">{result.name}</p>
                            <p className="text-xs text-muted-foreground">{result.position} • {result.school}</p>
                          </div>
                          {result.nil_value && (
                            <span className="text-sm font-bold text-primary">{formatCurrency(result.nil_value)}</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <p className="text-muted-foreground mb-4 text-sm">
                  See how a player&apos;s NIL value would change at different schools based on market size and brand value.
                </p>
                {selectedPlayer ? (
                  <div className="flex items-center gap-4 p-4 bg-card rounded-lg border border-border mb-6">
                    {selectedPlayer.headshot_url ? (
                      <Image
                        src={selectedPlayer.headshot_url}
                        alt={selectedPlayer.player_name}
                        width={50}
                        height={50}
                        className="rounded-full object-cover"
                        unoptimized
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                        <span className="text-sm font-bold text-primary">
                          {selectedPlayer.player_name?.split(" ").map(n => n[0]).join("").slice(0, 2)}
                        </span>
                      </div>
                    )}
                    <div className="flex-1">
                      <p className="font-bold">{selectedPlayer.player_name}</p>
                      <p className="text-sm text-muted-foreground">
                        {selectedPlayer.position} • {selectedPlayer.school}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-primary">{formatCurrency(selectedPlayer.valuation)}</p>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4 text-muted-foreground">
                    <DollarSign className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Search above or select from the Search Players tab</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Transfer Value Chart */}
            {selectedPlayer && (
              <TransferValueChart
                currentSchool={selectedPlayer.school}
                currentValue={selectedPlayer.valuation}
                position={selectedPlayer.position}
              />
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
