"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import Image from "next/image";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
} from "@/components/ui/table"; // Used in Team Rankings tab
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Search,
  ArrowRightLeft,
  Star,
  Filter,
  Download,
  RefreshCw,
  ChevronRight,
  TrendingUp,
  Users,
  School,
  Calendar,
  Loader2,
  AlertCircle,
  Ruler,
  Weight,
  DollarSign,
  MapPin,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getActivePortalPlayers, type PortalPlayer } from "@/lib/api/portal";
import { getPlayerStats, type PlayerStats } from "@/lib/api/players";
import { calculateDetailedWAR, analyzeTransferValue, getSchoolTier, calculateTeamPortalScores, type TeamPortalScore, type WARPlayer } from "@/lib/api/war";
import { PlayerWARCard } from "@/components/charts/war-gauge";
import { HEIGHT_PRESETS, WEIGHT_PRESETS, formatHeight } from "@/lib/constants/presets";
import { useWatchlist } from "@/hooks/use-watchlist";
import { Heart, HeartOff } from "lucide-react";

const positions = ["All", "QB", "RB", "WR", "TE", "OT", "OG", "EDGE", "DT", "LB", "CB", "S"];
const statuses = ["All", "In Portal", "Committed", "Withdrawn"];
const starFilters = ["All", "5", "4+", "3+", "2+"];
const heightFilters = ["All", "6'4\"+", "6'2\"+", "6'0\"+", "5'10\"+"];
const weightFilters = ["All", "300+", "250+", "220+", "200+", "180+"];

function formatCurrency(value: number | undefined | null): string {
  if (value == null || isNaN(value)) return "$0";
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}K`;
  }
  return `$${value.toLocaleString()}`;
}

function getStatusBadge(status: string) {
  const styles: Record<string, string> = {
    available: "status-active",
    committed: "status-committed",
    withdrawn: "status-withdrawn",
    "In Portal": "status-active",
    Committed: "status-committed",
    Withdrawn: "status-withdrawn",
  };
  return styles[status] || "status-active";
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    available: "In Portal",
    committed: "Committed",
    withdrawn: "Withdrawn",
  };
  return labels[status] || status;
}

// Extend PortalPlayer type with measurables
interface PortalPlayerWithMeasurables extends PortalPlayer {
  height?: number;
  weight?: number;
  pff_overall?: number;
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

export default function PortalIntelligencePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPosition, setSelectedPosition] = useState("All");
  const [selectedStatus, setSelectedStatus] = useState("All");
  const [selectedStars, setSelectedStars] = useState("All");
  const [selectedHeight, setSelectedHeight] = useState("All");
  const [selectedWeight, setSelectedWeight] = useState("All");
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);

  // API state
  const [players, setPlayers] = useState<PortalPlayerWithMeasurables[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Player detail sheet
  const [selectedPlayer, setSelectedPlayer] = useState<PortalPlayerWithMeasurables | null>(null);
  const [playerStats, setPlayerStats] = useState<PlayerStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);

  // Fetch detailed stats when a player is selected
  useEffect(() => {
    if (selectedPlayer?.player_name) {
      setIsLoadingStats(true);
      getPlayerStats(selectedPlayer.player_name)
        .then((stats) => {
          setPlayerStats(stats);
        })
        .catch((err) => {
          console.error("Failed to fetch player stats:", err);
          setPlayerStats(null);
        })
        .finally(() => {
          setIsLoadingStats(false);
        });
    } else {
      setPlayerStats(null);
    }
  }, [selectedPlayer?.player_name]);

  // Watchlist
  const { isInWatchlist, toggleWatchlist } = useWatchlist();

  // WAR calculation for selected player
  const playerWAR = useMemo(() => {
    if (!selectedPlayer) return null;

    const targetSchool = selectedPlayer.destination_school || selectedPlayer.origin_school;
    const warResult = calculateDetailedWAR({
      position: selectedPlayer.position,
      stars: selectedPlayer.stars,
      nil_value: selectedPlayer.nil_valuation,
      destination_school: targetSchool,
      is_predicted_nil: true,
    });

    const transferValue = analyzeTransferValue(
      warResult.war,
      selectedPlayer.nil_valuation || 50000,
      selectedPlayer.position
    );

    return {
      ...warResult,
      winProbAdded: warResult.war * 7,
      transferValue,
    };
  }, [selectedPlayer]);

  // Stats computed from data
  const [stats, setStats] = useState({
    activeInPortal: 0,
    committed: 0,
    newToday: 0,
    schools: 0,
  });

  // Calculate team portal scores from committed players
  const teamScores = useMemo(() => {
    // Filter to committed players with destinations
    const committedPlayers = players.filter(
      (p) => p.status === "committed" && p.destination_school
    );

    // Convert to WAR format for scoring
    const warPlayers: WARPlayer[] = committedPlayers.map((p, index) => {
      const war = calculateDetailedWAR({
        position: p.position,
        stars: p.stars,
        nil_value: p.nil_valuation,
        destination_school: p.destination_school,
        is_predicted_nil: true,
      });

      return {
        rank: index + 1,
        player_id: p.player_id,
        player_name: p.player_name,
        position: p.position,
        school: p.destination_school || p.origin_school,
        nil_valuation: p.nil_valuation || 0,
        war: war.war,
        win_prob_added: war.war * 7,
        value_per_win: war.war > 0 ? (p.nil_valuation || 0) / war.war : 0,
        grade: war.war >= 2.0 ? "Elite" : war.war >= 1.2 ? "Premium" : war.war >= 0.6 ? "Solid" : "Average",
        stars: p.stars,
        origin_school: p.origin_school,
      };
    });

    // Calculate team scores - limit to top 20
    return calculateTeamPortalScores(warPlayers).slice(0, 20);
  }, [players]);

  // Pagination state
  const [totalInDatabase, setTotalInDatabase] = useState<number>(0);
  const [hasMore, setHasMore] = useState<boolean>(false);
  const [currentPage, setCurrentPage] = useState<number>(0);
  const pageSize = 50; // Show 50 players per page for readability

  // Fetch portal players with pagination support
  const fetchPlayers = useCallback(async (loadMore = false) => {
    setIsLoading(true);
    setError(null);

    try {
      // Map UI status to API status
      let apiStatus: "available" | "committed" | "all" | undefined = "all";
      if (selectedStatus === "In Portal") {
        apiStatus = "available";
      } else if (selectedStatus === "Committed") {
        apiStatus = "committed";
      } else if (selectedStatus === "All") {
        apiStatus = "all";
      }

      const params: {
        position?: string;
        status?: "available" | "committed" | "all";
        limit: number;
        offset: number;
        min_stars?: number;
        search?: string;
      } = {
        limit: pageSize,
        offset: loadMore ? (currentPage + 1) * pageSize : 0,
        status: apiStatus,
      };

      if (selectedPosition !== "All") {
        params.position = selectedPosition;
      }

      // API-level star filter
      if (selectedStars !== "All") {
        const minStars = parseInt(selectedStars.replace("+", ""));
        if (!isNaN(minStars)) {
          params.min_stars = minStars;
        }
      }

      // Server-side search
      if (searchQuery && searchQuery.length >= 2) {
        params.search = searchQuery;
      }

      const response = await getActivePortalPlayers(params);

      // Response includes pagination info
      const playersList = response.players || [];

      if (loadMore) {
        setPlayers(prev => [...prev, ...playersList] as PortalPlayerWithMeasurables[]);
        setCurrentPage(prev => prev + 1);
      } else {
        setPlayers(playersList as PortalPlayerWithMeasurables[]);
        setCurrentPage(0);
      }

      setTotalCount(response.total || playersList.length);
      setTotalInDatabase(response.total_count || response.total || 0);
      setHasMore(response.has_more || false);

      // Use stats from API (calculated across ALL matching players, not just loaded ones)
      setStats({
        activeInPortal: response.active_in_portal || 0,
        committed: response.committed || 0,
        newToday: Math.floor((response.total_count || response.total) * 0.02),
        schools: response.schools_active || 0,
      });
    } catch (err) {
      console.error("Failed to fetch portal players:", err);
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setIsLoading(false);
    }
  }, [selectedPosition, selectedStatus, selectedStars, searchQuery, currentPage, pageSize]);

  // Initial load and refetch on filter changes
  useEffect(() => {
    fetchPlayers(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPosition, selectedStatus, selectedStars]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery.length >= 2 || searchQuery.length === 0) {
        fetchPlayers(false);
      }
    }, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery]);

  // Client-side filtering (search + measurables)
  const filteredPlayers = players.filter((player) => {
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      const matchesSearch =
        player.player_name.toLowerCase().includes(query) ||
        player.origin_school.toLowerCase().includes(query) ||
        (player.destination_school?.toLowerCase().includes(query) ?? false);
      if (!matchesSearch) return false;
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

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <ArrowRightLeft className="h-8 w-8 text-primary" />
            Portal Intelligence
          </h1>
          <p className="text-muted-foreground mt-1">
            Track {totalCount > 0 ? totalCount.toLocaleString() : "11,000"}+ transfer portal entries in real-time
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

      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                <TrendingUp className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Active in Portal</p>
                <p className="text-2xl font-bold">{(stats.activeInPortal || 0).toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <Users className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Committed</p>
                <p className="text-2xl font-bold">{(stats.committed || 0).toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                <Calendar className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Total Players</p>
                <p className="text-2xl font-bold">{totalInDatabase.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                <School className="h-5 w-5 text-purple-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Schools Active</p>
                <p className="text-2xl font-bold">{stats.schools}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="players" className="space-y-6">
        <TabsList className="bg-card border border-border">
          <TabsTrigger
            value="players"
            className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
          >
            <Users className="h-4 w-4 mr-2" />
            Players
          </TabsTrigger>
          <TabsTrigger
            value="rankings"
            className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
          >
            <School className="h-4 w-4 mr-2" />
            Team Rankings
          </TabsTrigger>
        </TabsList>

        {/* Players Tab */}
        <TabsContent value="players" className="space-y-6">
          {/* Filters */}
          <Card className="glass">
            <CardContent className="p-6 space-y-4">
              {/* Primary Filters Row */}
              <div className="flex flex-col lg:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search players or schools..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-input border-border h-11"
                    />
                  </div>
                </div>
                <Select value={selectedPosition} onValueChange={setSelectedPosition}>
                  <SelectTrigger className="w-full lg:w-32 h-11">
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
                <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                  <SelectTrigger className="w-full lg:w-36 h-11">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    {statuses.map((status) => (
                      <SelectItem key={status} value={status}>
                        {status}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
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
                <div className="flex flex-col lg:flex-row gap-4 pt-2 border-t border-border">
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
                <p className="text-muted-foreground">Loading portal entries...</p>
              </CardContent>
            </Card>
          )}

          {/* Players List */}
          {!isLoading && !error && (
            <Card className="glass overflow-hidden">
              <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
                <CardTitle className="text-sm font-bold uppercase tracking-wider flex items-center justify-between">
                  <span>Transfer Portal Entries</span>
                  <Badge variant="secondary">{filteredPlayers.length} players</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {filteredPlayers.length === 0 ? (
                  <div className="text-center py-12 text-muted-foreground">
                    No players found matching your criteria
                  </div>
                ) : (
                  <div className="divide-y divide-border">
                    {filteredPlayers.slice(0, 200).map((player) => (
                      <div
                        key={player.player_id}
                        className="p-4 hover:bg-card/50 cursor-pointer transition-colors flex items-center gap-4"
                        onClick={() => setSelectedPlayer(player)}
                      >
                        {/* Player Photo - BIGGER */}
                        {player.headshot_url ? (
                          <Image
                            src={player.headshot_url}
                            alt={player.player_name}
                            width={64}
                            height={64}
                            className="rounded-full object-cover flex-shrink-0"
                            unoptimized
                          />
                        ) : (
                          <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
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
                            <Badge className={cn("text-xs flex-shrink-0", getStatusBadge(player.status))}>
                              {getStatusLabel(player.status)}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-4 text-sm text-muted-foreground">
                            <span className="flex items-center gap-1">
                              <School className="h-3 w-3" />
                              {player.origin_school}
                            </span>
                            {player.destination_school && (
                              <>
                                <ChevronRight className="h-3 w-3" />
                                <span className="text-primary font-medium">{player.destination_school}</span>
                              </>
                            )}
                          </div>
                          {/* Stars */}
                          {player.stars && (
                            <div className="flex mt-1 text-yellow-500">
                              {Array.from({ length: Math.min(player.stars, 5) }).map((_, i) => (
                                <Star key={i} className="h-3 w-3 fill-yellow-500" />
                              ))}
                            </div>
                          )}
                          {/* Measurables (if showing advanced filters) */}
                          {showAdvancedFilters && (player.height || player.weight || player.pff_overall) && (
                            <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                              {player.height && player.weight && (
                                <span className="flex items-center gap-1">
                                  <Ruler className="h-3 w-3" />
                                  {formatHeight(player.height)} / {player.weight} lbs
                                </span>
                              )}
                              {player.pff_overall && (
                                <Badge
                                  variant="outline"
                                  className={cn(
                                    "font-mono text-xs",
                                    player.pff_overall >= 80 && "border-green-500 text-green-500",
                                    player.pff_overall >= 70 && player.pff_overall < 80 && "border-yellow-500 text-yellow-500",
                                    player.pff_overall < 70 && "border-orange-500 text-orange-500"
                                  )}
                                >
                                  PIQ {player.pff_overall.toFixed(1)}
                                </Badge>
                              )}
                            </div>
                          )}
                        </div>

                        {/* NIL Value - Right Side */}
                        <div className="text-right flex-shrink-0">
                          {player.nil_valuation ? (
                            <div className="text-xl font-bold text-primary">
                              {formatCurrency(player.nil_valuation)}
                            </div>
                          ) : (
                            <div className="text-muted-foreground">—</div>
                          )}
                        </div>

                        {/* Chevron */}
                        <ChevronRight className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                      </div>
                    ))}
                  </div>
                )}

                {/* Load More / Pagination Info */}
                <div className="flex items-center justify-between p-4 border-t border-border bg-card/50">
                  <div className="text-sm text-muted-foreground">
                    Showing {Math.min(filteredPlayers.length, 200).toLocaleString()} of {totalInDatabase.toLocaleString()} portal players
                    {searchQuery && ` matching "${searchQuery}"`}
                  </div>
                  {hasMore && (
                    <Button
                      variant="outline"
                      onClick={() => fetchPlayers(true)}
                      disabled={isLoading}
                      className="gap-2"
                    >
                      {isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <RefreshCw className="h-4 w-4" />
                      )}
                      Load More
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Team Rankings Tab */}
        <TabsContent value="rankings" className="space-y-6">
          <Card className="glass overflow-hidden">
            <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
              <CardTitle className="text-sm font-bold uppercase tracking-wider flex items-center justify-between">
                <span>Top Portal Classes (2026)</span>
                <Badge variant="secondary">{teamScores.length} teams</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {teamScores.length === 0 ? (
                <div className="p-6 text-center text-muted-foreground">
                  <p>Loading team rankings...</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent border-border">
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground w-12">#</TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Team</TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-center">Grade</TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-center">Transfers</TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-right">WAR Added</TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-right">NIL Invested</TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-right">Score</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {teamScores.map((team, index) => (
                      <TableRow key={team.team} className="border-border">
                        <TableCell className="font-mono text-muted-foreground">{index + 1}</TableCell>
                        <TableCell className="font-semibold">{team.team}</TableCell>
                        <TableCell className="text-center">
                          <Badge
                            className={cn(
                              "font-mono text-xs",
                              team.grade === "A+" && "bg-primary text-primary-foreground",
                              team.grade === "A" && "bg-primary/80 text-primary-foreground",
                              team.grade.startsWith("B") && "bg-blue-500 text-white",
                              team.grade.startsWith("C") && "bg-yellow-500 text-black",
                              team.grade === "D" && "bg-red-500 text-white"
                            )}
                          >
                            {team.grade}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-center font-mono">
                          {team.breakdown.transfers_in}
                        </TableCell>
                        <TableCell className="text-right font-bold text-green-500">
                          +{team.war_added.toFixed(2)}
                        </TableCell>
                        <TableCell className="text-right font-mono text-muted-foreground">
                          {formatCurrency(team.total_nil_invested)}
                        </TableCell>
                        <TableCell className="text-right font-bold text-primary">
                          {team.portal_score.toFixed(1)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

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
                      <Badge className={cn("text-xs", getStatusBadge(selectedPlayer.status))}>
                        {getStatusLabel(selectedPlayer.status)}
                      </Badge>
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

              <div className="space-y-6">
                {/* Transfer Info */}
                <Card className="glass">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                      <ArrowRightLeft className="h-4 w-4" />
                      Transfer Info
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 pt-0">
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground flex items-center gap-2">
                          <School className="h-4 w-4" />
                          From
                        </span>
                        <span className="font-semibold">{selectedPlayer.origin_school}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-muted-foreground flex items-center gap-2">
                          <MapPin className="h-4 w-4" />
                          To
                        </span>
                        <span className="font-semibold text-primary">
                          {selectedPlayer.destination_school || "In Portal"}
                        </span>
                      </div>
                      {selectedPlayer.origin_conference && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-muted-foreground">Conference</span>
                          <span className="font-semibold">{selectedPlayer.origin_conference}</span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>

                {/* NIL Value */}
                {selectedPlayer.nil_valuation && (
                  <Card className="glass">
                    <CardContent className="p-4">
                      <div className="text-center">
                        <p className="text-sm text-muted-foreground mb-1">NIL Valuation</p>
                        <p className="text-3xl font-bold text-primary">
                          {formatCurrency(selectedPlayer.nil_valuation)}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                )}

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

                {/* Performance Grade */}
                {selectedPlayer.pff_overall && (
                  <Card className="glass">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                        <TrendingUp className="h-4 w-4" />
                        Performance Grade
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 pt-0">
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
                    </CardContent>
                  </Card>
                )}

                {/* Position-Specific Stats */}
                {isLoadingStats ? (
                  <Card className="glass">
                    <CardContent className="p-4 flex items-center justify-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm text-muted-foreground">Loading stats...</span>
                    </CardContent>
                  </Card>
                ) : playerStats && (
                  <Card className="glass">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                        <TrendingUp className="h-4 w-4" />
                        Season Stats
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-4 pt-0">
                      <div className="grid grid-cols-2 gap-3">
                        {/* QB Stats */}
                        {playerStats.passing && (
                          <>
                            {playerStats.passing.yards && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Pass Yards</p>
                                <p className="text-lg font-bold">{playerStats.passing.yards.toLocaleString()}</p>
                              </div>
                            )}
                            {playerStats.passing.touchdowns && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Pass TDs</p>
                                <p className="text-lg font-bold">{playerStats.passing.touchdowns}</p>
                              </div>
                            )}
                            {playerStats.passing.completion_pct && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Comp %</p>
                                <p className="text-lg font-bold">{playerStats.passing.completion_pct.toFixed(1)}%</p>
                              </div>
                            )}
                            {playerStats.passing.passer_rating && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Passer Rating</p>
                                <p className="text-lg font-bold">{playerStats.passing.passer_rating.toFixed(1)}</p>
                              </div>
                            )}
                          </>
                        )}

                        {/* RB Stats */}
                        {playerStats.rushing && (
                          <>
                            {playerStats.rushing.yards && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Rush Yards</p>
                                <p className="text-lg font-bold">{playerStats.rushing.yards.toLocaleString()}</p>
                              </div>
                            )}
                            {playerStats.rushing.touchdowns && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Rush TDs</p>
                                <p className="text-lg font-bold">{playerStats.rushing.touchdowns}</p>
                              </div>
                            )}
                            {playerStats.rushing.yards_per_carry && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">YPC</p>
                                <p className="text-lg font-bold">{playerStats.rushing.yards_per_carry.toFixed(1)}</p>
                              </div>
                            )}
                            {playerStats.rushing.elusive_rating && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Elusive Rating</p>
                                <p className="text-lg font-bold">{playerStats.rushing.elusive_rating.toFixed(1)}</p>
                              </div>
                            )}
                          </>
                        )}

                        {/* WR/TE Stats */}
                        {playerStats.receiving && (
                          <>
                            {playerStats.receiving.receptions && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Receptions</p>
                                <p className="text-lg font-bold">{playerStats.receiving.receptions}</p>
                              </div>
                            )}
                            {playerStats.receiving.yards && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Rec Yards</p>
                                <p className="text-lg font-bold">{playerStats.receiving.yards.toLocaleString()}</p>
                              </div>
                            )}
                            {playerStats.receiving.touchdowns && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Rec TDs</p>
                                <p className="text-lg font-bold">{playerStats.receiving.touchdowns}</p>
                              </div>
                            )}
                            {playerStats.receiving.yards_per_route_run && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Yds/Route</p>
                                <p className="text-lg font-bold">{playerStats.receiving.yards_per_route_run.toFixed(2)}</p>
                              </div>
                            )}
                          </>
                        )}

                        {/* Pass Rush Stats */}
                        {playerStats.pass_rush && (
                          <>
                            {playerStats.pass_rush.sacks && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Sacks</p>
                                <p className="text-lg font-bold">{playerStats.pass_rush.sacks}</p>
                              </div>
                            )}
                            {playerStats.pass_rush.pressures && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Pressures</p>
                                <p className="text-lg font-bold">{playerStats.pass_rush.pressures}</p>
                              </div>
                            )}
                            {playerStats.pass_rush.pass_rush_win_rate && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Win Rate</p>
                                <p className="text-lg font-bold">{playerStats.pass_rush.pass_rush_win_rate.toFixed(1)}%</p>
                              </div>
                            )}
                            {playerStats.pass_rush.hurries && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Hurries</p>
                                <p className="text-lg font-bold">{playerStats.pass_rush.hurries}</p>
                              </div>
                            )}
                          </>
                        )}

                        {/* Coverage Stats */}
                        {playerStats.coverage && (
                          <>
                            {playerStats.coverage.interceptions && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">INTs</p>
                                <p className="text-lg font-bold">{playerStats.coverage.interceptions}</p>
                              </div>
                            )}
                            {playerStats.coverage.pass_breakups && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Pass Breakups</p>
                                <p className="text-lg font-bold">{playerStats.coverage.pass_breakups}</p>
                              </div>
                            )}
                            {playerStats.coverage.passer_rating_allowed && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Rating Allowed</p>
                                <p className="text-lg font-bold">{playerStats.coverage.passer_rating_allowed.toFixed(1)}</p>
                              </div>
                            )}
                            {playerStats.coverage.forced_incompletes && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Forced Incmpl</p>
                                <p className="text-lg font-bold">{playerStats.coverage.forced_incompletes}</p>
                              </div>
                            )}
                          </>
                        )}

                        {/* O-Line Stats */}
                        {playerStats.blocking && (
                          <>
                            {playerStats.blocking.pass_blocking_efficiency && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Pass Block Eff</p>
                                <p className="text-lg font-bold">{playerStats.blocking.pass_blocking_efficiency.toFixed(1)}</p>
                              </div>
                            )}
                            {playerStats.blocking.pressures_allowed !== undefined && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Press Allowed</p>
                                <p className="text-lg font-bold">{playerStats.blocking.pressures_allowed}</p>
                              </div>
                            )}
                            {playerStats.blocking.sacks_allowed !== undefined && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Sacks Allowed</p>
                                <p className="text-lg font-bold">{playerStats.blocking.sacks_allowed}</p>
                              </div>
                            )}
                            {playerStats.blocking.run_block_percent && (
                              <div className="text-center p-2 bg-card rounded-lg">
                                <p className="text-xs text-muted-foreground">Run Block %</p>
                                <p className="text-lg font-bold">{playerStats.blocking.run_block_percent.toFixed(1)}%</p>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* WAR / Win Impact Analysis - Fit Score & NIL Impact buttons scroll here */}
                {playerWAR && (
                  <div data-war-card>
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
                  </div>
                )}

                {/* Quick Actions */}
                <div className="flex flex-col gap-2">
                  <Button
                    className="w-full"
                    variant={isInWatchlist(selectedPlayer.player_id) ? "default" : "outline"}
                    onClick={() =>
                      toggleWatchlist({
                        id: selectedPlayer.player_id,
                        player_name: selectedPlayer.player_name,
                        position: selectedPlayer.position,
                        school: selectedPlayer.destination_school || selectedPlayer.origin_school,
                        nil_valuation: selectedPlayer.nil_valuation || 0,
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
                    <Button
                      className="flex-1"
                      variant="outline"
                      onClick={() => {
                        // Scroll to WAR card which shows fit/impact analysis
                        const warCard = document.querySelector('[data-war-card]');
                        warCard?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                      }}
                    >
                      <TrendingUp className="h-4 w-4 mr-2" />
                      Fit Score
                    </Button>
                    <Button
                      className="flex-1"
                      variant="outline"
                      onClick={() => {
                        // Scroll to WAR card which shows NIL impact/transfer value
                        const warCard = document.querySelector('[data-war-card]');
                        warCard?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                      }}
                    >
                      <DollarSign className="h-4 w-4 mr-2" />
                      NIL Impact
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
