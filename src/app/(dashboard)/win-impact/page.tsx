"use client";

import { useState } from "react";
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
import {
  TrendingUp,
  Search,
  Calculator,
  Target,
  Trophy,
  Users,
  BarChart3,
  ArrowRight,
  Info,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

// Mock player impact data
const impactPlayers = [
  {
    id: 1,
    name: "Arch Manning",
    position: "QB",
    school: "Texas",
    war: 2.8,
    winProbAdded: 18.5,
    nilValue: 5440974,
    valuePerWin: 1942491,
    grade: "Elite",
  },
  {
    id: 2,
    name: "Travis Hunter",
    position: "CB/WR",
    school: "Colorado",
    war: 3.2,
    winProbAdded: 22.1,
    nilValue: 3800000,
    valuePerWin: 1187500,
    grade: "Elite",
  },
  {
    id: 3,
    name: "Jeremiah Smith",
    position: "WR",
    school: "Ohio State",
    war: 2.4,
    winProbAdded: 15.2,
    nilValue: 4199730,
    valuePerWin: 1749888,
    grade: "Elite",
  },
  {
    id: 4,
    name: "Dylan Raiola",
    position: "QB",
    school: "Nebraska",
    war: 1.8,
    winProbAdded: 12.4,
    nilValue: 2900000,
    valuePerWin: 1611111,
    grade: "Premium",
  },
];

const positions = ["All", "QB", "RB", "WR", "TE", "OL", "DL", "LB", "CB", "S"];

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
    Elite: "bg-primary text-primary-foreground",
    Premium: "bg-purple-500 text-white",
    Solid: "bg-blue-500 text-white",
    Average: "bg-slate-500 text-white",
  };
  return colors[grade] || "bg-slate-500 text-white";
}

export default function WinImpactPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPosition, setSelectedPosition] = useState("All");
  const [showCalculator, setShowCalculator] = useState(false);

  const filteredPlayers = impactPlayers.filter((player) => {
    const matchesSearch =
      player.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      player.school.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesPosition =
      selectedPosition === "All" || player.position.includes(selectedPosition);
    return matchesSearch && matchesPosition;
  });

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
            Quantify player value with Wins Above Replacement (WAR)
          </p>
        </div>
        <Button
          onClick={() => setShowCalculator(!showCalculator)}
          className="bg-primary text-primary-foreground hover:bg-primary/90"
        >
          <Calculator className="h-4 w-4 mr-2" />
          WAR Calculator
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                <Trophy className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Avg WAR (Top 100)</p>
                <p className="text-2xl font-bold">1.85</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                <TrendingUp className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Highest WAR</p>
                <p className="text-2xl font-bold">3.2</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <Target className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Avg $/Win</p>
                <p className="text-2xl font-bold">$1.62M</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                <Users className="h-5 w-5 text-purple-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Elite Players</p>
                <p className="text-2xl font-bold">247</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

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
                    <Input placeholder="Enter player name" className="bg-input" />
                  </div>
                  <div className="space-y-2">
                    <Label>Position</Label>
                    <Select>
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
                    <Label>PFF Grade</Label>
                    <Input type="number" placeholder="e.g., 85.5" className="bg-input" />
                  </div>
                  <div className="space-y-2">
                    <Label>Target School</Label>
                    <Input placeholder="School name" className="bg-input" />
                  </div>
                </div>
                <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90">
                  <Zap className="h-4 w-4 mr-2" />
                  Calculate Impact
                </Button>
              </div>

              {/* Result Preview */}
              <div className="flex items-center justify-center">
                <div className="text-center p-8">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
                    <Info className="h-8 w-8 text-primary" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Enter Player Details</h3>
                  <p className="text-muted-foreground text-sm">
                    Calculate projected Wins Above Replacement and dollar value per win.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search & Filter */}
      <Card className="glass">
        <CardContent className="p-6">
          <div className="flex flex-col lg:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search players..."
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
        </CardContent>
      </Card>

      {/* Impact Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filteredPlayers.map((player) => (
          <Card key={player.id} className="glass card-hover overflow-hidden">
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold">{player.name}</h3>
                  <p className="text-muted-foreground text-sm">
                    {player.position} • {player.school}
                  </p>
                </div>
                <Badge className={cn("font-semibold", getGradeColor(player.grade))}>
                  {player.grade}
                </Badge>
              </div>

              {/* WAR Gauge */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-muted-foreground">Wins Above Replacement</span>
                  <span className="text-2xl font-bold text-primary">{player.war.toFixed(1)}</span>
                </div>
                <Progress value={(player.war / 4) * 100} className="h-3" />
                <div className="flex justify-between mt-1 text-xs text-muted-foreground">
                  <span>0</span>
                  <span>4.0 (Elite)</span>
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center p-3 rounded-lg bg-card">
                  <p className="text-xs text-muted-foreground uppercase">Win Prob Added</p>
                  <p className="text-lg font-bold text-green-500">+{player.winProbAdded}%</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-card">
                  <p className="text-xs text-muted-foreground uppercase">NIL Value</p>
                  <p className="text-lg font-bold text-primary">{formatCurrency(player.nilValue)}</p>
                </div>
                <div className="text-center p-3 rounded-lg bg-card">
                  <p className="text-xs text-muted-foreground uppercase">$/Win</p>
                  <p className="text-lg font-bold">{formatCurrency(player.valuePerWin)}</p>
                </div>
              </div>

              <Button variant="outline" className="w-full border-primary text-primary hover:bg-primary hover:text-primary-foreground">
                View Full Analysis
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Info Section */}
      <Card className="glass">
        <CardContent className="p-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
              <BarChart3 className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-bold mb-2">How We Calculate Win Impact</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Our WAR (Wins Above Replacement) model uses advanced analytics including PFF grades,
                historical transfer outcomes, position value, and team context to project how many
                additional wins a player adds to their team compared to an average replacement.
                This metric helps you evaluate if a player&apos;s NIL valuation represents good ROI.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
