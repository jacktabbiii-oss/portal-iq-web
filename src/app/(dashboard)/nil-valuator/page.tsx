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
import { HEIGHT_PRESETS, WEIGHT_PRESETS, formatHeight } from "@/lib/constants/presets";

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
        <TabsList className="bg-card border border-border">
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
                        <TableCell colSpan={showAdvancedFilters ? 10 : 8} className="text-center py-8 text-muted-foreground">
                          No players found matching your criteria
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredPlayers.map((player) => (
                        <TableRow
                          key={player.player_id}
                          className="cursor-pointer hover:bg-card border-border"
                        >
                          <TableCell className="text-muted-foreground font-mono text-sm">
                            {player.rank}
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
    </div>
  );
}
