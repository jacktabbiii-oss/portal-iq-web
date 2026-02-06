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
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getActivePortalPlayers, type PortalPlayer } from "@/lib/api/portal";

const positions = ["All", "QB", "RB", "WR", "TE", "OL", "DL", "LB", "CB", "S"];
const statuses = ["All", "In Portal", "Committed", "Withdrawn"];

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

export default function PortalIntelligencePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPosition, setSelectedPosition] = useState("All");
  const [selectedStatus, setSelectedStatus] = useState("All");

  // API state
  const [players, setPlayers] = useState<PortalPlayer[]>([]);
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
      } = { limit: 200, status: apiStatus };

      if (selectedPosition !== "All") {
        params.position = selectedPosition;
      }

      const response = await getActivePortalPlayers(params);
      setPlayers(response);

      // Calculate stats
      const activeCount = response.filter((p) => p.status === "available").length;
      const committedCount = response.filter((p) => p.status === "committed").length;
      const schools = new Set(response.map((p) => p.origin_school)).size;

      setStats({
        activeInPortal: activeCount,
        committed: committedCount,
        newToday: Math.floor(activeCount * 0.02), // Approximate
        schools,
      });
    } catch (err) {
      console.error("Failed to fetch portal players:", err);
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setIsLoading(false);
    }
  }, [selectedPosition, selectedStatus]);

  // Initial load and refetch on filter changes
  useEffect(() => {
    fetchPlayers();
  }, [fetchPlayers]);

  // Client-side search filtering
  const filteredPlayers = players.filter((player) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      player.player_name.toLowerCase().includes(query) ||
      player.origin_school.toLowerCase().includes(query) ||
      (player.destination_school?.toLowerCase().includes(query) ?? false)
    );
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
                <p className="text-2xl font-bold">{players.length.toLocaleString()}</p>
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
                <Button
                  className="h-11 bg-primary text-primary-foreground hover:bg-primary/90"
                  onClick={fetchPlayers}
                  disabled={isLoading}
                >
                  <Filter className="h-4 w-4 mr-2" />
                  Apply
                </Button>
              </div>
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
                        Position
                      </TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">
                        From
                      </TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">
                        To
                      </TableHead>
                      <TableHead className="text-xs uppercase tracking-wider text-muted-foreground">
                        Stars
                      </TableHead>
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
                        <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                          No players found matching your criteria
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredPlayers.map((player) => (
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
                          <TableCell className="text-muted-foreground">
                            {player.origin_school}
                          </TableCell>
                          <TableCell className="text-primary font-medium">
                            {player.destination_school || "—"}
                          </TableCell>
                          <TableCell>
                            {player.stars ? (
                              <div className="flex text-yellow-500">
                                {Array.from({ length: player.stars }).map((_, i) => (
                                  <Star key={i} className="h-3 w-3 fill-yellow-500" />
                                ))}
                              </div>
                            ) : (
                              "—"
                            )}
                          </TableCell>
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
