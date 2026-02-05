"use client";

import { useState } from "react";
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
  MapPin,
} from "lucide-react";
import { cn } from "@/lib/utils";

// Mock portal data
const portalPlayers = [
  {
    id: 1,
    name: "Marcus Johnson",
    position: "QB",
    originSchool: "USC",
    destinationSchool: "Alabama",
    stars: 4,
    status: "Committed",
    entryDate: "2026-01-15",
    nilProjection: 1200000,
  },
  {
    id: 2,
    name: "Tyler Williams",
    position: "WR",
    originSchool: "Oregon",
    destinationSchool: null,
    stars: 5,
    status: "In Portal",
    entryDate: "2026-01-28",
    nilProjection: 850000,
  },
  {
    id: 3,
    name: "David Brown",
    position: "RB",
    originSchool: "Michigan",
    destinationSchool: "Texas",
    stars: 4,
    status: "Committed",
    entryDate: "2026-01-10",
    nilProjection: 650000,
  },
  {
    id: 4,
    name: "Chris Anderson",
    position: "DL",
    originSchool: "Georgia",
    destinationSchool: null,
    stars: 4,
    status: "In Portal",
    entryDate: "2026-02-01",
    nilProjection: 720000,
  },
  {
    id: 5,
    name: "James Wilson",
    position: "LB",
    originSchool: "Ohio State",
    destinationSchool: "Miami",
    stars: 3,
    status: "Committed",
    entryDate: "2026-01-20",
    nilProjection: 450000,
  },
];

const topPortalClasses = [
  { rank: 1, school: "Indiana", score: 56, incoming: 18, outgoing: 12 },
  { rank: 2, school: "LSU", score: 51, incoming: 15, outgoing: 8 },
  { rank: 3, school: "Texas Tech", score: 50, incoming: 22, outgoing: 14 },
  { rank: 4, school: "Texas", score: 48, incoming: 12, outgoing: 6 },
  { rank: 5, school: "Alabama", score: 45, incoming: 14, outgoing: 10 },
];

const positions = ["All", "QB", "RB", "WR", "TE", "OL", "DL", "LB", "CB", "S"];
const statuses = ["All", "In Portal", "Committed", "Withdrawn"];

function formatCurrency(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}K`;
  }
  return `$${value.toLocaleString()}`;
}

function getStatusBadge(status: string) {
  const styles: Record<string, string> = {
    "In Portal": "status-active",
    "Committed": "status-committed",
    "Withdrawn": "status-withdrawn",
  };
  return styles[status] || "status-active";
}

export default function PortalIntelligencePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPosition, setSelectedPosition] = useState("All");
  const [selectedStatus, setSelectedStatus] = useState("All");

  const filteredPlayers = portalPlayers.filter((player) => {
    const matchesSearch =
      player.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      player.originSchool.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesPosition =
      selectedPosition === "All" || player.position === selectedPosition;
    const matchesStatus = selectedStatus === "All" || player.status === selectedStatus;
    return matchesSearch && matchesPosition && matchesStatus;
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
            Track 14,000+ transfer portal entries in real-time
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
                <p className="text-2xl font-bold">2,847</p>
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
                <p className="text-xs text-muted-foreground uppercase">Committed Today</p>
                <p className="text-2xl font-bold">42</p>
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
                <p className="text-xs text-muted-foreground uppercase">New Entries Today</p>
                <p className="text-2xl font-bold">+18</p>
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
                <p className="text-2xl font-bold">134</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="players" className="space-y-6">
        <TabsList className="bg-card border border-border">
          <TabsTrigger value="players" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            <Users className="h-4 w-4 mr-2" />
            Players
          </TabsTrigger>
          <TabsTrigger value="rankings" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            <School className="h-4 w-4 mr-2" />
            Team Rankings
          </TabsTrigger>
        </TabsList>

        {/* Players Tab */}
        <TabsContent value="players" className="space-y-6">
          {/* Filters */}
          <Card className="glass">
            <CardContent className="p-6">
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
                <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                  <SelectTrigger className="w-full lg:w-40 h-11">
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
                <Button className="h-11 bg-primary text-primary-foreground hover:bg-primary/90">
                  <Filter className="h-4 w-4 mr-2" />
                  Apply
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Players Table */}
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
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Player</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Position</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">From</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">To</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Stars</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">Status</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-right">NIL Projection</TableHead>
                    <TableHead className="w-10"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredPlayers.map((player) => (
                    <TableRow key={player.id} className="cursor-pointer hover:bg-card border-border">
                      <TableCell className="font-semibold">{player.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-xs">
                          {player.position}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-muted-foreground">{player.originSchool}</TableCell>
                      <TableCell className="text-primary font-medium">
                        {player.destinationSchool || "—"}
                      </TableCell>
                      <TableCell>
                        <div className="flex text-yellow-500">
                          {Array.from({ length: player.stars }).map((_, i) => (
                            <Star key={i} className="h-3 w-3 fill-yellow-500" />
                          ))}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={cn("text-xs", getStatusBadge(player.status))}>
                          {player.status}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-bold text-primary">
                        {formatCurrency(player.nilProjection)}
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

        {/* Team Rankings Tab */}
        <TabsContent value="rankings" className="space-y-6">
          <Card className="glass overflow-hidden">
            <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
              <CardTitle className="text-sm font-bold uppercase tracking-wider">
                Top Portal Classes (2026)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent border-border">
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground w-16">Rank</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">School</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-center">Incoming</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-center">Outgoing</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-center">Net</TableHead>
                    <TableHead className="text-xs uppercase tracking-wider text-muted-foreground text-right">Score</TableHead>
                    <TableHead className="w-10"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topPortalClasses.map((team) => (
                    <TableRow key={team.rank} className="cursor-pointer hover:bg-card border-border">
                      <TableCell>
                        <Badge
                          variant={team.rank <= 3 ? "default" : "secondary"}
                          className={cn(
                            "w-8 h-8 rounded-full flex items-center justify-center font-bold",
                            team.rank === 1 && "bg-primary text-primary-foreground"
                          )}
                        >
                          {team.rank}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-semibold text-lg">{team.school}</TableCell>
                      <TableCell className="text-center text-green-500 font-semibold">
                        +{team.incoming}
                      </TableCell>
                      <TableCell className="text-center text-red-500 font-semibold">
                        -{team.outgoing}
                      </TableCell>
                      <TableCell className="text-center font-bold">
                        <span className={team.incoming - team.outgoing >= 0 ? "text-green-500" : "text-red-500"}>
                          {team.incoming - team.outgoing >= 0 ? "+" : ""}{team.incoming - team.outgoing}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge variant="secondary" className="font-bold text-lg">
                          {team.score}
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
      </Tabs>
    </div>
  );
}
