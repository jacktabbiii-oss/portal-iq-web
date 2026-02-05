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
} from "lucide-react";
import { cn } from "@/lib/utils";

// Mock player data - in production, this comes from API
const topPlayers = [
  {
    id: 1,
    name: "Arch Manning",
    position: "QB",
    school: "Texas",
    conference: "SEC",
    stars: 5,
    nilValue: 5440974,
    change: 12.5,
    tier: "mega",
    pffGrade: 92.3,
    followers: 1200000,
  },
  {
    id: 2,
    name: "Jeremiah Smith",
    position: "WR",
    school: "Ohio State",
    conference: "Big Ten",
    stars: 5,
    nilValue: 4199730,
    change: 8.2,
    tier: "mega",
    pffGrade: 94.1,
    followers: 890000,
  },
  {
    id: 3,
    name: "Sam Leavitt",
    position: "QB",
    school: "Arizona State",
    conference: "Big 12",
    stars: 4,
    nilValue: 4029364,
    change: -2.1,
    tier: "mega",
    pffGrade: 88.5,
    followers: 650000,
  },
  {
    id: 4,
    name: "Travis Hunter",
    position: "CB/WR",
    school: "Colorado",
    conference: "Big 12",
    stars: 5,
    nilValue: 3800000,
    change: 5.4,
    tier: "mega",
    pffGrade: 96.2,
    followers: 1500000,
  },
  {
    id: 5,
    name: "Dylan Raiola",
    position: "QB",
    school: "Nebraska",
    conference: "Big Ten",
    stars: 5,
    nilValue: 2900000,
    change: 15.2,
    tier: "premium",
    pffGrade: 82.1,
    followers: 420000,
  },
];

const positions = ["All", "QB", "RB", "WR", "TE", "OL", "DL", "LB", "CB", "S"];
const conferences = ["All", "SEC", "Big Ten", "Big 12", "ACC", "Pac-12", "AAC", "MWC", "Sun Belt", "C-USA"];

function formatCurrency(value: number): string {
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
  };
  return styles[tier] || "tier-entry";
}

export default function NILValuatorPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPosition, setSelectedPosition] = useState("All");
  const [selectedConference, setSelectedConference] = useState("All");
  const [activeTab, setActiveTab] = useState("search");

  // Filter players based on search and filters
  const filteredPlayers = topPlayers.filter((player) => {
    const matchesSearch =
      player.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      player.school.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesPosition =
      selectedPosition === "All" || player.position.includes(selectedPosition);
    const matchesConference =
      selectedConference === "All" || player.conference === selectedConference;
    return matchesSearch && matchesPosition && matchesConference;
  });

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
          <Button variant="outline" size="sm">
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-card border border-border">
          <TabsTrigger value="search" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            <Search className="h-4 w-4 mr-2" />
            Search Players
          </TabsTrigger>
          <TabsTrigger value="custom" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
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

                <Button className="h-11 bg-primary text-primary-foreground hover:bg-primary/90">
                  <Filter className="h-4 w-4 mr-2" />
                  Apply Filters
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Results Table */}
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
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Player</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Position</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">School</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Stars</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-right">NIL Value</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-right">Change</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Tier</TableHead>
                    <TableHead className="w-10"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredPlayers.map((player) => (
                    <TableRow
                      key={player.id}
                      className="cursor-pointer hover:bg-card border-border"
                    >
                      <TableCell className="font-semibold">{player.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-xs">
                          {player.position}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{player.school}</TableCell>
                      <TableCell>
                        <div className="flex text-yellow-500">
                          {Array.from({ length: player.stars }).map((_, i) => (
                            <Star key={i} className="h-3 w-3 fill-yellow-500" />
                          ))}
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-bold text-primary">
                        {formatCurrency(player.nilValue)}
                      </TableCell>
                      <TableCell className="text-right">
                        <span
                          className={cn(
                            "flex items-center justify-end gap-1 font-semibold text-sm",
                            player.change >= 0 ? "text-green-500" : "text-red-500"
                          )}
                        >
                          {player.change >= 0 ? (
                            <TrendingUp className="h-3 w-3" />
                          ) : (
                            <TrendingDown className="h-3 w-3" />
                          )}
                          {Math.abs(player.change)}%
                        </span>
                      </TableCell>
                      <TableCell>
                        <Badge className={cn("font-semibold text-xs uppercase", getTierBadge(player.tier))}>
                          {player.tier}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <ChevronRight className="h-4 w-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
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
                    <Input placeholder="Enter player name" className="bg-input" />
                  </div>
                  <div className="space-y-2">
                    <Label>School</Label>
                    <Input placeholder="Enter school" className="bg-input" />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Position</Label>
                    <Select>
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
                    <Select>
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
                    <Input type="number" placeholder="e.g., 50000" className="bg-input" />
                  </div>
                  <div className="space-y-2">
                    <Label>Twitter/X Followers</Label>
                    <Input type="number" placeholder="e.g., 25000" className="bg-input" />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>PFF Grade (Optional)</Label>
                  <Input type="number" placeholder="e.g., 85.5" className="bg-input" />
                </div>

                <Button className="w-full bg-primary text-primary-foreground hover:bg-primary/90 mt-4">
                  <Sparkles className="h-4 w-4 mr-2" />
                  Calculate NIL Value
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
              <p className="text-xs text-muted-foreground uppercase tracking-wider">Portal Flow</p>
              <p className="text-lg font-bold">+847 this month</p>
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
              <p className="text-lg font-bold">$892,450</p>
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
              <p className="text-lg font-bold">$15.6B</p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
