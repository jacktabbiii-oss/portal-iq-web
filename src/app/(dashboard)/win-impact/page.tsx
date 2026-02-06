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

const positions = ["All", "QB", "RB", "WR", "TE", "OT", "OG", "C", "DL", "EDGE", "LB", "CB", "S"];

const CHART_COLORS = ["#D4AF37", "#22C55E", "#3B82F6", "#A855F7", "#F59E0B", "#EF4444"];

function formatCurrency(value: number): string {
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

  // Fetch WAR data
  const fetchPlayers = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const params: { position?: string; limit: number } = { limit: 200 };
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

  // Chart data - WAR vs NIL scatter
  const warVsNILData = useMemo(() => {
    return filteredPlayers.slice(0, 50).map(p => ({
      name: p.player_name,
      war: p.war,
      nil: p.nil_valuation / 1000000,
      grade: p.grade,
    }));
  }, [filteredPlayers]);

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
                    <Label>PFF Grade (optional)</Label>
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
                <p className="text-2xl font-bold">{stats.totalPlayers.toLocaleString()}</p>
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
              </CardHeader>
              <CardContent className="p-6">
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={positionWARData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                      <XAxis type="number" domain={[0, 3]} stroke="#888" />
                      <YAxis dataKey="position" type="category" stroke="#888" width={50} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#1a2744",
                          border: "1px solid #333",
                          borderRadius: "8px",
                        }}
                        formatter={(value) => [typeof value === 'number' ? value.toFixed(2) : '0', "Avg WAR"]}
                      />
                      <Bar dataKey="avgWAR" fill="#D4AF37" radius={[0, 4, 4, 0]}>
                        {positionWARData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* NIL vs WAR Scatter */}
            <Card className="glass">
              <CardHeader className="border-b border-border">
                <CardTitle className="text-sm font-bold uppercase tracking-wider">
                  NIL vs Win Impact Correlation
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                <div className="h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart margin={{ top: 10, right: 10, bottom: 20, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                      <XAxis
                        type="number"
                        dataKey="nil"
                        name="NIL"
                        unit="M"
                        stroke="#888"
                        tickFormatter={(v) => `$${v}M`}
                      />
                      <YAxis type="number" dataKey="war" name="WAR" stroke="#888" />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#1a2744",
                          border: "1px solid #333",
                          borderRadius: "8px",
                        }}
                        formatter={(value, name) => {
                          const v = typeof value === 'number' ? value : 0;
                          if (name === "nil") return [`$${v.toFixed(2)}M`, "NIL Value"];
                          return [v.toFixed(2), "WAR"];
                        }}
                      />
                      <Scatter data={warVsNILData} fill="#D4AF37">
                        {warVsNILData.map((entry, index) => {
                          const gradeColors: Record<string, string> = {
                            Elite: "#D4AF37",
                            Premium: "#A855F7",
                            Solid: "#3B82F6",
                            Average: "#64748B",
                          };
                          return (
                            <Cell key={`cell-${index}`} fill={gradeColors[entry.grade] || "#D4AF37"} />
                          );
                        })}
                      </Scatter>
                    </ScatterChart>
                  </ResponsiveContainer>
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
            </CardHeader>
            <CardContent className="p-6">
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={warDistributionData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="range" stroke="#888" />
                    <YAxis stroke="#888" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1a2744",
                        border: "1px solid #333",
                        borderRadius: "8px",
                      }}
                    />
                    <Area type="monotone" dataKey="count" stroke="#D4AF37" fill="#D4AF37" fillOpacity={0.3} />
                  </AreaChart>
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
            <p className="text-sm text-muted-foreground">Detailed WAR breakdown and win impact projection</p>
          </div>

          {/* Player Search */}
          <Card className="glass">
            <CardContent className="p-6">
              <div className="flex flex-col lg:flex-row gap-4">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search players by name..."
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
              <div className="mt-4 max-h-[300px] overflow-y-auto">
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
                {/* Player Info Card */}
                <Card className="glass border-l-4 border-l-primary">
                  <CardContent className="p-6">
                    <h3 className="text-2xl font-bold text-primary mb-4">{selectedPlayer.player_name}</h3>
                    <div className="space-y-2 text-sm">
                      <p><span className="text-muted-foreground">Position:</span> {selectedPlayer.position}</p>
                      <p><span className="text-muted-foreground">School:</span> {selectedPlayer.school}</p>
                      <p><span className="text-muted-foreground">Stars:</span> {"⭐".repeat(selectedPlayer.stars || 3)}</p>
                      <p><span className="text-muted-foreground">NIL Value:</span> {formatCurrency(selectedPlayer.nil_valuation)}</p>
                    </div>
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
          <div className="mb-4">
            <h2 className="text-xl font-bold uppercase italic">Team Portal Impact Rankings</h2>
            <p className="text-sm text-muted-foreground">Proprietary team impact scores based on portal acquisitions</p>
          </div>

          {/* Team Scores Chart */}
          <Card className="glass">
            <CardHeader className="border-b border-border">
              <CardTitle className="text-sm font-bold uppercase tracking-wider">
                Portal IQ Team Impact Scores (Top 20)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={teamScores.slice(0, 20)} layout="horizontal">
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="team" stroke="#888" angle={-45} textAnchor="end" height={100} fontSize={11} />
                    <YAxis stroke="#888" domain={[0, 100]} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1a2744",
                        border: "1px solid #333",
                        borderRadius: "8px",
                      }}
                      formatter={(value, name) => {
                        const v = typeof value === 'number' ? value : 0;
                        if (name === "portal_score") return [v.toFixed(1), "Score"];
                        return [v, name];
                      }}
                    />
                    <Bar dataKey="portal_score" radius={[4, 4, 0, 0]}>
                      {teamScores.slice(0, 20).map((entry, index) => {
                        let color = "#64748B";
                        if (entry.grade === "A+" || entry.grade === "A") color = "#D4AF37";
                        else if (entry.grade === "B+" || entry.grade === "B") color = "#A855F7";
                        else if (entry.grade === "C+" || entry.grade === "C") color = "#3B82F6";
                        return <Cell key={`cell-${index}`} fill={color} />;
                      })}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Team Details Selector */}
          <Card className="glass">
            <CardHeader className="border-b border-border">
              <CardTitle>Team Details</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="mb-4">
                <Label>Select Team for Detailed Analysis</Label>
                <Select
                  value={selectedTeam?.team || ""}
                  onValueChange={(team) => {
                    const t = teamScores.find(s => s.team === team);
                    setSelectedTeam(t || null);
                  }}
                >
                  <SelectTrigger className="w-full max-w-md mt-2">
                    <SelectValue placeholder="Choose a team..." />
                  </SelectTrigger>
                  <SelectContent>
                    {teamScores.map((team) => (
                      <SelectItem key={team.team} value={team.team}>
                        {team.team} ({team.grade})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {selectedTeam && (
                <div className="space-y-6">
                  {/* Summary Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Card className="bg-card">
                      <CardContent className="p-4 text-center">
                        <p className="text-xs text-muted-foreground uppercase mb-2">Portal Grade</p>
                        <Badge className={cn("text-2xl px-4 py-1", getGradeColor(selectedTeam.grade))}>
                          {selectedTeam.grade}
                        </Badge>
                      </CardContent>
                    </Card>
                    <Card className="bg-card">
                      <CardContent className="p-4 text-center">
                        <p className="text-xs text-muted-foreground uppercase mb-2">Portal IQ Score</p>
                        <p className="text-2xl font-bold">{selectedTeam.portal_score.toFixed(1)}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-card">
                      <CardContent className="p-4 text-center">
                        <p className="text-xs text-muted-foreground uppercase mb-2">WAR Added</p>
                        <p className="text-2xl font-bold text-green-500">+{selectedTeam.war_added.toFixed(2)}</p>
                      </CardContent>
                    </Card>
                    <Card className="bg-card">
                      <CardContent className="p-4 text-center">
                        <p className="text-xs text-muted-foreground uppercase mb-2">Net WAR</p>
                        <p className="text-2xl font-bold">{selectedTeam.net_war >= 0 ? "+" : ""}{selectedTeam.net_war.toFixed(2)}</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Detailed Breakdown */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-4 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground uppercase mb-1">Transfers In</p>
                      <p className="text-xl font-bold">{selectedTeam.breakdown.transfers_in}</p>
                    </div>
                    <div className="text-center p-4 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground uppercase mb-1">Avg WAR/Transfer</p>
                      <p className="text-xl font-bold">{selectedTeam.avg_war_per_transfer.toFixed(2)}</p>
                    </div>
                    <div className="text-center p-4 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground uppercase mb-1">Position Balance</p>
                      <p className="text-xl font-bold">{(selectedTeam.breakdown.position_balance * 100).toFixed(0)}%</p>
                    </div>
                    <div className="text-center p-4 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground uppercase mb-1">Star Quality</p>
                      <p className="text-xl font-bold">{selectedTeam.breakdown.star_quality.toFixed(2)}</p>
                    </div>
                  </div>

                  {/* Star Distribution */}
                  <div>
                    <h4 className="text-sm font-bold uppercase mb-3">Transfer Quality Distribution</h4>
                    <div className="grid grid-cols-4 gap-4">
                      <div className="text-center p-4 rounded-lg bg-card border border-border">
                        <Star className="h-5 w-5 text-primary mx-auto mb-1" />
                        <p className="text-xs text-muted-foreground">5-Star</p>
                        <p className="text-xl font-bold">{selectedTeam.breakdown.star_distribution[5] || 0}</p>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-card border border-border">
                        <Star className="h-5 w-5 text-purple-500 mx-auto mb-1" />
                        <p className="text-xs text-muted-foreground">4-Star</p>
                        <p className="text-xl font-bold">{selectedTeam.breakdown.star_distribution[4] || 0}</p>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-card border border-border">
                        <Star className="h-5 w-5 text-blue-500 mx-auto mb-1" />
                        <p className="text-xs text-muted-foreground">3-Star</p>
                        <p className="text-xl font-bold">{selectedTeam.breakdown.star_distribution[3] || 0}</p>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-card border border-border">
                        <Star className="h-5 w-5 text-slate-500 mx-auto mb-1" />
                        <p className="text-xs text-muted-foreground">2-Star</p>
                        <p className="text-xl font-bold">{selectedTeam.breakdown.star_distribution[2] || 0}</p>
                      </div>
                    </div>
                  </div>

                  {/* Incoming Transfers Table */}
                  {selectedTeam.incoming_players && selectedTeam.incoming_players.length > 0 && (
                    <div>
                      <h4 className="text-sm font-bold uppercase mb-3">{selectedTeam.team} Incoming Transfers</h4>
                      <div className="overflow-x-auto">
                        <table className="w-full">
                          <thead>
                            <tr className="border-b border-border">
                              <th className="text-left p-3 text-xs uppercase text-muted-foreground">Player</th>
                              <th className="text-left p-3 text-xs uppercase text-muted-foreground">Position</th>
                              <th className="text-left p-3 text-xs uppercase text-muted-foreground">From</th>
                              <th className="text-center p-3 text-xs uppercase text-muted-foreground">Stars</th>
                              <th className="text-right p-3 text-xs uppercase text-muted-foreground">WAR</th>
                            </tr>
                          </thead>
                          <tbody>
                            {selectedTeam.incoming_players
                              .sort((a, b) => b.war - a.war)
                              .slice(0, 15)
                              .map((player) => (
                              <tr key={player.player_id} className="border-b border-border/50">
                                <td className="p-3 font-semibold">{player.player_name}</td>
                                <td className="p-3 text-muted-foreground">{player.position}</td>
                                <td className="p-3 text-muted-foreground">{player.origin_school || "Unknown"}</td>
                                <td className="p-3 text-center">{"⭐".repeat(player.stars || 3)}</td>
                                <td className="p-3 text-right font-bold text-primary">{player.war.toFixed(2)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {!selectedTeam && (
                <div className="text-center py-8">
                  <Building2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Select a team above to see detailed portal analysis</p>
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
