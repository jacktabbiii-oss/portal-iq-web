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
import { RiskBadge } from "@/components/cards/tier-badge";
import { formatCurrency, formatPercentage, getRiskLevel, POSITIONS } from "@/lib/utils";
import {
  Users,
  DollarSign,
  TrendingUp,
  Target,
  Calculator,
  ShoppingCart,
  Trophy,
  Download,
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
} from "recharts";

// Demo data
const rosterPlayers = [
  { name: "Marcus Davis", position: "QB", classYear: "Senior", rating: 0.92, nilValue: 1200000, flightRisk: 0.15, starter: true },
  { name: "Jordan Williams", position: "RB", classYear: "Junior", rating: 0.88, nilValue: 450000, flightRisk: 0.35, starter: true },
  { name: "DeShawn Thomas", position: "WR", classYear: "Senior", rating: 0.90, nilValue: 680000, flightRisk: 0.22, starter: true },
  { name: "Chris Johnson", position: "WR", classYear: "Sophomore", rating: 0.85, nilValue: 320000, flightRisk: 0.45, starter: true },
  { name: "Tyler Brown", position: "TE", classYear: "Junior", rating: 0.82, nilValue: 280000, flightRisk: 0.28, starter: true },
  { name: "Mike Wilson", position: "OT", classYear: "Senior", rating: 0.89, nilValue: 520000, flightRisk: 0.18, starter: true },
  { name: "James Lee", position: "OG", classYear: "Junior", rating: 0.84, nilValue: 350000, flightRisk: 0.32, starter: true },
  { name: "Kevin Miller", position: "EDGE", classYear: "Senior", rating: 0.91, nilValue: 750000, flightRisk: 0.12, starter: true },
  { name: "Ryan Taylor", position: "DT", classYear: "Junior", rating: 0.86, nilValue: 420000, flightRisk: 0.38, starter: true },
  { name: "David Smith", position: "CB", classYear: "Senior", rating: 0.88, nilValue: 580000, flightRisk: 0.25, starter: true },
];

const positionAllocation = [
  { position: "QB", current: 1200000, recommended: 1500000 },
  { position: "RB", current: 450000, recommended: 400000 },
  { position: "WR", current: 1000000, recommended: 1200000 },
  { position: "TE", current: 280000, recommended: 300000 },
  { position: "OL", current: 1200000, recommended: 1400000 },
  { position: "DL", current: 1170000, recommended: 1300000 },
  { position: "LB", current: 650000, recommended: 700000 },
  { position: "DB", current: 1100000, recommended: 1200000 },
];

const shoppingList = [
  { position: "QB", priority: 1, current: 2, target: 3, avgRating: 0.85, type: "Depth", estCost: 200000, fitScore: 88 },
  { position: "WR", priority: 2, current: 4, target: 6, avgRating: 0.82, type: "Starter", estCost: 450000, fitScore: 92 },
  { position: "EDGE", priority: 3, current: 3, target: 4, avgRating: 0.84, type: "Rotation", estCost: 350000, fitScore: 85 },
  { position: "CB", priority: 4, current: 4, target: 5, avgRating: 0.80, type: "Depth", estCost: 280000, fitScore: 78 },
];

const CHART_COLORS = ["#00C853", "#2196F3", "#9C27B0", "#FFD700", "#FF9800", "#F44336", "#00BCD4", "#8BC34A"];

export default function RosterBuilderPage() {
  const [selectedSchool, setSelectedSchool] = useState("Georgia");
  const [budget, setBudget] = useState("12000000");
  const [winTarget, setWinTarget] = useState("11");

  const totalNIL = rosterPlayers.reduce((sum, p) => sum + p.nilValue, 0);
  const avgRating = rosterPlayers.reduce((sum, p) => sum + p.rating, 0) / rosterPlayers.length;

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Users className="h-8 w-8 text-orange-500" />
            Roster Builder
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage your roster, optimize NIL budget, and build winning teams
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={selectedSchool} onValueChange={setSelectedSchool}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {["Georgia", "Alabama", "Ohio State", "Michigan", "Texas", "USC"].map((school) => (
                <SelectItem key={school} value={school}>{school}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Stats overview */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatCard
          title="Projected Wins"
          value="10.5"
          change="+1.2 vs last year"
          changeType="positive"
          icon={Trophy}
        />
        <StatCard
          title="Roster Size"
          value="85"
          description="12 starters"
          icon={Users}
        />
        <StatCard
          title="Total NIL Spend"
          value={formatCurrency(totalNIL, { compact: true })}
          description="Current allocation"
          icon={DollarSign}
        />
        <StatCard
          title="Budget Remaining"
          value={formatCurrency(parseInt(budget) - totalNIL, { compact: true })}
          icon={Calculator}
        />
        <StatCard
          title="Avg Rating"
          value={(avgRating * 100).toFixed(1)}
          description="Team average"
          icon={TrendingUp}
        />
      </div>

      <Tabs defaultValue="roster" className="space-y-6">
        <TabsList className="bg-secondary">
          <TabsTrigger value="roster" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Roster View
          </TabsTrigger>
          <TabsTrigger value="optimizer" className="flex items-center gap-2">
            <Calculator className="h-4 w-4" />
            Budget Optimizer
          </TabsTrigger>
          <TabsTrigger value="scenarios" className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            What-If
          </TabsTrigger>
          <TabsTrigger value="shopping" className="flex items-center gap-2">
            <ShoppingCart className="h-4 w-4" />
            Shopping List
          </TabsTrigger>
        </TabsList>

        {/* Roster View Tab */}
        <TabsContent value="roster" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Roster composition chart */}
            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle>Roster Composition</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={[
                          { name: "Offense", value: 45 },
                          { name: "Defense", value: 35 },
                          { name: "Special Teams", value: 5 },
                        ]}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={80}
                        dataKey="value"
                        label={({ name, percent }) =>
                          `${name ?? ""}: ${((percent ?? 0) * 100).toFixed(0)}%`
                        }
                      >
                        {[0, 1, 2].map((i) => (
                          <Cell key={i} fill={CHART_COLORS[i]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#16213e",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: "8px",
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Player list */}
            <Card className="lg:col-span-2 bg-card border-border/50">
              <CardHeader>
                <CardTitle>Current Roster</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-96 overflow-y-auto scrollbar-thin">
                  {rosterPlayers.map((player, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center text-orange-400 font-bold text-xs">
                          {player.position}
                        </div>
                        <div>
                          <p className="font-medium">{player.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {player.classYear} • {player.starter ? "Starter" : "Backup"}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="font-medium">{(player.rating * 100).toFixed(0)}</p>
                          <p className="text-xs text-muted-foreground">Rating</p>
                        </div>
                        <div className="text-right min-w-[80px]">
                          <p className="font-medium text-primary">
                            {formatCurrency(player.nilValue, { compact: true })}
                          </p>
                          <p className="text-xs text-muted-foreground">NIL</p>
                        </div>
                        <RiskBadge level={getRiskLevel(player.flightRisk)} />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Budget Optimizer Tab */}
        <TabsContent value="optimizer" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Optimization controls */}
            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle>Optimization Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Total NIL Budget</Label>
                  <Input
                    type="number"
                    value={budget}
                    onChange={(e) => setBudget(e.target.value)}
                    placeholder="12000000"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Win Target</Label>
                  <Select value={winTarget} onValueChange={setWinTarget}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {[8, 9, 10, 11, 12, 13].map((w) => (
                        <SelectItem key={w} value={String(w)}>{w} Wins</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2 pt-2">
                  <input type="checkbox" id="retention" className="rounded" defaultChecked />
                  <Label htmlFor="retention" className="text-sm">Prioritize retention</Label>
                </div>
                <Button className="w-full">
                  <Calculator className="h-4 w-4 mr-2" />
                  Optimize Budget
                </Button>
              </CardContent>
            </Card>

            {/* Allocation chart */}
            <Card className="lg:col-span-2 bg-card border-border/50">
              <CardHeader>
                <CardTitle>Position Budget Allocation</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={positionAllocation} layout="vertical">
                      <XAxis
                        type="number"
                        stroke="#a1a1aa"
                        tickFormatter={(v) => formatCurrency(v, { compact: true })}
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
                      <Bar dataKey="current" fill="#2196F3" name="Current" radius={[0, 4, 4, 0]} />
                      <Bar dataKey="recommended" fill="#00C853" name="Recommended" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* What-If Scenarios Tab */}
        <TabsContent value="scenarios" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Add player */}
            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span className="text-green-500">+</span> Add Player
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label>Player Name</Label>
                    <Input placeholder="Name" />
                  </div>
                  <div className="space-y-2">
                    <Label>Position</Label>
                    <Select>
                      <SelectTrigger>
                        <SelectValue placeholder="Position" />
                      </SelectTrigger>
                      <SelectContent>
                        {POSITIONS.map((pos) => (
                          <SelectItem key={pos} value={pos}>{pos}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-2">
                    <Label>Overall Rating</Label>
                    <Input type="number" step="0.01" min="0.70" max="0.98" placeholder="0.85" />
                  </div>
                  <div className="space-y-2">
                    <Label>NIL Cost</Label>
                    <Input type="number" placeholder="350000" />
                  </div>
                </div>
                <Button className="w-full" variant="outline">Add to Scenario</Button>
              </CardContent>
            </Card>

            {/* Remove player */}
            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span className="text-red-500">−</span> Remove Player
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Select Player to Remove</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Choose player" />
                    </SelectTrigger>
                    <SelectContent>
                      {rosterPlayers.map((player) => (
                        <SelectItem key={player.name} value={player.name}>
                          {player.name} ({player.position})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button className="w-full" variant="outline">Remove from Roster</Button>

                <div className="pt-4 border-t border-border">
                  <Button className="w-full">
                    <Target className="h-4 w-4 mr-2" />
                    Calculate Impact
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Scenario results */}
          <Card className="bg-card border-border/50">
            <CardHeader>
              <CardTitle>Scenario Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 rounded-lg bg-secondary/50">
                  <p className="text-3xl font-bold">10.5</p>
                  <p className="text-xs text-muted-foreground">Current Wins</p>
                </div>
                <div className="text-center p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                  <p className="text-3xl font-bold text-green-500">11.8</p>
                  <p className="text-xs text-muted-foreground">Projected Wins</p>
                </div>
                <div className="text-center p-4 rounded-lg bg-primary/10 border border-primary/20">
                  <p className="text-3xl font-bold text-primary">+1.3</p>
                  <p className="text-xs text-muted-foreground">Win Delta</p>
                </div>
                <div className="text-center p-4 rounded-lg bg-secondary/50">
                  <p className="text-3xl font-bold">$270K</p>
                  <p className="text-xs text-muted-foreground">Cost per Win</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Shopping List Tab */}
        <TabsContent value="shopping" className="space-y-6">
          <Card className="bg-card border-border/50">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Portal Shopping List</CardTitle>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">Available Budget</p>
                  <p className="text-xl font-bold text-primary">
                    {formatCurrency(parseInt(budget) - totalNIL)}
                  </p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {shoppingList.map((item, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-4 rounded-lg bg-secondary/50"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold text-sm">
                        #{item.priority}
                      </div>
                      <div>
                        <p className="font-medium">{item.position}</p>
                        <p className="text-sm text-muted-foreground">
                          Current: {item.current} • Target: {item.target}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <p className="font-medium">{(item.avgRating * 100).toFixed(0)}</p>
                        <p className="text-xs text-muted-foreground">Avg Rating</p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">{item.type}</p>
                        <p className="text-xs text-muted-foreground">Need Type</p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium text-primary">
                          {formatCurrency(item.estCost, { compact: true })}
                        </p>
                        <p className="text-xs text-muted-foreground">Est. Cost</p>
                      </div>
                      <div className="text-right min-w-[60px]">
                        <p className="text-lg font-bold text-green-500">{item.fitScore}%</p>
                        <p className="text-xs text-muted-foreground">Fit</p>
                      </div>
                      <Button size="sm" variant="outline">
                        Find Targets
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
