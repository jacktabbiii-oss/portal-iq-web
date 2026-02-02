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
import { GradeBadge, StockTrendBadge } from "@/components/cards/tier-badge";
import { formatCurrency, POSITIONS } from "@/lib/utils";
import {
  Trophy,
  Search,
  BarChart3,
  Users,
  TrendingUp,
  DollarSign,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  Legend,
} from "recharts";

// Demo data
const draftProspects = [
  { name: "Caleb Williams", school: "USC", position: "QB", grade: "A+", round: 1, pick: "1-3", trend: "stable" as const, rookie: 38000000, career: 250000000 },
  { name: "Marvin Harrison Jr", school: "Ohio State", position: "WR", grade: "A+", round: 1, pick: "3-6", trend: "stable" as const, rookie: 32000000, career: 180000000 },
  { name: "Quinyon Mitchell", school: "Toledo", position: "CB", grade: "A", round: 1, pick: "8-15", trend: "rising" as const, rookie: 22000000, career: 120000000 },
  { name: "Brock Bowers", school: "Georgia", position: "TE", grade: "A", round: 1, pick: "10-18", trend: "stable" as const, rookie: 18000000, career: 100000000 },
  { name: "Olumuyiwa Fashanu", school: "Penn State", position: "OT", grade: "A-", round: 1, pick: "12-20", trend: "rising" as const, rookie: 16000000, career: 90000000 },
  { name: "Dallas Turner", school: "Alabama", position: "EDGE", grade: "A", round: 1, pick: "5-12", trend: "stable" as const, rookie: 24000000, career: 140000000 },
  { name: "Rome Odunze", school: "Washington", position: "WR", grade: "A-", round: 1, pick: "8-16", trend: "falling" as const, rookie: 20000000, career: 110000000 },
  { name: "Byron Murphy II", school: "Texas", position: "DT", grade: "A-", round: 1, pick: "15-25", trend: "rising" as const, rookie: 14000000, career: 80000000 },
];

const careerEarningsProjection = [
  { year: "Rookie", value: 8500000 },
  { year: "Year 2", value: 9200000 },
  { year: "Year 3", value: 10500000 },
  { year: "Year 4", value: 12000000 },
  { year: "Year 5", value: 35000000 },
  { year: "Year 6", value: 38000000 },
  { year: "Year 7", value: 42000000 },
  { year: "Year 8", value: 45000000 },
];

export default function DraftTrackerPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [positionFilter, setPositionFilter] = useState("all");
  const [selectedProspect, setSelectedProspect] = useState(draftProspects[0]);

  const filteredProspects = draftProspects.filter((prospect) => {
    if (positionFilter !== "all" && prospect.position !== positionFilter) return false;
    if (searchQuery && !prospect.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Trophy className="h-8 w-8 text-purple-500" />
          Draft Tracker
        </h1>
        <p className="text-muted-foreground mt-1">
          NFL draft projections, career earnings estimates, and prospect analysis
        </p>
      </div>

      <Tabs defaultValue="board" className="space-y-6">
        <TabsList className="bg-secondary">
          <TabsTrigger value="board" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Draft Board
          </TabsTrigger>
          <TabsTrigger value="lookup" className="flex items-center gap-2">
            <Search className="h-4 w-4" />
            Player Lookup
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Analytics
          </TabsTrigger>
        </TabsList>

        {/* Draft Board Tab */}
        <TabsContent value="board" className="space-y-6">
          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              title="2025 Draft Prospects"
              value="342"
              description="Eligible players"
              icon={Users}
            />
            <StatCard
              title="First Round Proj."
              value="32"
              description="Top prospects"
              icon={Trophy}
            />
            <StatCard
              title="Avg. Top 10 Value"
              value="$28.5M"
              description="Rookie contract"
              icon={DollarSign}
            />
            <StatCard
              title="Most Drafted Pos."
              value="WR"
              description="45 projected picks"
              icon={TrendingUp}
            />
          </div>

          {/* Big Board */}
          <Card className="bg-card border-border/50">
            <CardHeader>
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <CardTitle>2025 Big Board</CardTitle>
                <div className="flex flex-wrap gap-3">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search prospects..."
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
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {filteredProspects.map((prospect, i) => (
                  <div
                    key={i}
                    className={`flex items-center justify-between p-4 rounded-lg transition-colors cursor-pointer ${
                      selectedProspect.name === prospect.name
                        ? "bg-primary/10 border border-primary/30"
                        : "bg-secondary/50 hover:bg-secondary"
                    }`}
                    onClick={() => setSelectedProspect(prospect)}
                  >
                    <div className="flex items-center gap-4">
                      <span className="text-2xl font-bold text-muted-foreground w-8">
                        #{i + 1}
                      </span>
                      <div className="w-10 h-10 rounded-full bg-purple-500/20 flex items-center justify-center text-purple-400 font-bold text-sm">
                        {prospect.position}
                      </div>
                      <div>
                        <p className="font-medium">{prospect.name}</p>
                        <p className="text-sm text-muted-foreground">
                          {prospect.position} • {prospect.school}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <GradeBadge grade={prospect.grade} />
                      <div className="text-right min-w-[80px]">
                        <p className="font-medium">Rd {prospect.round}</p>
                        <p className="text-xs text-muted-foreground">Pick {prospect.pick}</p>
                      </div>
                      <StockTrendBadge trend={prospect.trend} />
                      <div className="text-right min-w-[100px]">
                        <p className="font-semibold text-primary">
                          {formatCurrency(prospect.rookie, { compact: true })}
                        </p>
                        <p className="text-xs text-muted-foreground">Rookie Contract</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Player Lookup Tab */}
        <TabsContent value="lookup" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Selected prospect details */}
            <Card className="lg:col-span-2 bg-card border-border/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-2xl">{selectedProspect.name}</CardTitle>
                    <p className="text-muted-foreground">
                      {selectedProspect.position} • {selectedProspect.school}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <GradeBadge grade={selectedProspect.grade} className="text-lg px-3 py-1" />
                    <StockTrendBadge trend={selectedProspect.trend} />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Draft projection */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 rounded-lg bg-secondary/50">
                    <p className="text-3xl font-bold text-primary">{selectedProspect.round}</p>
                    <p className="text-xs text-muted-foreground">Projected Round</p>
                  </div>
                  <div className="text-center p-4 rounded-lg bg-secondary/50">
                    <p className="text-2xl font-bold">{selectedProspect.pick}</p>
                    <p className="text-xs text-muted-foreground">Pick Range</p>
                  </div>
                  <div className="text-center p-4 rounded-lg bg-secondary/50">
                    <p className="text-2xl font-bold">99%</p>
                    <p className="text-xs text-muted-foreground">Draft Probability</p>
                  </div>
                  <div className="text-center p-4 rounded-lg bg-secondary/50">
                    <p className="text-2xl font-bold text-primary">3000</p>
                    <p className="text-xs text-muted-foreground">Draft Value</p>
                  </div>
                </div>

                {/* Financial projections */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                    <p className="text-sm text-green-400">Rookie Contract</p>
                    <p className="text-2xl font-bold text-green-500">
                      {formatCurrency(selectedProspect.rookie, { compact: true })}
                    </p>
                    <p className="text-xs text-muted-foreground">4-year estimated</p>
                  </div>
                  <div className="p-4 rounded-lg bg-primary/10 border border-primary/20">
                    <p className="text-sm text-primary">Career Earnings</p>
                    <p className="text-2xl font-bold text-primary">
                      {formatCurrency(selectedProspect.career, { compact: true })}
                    </p>
                    <p className="text-xs text-muted-foreground">Lifetime projection</p>
                  </div>
                  <div className="p-4 rounded-lg bg-purple-500/10 border border-purple-500/20">
                    <p className="text-sm text-purple-400">Signing Bonus</p>
                    <p className="text-2xl font-bold text-purple-500">
                      {formatCurrency(selectedProspect.rookie * 0.6, { compact: true })}
                    </p>
                    <p className="text-xs text-muted-foreground">Guaranteed</p>
                  </div>
                </div>

                {/* Career earnings chart */}
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={careerEarningsProjection}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis dataKey="year" stroke="#a1a1aa" />
                      <YAxis
                        stroke="#a1a1aa"
                        tickFormatter={(v) => formatCurrency(v, { compact: true })}
                      />
                      <Tooltip
                        formatter={(value) => formatCurrency(value as number)}
                        contentStyle={{
                          backgroundColor: "#16213e",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: "8px",
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#00C853"
                        strokeWidth={2}
                        dot={{ fill: "#00C853" }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Strengths and comparables */}
            <div className="space-y-6">
              <Card className="bg-card border-border/50">
                <CardHeader>
                  <CardTitle>Strengths</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {["Elite arm talent", "Pocket mobility", "Deep ball accuracy", "Pre-snap reads"].map((strength, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <span className="text-green-500">✓</span>
                      {strength}
                    </div>
                  ))}
                </CardContent>
              </Card>

              <Card className="bg-card border-border/50">
                <CardHeader>
                  <CardTitle>Comparable Prospects</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {[
                    { name: "Patrick Mahomes", pick: "10th overall", year: 2017 },
                    { name: "Justin Herbert", pick: "6th overall", year: 2020 },
                    { name: "Joe Burrow", pick: "1st overall", year: 2020 },
                  ].map((comp, i) => (
                    <div key={i} className="p-3 rounded-lg bg-secondary/50">
                      <p className="font-medium">{comp.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {comp.pick} • {comp.year}
                      </p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle>Picks by Position (Projected)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={[
                        { position: "WR", picks: 45 },
                        { position: "CB", picks: 38 },
                        { position: "EDGE", picks: 35 },
                        { position: "OT", picks: 28 },
                        { position: "QB", picks: 12 },
                        { position: "DT", picks: 25 },
                        { position: "LB", picks: 22 },
                        { position: "S", picks: 18 },
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
                      <Bar dataKey="picks" fill="#9C27B0" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card border-border/50">
              <CardHeader>
                <CardTitle>Draft Value by Round</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={[
                        { round: "Rd 1", avgContract: 22000000 },
                        { round: "Rd 2", avgContract: 8500000 },
                        { round: "Rd 3", avgContract: 5200000 },
                        { round: "Rd 4", avgContract: 4100000 },
                        { round: "Rd 5", avgContract: 3800000 },
                        { round: "Rd 6", avgContract: 3500000 },
                        { round: "Rd 7", avgContract: 3200000 },
                      ]}
                    >
                      <XAxis dataKey="round" stroke="#a1a1aa" />
                      <YAxis
                        stroke="#a1a1aa"
                        tickFormatter={(v) => formatCurrency(v, { compact: true })}
                      />
                      <Tooltip
                        formatter={(value) => formatCurrency(value as number)}
                        contentStyle={{
                          backgroundColor: "#16213e",
                          border: "1px solid rgba(255,255,255,0.1)",
                          borderRadius: "8px",
                        }}
                      />
                      <Bar dataKey="avgContract" fill="#00C853" radius={[4, 4, 0, 0]} />
                    </BarChart>
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
