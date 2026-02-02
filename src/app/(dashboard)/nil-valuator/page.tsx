"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { StatCard } from "@/components/cards/stat-card";
import { TierBadge } from "@/components/cards/tier-badge";
import {
  formatCurrency,
  formatPercentage,
  POSITIONS,
  CLASS_YEARS,
  tierConfig,
} from "@/lib/utils";
import type { NILTier, NILValuation } from "@/types";
import { DollarSign, Search, TrendingUp, Users, BarChart3 } from "lucide-react";
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
  Legend,
} from "recharts";

// Demo valuation result
const demoValuation: NILValuation = {
  player_name: "Arch Manning",
  school: "Texas",
  position: "QB",
  predicted_value: 2500000,
  value_tier: "mega",
  tier_probabilities: {
    mega: 0.85,
    premium: 0.12,
    solid: 0.03,
    moderate: 0,
    entry: 0,
  },
  confidence: 0.88,
  value_breakdown: {
    base_value: 800000,
    social_media_premium: 650000,
    school_brand_factor: 500000,
    position_market_factor: 350000,
    draft_potential_premium: 200000,
  },
  comparable_players: [
    { name: "Quinn Ewers", school: "Texas", value: 3000000 },
    { name: "Caleb Williams", school: "USC", value: 3200000 },
    { name: "Jalen Milroe", school: "Alabama", value: 1800000 },
  ],
  percentile: 99.2,
};

// Demo leaderboard data
const leaderboardData = [
  { name: "Caleb Williams", school: "USC", position: "QB", value: 3200000, tier: "mega" as NILTier },
  { name: "Travis Hunter", school: "Colorado", position: "CB", value: 2800000, tier: "mega" as NILTier },
  { name: "Arch Manning", school: "Texas", position: "QB", value: 2500000, tier: "mega" as NILTier },
  { name: "Quinn Ewers", school: "Texas", position: "QB", value: 3000000, tier: "mega" as NILTier },
  { name: "Jalen Milroe", school: "Alabama", position: "QB", value: 1800000, tier: "mega" as NILTier },
  { name: "Nico Iamaleava", school: "Tennessee", position: "QB", value: 1500000, tier: "mega" as NILTier },
  { name: "Carson Beck", school: "Georgia", position: "QB", value: 1400000, tier: "mega" as NILTier },
  { name: "Dillon Gabriel", school: "Oregon", position: "QB", value: 1200000, tier: "mega" as NILTier },
];

const CHART_COLORS = ["#00C853", "#2196F3", "#9C27B0", "#FFD700", "#FF9800"];

export default function NILValuatorPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPlayer, setSelectedPlayer] = useState<NILValuation | null>(demoValuation);
  const [isLoading, setIsLoading] = useState(false);

  // Custom player form state
  const [customPlayer, setCustomPlayer] = useState({
    name: "",
    school: "",
    position: "QB",
    classYear: "Junior",
    stars: "5",
    overallRating: "0.90",
    instagramFollowers: "",
    twitterFollowers: "",
  });

  const handleSearch = () => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setSelectedPlayer(demoValuation);
      setIsLoading(false);
    }, 500);
  };

  const handleCustomValuation = () => {
    setIsLoading(true);
    // Simulate API call with custom data
    setTimeout(() => {
      setSelectedPlayer({
        ...demoValuation,
        player_name: customPlayer.name || "Custom Player",
        school: customPlayer.school || "Unknown School",
        position: customPlayer.position,
      });
      setIsLoading(false);
    }, 500);
  };

  // Prepare breakdown chart data
  const breakdownData = selectedPlayer?.value_breakdown
    ? Object.entries(selectedPlayer.value_breakdown).map(([key, value]) => ({
        name: key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
        value,
      }))
    : [];

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <DollarSign className="h-8 w-8 text-primary" />
          NIL Valuator
        </h1>
        <p className="text-muted-foreground mt-1">
          Get AI-powered NIL valuations for any college football player
        </p>
      </div>

      <Tabs defaultValue="lookup" className="space-y-6">
        <TabsList className="bg-secondary">
          <TabsTrigger value="lookup" className="flex items-center gap-2">
            <Search className="h-4 w-4" />
            Player Lookup
          </TabsTrigger>
          <TabsTrigger value="leaderboard" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Leaderboard
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Analytics
          </TabsTrigger>
        </TabsList>

        {/* Player Lookup Tab */}
        <TabsContent value="lookup" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Search/Input panel */}
            <Card className="lg:col-span-1 bg-card border-border/50">
              <CardHeader>
                <CardTitle>Find a Player</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Quick search */}
                <div className="space-y-2">
                  <Label>Search Existing Player</Label>
                  <div className="flex gap-2">
                    <Input
                      placeholder="Player name..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    <Button onClick={handleSearch} disabled={isLoading}>
                      <Search className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-border" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-card px-2 text-muted-foreground">
                      Or enter custom profile
                    </span>
                  </div>
                </div>

                {/* Custom player form */}
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label htmlFor="name">Name</Label>
                      <Input
                        id="name"
                        placeholder="Player name"
                        value={customPlayer.name}
                        onChange={(e) =>
                          setCustomPlayer({ ...customPlayer, name: e.target.value })
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="school">School</Label>
                      <Input
                        id="school"
                        placeholder="School"
                        value={customPlayer.school}
                        onChange={(e) =>
                          setCustomPlayer({ ...customPlayer, school: e.target.value })
                        }
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label>Position</Label>
                      <Select
                        value={customPlayer.position}
                        onValueChange={(value) =>
                          setCustomPlayer({ ...customPlayer, position: value })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {POSITIONS.map((pos) => (
                            <SelectItem key={pos} value={pos}>
                              {pos}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Class Year</Label>
                      <Select
                        value={customPlayer.classYear}
                        onValueChange={(value) =>
                          setCustomPlayer({ ...customPlayer, classYear: value })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {CLASS_YEARS.map((year) => (
                            <SelectItem key={year} value={year}>
                              {year}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-2">
                      <Label>Stars</Label>
                      <Select
                        value={customPlayer.stars}
                        onValueChange={(value) =>
                          setCustomPlayer({ ...customPlayer, stars: value })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {[5, 4, 3, 2].map((s) => (
                            <SelectItem key={s} value={String(s)}>
                              {s} Star
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label>Overall Rating</Label>
                      <Input
                        type="number"
                        step="0.01"
                        min="0.60"
                        max="1.00"
                        value={customPlayer.overallRating}
                        onChange={(e) =>
                          setCustomPlayer({ ...customPlayer, overallRating: e.target.value })
                        }
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label>Instagram Followers</Label>
                    <Input
                      type="number"
                      placeholder="e.g., 500000"
                      value={customPlayer.instagramFollowers}
                      onChange={(e) =>
                        setCustomPlayer({ ...customPlayer, instagramFollowers: e.target.value })
                      }
                    />
                  </div>
                  <Button
                    className="w-full"
                    onClick={handleCustomValuation}
                    disabled={isLoading}
                  >
                    Get Valuation
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Results panel */}
            <div className="lg:col-span-2 space-y-6">
              {selectedPlayer ? (
                <>
                  {/* Metrics row */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <StatCard
                      title="Predicted NIL Value"
                      value={formatCurrency(selectedPlayer.predicted_value, { compact: true })}
                      icon={DollarSign}
                    />
                    <Card className="bg-card border-border/50">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                          Value Tier
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <TierBadge tier={selectedPlayer.value_tier} className="text-lg px-3 py-1" />
                      </CardContent>
                    </Card>
                    <StatCard
                      title="Confidence"
                      value={formatPercentage(selectedPlayer.confidence)}
                      icon={TrendingUp}
                    />
                    <StatCard
                      title="Percentile"
                      value={`${selectedPlayer.percentile?.toFixed(1)}%`}
                      icon={Users}
                    />
                  </div>

                  {/* Player info and chart */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Value breakdown chart */}
                    <Card className="bg-card border-border/50">
                      <CardHeader>
                        <CardTitle>Value Breakdown</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="h-64">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={breakdownData}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={90}
                                paddingAngle={2}
                                dataKey="value"
                                label={({ percent }) =>
                                  `${((percent ?? 0) * 100).toFixed(0)}%`
                                }
                              >
                                {breakdownData.map((_, index) => (
                                  <Cell
                                    key={`cell-${index}`}
                                    fill={CHART_COLORS[index % CHART_COLORS.length]}
                                  />
                                ))}
                              </Pie>
                              <Tooltip
                                formatter={(value) => formatCurrency(value as number)}
                                contentStyle={{
                                  backgroundColor: "#16213e",
                                  border: "1px solid rgba(255,255,255,0.1)",
                                  borderRadius: "8px",
                                }}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                        <div className="mt-4 space-y-2">
                          {breakdownData.map((item, i) => (
                            <div
                              key={item.name}
                              className="flex items-center justify-between text-sm"
                            >
                              <div className="flex items-center gap-2">
                                <div
                                  className="w-3 h-3 rounded-full"
                                  style={{ backgroundColor: CHART_COLORS[i % CHART_COLORS.length] }}
                                />
                                <span className="text-muted-foreground">{item.name}</span>
                              </div>
                              <span className="font-medium">{formatCurrency(item.value)}</span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>

                    {/* Comparable players */}
                    <Card className="bg-card border-border/50">
                      <CardHeader>
                        <CardTitle>Comparable Players</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        {selectedPlayer.comparable_players?.map((player, i) => (
                          <div
                            key={i}
                            className="flex items-center justify-between p-3 rounded-lg bg-secondary/50"
                          >
                            <div>
                              <p className="font-medium">{player.name}</p>
                              <p className="text-sm text-muted-foreground">
                                {player.school}
                              </p>
                            </div>
                            <span className="font-semibold text-primary">
                              {formatCurrency(player.value, { compact: true })}
                            </span>
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  </div>
                </>
              ) : (
                <Card className="bg-card border-border/50 h-96 flex items-center justify-center">
                  <div className="text-center text-muted-foreground">
                    <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                    <p>Search for a player or enter a custom profile</p>
                    <p className="text-sm">to see their NIL valuation</p>
                  </div>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Leaderboard Tab */}
        <TabsContent value="leaderboard" className="space-y-6">
          <Card className="bg-card border-border/50">
            <CardHeader>
              <CardTitle>NIL Leaderboard</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {leaderboardData.map((player, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-4 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <span className="text-2xl font-bold text-muted-foreground w-8">
                        #{i + 1}
                      </span>
                      <div>
                        <p className="font-medium">{player.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {player.position} • {player.school}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <TierBadge tier={player.tier} />
                      <span className="text-xl font-bold text-primary min-w-[100px] text-right">
                        {formatCurrency(player.value, { compact: true })}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle>NIL Value by Position</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={[
                        { position: "QB", value: 1800000 },
                        { position: "WR", value: 650000 },
                        { position: "RB", value: 450000 },
                        { position: "CB", value: 550000 },
                        { position: "EDGE", value: 480000 },
                        { position: "OT", value: 320000 },
                      ]}
                      layout="vertical"
                    >
                      <XAxis
                        type="number"
                        tickFormatter={(v) => formatCurrency(v, { compact: true })}
                        stroke="#a1a1aa"
                      />
                      <YAxis type="category" dataKey="position" stroke="#a1a1aa" />
                      <Tooltip
                        formatter={(value) => formatCurrency(value as number)}
                        contentStyle={{
                          backgroundColor: "#16213e",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: "8px",
                        }}
                      />
                      <Bar dataKey="value" fill="#00C853" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle>NIL Distribution by Tier</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={[
                          { name: "Mega ($1M+)", value: 45, tier: "mega" },
                          { name: "Premium ($250K-$1M)", value: 120, tier: "premium" },
                          { name: "Solid ($50K-$250K)", value: 350, tier: "solid" },
                          { name: "Moderate ($10K-$50K)", value: 800, tier: "moderate" },
                          { name: "Entry (<$10K)", value: 2500, tier: "entry" },
                        ]}
                        cx="50%"
                        cy="50%"
                        outerRadius={100}
                        dataKey="value"
                        label={({ name }) => (name ?? "").split(" ")[0]}
                      >
                        {["mega", "premium", "solid", "moderate", "entry"].map((tier, i) => (
                          <Cell
                            key={tier}
                            fill={tierConfig[tier as NILTier].color}
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#16213e",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: "8px",
                        }}
                      />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
