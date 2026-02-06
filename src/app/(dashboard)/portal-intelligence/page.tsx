"use client";

import { useState, useEffect, useCallback } from "react";
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
} from "@/components/ui/table";
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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getActivePortalPlayers, type PortalPlayer } from "@/lib/api/portal";
import { HEIGHT_PRESETS, WEIGHT_PRESETS, formatHeight } from "@/lib/constants/presets";

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

  // Stats computed from data
  const [stats, setStats] = useState({
    activeInPortal: 0,
    committed: 0,
    newToday: 0,
    schools: 0,
  });

  // Fetch portal players
  const fetchPlayers = useCallback(async () => {
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
        min_stars?: number;
      } = { limit: 500, status: apiStatus };

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

      const response = await getActivePortalPlayers(params);

      // Response is { players: [], total: N }
      const playersList = response.players || [];
      setPlayers(playersList as PortalPlayerWithMeasurables[]);
      setTotalCount(response.total || playersList.length);

      // Calculate stats from full dataset
      const activeCount = playersList.filter((p) => p.status === "available").length;
      const committedCount = playersList.filter((p) => p.status === "committed").length;
      const schools = new Set(playersList.map((p) => p.origin_school)).size;

      setStats({
        activeInPortal: activeCount,
        committed: committedCount,
        newToday: Math.floor(response.total * 0.02), // Approximate based on total
        schools,
      });
    } catch (err) {
      console.error("Failed to fetch portal players:", err);
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setIsLoading(false);
    }
  }, [selectedPosition, selectedStatus, selectedStars]);

  // Initial load and refetch on filter changes
  useEffect(() => {
    fetchPlayers();
  }, [fetchPlayers]);

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
          <Button variant="outline" size="sm" onClick={fetchPlayers} disabled={isLoading}>
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
                <p className="text-2xl font-bold">{totalCount.toLocaleString()}</p>
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
                  onClick={fetchPlayers}
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
                <p className="text-muted-foreground">Loading portal entries...</p>
              </CardContent>
            </Card>
          )}

          {/* Players Table */}
          {!isLoading && !error && (
            <Card className="glass overflow-hidden">
              <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
                <CardTitle className="text-sm font-bold uppercase tracking-wider flex items-center justify-between">
                  <span>Transfer Portal Entries</span>
                  <Badge variant="secondary">{filteredPlayers.length} players</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent border-border">
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">
                        Player
                      </TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">
                        Pos
                      </TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">
                        From
                      </TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">
                        To
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
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">
                        Status
                      </TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-right">
                        NIL Value
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
                      filteredPlayers.slice(0, 200).map((player) => (
                        <TableRow
                          key={player.player_id}
                          className="cursor-pointer hover:bg-card border-border"
                        >
                          <TableCell className="font-semibold">{player.player_name}</TableCell>
                          <TableCell>
                            <Badge variant="outline" className="font-mono text-xs">
                              {player.position}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-muted-foreground text-sm">
                            {player.origin_school}
                          </TableCell>
                          <TableCell className="text-primary font-medium text-sm">
                            {player.destination_school || "—"}
                          </TableCell>
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
                          <TableCell>
                            <Badge className={cn("text-xs", getStatusBadge(player.status))}>
                              {getStatusLabel(player.status)}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-right font-bold text-primary">
                            {player.nil_valuation ? formatCurrency(player.nil_valuation) : "—"}
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

        {/* Team Rankings Tab */}
        <TabsContent value="rankings" className="space-y-6">
          <Card className="glass overflow-hidden">
            <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
              <CardTitle className="text-sm font-bold uppercase tracking-wider">
                Top Portal Classes (2026)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6 text-center text-muted-foreground">
              <p>Team rankings data coming soon.</p>
              <p className="text-sm mt-2">
                This will show incoming/outgoing transfer counts and net talent change per school.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
