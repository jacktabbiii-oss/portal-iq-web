"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { StatCard } from "@/components/cards/stat-card";
import { RiskBadge } from "@/components/cards/tier-badge";
import {
  formatCurrency,
  formatPercentage,
  formatRelativeTime,
  POSITIONS,
  CONFERENCES,
  getRiskLevel,
} from "@/lib/utils";
import type { RiskLevel } from "@/types";
import {
  ArrowRightLeft,
  Search,
  AlertTriangle,
  Target,
  Users,
  TrendingUp,
  TrendingDown,
  School,
} from "lucide-react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
} from "recharts";

// Demo data
const portalPlayers = [
  { name: "Marcus Johnson", position: "QB", fromSchool: "UCLA", stars: 4, rating: 0.89, nilEstimate: 450000, entryDate: "2024-01-15T10:30:00Z", status: "active" },
  { name: "DeShawn Williams", position: "WR", fromSchool: "Florida State", stars: 4, rating: 0.85, nilEstimate: 280000, entryDate: "2024-01-15T09:15:00Z", status: "active" },
  { name: "Tyler Brown", position: "CB", fromSchool: "Michigan State", stars: 3, rating: 0.82, nilEstimate: 150000, entryDate: "2024-01-14T16:00:00Z", status: "committed" },
  { name: "James Wilson", position: "RB", fromSchool: "Arkansas", stars: 4, rating: 0.86, nilEstimate: 220000, entryDate: "2024-01-14T12:00:00Z", status: "active" },
  { name: "Chris Davis", position: "EDGE", fromSchool: "Tennessee", stars: 5, rating: 0.91, nilEstimate: 520000, entryDate: "2024-01-13T18:30:00Z", status: "active" },
];

const atRiskPlayers = [
  { name: "Jordan Smith", school: "Tennessee", position: "WR", risk: 0.82, factors: ["Below market NIL", "Lack of playing time"] },
  { name: "Mike Johnson", school: "Alabama", position: "LB", risk: 0.68, factors: ["Coaching change", "Position competition"] },
  { name: "David Lee", school: "Georgia", position: "RB", risk: 0.55, factors: ["Depth chart position", "NIL opportunity"] },
  { name: "Ryan Taylor", school: "Ohio State", position: "CB", risk: 0.45, factors: ["Playing time concerns"] },
  { name: "Kevin Brown", school: "Texas", position: "OT", risk: 0.32, factors: ["Starter concern"] },
];

const fitAnalysisData = [
  { category: "Positional Need", value: 92 },
  { category: "Production Upgrade", value: 85 },
  { category: "Tier Match", value: 78 },
  { category: "NIL Budget Fit", value: 70 },
  { category: "Geographic Proximity", value: 65 },
  { category: "Scheme Fit", value: 88 },
];

const RISK_COLORS = {
  critical: "#ef4444",
  high: "#f97316",
  moderate: "#eab308",
  low: "#22c55e",
};

export default function PortalIntelligencePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [positionFilter, setPositionFilter] = useState("all");
  const [conferenceFilter, setConferenceFilter] = useState("all");
  const [selectedSchool, setSelectedSchool] = useState("Tennessee");
  const [selectedPlayer, setSelectedPlayer] = useState("");
  const [targetSchool, setTargetSchool] = useState("");

  const filteredPlayers = portalPlayers.filter((player) => {
    if (positionFilter !== "all" && player.position !== positionFilter) return false;
    if (searchQuery && !player.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <ArrowRightLeft className="h-8 w-8 text-blue-500" />
          Portal Intelligence
        </h1>
        <p className="text-muted-foreground mt-1">
          Track transfer portal movements, predict flight risk, and analyze fits
        </p>
      </div>

      <Tabs defaultValue="portal" className="space-y-6">
        <TabsList className="bg-secondary">
          <TabsTrigger value="portal" className="flex items-center gap-2">
            <ArrowRightLeft className="h-4 w-4" />
            Active Portal
          </TabsTrigger>
          <TabsTrigger value="flight-risk" className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" />
            Flight Risk
          </TabsTrigger>
          <TabsTrigger value="fit-analyzer" className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            Fit Analyzer
          </TabsTrigger>
        </TabsList>

        {/* Active Portal Tab */}
        <TabsContent value="portal" className="space-y-6">
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              title="Active Entries"
              value="2,156"
              change="+37 today"
              changeType="positive"
              icon={Users}
            />
            <StatCard
              title="Committed"
              value="1,245"
              description="57.8% placement rate"
              icon={School}
            />
            <StatCard
              title="Avg. Portal NIL"
              value="$185K"
              change="+12% vs last year"
              changeType="positive"
              icon={TrendingUp}
            />
            <StatCard
              title="Top Position"
              value="QB"
              description="342 active entries"
              icon={ArrowRightLeft}
            />
          </div>

          {/* Filters and table */}
          <Card className="bg-card border-border/50">
            <CardHeader>
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <CardTitle>Portal Players</CardTitle>
                <div className="flex flex-wrap gap-3">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search players..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10 w-48"
                    />
                  </div>
                  <Select value={positionFilter} onValueChange={setPositionFilter}>
                    <SelectTrigger className="w-32">
                      <SelectValue placeholder="Position" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Positions</SelectItem>
                      {POSITIONS.map((pos) => (
                        <SelectItem key={pos} value={pos}>{pos}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select value={conferenceFilter} onValueChange={setConferenceFilter}>
                    <SelectTrigger className="w-40">
                      <SelectValue placeholder="Conference" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Conferences</SelectItem>
                      {CONFERENCES.map((conf) => (
                        <SelectItem key={conf} value={conf}>{conf}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {filteredPlayers.map((player, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-4 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold">
                        {player.position}
                      </div>
                      <div>
                        <p className="font-medium">{player.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {player.stars}★ • from {player.fromSchool}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <p className="font-medium">{formatCurrency(player.nilEstimate, { compact: true })}</p>
                        <p className="text-xs text-muted-foreground">Est. NIL</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm">{(player.rating * 100).toFixed(0)}</p>
                        <p className="text-xs text-muted-foreground">Rating</p>
                      </div>
                      <div className="text-right min-w-[80px]">
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          player.status === "active"
                            ? "bg-blue-500/20 text-blue-400"
                            : "bg-green-500/20 text-green-400"
                        }`}>
                          {player.status}
                        </span>
                      </div>
                      <div className="text-right text-sm text-muted-foreground min-w-[80px]">
                        {formatRelativeTime(player.entryDate)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Flight Risk Tab */}
        <TabsContent value="flight-risk" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Team selector and stats */}
            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle>Select Team</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Select value={selectedSchool} onValueChange={setSelectedSchool}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select school" />
                  </SelectTrigger>
                  <SelectContent>
                    {["Alabama", "Georgia", "Ohio State", "Michigan", "Texas", "Tennessee", "USC"].map((school) => (
                      <SelectItem key={school} value={school}>{school}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button className="w-full">Analyze Roster</Button>

                <div className="pt-4 space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Total Roster</span>
                    <span className="font-semibold">85 players</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">High Risk</span>
                    <span className="font-semibold text-orange-500">12 players</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Est. Wins at Risk</span>
                    <span className="font-semibold text-red-500">2.3 wins</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Retention Budget</span>
                    <span className="font-semibold text-primary">$1.8M</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Risk distribution */}
            <Card className="bg-card border-border/50 lg:col-span-2">
              <CardHeader>
                <CardTitle>At-Risk Players</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {atRiskPlayers.map((player, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-4 rounded-lg bg-secondary/50"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center text-orange-400 font-bold text-sm">
                        {player.position}
                      </div>
                      <div>
                        <p className="font-medium">{player.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {player.school} • {player.position}
                        </p>
                        <div className="flex gap-1 mt-1">
                          {player.factors.map((factor, j) => (
                            <span
                              key={j}
                              className="text-xs px-2 py-0.5 rounded bg-secondary text-muted-foreground"
                            >
                              {factor}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-lg font-bold">{formatPercentage(player.risk)}</p>
                        <p className="text-xs text-muted-foreground">Flight Risk</p>
                      </div>
                      <RiskBadge level={getRiskLevel(player.risk)} />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Risk by position chart */}
          <Card className="bg-card border-border/50">
            <CardHeader>
              <CardTitle>Risk by Position</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={[
                      { position: "QB", highRisk: 2, moderate: 1, low: 3 },
                      { position: "RB", highRisk: 1, moderate: 3, low: 4 },
                      { position: "WR", highRisk: 3, moderate: 4, low: 6 },
                      { position: "TE", highRisk: 0, moderate: 1, low: 3 },
                      { position: "OL", highRisk: 2, moderate: 2, low: 8 },
                      { position: "DL", highRisk: 1, moderate: 2, low: 5 },
                      { position: "LB", highRisk: 2, moderate: 3, low: 4 },
                      { position: "DB", highRisk: 1, moderate: 2, low: 6 },
                    ]}
                  >
                    <XAxis dataKey="position" stroke="#a1a1aa" />
                    <YAxis stroke="#a1a1aa" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#16213e",
                        border: "1px solid rgba(255,255,255,0.1)",
                        borderRadius: "8px",
                      }}
                    />
                    <Bar dataKey="highRisk" stackId="a" fill={RISK_COLORS.high} name="High Risk" />
                    <Bar dataKey="moderate" stackId="a" fill={RISK_COLORS.moderate} name="Moderate" />
                    <Bar dataKey="low" stackId="a" fill={RISK_COLORS.low} name="Low Risk" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Fit Analyzer Tab */}
        <TabsContent value="fit-analyzer" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Selection panel */}
            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle>Analyze Fit</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm text-muted-foreground">Portal Player</label>
                  <Select value={selectedPlayer} onValueChange={setSelectedPlayer}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select player" />
                    </SelectTrigger>
                    <SelectContent>
                      {portalPlayers.map((player) => (
                        <SelectItem key={player.name} value={player.name}>
                          {player.name} ({player.position})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm text-muted-foreground">Target School</label>
                  <Select value={targetSchool} onValueChange={setTargetSchool}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select school" />
                    </SelectTrigger>
                    <SelectContent>
                      {["Alabama", "Georgia", "Ohio State", "Michigan", "Texas", "USC", "Oregon"].map((school) => (
                        <SelectItem key={school} value={school}>{school}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button className="w-full">Analyze Fit</Button>
              </CardContent>
            </Card>

            {/* Fit results */}
            <Card className="bg-card border-border/50 lg:col-span-2">
              <CardHeader>
                <CardTitle>Fit Analysis Results</CardTitle>
              </CardHeader>
              <CardContent>
                {selectedPlayer && targetSchool ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Metrics */}
                    <div className="space-y-4">
                      <div className="text-center p-6 rounded-lg bg-secondary/50">
                        <p className="text-4xl font-bold text-primary">87%</p>
                        <p className="text-muted-foreground">Overall Fit Score</p>
                        <p className="text-sm mt-2 font-medium text-green-500">Grade: A-</p>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-center p-4 rounded-lg bg-secondary/50">
                          <p className="text-xl font-bold">$425K</p>
                          <p className="text-xs text-muted-foreground">Projected NIL</p>
                        </div>
                        <div className="text-center p-4 rounded-lg bg-secondary/50">
                          <p className="text-xl font-bold">Starter</p>
                          <p className="text-xs text-muted-foreground">Projected Role</p>
                        </div>
                      </div>
                    </div>

                    {/* Radar chart */}
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart data={fitAnalysisData}>
                          <PolarGrid stroke="rgba(255,255,255,0.1)" />
                          <PolarAngleAxis
                            dataKey="category"
                            tick={{ fill: "#a1a1aa", fontSize: 10 }}
                          />
                          <Radar
                            dataKey="value"
                            stroke="#00C853"
                            fill="#00C853"
                            fillOpacity={0.3}
                          />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                ) : (
                  <div className="h-64 flex items-center justify-center text-muted-foreground">
                    <div className="text-center">
                      <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
                      <p>Select a player and target school</p>
                      <p className="text-sm">to see the fit analysis</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
