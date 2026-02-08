"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
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
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  TrendingUp,
  Search,
  Calculator,
  Target,
  Trophy,
  Users,
  BarChart3,
  ArrowRight,
  Zap,
  RefreshCw,
  Loader2,
  AlertCircle,
  Info,
  Building2,
  Star,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  Cell,
  PieChart,
  Pie,
  Legend,
  AreaChart,
  Area,
  Brush,
  ReferenceArea,
  ZAxis,
} from "recharts";
import {
  getWARLeaderboard,
  calculatePlayerWAR,
  calculateDetailedWAR,
  analyzeTransferValue,
  projectTransferImpact,
  calculateTeamPortalScores,
  getSchoolTier,
  getSchoolList,
  type WARPlayer,
  type DetailedWARResult,
  type TransferValueAnalysis,
  type TransferImpactProjection,
  type TeamPortalScore,
} from "@/lib/api/war";
import { searchPlayers, getPlayerStats, type PlayerSearchResult, type PlayerStats } from "@/lib/api/players";
import { getPortalTeamRankings, getTeamPortalActivity, type TeamRanking, type PortalPlayer } from "@/lib/api/portal";

const positions = ["All", "QB", "RB", "WR", "TE", "OT", "OG", "C", "DL", "EDGE", "LB", "CB", "S"];

const CHART_COLORS = ["#D4AF37", "#22C55E", "#3B82F6", "#A855F7", "#F59E0B", "#EF4444"];

function formatCurrency(value: number | undefined | null): string {
  if (value == null || isNaN(value)) return "$0";
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}K`;
  }
  return `$${value.toLocaleString()}`;
}

function getGradeColor(grade: string): string {
  const colors: Record<string, string> = {
    "A+": "bg-primary text-primary-foreground",
    "A": "bg-primary text-primary-foreground",
    "B+": "bg-purple-500 text-white",
    "B": "bg-purple-500/80 text-white",
    "C+": "bg-blue-500 text-white",
    "C": "bg-blue-500/80 text-white",
    "D": "bg-slate-500 text-white",
    Elite: "bg-primary text-primary-foreground",
    Premium: "bg-purple-500 text-white",
    Solid: "bg-blue-500 text-white",
    Average: "bg-slate-500 text-white",
  };
  return colors[grade] || "bg-slate-500 text-white";
}

// WAR Gauge Component (SVG circular gauge like Streamlit)
function WARGauge({ war, label = "WAR", percentile = 50 }: { war: number; label?: string; percentile?: number }) {
  const progress = Math.min(war / 5.0, 1.0);
  const circumference = 282.7; // 2 * PI * 45
  const dashoffset = circumference * (1 - progress);

  let tierLabel = "Developing";
  if (war >= 3.0) tierLabel = "Elite Impact";
  else if (war >= 2.0) tierLabel = "High Impact";
  else if (war >= 1.0) tierLabel = "Solid Impact";

  return (
    <Card className="glass">
      <CardContent className="p-6">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">Win Impact Gauge</h3>
          <Badge className={cn("font-semibold", war >= 2 ? "bg-primary" : "bg-muted")}>
            {tierLabel}
          </Badge>
        </div>

        <div className="flex flex-col items-center">
          {/* SVG Gauge */}
          <div className="relative w-48 h-48 flex items-center justify-center mb-4">
            <svg className="absolute w-full h-full -rotate-90" viewBox="0 0 100 100">
              {/* Background circle */}
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="transparent"
                stroke="hsl(var(--muted))"
                strokeWidth="8"
              />
              {/* Progress arc */}
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="transparent"
                stroke="hsl(var(--primary))"
                strokeWidth="8"
                strokeDasharray={circumference}
                strokeDashoffset={dashoffset}
                strokeLinecap="round"
                className="drop-shadow-[0_0_8px_rgba(212,175,55,0.5)]"
              />
            </svg>
            {/* Center text */}
            <div className="text-center z-10">
              <span className="text-5xl font-extrabold text-foreground">{war.toFixed(1)}</span>
              <p className="text-sm font-bold text-primary uppercase tracking-widest mt-1">{label}</p>
            </div>
          </div>

          {/* Percentile bar */}
          <div className="w-full max-w-xs">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-muted-foreground uppercase tracking-wider">Percentile</span>
              <span className="font-bold">{percentile}th</span>
            </div>
            <Progress value={percentile} className="h-2" />
            <p className="text-xs text-muted-foreground text-center mt-2">
              0.0 - 5.0 Wins Above Replacement Scale
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Value Breakdown Component (stacked bar showing factor contributions)
function ValueBreakdown({ breakdown }: { breakdown?: { position: number; performance: number; stars: number; school: number } }) {
  const { position = 40, performance = 30, stars = 15, school = 15 } = breakdown || {};

  return (
    <Card className="glass">
      <CardContent className="p-6">
        <div className="mb-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-foreground">Value Component Breakdown</h3>
          <p className="text-xs text-muted-foreground mt-1">Factors contributing to total WAR</p>
        </div>

        {/* Stacked bar */}
        <div className="w-full h-10 flex rounded-lg overflow-hidden border border-border mb-4">
          <div
            className="h-full bg-primary flex items-center justify-center"
            style={{ width: `${position}%` }}
          >
            <span className="text-xs font-bold text-primary-foreground">{position}%</span>
          </div>
          <div
            className="h-full bg-primary/60 flex items-center justify-center"
            style={{ width: `${performance}%` }}
          >
            <span className="text-xs font-bold text-primary-foreground">{performance}%</span>
          </div>
          <div
            className="h-full bg-primary/30 flex items-center justify-center"
            style={{ width: `${stars}%` }}
          >
            <span className="text-xs font-bold">{stars}%</span>
          </div>
          <div
            className="h-full bg-primary/10 flex items-center justify-center"
            style={{ width: `${school}%` }}
          >
            <span className="text-xs font-bold">{school}%</span>
          </div>
        </div>

        {/* Legend */}
        <div className="grid grid-cols-2 gap-3">
          <div className="flex items-start gap-2">
            <div className="w-3 h-3 rounded bg-primary mt-0.5" />
            <div>
              <p className="text-xs font-semibold">Position Value</p>
              <p className="text-xs text-muted-foreground">Positional scarcity</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-3 h-3 rounded bg-primary/60 mt-0.5" />
            <div>
              <p className="text-xs font-semibold">Performance</p>
              <p className="text-xs text-muted-foreground">On-field metrics</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-3 h-3 rounded bg-primary/30 mt-0.5" />
            <div>
              <p className="text-xs font-semibold">Star Rating</p>
              <p className="text-xs text-muted-foreground">Recruiting profile</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-3 h-3 rounded bg-primary/10 mt-0.5" />
            <div>
              <p className="text-xs font-semibold">School Tier</p>
              <p className="text-xs text-muted-foreground">Program strength</p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// Factor Breakdown Card Component
function FactorCard({ label, value, isBonus = false }: { label: string; value: string; isBonus?: boolean }) {
  return (
    <div className="bg-card p-3 rounded-lg border border-border">
      <p className="text-xs text-muted-foreground mb-1">{label}</p>
      <p className={cn("text-lg font-bold", isBonus ? "text-primary" : "text-foreground")}>
        {isBonus ? "+" : ""}{value}
      </p>
    </div>
  );
}

export default function WinImpactPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPosition, setSelectedPosition] = useState("All");
  const [showCalculator, setShowCalculator] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

  // API state
  const [players, setPlayers] = useState<WARPlayer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Calculator state
  const [calcName, setCalcName] = useState("");
  const [calcPosition, setCalcPosition] = useState("");
  const [calcSchool, setCalcSchool] = useState("");
  const [calcNIL, setCalcNIL] = useState("");
  const [calcPFF, setCalcPFF] = useState("");
  const [calcResult, setCalcResult] = useState<WARPlayer | null>(null);
  const [isCalculating, setIsCalculating] = useState(false);

  // Player Analysis state
  const [selectedPlayer, setSelectedPlayer] = useState<WARPlayer | null>(null);
  const [playerWARResult, setPlayerWARResult] = useState<DetailedWARResult | null>(null);
  const [transferValue, setTransferValue] = useState<TransferValueAnalysis | null>(null);
  const [transferImpact, setTransferImpact] = useState<TransferImpactProjection | null>(null);
  const [targetSchool, setTargetSchool] = useState("");

  // Team Impact state
  const [teamScores, setTeamScores] = useState<TeamPortalScore[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<TeamPortalScore | null>(null);

  // Full player stats (fetched when player is selected)
  const [fullPlayerStats, setFullPlayerStats] = useState<PlayerStats | null>(null);
  const [isLoadingStats, setIsLoadingStats] = useState(false);

  // Portal team rankings from API (real data)
  const [portalTeamRankings, setPortalTeamRankings] = useState<TeamRanking[]>([]);
  const [isLoadingTeamRankings, setIsLoadingTeamRankings] = useState(false);
  const [teamPortalActivity, setTeamPortalActivity] = useState<{
    incoming: PortalPlayer[];
    outgoing: PortalPlayer[];
    net_talent_change: number;
  } | null>(null);

  // Player search state (for analyzing any player)
  const [playerSearchQuery, setPlayerSearchQuery] = useState("");
  const [playerSearchResults, setPlayerSearchResults] = useState<PlayerSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchDebounce, setSearchDebounce] = useState<NodeJS.Timeout | null>(null);

  // Fetch WAR data
  const fetchPlayers = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params: { position?: string; limit: number } = { limit: 500 };
      if (selectedPosition !== "All") {
        params.position = selectedPosition;
      }

      const data = await getWARLeaderboard(params);
      setPlayers(data);

      // Calculate team scores from player data
      const scores = calculateTeamPortalScores(data);
      setTeamScores(scores);
    } catch (err) {
      console.error("Failed to fetch WAR data:", err);
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setIsLoading(false);
    }
  }, [selectedPosition]);

  useEffect(() => {
    fetchPlayers();
  }, [fetchPlayers]);

  // Fetch real team portal rankings from API
  const fetchTeamRankings = useCallback(async () => {
    setIsLoadingTeamRankings(true);
    try {
      const response = await getPortalTeamRankings(30);
      setPortalTeamRankings(response.rankings || []);
    } catch (err) {
      console.error("Failed to fetch team rankings:", err);
      setPortalTeamRankings([]);
    } finally {
      setIsLoadingTeamRankings(false);
    }
  }, []);

  // Fetch team rankings when team tab is active
  useEffect(() => {
    if (activeTab === "team" && portalTeamRankings.length === 0) {
      fetchTeamRankings();
    }
  }, [activeTab, portalTeamRankings.length, fetchTeamRankings]);

  // Fetch team portal activity when a team is selected
  const fetchTeamActivity = useCallback(async (teamName: string) => {
    try {
      const activity = await getTeamPortalActivity(teamName);
      setTeamPortalActivity({
        incoming: activity.incoming || [],
        outgoing: activity.outgoing || [],
        net_talent_change: activity.net_talent_change || 0,
      });
    } catch (err) {
      console.error("Failed to fetch team activity:", err);
      setTeamPortalActivity(null);
    }
  }, []);

  // Filter players by search
  const filteredPlayers = useMemo(() => {
    return players.filter((player) => {
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase();
      return (
        player.player_name.toLowerCase().includes(query) ||
        player.school.toLowerCase().includes(query)
      );
    });
  }, [players, searchQuery]);

  // Calculate aggregate stats
  const stats = useMemo(() => ({
    avgWAR: players.length > 0 ? (players.reduce((sum, p) => sum + p.war, 0) / players.length).toFixed(2) : "0",
    totalWAR: players.reduce((sum, p) => sum + p.war, 0).toFixed(1),
    highestWAR: players.length > 0 ? Math.max(...players.map(p => p.war)).toFixed(1) : "0",
    avgValuePerWin: players.length > 0 ? formatCurrency(players.reduce((sum, p) => sum + p.value_per_win, 0) / players.length) : "$0",
    elitePlayers: players.filter(p => p.grade === "Elite").length,
    totalPlayers: players.length,
  }), [players]);

  // Chart data - Position WAR
  const positionWARData = useMemo(() => {
    return positions.slice(1).map(pos => {
      const posPlayers = players.filter(p => p.position.toUpperCase().includes(pos));
      return {
        position: pos,
        avgWAR: posPlayers.length > 0 ? posPlayers.reduce((sum, p) => sum + p.war, 0) / posPlayers.length : 0,
        count: posPlayers.length,
      };
    }).filter(d => d.count > 0).sort((a, b) => b.avgWAR - a.avgWAR);
  }, [players]);

  // Chart data - Grade distribution
  const gradeDistribution = useMemo(() => [
    { name: "Elite", value: players.filter(p => p.grade === "Elite").length, color: "#D4AF37" },
    { name: "Premium", value: players.filter(p => p.grade === "Premium").length, color: "#A855F7" },
    { name: "Solid", value: players.filter(p => p.grade === "Solid").length, color: "#3B82F6" },
    { name: "Average", value: players.filter(p => p.grade === "Average").length, color: "#64748B" },
  ], [players]);

  // Chart data - WAR vs NIL scatter (include more player info for tooltips)
  const warVsNILData = useMemo(() => {
    return filteredPlayers.slice(0, 100).map(p => ({
      name: p.player_name,
      war: p.war,
      nil: p.nil_valuation / 1000000,
      nilRaw: p.nil_valuation,
      grade: p.grade,
      position: p.position,
      school: p.school,
      stars: p.stars || 3,
      player_id: p.player_id,
    }));
  }, [filteredPlayers]);

  // Zoom state for scatter chart
  const [scatterZoom, setScatterZoom] = useState<{
    xMin: number | null;
    xMax: number | null;
    yMin: number | null;
    yMax: number | null;
    refAreaLeft: number | null;
    refAreaRight: number | null;
  }>({
    xMin: null,
    xMax: null,
    yMin: null,
    yMax: null,
    refAreaLeft: null,
    refAreaRight: null,
  });

  // Selected point on scatter chart
  const [hoveredPlayer, setHoveredPlayer] = useState<typeof warVsNILData[0] | null>(null);

  // Reset zoom
  const resetZoom = () => {
    setScatterZoom({
      xMin: null,
      xMax: null,
      yMin: null,
      yMax: null,
      refAreaLeft: null,
      refAreaRight: null,
    });
  };

  // Calculate domain for scatter chart
  const scatterDomain = useMemo(() => {
    if (scatterZoom.xMin !== null && scatterZoom.xMax !== null) {
      return {
        x: [scatterZoom.xMin, scatterZoom.xMax] as [number, number],
        y: [scatterZoom.yMin || 0, scatterZoom.yMax || 5] as [number, number],
      };
    }
    // Auto domain from data
    const maxNil = Math.max(...warVsNILData.map(d => d.nil), 1);
    const maxWar = Math.max(...warVsNILData.map(d => d.war), 3);
    return {
      x: [0, Math.ceil(maxNil * 1.1)] as [number, number],
      y: [0, Math.ceil(maxWar * 1.1)] as [number, number],
    };
  }, [warVsNILData, scatterZoom]);

  // Chart data - WAR Distribution histogram
  const warDistributionData = useMemo(() => {
    const bins = [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0];
    return bins.map((bin, i) => {
      const nextBin = bins[i + 1] || 5;
      const count = players.filter(p => p.war >= bin && p.war < nextBin).length;
      return {
        range: `${bin.toFixed(1)}-${nextBin.toFixed(1)}`,
        count,
      };
    });
  }, [players]);

  // Handle player selection for analysis
  const handlePlayerSelect = (player: WARPlayer) => {
    setSelectedPlayer(player);

    // Calculate detailed WAR
    const warResult = calculateDetailedWAR({
      position: player.position,
      stars: player.stars || 3,
      nil_value: player.nil_valuation,
      destination_school: player.school,
      is_predicted_nil: true,
    });
    setPlayerWARResult(warResult);

    // Calculate transfer value
    const valueAnalysis = analyzeTransferValue(player.war, player.nil_valuation, player.position);
    setTransferValue(valueAnalysis);

    // Calculate transfer impact for current school
    const { tier } = getSchoolTier(player.school);
    const impact = projectTransferImpact(player.war, tier);
    setTransferImpact(impact);
  };

  // Handle target school change for transfer projection
  const handleTargetSchoolChange = (school: string) => {
    setTargetSchool(school);
    if (selectedPlayer) {
      const { tier } = getSchoolTier(school);
      const impact = projectTransferImpact(selectedPlayer.war, tier);
      setTransferImpact(impact);
    }
  };

  // Handle calculate WAR
  const handleCalculate = async () => {
    if (!calcName || !calcPosition || !calcSchool || !calcNIL) return;

    setIsCalculating(true);
    try {
      const result = await calculatePlayerWAR({
        name: calcName,
        position: calcPosition,
        school: calcSchool,
        nil_valuation: parseFloat(calcNIL),
        pff_grade: calcPFF ? parseFloat(calcPFF) : undefined,
      });
      setCalcResult(result);
    } catch (err) {
      console.error("Calculate error:", err);
    } finally {
      setIsCalculating(false);
    }
  };

  const schoolList = useMemo(() => getSchoolList(), []);

  // Search for any player in the database
  const handlePlayerSearch = useCallback(async (query: string) => {
    if (query.length < 2) {
      setPlayerSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const results = await searchPlayers(query, "all", 20);
      setPlayerSearchResults(results.players || []);
    } catch (err) {
      console.error("Player search error:", err);
      setPlayerSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  // Debounced search
  const handleSearchInputChange = (value: string) => {
    setPlayerSearchQuery(value);
    if (searchDebounce) clearTimeout(searchDebounce);
    const timeout = setTimeout(() => handlePlayerSearch(value), 300);
    setSearchDebounce(timeout);
  };

  // Select a player from search results to analyze
  const handleSearchResultSelect = async (result: PlayerSearchResult) => {
    // Clear previous stats
    setFullPlayerStats(null);
    setIsLoadingStats(true);

    // Convert search result to WAR player format and calculate
    const warResult = await calculatePlayerWAR({
      name: result.name,
      position: result.position,
      school: result.school,
      nil_valuation: result.nil_value || 0,
    });

    // Set as selected player (with stars from search result)
    warResult.stars = result.stars;
    warResult.headshot_url = result.headshot_url;
    setSelectedPlayer(warResult);

    // Fetch full player stats (PFF grades, height, weight, etc.)
    try {
      const stats = await getPlayerStats(result.name, 2025);
      setFullPlayerStats(stats);

      // Recalculate WAR with actual PFF data if available
      if (stats.pff?.overall) {
        const updatedWAR = await calculatePlayerWAR({
          name: result.name,
          position: result.position,
          school: result.school,
          nil_valuation: stats.nil_value || result.nil_value || 0,
          pff_grade: stats.pff.overall,
        });
        updatedWAR.stars = stats.stars || result.stars;
        updatedWAR.headshot_url = stats.headshot_url;
        setSelectedPlayer(updatedWAR);
      }
    } catch (err) {
      console.error("Failed to fetch player stats:", err);
    } finally {
      setIsLoadingStats(false);
    }

    // Calculate detailed WAR
    const detailedWAR = calculateDetailedWAR({
      position: result.position,
      stars: result.stars || 3,
      nil_value: result.nil_value || 0,
      destination_school: result.school,
      is_predicted_nil: true,
    });
    setPlayerWARResult(detailedWAR);

    // Calculate transfer value
    const valueAnalysis = analyzeTransferValue(warResult.war, result.nil_value || 0, result.position);
    setTransferValue(valueAnalysis);

    // Calculate transfer impact
    const { tier } = getSchoolTier(result.school);
    const impact = projectTransferImpact(warResult.war, tier);
    setTransferImpact(impact);

    // Clear search
    setPlayerSearchQuery("");
    setPlayerSearchResults([]);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <TrendingUp className="h-8 w-8 text-primary" />
            Win Impact Analytics
          </h1>
          <p className="text-muted-foreground mt-1">
            Proprietary WAR Calculator & Win Projection Analysis
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="border-primary text-primary">
            Proprietary Algorithm
          </Badge>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchPlayers}
            disabled={isLoading}
          >
            <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
            Refresh
          </Button>
          <Button
            onClick={() => setShowCalculator(!showCalculator)}
            className="bg-primary text-primary-foreground hover:bg-primary/90"
          >
            <Calculator className="h-4 w-4 mr-2" />
            WAR Calculator
          </Button>
        </div>
      </div>

      {/* Algorithm Info Collapsible */}
      <Card className="glass border-primary/30">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-primary shrink-0 mt-0.5" />
            <div className="text-sm text-muted-foreground">
              <span className="font-semibold text-foreground">Portal IQ WAR (Wins Above Replacement)</span> considers:
              Position Value & Scarcity, Recruiting Profile (stars + rating), NIL Market Signal,
              Destination School Tier, Physical Measurables, and Experience Factor.
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Calculator Panel */}
      {showCalculator && (
        <Card className="glass border-primary">
          <CardHeader className="border-b border-border">
            <CardTitle className="flex items-center gap-2">
              <Calculator className="h-5 w-5 text-primary" />
              Win Impact Calculator
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Input Form */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Player Name</Label>
                    <Input
                      placeholder="Enter player name"
                      className="bg-input"
                      value={calcName}
                      onChange={(e) => setCalcName(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Position</Label>
                    <Select value={calcPosition} onValueChange={setCalcPosition}>
                      <SelectTrigger className="bg-input">
                        <SelectValue placeholder="Select" />
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
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>NIL Value ($)</Label>
                    <Input
                      type="number"
                      placeholder="e.g., 500000"
                      className="bg-input"
                      value={calcNIL}
                      onChange={(e) => setCalcNIL(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Performance Grade (optional)</Label>
                    <Input
                      type="number"
                      placeholder="e.g., 85.5"
                      className="bg-input"
                      value={calcPFF}
                      onChange={(e) => setCalcPFF(e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Target School</Label>
                  <Input
                    placeholder="School name"
                    className="bg-input"
                    value={calcSchool}
                    onChange={(e) => setCalcSchool(e.target.value)}
                  />
                </div>
                <Button
                  className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
                  onClick={handleCalculate}
                  disabled={isCalculating || !calcName || !calcPosition || !calcSchool || !calcNIL}
                >
                  {isCalculating ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Zap className="h-4 w-4 mr-2" />
                  )}
                  Calculate Impact
                </Button>
              </div>

              {/* Result Preview */}
              <div className="flex items-center justify-center">
                {calcResult ? (
                  <div className="w-full p-6 rounded-lg bg-card border border-border">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-xl font-bold">{calcResult.player_name}</h3>
                        <p className="text-muted-foreground text-sm">
                          {calcResult.position} • {calcResult.school}
                        </p>
                      </div>
                      <Badge className={cn("font-semibold", getGradeColor(calcResult.grade))}>
                        {calcResult.grade}
                      </Badge>
                    </div>
                    <div className="mb-4">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-muted-foreground">Wins Above Replacement</span>
                        <span className="text-2xl font-bold text-primary">{calcResult.war}</span>
                      </div>
                      <Progress value={(calcResult.war / 4) * 100} className="h-3" />
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center p-2 rounded-lg bg-background">
                        <p className="text-xs text-muted-foreground">Win Prob Added</p>
                        <p className="text-lg font-bold text-green-500">+{calcResult.win_prob_added}%</p>
                      </div>
                      <div className="text-center p-2 rounded-lg bg-background">
                        <p className="text-xs text-muted-foreground">NIL Value</p>
                        <p className="text-lg font-bold text-primary">{formatCurrency(calcResult.nil_valuation)}</p>
                      </div>
                      <div className="text-center p-2 rounded-lg bg-background">
                        <p className="text-xs text-muted-foreground">$/Win</p>
                        <p className="text-lg font-bold">{formatCurrency(calcResult.value_per_win)}</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center p-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
                      <Calculator className="h-8 w-8 text-primary" />
                    </div>
                    <h3 className="text-lg font-semibold mb-2">Enter Player Details</h3>
                    <p className="text-muted-foreground text-sm">
                      Calculate projected Wins Above Replacement and dollar value per win.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-card border border-border">
          <TabsTrigger
            value="overview"
            className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
          >
            <BarChart3 className="h-4 w-4 mr-2" />
            Impact Overview
          </TabsTrigger>
          <TabsTrigger
            value="player"
            className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
          >
            <Search className="h-4 w-4 mr-2" />
            Player Analysis
          </TabsTrigger>
          <TabsTrigger
            value="team"
            className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
          >
            <Trophy className="h-4 w-4 mr-2" />
            Team Portal Impact
          </TabsTrigger>
        </TabsList>

        {/* ===== OVERVIEW TAB ===== */}
        <TabsContent value="overview" className="space-y-6">
          {/* Stats Overview */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="glass">
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground uppercase mb-1">Players Analyzed</p>
                <p className="text-2xl font-bold">{(stats.totalPlayers || 0).toLocaleString()}</p>
              </CardContent>
            </Card>
            <Card className="glass border-primary/50">
              <CardContent className="p-4">
                <p className="text-xs text-primary uppercase mb-1">Avg Portal IQ WAR</p>
                <p className="text-2xl font-bold text-primary">{stats.avgWAR}</p>
              </CardContent>
            </Card>
            <Card className="glass">
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground uppercase mb-1">Total WAR Pool</p>
                <p className="text-2xl font-bold">{stats.totalWAR}</p>
              </CardContent>
            </Card>
            <Card className="glass">
              <CardContent className="p-4">
                <p className="text-xs text-muted-foreground uppercase mb-1">Avg NIL per WAR</p>
                <p className="text-2xl font-bold">{stats.avgValuePerWin}</p>
              </CardContent>
            </Card>
          </div>

          {/* WAR Gauge and Value Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <WARGauge war={parseFloat(stats.avgWAR)} label="AVG WAR" percentile={Math.min(Math.round(parseFloat(stats.avgWAR) / 5 * 100 * 0.9), 99)} />
            <ValueBreakdown />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* WAR by Position */}
            <Card className="glass">
              <CardHeader className="border-b border-border">
                <CardTitle className="text-sm font-bold uppercase tracking-wider">
                  Average WAR by Position
                </CardTitle>
                <p className="text-xs text-muted-foreground mt-1">
                  Click on a position bar to filter the leaderboard
                </p>
              </CardHeader>
              <CardContent className="p-6">
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={positionWARData}
                      layout="vertical"
                      onClick={(data) => {
                        const payload = (data as unknown as { activePayload?: Array<{ payload: { position: string } }> })?.activePayload?.[0];
                        if (payload) {
                          setSelectedPosition(payload.payload.position);
                        }
                      }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                      <XAxis type="number" domain={[0, 3]} stroke="#888" />
                      <YAxis dataKey="position" type="category" stroke="#888" width={50} />
                      <Tooltip
                        cursor={{ fill: 'rgba(212, 175, 55, 0.1)' }}
                        content={({ active, payload }) => {
                          if (active && payload && payload.length > 0) {
                            const data = payload[0].payload;
                            return (
                              <div className="bg-[#1a2744] border border-border rounded-lg p-3 shadow-lg">
                                <p className="font-bold text-primary text-lg">{data.position}</p>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm mt-2">
                                  <span className="text-muted-foreground">Avg WAR:</span>
                                  <span className="font-bold text-green-400">{data.avgWAR.toFixed(2)}</span>
                                  <span className="text-muted-foreground">Players:</span>
                                  <span className="font-bold">{data.count.toLocaleString()}</span>
                                </div>
                                <p className="text-xs text-muted-foreground mt-2 italic">Click to filter</p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Bar
                        dataKey="avgWAR"
                        fill="#D4AF37"
                        radius={[0, 4, 4, 0]}
                        style={{ cursor: 'pointer' }}
                      >
                        {positionWARData.map((entry, index) => (
                          <Cell
                            key={`cell-${index}`}
                            fill={CHART_COLORS[index % CHART_COLORS.length]}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* NIL vs WAR Scatter - Interactive with zoom */}
            <Card className="glass">
              <CardHeader className="border-b border-border">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-bold uppercase tracking-wider">
                    NIL vs Win Impact Correlation
                  </CardTitle>
                  {(scatterZoom.xMin !== null) && (
                    <Button variant="outline" size="sm" onClick={resetZoom}>
                      Reset Zoom
                    </Button>
                  )}
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Click any dot to see player details. Use brush below to zoom.
                </p>
              </CardHeader>
              <CardContent className="p-6">
                <div className="h-[350px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart margin={{ top: 10, right: 20, bottom: 40, left: 10 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                      <XAxis
                        type="number"
                        dataKey="nil"
                        name="NIL"
                        domain={scatterDomain.x}
                        stroke="#888"
                        tickFormatter={(v) => `$${v.toFixed(1)}M`}
                        label={{ value: "NIL Value ($M)", position: "bottom", offset: 0, fill: "#888" }}
                      />
                      <YAxis
                        type="number"
                        dataKey="war"
                        name="WAR"
                        domain={scatterDomain.y}
                        stroke="#888"
                        label={{ value: "WAR", angle: -90, position: "insideLeft", fill: "#888" }}
                      />
                      <ZAxis type="number" dataKey="stars" range={[60, 200]} name="Stars" />
                      <Tooltip
                        cursor={{ strokeDasharray: '3 3' }}
                        content={({ active, payload }) => {
                          if (active && payload && payload.length > 0) {
                            const data = payload[0].payload;
                            return (
                              <div className="bg-[#1a2744] border border-border rounded-lg p-3 shadow-lg">
                                <p className="font-bold text-primary text-base">{data.name}</p>
                                <p className="text-sm text-muted-foreground mb-2">
                                  {data.position} • {data.school}
                                </p>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                                  <span className="text-muted-foreground">WAR:</span>
                                  <span className="font-bold text-green-400">{data.war.toFixed(2)}</span>
                                  <span className="text-muted-foreground">NIL Value:</span>
                                  <span className="font-bold">${(data.nil).toFixed(2)}M</span>
                                  <span className="text-muted-foreground">Stars:</span>
                                  <span>{"⭐".repeat(data.stars)}</span>
                                  <span className="text-muted-foreground">Grade:</span>
                                  <span className={cn(
                                    "font-semibold",
                                    data.grade === "Elite" && "text-primary",
                                    data.grade === "Premium" && "text-purple-400",
                                    data.grade === "Solid" && "text-blue-400"
                                  )}>{data.grade}</span>
                                </div>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Scatter
                        data={warVsNILData}
                        fill="#D4AF37"
                        onClick={(data) => {
                          // Find player and select them
                          const player = players.find(p => p.player_id === data.player_id);
                          if (player) handlePlayerSelect(player);
                        }}
                        style={{ cursor: 'pointer' }}
                      >
                        {warVsNILData.map((entry, index) => {
                          const gradeColors: Record<string, string> = {
                            Elite: "#D4AF37",
                            Premium: "#A855F7",
                            Solid: "#3B82F6",
                            Average: "#64748B",
                          };
                          return (
                            <Cell
                              key={`cell-${index}`}
                              fill={gradeColors[entry.grade] || "#D4AF37"}
                              stroke={hoveredPlayer?.player_id === entry.player_id ? "#fff" : "none"}
                              strokeWidth={hoveredPlayer?.player_id === entry.player_id ? 2 : 0}
                            />
                          );
                        })}
                      </Scatter>
                      <Brush
                        dataKey="nil"
                        height={30}
                        stroke="#D4AF37"
                        fill="#1a2744"
                        onChange={(e) => {
                          if (e.startIndex !== undefined && e.endIndex !== undefined) {
                            const subset = warVsNILData.slice(e.startIndex, e.endIndex + 1);
                            if (subset.length > 1) {
                              const xVals = subset.map(d => d.nil);
                              const yVals = subset.map(d => d.war);
                              setScatterZoom({
                                ...scatterZoom,
                                xMin: Math.min(...xVals) * 0.9,
                                xMax: Math.max(...xVals) * 1.1,
                                yMin: Math.min(...yVals) * 0.9,
                                yMax: Math.max(...yVals) * 1.1,
                              });
                            }
                          }
                        }}
                      />
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>

                {/* Legend */}
                <div className="flex items-center justify-center gap-6 mt-4">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-primary" />
                    <span className="text-xs text-muted-foreground">Elite</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-purple-500" />
                    <span className="text-xs text-muted-foreground">Premium</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-blue-500" />
                    <span className="text-xs text-muted-foreground">Solid</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-slate-500" />
                    <span className="text-xs text-muted-foreground">Average</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* WAR Distribution */}
          <Card className="glass">
            <CardHeader className="border-b border-border">
              <CardTitle className="text-sm font-bold uppercase tracking-wider">
                WAR Distribution Across All Players
              </CardTitle>
              <p className="text-xs text-muted-foreground mt-1">
                Click on a bar to filter the player list by WAR range
              </p>
            </CardHeader>
            <CardContent className="p-6">
              <div className="h-[280px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={warDistributionData}
                    onClick={(data) => {
                      const payload = (data as unknown as { activePayload?: Array<{ payload: { range: string } }> })?.activePayload?.[0];
                      if (payload) {
                        // Could filter players by this range
                        console.log("Clicked WAR range:", payload.payload.range);
                      }
                    }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="range" stroke="#888" />
                    <YAxis stroke="#888" />
                    <Tooltip
                      cursor={{ fill: 'rgba(212, 175, 55, 0.1)' }}
                      content={({ active, payload }) => {
                        if (active && payload && payload.length > 0) {
                          const data = payload[0].payload;
                          const percentage = ((data.count / players.length) * 100).toFixed(1);
                          return (
                            <div className="bg-[#1a2744] border border-border rounded-lg p-3 shadow-lg">
                              <p className="font-bold text-primary">WAR: {data.range}</p>
                              <p className="text-sm">
                                <span className="text-muted-foreground">Players:</span>{" "}
                                <span className="font-bold">{data.count.toLocaleString()}</span>
                              </p>
                              <p className="text-sm">
                                <span className="text-muted-foreground">Percentage:</span>{" "}
                                <span className="font-bold">{percentage}%</span>
                              </p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Bar
                      dataKey="count"
                      radius={[4, 4, 0, 0]}
                      style={{ cursor: 'pointer' }}
                    >
                      {warDistributionData.map((entry, index) => {
                        // Color gradient based on WAR tier
                        let color = "#64748B";
                        if (entry.range.startsWith("3") || entry.range.startsWith("4")) color = "#D4AF37";
                        else if (entry.range.startsWith("2")) color = "#A855F7";
                        else if (entry.range.startsWith("1")) color = "#3B82F6";
                        return <Cell key={`cell-${index}`} fill={color} />;
                      })}
                    </Bar>
                    <Brush
                      dataKey="range"
                      height={25}
                      stroke="#D4AF37"
                      fill="#1a2744"
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Top Impact Players Table */}
          <Card className="glass">
            <CardHeader className="border-b border-border">
              <CardTitle className="text-sm font-bold uppercase tracking-wider">
                Top Win Impact Players
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left p-4 text-xs uppercase text-muted-foreground">Player</th>
                      <th className="text-left p-4 text-xs uppercase text-muted-foreground">Pos</th>
                      <th className="text-left p-4 text-xs uppercase text-muted-foreground">School</th>
                      <th className="text-right p-4 text-xs uppercase text-muted-foreground">NIL Value</th>
                      <th className="text-right p-4 text-xs uppercase text-muted-foreground">WAR</th>
                      <th className="text-center p-4 text-xs uppercase text-muted-foreground">Grade</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredPlayers.slice(0, 15).map((player) => (
                      <tr key={player.player_id} className="border-b border-border/50 hover:bg-muted/50">
                        <td className="p-4 font-semibold">{player.player_name}</td>
                        <td className="p-4 text-muted-foreground">{player.position}</td>
                        <td className="p-4 text-muted-foreground">{player.school}</td>
                        <td className="p-4 text-right">{formatCurrency(player.nil_valuation)}</td>
                        <td className="p-4 text-right font-bold text-primary">{player.war.toFixed(2)}</td>
                        <td className="p-4 text-center">
                          <Badge className={cn("font-semibold", getGradeColor(player.grade))}>
                            {player.grade}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* ===== PLAYER ANALYSIS TAB ===== */}
        <TabsContent value="player" className="space-y-6">
          <div className="mb-4">
            <h2 className="text-xl font-bold uppercase italic">Individual Player Analysis</h2>
            <p className="text-sm text-muted-foreground">Search any player in our database to analyze their WAR and win impact</p>
          </div>

          {/* Global Player Search */}
          <Card className="glass border-primary/50">
            <CardHeader className="border-b border-border">
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5 text-primary" />
                Search Any Player
              </CardTitle>
              <p className="text-xs text-muted-foreground">
                Search across 21,000+ players to analyze their WAR
              </p>
            </CardHeader>
            <CardContent className="p-6">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Type a player name (e.g., Travis Hunter, Cam Ward)..."
                  value={playerSearchQuery}
                  onChange={(e) => handleSearchInputChange(e.target.value)}
                  className="pl-10 bg-input border-border h-12 text-base"
                />
                {isSearching && (
                  <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-primary" />
                )}
              </div>

              {/* Search Results Dropdown */}
              {playerSearchResults.length > 0 && (
                <div className="mt-2 border border-border rounded-lg bg-card max-h-[300px] overflow-y-auto">
                  {playerSearchResults.map((result, idx) => (
                    <button
                      key={`${result.name}-${idx}`}
                      onClick={() => handleSearchResultSelect(result)}
                      className="w-full p-3 text-left hover:bg-muted transition-colors border-b border-border/50 last:border-b-0 flex items-center justify-between"
                    >
                      <div>
                        <p className="font-semibold">{result.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {result.position} • {result.school}
                        </p>
                      </div>
                      <div className="text-right">
                        {result.nil_value && (
                          <p className="text-sm font-bold text-primary">{formatCurrency(result.nil_value)}</p>
                        )}
                        {result.stars && (
                          <p className="text-xs">{"⭐".repeat(result.stars)}</p>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quick Filter from Loaded Data */}
          <Card className="glass">
            <CardHeader className="border-b border-border pb-4">
              <CardTitle className="text-sm">Or Browse Top Players</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="flex flex-col lg:flex-row gap-4 mb-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Filter loaded players..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 bg-input border-border h-11"
                    />
                  </div>
                </div>
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
              </div>

              {/* Player List */}
              <div className="max-h-[250px] overflow-y-auto">
                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-primary" />
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                    {filteredPlayers.slice(0, 30).map((player) => (
                      <button
                        key={player.player_id}
                        onClick={() => handlePlayerSelect(player)}
                        className={cn(
                          "p-3 rounded-lg text-left transition-colors border",
                          selectedPlayer?.player_id === player.player_id
                            ? "bg-primary/20 border-primary"
                            : "bg-card border-border hover:bg-muted"
                        )}
                      >
                        <p className="font-semibold text-sm">{player.player_name}</p>
                        <p className="text-xs text-muted-foreground">
                          {player.position} • {player.school}
                        </p>
                        <p className="text-xs font-bold text-primary mt-1">WAR: {player.war.toFixed(2)}</p>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Selected Player Analysis */}
          {selectedPlayer && playerWARResult && (
            <>
              {/* Player Card and WAR Breakdown */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Player Info Card - Now with full stats */}
                <Card className="glass border-l-4 border-l-primary">
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4 mb-4">
                      {(selectedPlayer.headshot_url || fullPlayerStats?.headshot_url) && (
                        <img
                          src={selectedPlayer.headshot_url || fullPlayerStats?.headshot_url}
                          alt={selectedPlayer.player_name}
                          className="w-16 h-16 rounded-lg object-cover bg-muted"
                        />
                      )}
                      <div>
                        <h3 className="text-xl font-bold text-primary">{selectedPlayer.player_name}</h3>
                        <p className="text-sm text-muted-foreground">{selectedPlayer.position} • {selectedPlayer.school}</p>
                      </div>
                    </div>

                    {isLoadingStats ? (
                      <div className="flex items-center justify-center py-4">
                        <Loader2 className="h-5 w-5 animate-spin text-primary" />
                        <span className="ml-2 text-sm text-muted-foreground">Loading full stats...</span>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {/* Basic Info */}
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <span className="text-muted-foreground">Stars:</span>{" "}
                            <span className="font-semibold">{"⭐".repeat(fullPlayerStats?.stars || selectedPlayer.stars || 3)}</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">NIL:</span>{" "}
                            <span className="font-semibold text-primary">{formatCurrency(fullPlayerStats?.nil_value || selectedPlayer.nil_valuation)}</span>
                          </div>
                        </div>

                        {/* Physical Measurables */}
                        {(fullPlayerStats?.height || fullPlayerStats?.weight) && (
                          <div className="grid grid-cols-2 gap-2 text-sm border-t border-border pt-3">
                            {fullPlayerStats.height && (
                              <div>
                                <span className="text-muted-foreground">Height:</span>{" "}
                                <span className="font-semibold">{Math.floor(fullPlayerStats.height / 12)}&apos;{Math.round(fullPlayerStats.height % 12)}&quot;</span>
                              </div>
                            )}
                            {fullPlayerStats.weight && (
                              <div>
                                <span className="text-muted-foreground">Weight:</span>{" "}
                                <span className="font-semibold">{fullPlayerStats.weight} lbs</span>
                              </div>
                            )}
                          </div>
                        )}

                        {/* PFF Grades */}
                        {fullPlayerStats?.pff?.overall && (
                          <div className="border-t border-border pt-3">
                            <p className="text-xs text-muted-foreground uppercase mb-2">PFF Grades</p>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              <div className="flex justify-between">
                                <span className="text-muted-foreground">Overall:</span>
                                <span className={cn("font-bold", fullPlayerStats.pff.overall >= 80 ? "text-green-500" : fullPlayerStats.pff.overall >= 70 ? "text-yellow-500" : "text-muted-foreground")}>
                                  {fullPlayerStats.pff.overall.toFixed(1)}
                                </span>
                              </div>
                              {fullPlayerStats.pff.offense && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Offense:</span>
                                  <span className="font-semibold">{fullPlayerStats.pff.offense.toFixed(1)}</span>
                                </div>
                              )}
                              {fullPlayerStats.pff.defense && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Defense:</span>
                                  <span className="font-semibold">{fullPlayerStats.pff.defense.toFixed(1)}</span>
                                </div>
                              )}
                              {fullPlayerStats.pff.passing && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Passing:</span>
                                  <span className="font-semibold">{fullPlayerStats.pff.passing.toFixed(1)}</span>
                                </div>
                              )}
                              {fullPlayerStats.pff.rushing && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Rushing:</span>
                                  <span className="font-semibold">{fullPlayerStats.pff.rushing.toFixed(1)}</span>
                                </div>
                              )}
                              {fullPlayerStats.pff.receiving && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Receiving:</span>
                                  <span className="font-semibold">{fullPlayerStats.pff.receiving.toFixed(1)}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Position-Specific Stats */}
                        {fullPlayerStats?.passing && (
                          <div className="border-t border-border pt-3">
                            <p className="text-xs text-muted-foreground uppercase mb-2">Passing Stats</p>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              {fullPlayerStats.passing.passer_rating && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Passer Rating:</span>
                                  <span className="font-semibold">{fullPlayerStats.passing.passer_rating.toFixed(1)}</span>
                                </div>
                              )}
                              {fullPlayerStats.passing.completion_pct && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Comp %:</span>
                                  <span className="font-semibold">{fullPlayerStats.passing.completion_pct.toFixed(1)}%</span>
                                </div>
                              )}
                              {fullPlayerStats.passing.big_time_throw_pct && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">BTT %:</span>
                                  <span className="font-semibold">{fullPlayerStats.passing.big_time_throw_pct.toFixed(1)}%</span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {fullPlayerStats?.rushing && (
                          <div className="border-t border-border pt-3">
                            <p className="text-xs text-muted-foreground uppercase mb-2">Rushing Stats</p>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              {fullPlayerStats.rushing.elusive_rating && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Elusive Rating:</span>
                                  <span className="font-semibold">{fullPlayerStats.rushing.elusive_rating.toFixed(1)}</span>
                                </div>
                              )}
                              {fullPlayerStats.rushing.yards_per_carry && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">YPC:</span>
                                  <span className="font-semibold">{fullPlayerStats.rushing.yards_per_carry.toFixed(1)}</span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {fullPlayerStats?.receiving && (
                          <div className="border-t border-border pt-3">
                            <p className="text-xs text-muted-foreground uppercase mb-2">Receiving Stats</p>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              {fullPlayerStats.receiving.yards_per_route_run && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">YPRR:</span>
                                  <span className="font-semibold">{fullPlayerStats.receiving.yards_per_route_run.toFixed(2)}</span>
                                </div>
                              )}
                              {fullPlayerStats.receiving.drop_rate && (
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Drop Rate:</span>
                                  <span className="font-semibold">{fullPlayerStats.receiving.drop_rate.toFixed(1)}%</span>
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* WAR Breakdown */}
                <Card className="glass lg:col-span-2">
                  <CardHeader className="border-b border-border">
                    <CardTitle className="flex items-center justify-between">
                      <span>Portal IQ WAR Breakdown</span>
                      <div className="flex items-center gap-4">
                        <span className="text-3xl font-bold text-primary">{playerWARResult.war.toFixed(2)}</span>
                        <Badge className={cn("font-semibold", getGradeColor(selectedPlayer.grade))}>
                          {selectedPlayer.grade}
                        </Badge>
                      </div>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="text-center p-3 rounded-lg bg-card border border-border">
                        <p className="text-xs text-muted-foreground">Total WAR</p>
                        <p className="text-xl font-bold">{playerWARResult.war.toFixed(2)}</p>
                      </div>
                      <div className="text-center p-3 rounded-lg bg-card border border-border">
                        <p className="text-xs text-muted-foreground">WAR Range</p>
                        <p className="text-xl font-bold">{playerWARResult.war_low.toFixed(2)} - {playerWARResult.war_high.toFixed(2)}</p>
                      </div>
                      <div className="text-center p-3 rounded-lg bg-card border border-border">
                        <p className="text-xs text-muted-foreground">Confidence</p>
                        <p className="text-xl font-bold capitalize">{playerWARResult.confidence}</p>
                      </div>
                      <div className="text-center p-3 rounded-lg bg-card border border-border">
                        <p className="text-xs text-muted-foreground">School Tier</p>
                        <p className="text-xl font-bold capitalize">{playerWARResult.breakdown.school_tier}</p>
                      </div>
                    </div>

                    <h4 className="text-sm font-bold uppercase mb-3">Factor Breakdown</h4>
                    <div className="grid grid-cols-3 gap-3">
                      <FactorCard label="Base WAR (Position)" value={playerWARResult.breakdown.base_war.toFixed(2)} />
                      <FactorCard label="Position Scarcity" value={`×${playerWARResult.breakdown.position_scarcity.toFixed(2)}`} />
                      <FactorCard label="Star Multiplier" value={`×${playerWARResult.breakdown.star_multiplier.toFixed(2)}`} />
                      <FactorCard label="School Multiplier" value={`×${playerWARResult.breakdown.school_multiplier.toFixed(2)}`} />
                      <FactorCard label="Measurables Factor" value={`×${playerWARResult.breakdown.measurables_factor.toFixed(2)}`} />
                      <FactorCard label="NIL Market Bonus" value={playerWARResult.breakdown.nil_bonus.toFixed(2)} isBonus />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Transfer Value Analysis */}
              {transferValue && (
                <Card className="glass">
                  <CardHeader className="border-b border-border">
                    <CardTitle>Transfer Value Analysis</CardTitle>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="text-center p-4 rounded-lg bg-card border border-border">
                        <p className="text-xs text-muted-foreground uppercase mb-2">Cost per WAR</p>
                        <p className="text-xl font-bold">{formatCurrency(transferValue.cost_per_war)}</p>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-card border border-border">
                        <p className="text-xs text-muted-foreground uppercase mb-2">Fair Value/WAR</p>
                        <p className="text-xl font-bold">{formatCurrency(transferValue.fair_value_per_war)}</p>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-card border border-border">
                        <p className="text-xs text-muted-foreground uppercase mb-2">Value Rating</p>
                        <p className={cn(
                          "text-lg font-bold capitalize",
                          transferValue.value_rating.includes("value") ? "text-green-500" : "text-orange-500"
                        )}>
                          {transferValue.value_rating.replace(/_/g, " ")}
                        </p>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-card border border-border">
                        <p className="text-xs text-muted-foreground uppercase mb-2">Market Comparison</p>
                        <p className="text-lg font-bold">{transferValue.market_comparison}</p>
                      </div>
                    </div>
                    <div className="bg-primary/10 border border-primary/30 rounded-lg p-4">
                      <p className="text-sm"><strong>ROI Projection:</strong> {transferValue.roi_projection}</p>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Transfer Impact Projection */}
              <Card className="glass">
                <CardHeader className="border-b border-border">
                  <CardTitle>Transfer Impact Projection</CardTitle>
                </CardHeader>
                <CardContent className="p-6">
                  <p className="text-sm text-muted-foreground mb-4">How would this player impact different teams?</p>

                  <div className="mb-4">
                    <Label>Select Target School</Label>
                    <Select value={targetSchool} onValueChange={handleTargetSchoolChange}>
                      <SelectTrigger className="w-full max-w-md mt-2">
                        <SelectValue placeholder="Choose a school..." />
                      </SelectTrigger>
                      <SelectContent>
                        {schoolList.map((school) => (
                          <SelectItem key={school} value={school}>
                            {school}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {transferImpact && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center p-4 rounded-lg bg-card border border-border">
                        <p className="text-xs text-muted-foreground uppercase mb-2">School Tier</p>
                        <p className="text-xl font-bold capitalize">{getSchoolTier(targetSchool || selectedPlayer.school).tier}</p>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-card border border-border">
                        <p className="text-xs text-muted-foreground uppercase mb-2">Current Win Baseline</p>
                        <p className="text-xl font-bold">{transferImpact.current_baseline} wins</p>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-card border border-border">
                        <p className="text-xs text-muted-foreground uppercase mb-2">Projected Improvement</p>
                        <p className="text-xl font-bold text-green-500">+{transferImpact.projected_wins_added} wins</p>
                        <p className="text-xs text-muted-foreground">to {transferImpact.new_projected_wins} total</p>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-card border border-border">
                        <p className="text-xs text-muted-foreground uppercase mb-2">Playoff Impact</p>
                        <p className="text-xl font-bold">{transferImpact.playoff_impact}</p>
                      </div>
                    </div>
                  )}

                  {transferImpact && transferImpact.diminishing_factor < 1 && (
                    <p className="text-xs text-muted-foreground mt-4 italic">
                      Note: Diminishing returns factor of {(transferImpact.diminishing_factor * 100).toFixed(0)}% applied for already-competitive team.
                    </p>
                  )}
                </CardContent>
              </Card>
            </>
          )}

          {!selectedPlayer && (
            <Card className="glass">
              <CardContent className="p-12 flex flex-col items-center justify-center">
                <Search className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Select a Player</h3>
                <p className="text-muted-foreground text-center">
                  Search and click on a player above to see their detailed WAR breakdown
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ===== TEAM PORTAL IMPACT TAB ===== */}
        <TabsContent value="team" className="space-y-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold uppercase italic">Team Portal Impact Rankings</h2>
              <p className="text-sm text-muted-foreground">Real-time portal data with incoming and outgoing transfers</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchTeamRankings}
              disabled={isLoadingTeamRankings}
            >
              <RefreshCw className={cn("h-4 w-4 mr-2", isLoadingTeamRankings && "animate-spin")} />
              Refresh
            </Button>
          </div>

          {/* Team Rankings from API */}
          <Card className="glass">
            <CardHeader className="border-b border-border">
              <CardTitle className="text-sm font-bold uppercase tracking-wider flex items-center justify-between">
                <span>Top Portal Classes (2026)</span>
                <Badge variant="secondary">{portalTeamRankings.length} teams</Badge>
              </CardTitle>
              <p className="text-xs text-muted-foreground mt-1">
                Click on a team to see incoming/outgoing transfers
              </p>
            </CardHeader>
            <CardContent className="p-6">
              {isLoadingTeamRankings ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  <span className="ml-3 text-muted-foreground">Loading team rankings...</span>
                </div>
              ) : portalTeamRankings.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <Building2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No team rankings available yet.</p>
                  <p className="text-sm">Rankings will appear when players commit to new schools.</p>
                </div>
              ) : (
                <div className="h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={portalTeamRankings.slice(0, 20)}
                      layout="horizontal"
                      onClick={(data) => {
                        const payload = (data as unknown as { activePayload?: Array<{ payload: TeamRanking }> })?.activePayload?.[0];
                        if (payload) {
                          // Fetch portal activity for the selected team
                          fetchTeamActivity(payload.payload.team);
                        }
                      }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                      <XAxis dataKey="team" stroke="#888" angle={-45} textAnchor="end" height={100} fontSize={11} />
                      <YAxis stroke="#888" />
                      <Tooltip
                        cursor={{ fill: 'rgba(212, 175, 55, 0.1)' }}
                        content={({ active, payload }) => {
                          if (active && payload && payload.length > 0) {
                            const data = payload[0].payload as TeamRanking;
                            return (
                              <div className="bg-[#1a2744] border border-border rounded-lg p-4 shadow-lg min-w-[220px]">
                                <div className="flex items-center justify-between mb-2">
                                  <p className="font-bold text-primary text-lg">{data.team}</p>
                                  <Badge className={cn("font-semibold", getGradeColor(data.grade))}>
                                    {data.grade}
                                  </Badge>
                                </div>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
                                  <span className="text-muted-foreground">Portal Score:</span>
                                  <span className="font-bold">{data.portal_score.toFixed(1)}</span>
                                  <span className="text-muted-foreground">WAR Added:</span>
                                  <span className="font-bold text-green-400">+{data.war_added.toFixed(2)}</span>
                                  <span className="text-muted-foreground">NIL Invested:</span>
                                  <span className="font-bold">{formatCurrency(data.total_nil_invested)}</span>
                                  <span className="text-muted-foreground">Transfers In:</span>
                                  <span className="font-bold">{data.breakdown?.transfers_in || 0}</span>
                                  <span className="text-muted-foreground">Avg Stars:</span>
                                  <span className="font-bold">{data.breakdown?.avg_stars?.toFixed(1) || "N/A"}</span>
                                </div>
                                <p className="text-xs text-muted-foreground mt-3 italic">Click for full portal activity</p>
                              </div>
                            );
                          }
                          return null;
                        }}
                      />
                      <Bar dataKey="portal_score" radius={[4, 4, 0, 0]} style={{ cursor: 'pointer' }}>
                        {portalTeamRankings.slice(0, 20).map((entry, index) => {
                          let color = "#64748B";
                          if (entry.grade === "A+" || entry.grade === "A") color = "#D4AF37";
                          else if (entry.grade === "B+" || entry.grade === "B") color = "#A855F7";
                          else if (entry.grade === "C+" || entry.grade === "C") color = "#3B82F6";
                          return <Cell key={`cell-${index}`} fill={color} />;
                        })}
                      </Bar>
                      <Brush
                        dataKey="team"
                        height={25}
                        stroke="#D4AF37"
                        fill="#1a2744"
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Team Details Selector */}
          <Card className="glass">
            <CardHeader className="border-b border-border">
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-primary" />
                Team Portal Activity
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="mb-4">
                <Label>Select Team for Detailed Analysis</Label>
                <Select
                  onValueChange={(team) => {
                    fetchTeamActivity(team);
                  }}
                >
                  <SelectTrigger className="w-full max-w-md mt-2">
                    <SelectValue placeholder="Choose a team..." />
                  </SelectTrigger>
                  <SelectContent>
                    {portalTeamRankings.map((team) => (
                      <SelectItem key={team.team} value={team.team}>
                        {team.team} ({team.grade})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {teamPortalActivity ? (
                <div className="space-y-6">
                  {/* Summary Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Card className="bg-card">
                      <CardContent className="p-4 text-center">
                        <p className="text-xs text-muted-foreground uppercase mb-2">Incoming</p>
                        <p className="text-2xl font-bold text-green-500">+{teamPortalActivity.incoming.length}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-card">
                      <CardContent className="p-4 text-center">
                        <p className="text-xs text-muted-foreground uppercase mb-2">Outgoing</p>
                        <p className="text-2xl font-bold text-red-500">-{teamPortalActivity.outgoing.length}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-card">
                      <CardContent className="p-4 text-center">
                        <p className="text-xs text-muted-foreground uppercase mb-2">Net Talent</p>
                        <p className={cn(
                          "text-2xl font-bold",
                          teamPortalActivity.net_talent_change >= 0 ? "text-green-500" : "text-red-500"
                        )}>
                          {teamPortalActivity.net_talent_change >= 0 ? "+" : ""}{teamPortalActivity.net_talent_change} Stars
                        </p>
                      </CardContent>
                    </Card>
                    <Card className="bg-card">
                      <CardContent className="p-4 text-center">
                        <p className="text-xs text-muted-foreground uppercase mb-2">Total NIL In</p>
                        <p className="text-2xl font-bold text-primary">
                          {formatCurrency(teamPortalActivity.incoming.reduce((sum, p) => sum + (p.nil_valuation || 0), 0))}
                        </p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Incoming Transfers */}
                  {teamPortalActivity.incoming.length > 0 && (
                    <div>
                      <h4 className="text-sm font-bold uppercase mb-3 flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-green-500" />
                        Incoming Transfers ({teamPortalActivity.incoming.length})
                      </h4>
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead>
                            <tr className="border-b border-border">
                              <th className="text-left p-3 text-xs uppercase text-muted-foreground">Player</th>
                              <th className="text-left p-3 text-xs uppercase text-muted-foreground">Position</th>
                              <th className="text-left p-3 text-xs uppercase text-muted-foreground">From</th>
                              <th className="text-center p-3 text-xs uppercase text-muted-foreground">Stars</th>
                              <th className="text-right p-3 text-xs uppercase text-muted-foreground">NIL Value</th>
                            </tr>
                          </thead>
                          <tbody>
                            {teamPortalActivity.incoming
                              .sort((a, b) => (b.stars || 0) - (a.stars || 0))
                              .slice(0, 15)
                              .map((player, idx) => (
                              <tr key={`incoming-${idx}`} className="border-b border-border/50">
                                <td className="p-3 font-semibold">{player.player_name}</td>
                                <td className="p-3 text-muted-foreground">{player.position}</td>
                                <td className="p-3 text-muted-foreground">{player.origin_school || "Unknown"}</td>
                                <td className="p-3 text-center">{"⭐".repeat(player.stars || 3)}</td>
                                <td className="p-3 text-right font-bold text-primary">{formatCurrency(player.nil_valuation)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Outgoing Transfers */}
                  {teamPortalActivity.outgoing.length > 0 && (
                    <div>
                      <h4 className="text-sm font-bold uppercase mb-3 flex items-center gap-2">
                        <ArrowRight className="h-4 w-4 text-red-500" />
                        Outgoing Transfers ({teamPortalActivity.outgoing.length})
                      </h4>
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead>
                            <tr className="border-b border-border">
                              <th className="text-left p-3 text-xs uppercase text-muted-foreground">Player</th>
                              <th className="text-left p-3 text-xs uppercase text-muted-foreground">Position</th>
                              <th className="text-left p-3 text-xs uppercase text-muted-foreground">To</th>
                              <th className="text-center p-3 text-xs uppercase text-muted-foreground">Status</th>
                              <th className="text-right p-3 text-xs uppercase text-muted-foreground">Stars</th>
                            </tr>
                          </thead>
                          <tbody>
                            {teamPortalActivity.outgoing
                              .sort((a, b) => (b.stars || 0) - (a.stars || 0))
                              .slice(0, 15)
                              .map((player, idx) => (
                              <tr key={`outgoing-${idx}`} className="border-b border-border/50">
                                <td className="p-3 font-semibold">{player.player_name}</td>
                                <td className="p-3 text-muted-foreground">{player.position}</td>
                                <td className="p-3 text-muted-foreground">{player.destination_school || "Still in portal"}</td>
                                <td className="p-3 text-center">
                                  <Badge variant={player.status === "committed" ? "default" : "secondary"}>
                                    {player.status}
                                  </Badge>
                                </td>
                                <td className="p-3 text-right">{"⭐".repeat(player.stars || 3)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Building2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Select a team above to see incoming and outgoing transfers</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

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

      {/* Info Section */}
      <Card className="glass">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
              <BarChart3 className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-bold mb-2">About Portal IQ WAR Algorithm</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Our proprietary WAR (Wins Above Replacement) algorithm evaluates player impact using 6 key factors:
                Position Value & Scarcity, Recruiting Profile (stars + rating), NIL Market Signal,
                Destination School Tier, Physical Measurables, and Experience Factor. Unlike basic portal rankings,
                this creates a holistic view of true on-field impact. QBs have the highest individual impact (3.0 base WAR),
                followed by EDGE rushers (1.5) and CBs (1.2). This metric helps evaluate if a player&apos;s NIL valuation
                represents good ROI for your program.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
