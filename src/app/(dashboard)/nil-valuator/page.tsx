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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Search,
  TrendingUp,
  TrendingDown,
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
import { getNILLeaderboard, predictNIL, type NILLeaderboardPlayer, type PlayerInput } from "@/lib/api/nil";
import { calculateDetailedWAR, analyzeTransferValue, getSchoolTier } from "@/lib/api/war";
import { SocialGrowthSimulator } from "@/components/charts/nil-growth-chart";
import { TransferValueChart } from "@/components/charts/transfer-value-chart";
import { PlayerWARCard } from "@/components/charts/war-gauge";
import { HEIGHT_PRESETS, WEIGHT_PRESETS, formatHeight } from "@/lib/constants/presets";
import { useWatchlist } from "@/hooks/use-watchlist";
import { Heart, HeartOff } from "lucide-react";

const positions = ["All", "QB", "RB", "WR", "TE", "OL", "DL", "LB", "CB", "S"];
const conferences = ["All", "SEC", "Big Ten", "Big 12", "ACC", "Pac-12", "AAC", "MWC", "Sun Belt", "C-USA"];
const starFilters = ["All", "5", "4+", "3+", "2+"];
const heightFilters = ["All", "6'4\"+", "6'2\"+", "6'0\"+", "5'10\"+"];
const weightFilters = ["All", "300+", "250+", "220+", "200+", "180+"];

// Extended player type with measurables
interface NILPlayerWithMeasurables extends NILLeaderboardPlayer {
  height?: number;
  weight?: number;
  pff_overall?: number;
  pff_offense?: number;
  pff_defense?: number;
  stars?: number;
}

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
  if (value >= 1000000) {
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
    established: "tier-premium",
    emerging: "tier-solid",
    developing: "tier-moderate",
  };
  return styles[tier] || "tier-entry";
}

export default function NILValuatorPage() {
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

  // Watchlist
  const { isInWatchlist, toggleWatchlist } = useWatchlist();

  // Player detail sheet
  const [selectedPlayer, setSelectedPlayer] = useState<NILPlayerWithMeasurables | null>(null);

  // WAR calculation for selected player
  const playerWAR = useMemo(() => {
    if (!selectedPlayer) return null;

    const warResult = calculateDetailedWAR({
      position: selectedPlayer.position,
      stars: selectedPlayer.stars,
      nil_value: selectedPlayer.valuation,
      destination_school: selectedPlayer.school,
      is_predicted_nil: true,
    });

    const { tier } = getSchoolTier(selectedPlayer.school);
    const transferValue = analyzeTransferValue(
      warResult.war,
      selectedPlayer.valuation,
      selectedPlayer.position
    );

    return {
      ...warResult,
      winProbAdded: warResult.war * 7, // Each WAR = ~7% win probability
      transferValue,
    };
  }, [selectedPlayer]);

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

  // Fetch NIL leaderboard data
  const fetchPlayers = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params: {
        position?: string;
        conference?: string;
        limit: number;
      } = { limit: 100 };

      if (selectedPosition !== "All") {
        params.position = selectedPosition;
      }
      if (selectedConference !== "All") {
        params.conference = selectedConference;
      }

      const response = await getNILLeaderboard(params);
      setPlayers(response.players);
      setTotalPlayers(response.total);
    } catch (err) {
      console.error("Failed to fetch NIL leaderboard:", err);
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setIsLoading(false);
    }
  }, [selectedPosition, selectedConference]);

  // Initial load and refetch on filter changes
  useEffect(() => {
    fetchPlayers();
  }, [fetchPlayers]);

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
      const tier = value >= 1000000 ? "mega" : value >= 500000 ? "premium" : value >= 200000 ? "established" : value >= 50000 ? "emerging" : "developing";

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
            AI-powered NIL valuations for 17,500+ college athletes
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
          <Button variant="outline" size="sm" onClick={fetchPlayers} disabled={isLoading}>
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
                  onClick={fetchPlayers}
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

          {/* Error State */}
          {error && (
            <Card className="glass border-red-500/50">
              <CardContent className="p-6 flex items-center gap-4 text-red-500">
                <AlertCircle className="h-6 w-6" />
                <div>
                  <p className="font-semibold">Failed to load data</p>
                  <p className="text-sm text-muted-foreground">{error}</p>
                </div>
                <Button variant="outline" size="sm" onClick={fetchPlayers} className="ml-auto">
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
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent border-border">
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground w-12">
                        #
                      </TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground w-16">

                      </TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">
                        Player
                      </TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">
                        Position
                      </TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">
                        School
                      </TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-center">
                        Stars
                      </TableHead>
                      {showAdvancedFilters && (
                        <>
                          <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-center">
                            Ht/Wt
                          </TableHead>
                          <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-center">
                            PFF
                          </TableHead>
                        </>
                      )}
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-right">
                        NIL Value
                      </TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">
                        Tier
                      </TableHead>
                      <TableHead className="w-10"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredPlayers.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={showAdvancedFilters ? 11 : 9} className="text-center py-8 text-muted-foreground">
                          No players found matching your criteria
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredPlayers.map((player) => (
                        <TableRow
                          key={player.player_id}
                          className="cursor-pointer hover:bg-card border-border"
                          onClick={() => setSelectedPlayer(player)}
                        >
                          <TableCell className="text-muted-foreground font-mono text-sm">
                            {player.rank}
                          </TableCell>
                          <TableCell>
                            {player.headshot_url ? (
                              <Image
                                src={player.headshot_url}
                                alt={player.player_name}
                                width={40}
                                height={40}
                                className="rounded-full object-cover"
                                unoptimized
                              />
                            ) : (
                              <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                                <span className="text-xs font-bold text-primary">
                                  {player.player_name?.split(" ").map(n => n[0]).join("").slice(0, 2)}
                                </span>
                              </div>
                            )}
                          </TableCell>
                          <TableCell className="font-semibold">{player.player_name}</TableCell>
                          <TableCell>
                            <Badge variant="outline" className="font-mono text-xs">
                              {player.position}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-muted-foreground">{player.school}</TableCell>
                          <TableCell className="text-center">
                            {player.stars ? (
                              <div className="flex justify-center text-yellow-500">
                                {Array.from({ length: Math.min(player.stars, 5) }).map((_, i) => (
                                  <Star key={i} className="h-3 w-3 fill-yellow-500" />
                                ))}
                              </div>
                            ) : (
                              "—"
                            )}
                          </TableCell>
                          {showAdvancedFilters && (
                            <>
                              <TableCell className="text-center text-sm text-muted-foreground">
                                {player.height && player.weight
                                  ? `${formatHeight(player.height)} / ${player.weight}`
                                  : "—"}
                              </TableCell>
                              <TableCell className="text-center">
                                {player.pff_overall ? (
                                  <Badge
                                    variant="outline"
                                    className={cn(
                                      "font-mono text-xs",
                                      player.pff_overall >= 80 && "border-green-500 text-green-500",
                                      player.pff_overall >= 70 && player.pff_overall < 80 && "border-yellow-500 text-yellow-500",
                                      player.pff_overall < 70 && "border-orange-500 text-orange-500"
                                    )}
                                  >
                                    {player.pff_overall.toFixed(1)}
                                  </Badge>
                                ) : (
                                  "—"
                                )}
                              </TableCell>
                            </>
                          )}
                          <TableCell className="text-right font-bold text-primary">
                            {formatCurrency(player.valuation)}
                          </TableCell>
                          <TableCell>
                            <Badge
                              className={cn(
                                "font-semibold text-xs uppercase",
                                getTierBadge(player.nil_tier)
                              )}
                            >
                              {player.nil_tier}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <ChevronRight className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
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
                  <Label>PFF Grade (Optional)</Label>
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
                <p className="text-muted-foreground mb-4">
                  Choose a player from the leaderboard or enter custom values to simulate social media growth impact.
                </p>
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
                  <div className="text-center py-8 text-muted-foreground">
                    <TrendingUp className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Click on a player in the Search Players tab to select them</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Growth Simulator */}
            {selectedPlayer && (
              <SocialGrowthSimulator
                currentNILValue={selectedPlayer.valuation}
                currentFollowers={selectedPlayer.social_followers || 50000}
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
                <p className="text-muted-foreground mb-4">
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
                  <div className="text-center py-8 text-muted-foreground">
                    <DollarSign className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Click on a player in the Search Players tab to analyze their transfer value</p>
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

      {/* Market Stats Footer */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="glass p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <TrendingUp className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wider">Total Players</p>
              <p className="text-lg font-bold">{(totalPlayers || 0).toLocaleString()}</p>
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
              <p className="text-lg font-bold">
                {players.length > 0
                  ? formatCurrency(
                      players.reduce((sum, p) => sum + p.valuation, 0) / players.length
                    )
                  : "$0"}
              </p>
            </div>
          </div>
        </Card>
        <Card className="glass p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Star className="h-5 w-5 text-primary" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wider">Market Cap</p>
              <p className="text-lg font-bold">
                {formatCurrency(players.reduce((sum, p) => sum + p.valuation, 0))}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Player Detail Sheet */}
      <Sheet open={!!selectedPlayer} onOpenChange={(open) => !open && setSelectedPlayer(null)}>
        <SheetContent className="w-full sm:max-w-lg overflow-y-auto">
          {selectedPlayer && (
            <>
              <SheetHeader className="pb-6">
                <div className="flex items-center gap-4">
                  {selectedPlayer.headshot_url ? (
                    <Image
                      src={selectedPlayer.headshot_url}
                      alt={selectedPlayer.player_name}
                      width={80}
                      height={80}
                      className="rounded-full object-cover border-2 border-primary"
                      unoptimized
                    />
                  ) : (
                    <div className="w-20 h-20 rounded-full bg-primary/20 flex items-center justify-center border-2 border-primary">
                      <span className="text-xl font-bold text-primary">
                        {selectedPlayer.player_name?.split(" ").map(n => n[0]).join("").slice(0, 2)}
                      </span>
                    </div>
                  )}
                  <div>
                    <SheetTitle className="text-xl">{selectedPlayer.player_name}</SheetTitle>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="font-mono">
                        {selectedPlayer.position}
                      </Badge>
                      <span className="text-sm text-muted-foreground">{selectedPlayer.school}</span>
                    </div>
                    {selectedPlayer.stars && (
                      <div className="flex mt-1 text-yellow-500">
                        {Array.from({ length: Math.min(selectedPlayer.stars, 5) }).map((_, i) => (
                          <Star key={i} className="h-4 w-4 fill-yellow-500" />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </SheetHeader>

              {/* NIL Value Section */}
              <div className="space-y-6">
                <Card className="glass">
                  <CardContent className="p-4">
                    <div className="text-center">
                      <p className="text-sm text-muted-foreground mb-1">NIL Valuation</p>
                      <p className="text-3xl font-bold text-primary">
                        {formatCurrency(selectedPlayer.valuation)}
                      </p>
                      <Badge className={cn("mt-2 uppercase", getTierBadge(selectedPlayer.nil_tier))}>
                        {selectedPlayer.nil_tier} Tier
                      </Badge>
                    </div>
                  </CardContent>
                </Card>

                {/* Measurables */}
                {(selectedPlayer.height || selectedPlayer.weight) && (
                  <Card className="glass">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                        <Ruler className="h-4 w-4" />
                        Measurables
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 pt-0">
                      <div className="grid grid-cols-2 gap-4">
                        {selectedPlayer.height && (
                          <div className="text-center p-3 bg-card rounded-lg">
                            <p className="text-xs text-muted-foreground">Height</p>
                            <p className="text-lg font-bold">{formatHeight(selectedPlayer.height)}</p>
                          </div>
                        )}
                        {selectedPlayer.weight && (
                          <div className="text-center p-3 bg-card rounded-lg">
                            <p className="text-xs text-muted-foreground">Weight</p>
                            <p className="text-lg font-bold">{selectedPlayer.weight} lbs</p>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* PFF Grades */}
                {selectedPlayer.pff_overall && (
                  <Card className="glass">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                        <TrendingUp className="h-4 w-4" />
                        PFF Grades
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 pt-0">
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-muted-foreground">Overall</span>
                          <Badge
                            variant="outline"
                            className={cn(
                              "font-mono",
                              selectedPlayer.pff_overall >= 80 && "border-green-500 text-green-500",
                              selectedPlayer.pff_overall >= 70 && selectedPlayer.pff_overall < 80 && "border-yellow-500 text-yellow-500",
                              selectedPlayer.pff_overall < 70 && "border-orange-500 text-orange-500"
                            )}
                          >
                            {selectedPlayer.pff_overall.toFixed(1)}
                          </Badge>
                        </div>
                        {selectedPlayer.pff_offense && (
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-muted-foreground">Offense</span>
                            <span className="font-mono text-sm">{selectedPlayer.pff_offense.toFixed(1)}</span>
                          </div>
                        )}
                        {selectedPlayer.pff_defense && (
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-muted-foreground">Defense</span>
                            <span className="font-mono text-sm">{selectedPlayer.pff_defense.toFixed(1)}</span>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* WAR / Win Impact Analysis */}
                {playerWAR && (
                  <PlayerWARCard
                    war={playerWAR.war}
                    warLow={playerWAR.war_low}
                    warHigh={playerWAR.war_high}
                    confidence={playerWAR.confidence}
                    winProbAdded={playerWAR.winProbAdded}
                    breakdown={playerWAR.breakdown}
                    transferValue={{
                      costPerWAR: playerWAR.transferValue.cost_per_war,
                      fairValue: playerWAR.transferValue.fair_value_per_war,
                      valueRatio: playerWAR.transferValue.value_ratio,
                      valueRating: playerWAR.transferValue.value_rating,
                      roiProjection: playerWAR.transferValue.roi_projection,
                      marketComparison: playerWAR.transferValue.market_comparison,
                    }}
                  />
                )}

                {/* Quick Actions */}
                <div className="flex flex-col gap-2">
                  <Button
                    className={cn(
                      "w-full",
                      isInWatchlist(selectedPlayer.player_id)
                        ? "bg-primary text-primary-foreground hover:bg-primary/90"
                        : "variant-outline"
                    )}
                    variant={isInWatchlist(selectedPlayer.player_id) ? "default" : "outline"}
                    onClick={() =>
                      toggleWatchlist({
                        id: selectedPlayer.player_id,
                        player_name: selectedPlayer.player_name,
                        position: selectedPlayer.position,
                        school: selectedPlayer.school,
                        nil_valuation: selectedPlayer.valuation,
                        stars: selectedPlayer.stars,
                        headshot_url: selectedPlayer.headshot_url,
                      })
                    }
                  >
                    {isInWatchlist(selectedPlayer.player_id) ? (
                      <>
                        <HeartOff className="h-4 w-4 mr-2" />
                        Remove from Watchlist
                      </>
                    ) : (
                      <>
                        <Heart className="h-4 w-4 mr-2" />
                        Add to Watchlist
                      </>
                    )}
                  </Button>
                  <div className="flex gap-2">
                    <Button className="flex-1" variant="outline" onClick={() => setActiveTab("transfer")}>
                      <TrendingUp className="h-4 w-4 mr-2" />
                      Transfer Value
                    </Button>
                    <Button className="flex-1" variant="outline" onClick={() => setActiveTab("growth")}>
                      <DollarSign className="h-4 w-4 mr-2" />
                      Growth Sim
                    </Button>
                  </div>
                </div>
              </div>
            </>
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
