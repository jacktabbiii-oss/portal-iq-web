"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
  GitCompare,
  X,
  Plus,
  Star,
  Loader2,
  TrendingUp,
  TrendingDown,
  Minus,
  DollarSign,
  User,
  Trophy,
  GraduationCap,
  Percent,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  searchPlayers,
  getPlayerStats,
  getPlayerComparisons,
  formatNILValue,
  formatHeight,
  getPFFGradeColor,
  getSimilarityColor,
  type PlayerSearchResult,
  type PlayerStats,
  type PlayerComparison,
  type PlayerComparisonsResponse,
} from "@/lib/api/players";
import { PlayerRadarChart } from "@/components/charts/player-radar-chart";

interface ComparisonPlayer {
  searchResult: PlayerSearchResult;
  stats?: PlayerStats;
  loading?: boolean;
}

function StatComparison({
  label,
  value1,
  value2,
  format = "number",
  higherIsBetter = true,
}: {
  label: string;
  value1?: number | null;
  value2?: number | null;
  format?: "number" | "percent" | "currency" | "grade";
  higherIsBetter?: boolean;
}) {
  const formatValue = (val?: number | null) => {
    if (val == null) return "—";
    switch (format) {
      case "percent":
        return `${val.toFixed(1)}%`;
      case "currency":
        return formatNILValue(val);
      case "grade":
        return val.toFixed(1);
      default:
        return val.toFixed(1);
    }
  };

  const getComparisonIcon = () => {
    if (value1 == null || value2 == null) return null;
    const diff = value1 - value2;
    if (Math.abs(diff) < 0.1) return <Minus className="h-3 w-3 text-muted-foreground" />;
    if ((diff > 0 && higherIsBetter) || (diff < 0 && !higherIsBetter)) {
      return <TrendingUp className="h-3 w-3 text-green-500" />;
    }
    return <TrendingDown className="h-3 w-3 text-red-500" />;
  };

  const getBetterClass = (val1?: number | null, val2?: number | null, isFirst: boolean = true) => {
    if (val1 == null || val2 == null) return "";
    const diff = val1 - val2;
    if (Math.abs(diff) < 0.1) return "";
    const isBetter = (diff > 0 && higherIsBetter) || (diff < 0 && !higherIsBetter);
    if (isFirst) {
      return isBetter ? "text-green-500 font-bold" : "";
    } else {
      return !isBetter ? "text-green-500 font-bold" : "";
    }
  };

  return (
    <TableRow className="border-border">
      <TableCell className="text-muted-foreground text-sm">{label}</TableCell>
      <TableCell className={cn("text-right", getBetterClass(value1, value2, true))}>
        {formatValue(value1)}
      </TableCell>
      <TableCell className="text-center w-10">{getComparisonIcon()}</TableCell>
      <TableCell className={cn("text-left", getBetterClass(value1, value2, false))}>
        {formatValue(value2)}
      </TableCell>
    </TableRow>
  );
}

export default function PlayerComparisonPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<PlayerSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [players, setPlayers] = useState<ComparisonPlayer[]>([]);
  const [showSearch, setShowSearch] = useState(false);
  const [historicalComps, setHistoricalComps] = useState<PlayerComparisonsResponse | null>(null);
  const [isLoadingComps, setIsLoadingComps] = useState(false);

  // Fetch historical comparisons when player1 is loaded
  useEffect(() => {
    if (players[0]?.stats && !players[0]?.loading) {
      setIsLoadingComps(true);
      getPlayerComparisons(players[0].searchResult.name)
        .then((comps) => setHistoricalComps(comps))
        .catch((err) => {
          console.error("Failed to load comparisons:", err);
          setHistoricalComps(null);
        })
        .finally(() => setIsLoadingComps(false));
    } else {
      setHistoricalComps(null);
    }
  }, [players[0]?.stats]);

  // Search for players
  useEffect(() => {
    if (!searchQuery || searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }

    const timeoutId = setTimeout(async () => {
      setIsSearching(true);
      try {
        const response = await searchPlayers(searchQuery, "all", 10);
        setSearchResults(response.players);
      } catch (err) {
        console.error("Search failed:", err);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  // Add player to comparison
  const addPlayer = async (player: PlayerSearchResult) => {
    if (players.length >= 2) return;
    if (players.some((p) => p.searchResult.name === player.name)) return;

    const newPlayer: ComparisonPlayer = {
      searchResult: player,
      loading: true,
    };
    setPlayers((prev) => [...prev, newPlayer]);
    setSearchQuery("");
    setSearchResults([]);
    setShowSearch(false);

    try {
      const stats = await getPlayerStats(player.name);
      setPlayers((prev) =>
        prev.map((p) =>
          p.searchResult.name === player.name ? { ...p, stats, loading: false } : p
        )
      );
    } catch (err) {
      console.error("Failed to load player stats:", err);
      setPlayers((prev) =>
        prev.map((p) =>
          p.searchResult.name === player.name ? { ...p, loading: false } : p
        )
      );
    }
  };

  // Remove player from comparison
  const removePlayer = (name: string) => {
    setPlayers((prev) => prev.filter((p) => p.searchResult.name !== name));
  };

  const player1 = players[0];
  const player2 = players[1];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <GitCompare className="h-8 w-8 text-primary" />
            Player Comparison
          </h1>
          <p className="text-muted-foreground mt-1">
            Compare players side-by-side with stats, NIL values, and performance grades
          </p>
        </div>
      </div>

      {/* Player Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Player 1 Card */}
        <Card className={cn("glass", !player1 && "border-dashed")}>
          <CardContent className="p-6">
            {player1 ? (
              <div className="space-y-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-4">
                    {player1.searchResult.headshot_url ? (
                      <img
                        src={player1.searchResult.headshot_url}
                        alt={player1.searchResult.name}
                        className="w-16 h-16 rounded-lg object-cover"
                      />
                    ) : (
                      <div className="w-16 h-16 rounded-lg bg-primary/20 flex items-center justify-center">
                        <User className="h-8 w-8 text-primary" />
                      </div>
                    )}
                    <div>
                      <h3 className="text-xl font-bold">{player1.searchResult.name}</h3>
                      <p className="text-muted-foreground">
                        {player1.searchResult.position} • {player1.searchResult.school}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        {player1.searchResult.stars && (
                          <div className="flex text-yellow-500">
                            {Array.from({ length: player1.searchResult.stars }).map((_, i) => (
                              <Star key={i} className="h-3 w-3 fill-yellow-500" />
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => removePlayer(player1.searchResult.name)}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <DollarSign className="h-4 w-4 text-primary" />
                    <span className="font-bold text-primary text-lg">
                      {formatNILValue(player1.searchResult.nil_value)}
                    </span>
                  </div>
                  {player1.stats?.pff?.overall && (
                    <Badge className={getPFFGradeColor(player1.stats.pff.overall)}>
                      PIQ: {player1.stats.pff.overall.toFixed(1)}
                    </Badge>
                  )}
                </div>
                {player1.loading && (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Loading detailed stats...</span>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={() => setShowSearch(true)}
                className="w-full h-32 flex flex-col items-center justify-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <Plus className="h-8 w-8" />
                <span>Add Player 1</span>
              </button>
            )}
          </CardContent>
        </Card>

        {/* Player 2 Card */}
        <Card className={cn("glass", !player2 && "border-dashed")}>
          <CardContent className="p-6">
            {player2 ? (
              <div className="space-y-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-4">
                    {player2.searchResult.headshot_url ? (
                      <img
                        src={player2.searchResult.headshot_url}
                        alt={player2.searchResult.name}
                        className="w-16 h-16 rounded-lg object-cover"
                      />
                    ) : (
                      <div className="w-16 h-16 rounded-lg bg-primary/20 flex items-center justify-center">
                        <User className="h-8 w-8 text-primary" />
                      </div>
                    )}
                    <div>
                      <h3 className="text-xl font-bold">{player2.searchResult.name}</h3>
                      <p className="text-muted-foreground">
                        {player2.searchResult.position} • {player2.searchResult.school}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        {player2.searchResult.stars && (
                          <div className="flex text-yellow-500">
                            {Array.from({ length: player2.searchResult.stars }).map((_, i) => (
                              <Star key={i} className="h-3 w-3 fill-yellow-500" />
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => removePlayer(player2.searchResult.name)}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <DollarSign className="h-4 w-4 text-primary" />
                    <span className="font-bold text-primary text-lg">
                      {formatNILValue(player2.searchResult.nil_value)}
                    </span>
                  </div>
                  {player2.stats?.pff?.overall && (
                    <Badge className={getPFFGradeColor(player2.stats.pff.overall)}>
                      PIQ: {player2.stats.pff.overall.toFixed(1)}
                    </Badge>
                  )}
                </div>
                {player2.loading && (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm">Loading detailed stats...</span>
                  </div>
                )}
              </div>
            ) : player1 ? (
              <button
                onClick={() => setShowSearch(true)}
                className="w-full h-32 flex flex-col items-center justify-center gap-2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <Plus className="h-8 w-8" />
                <span>Add Player 2</span>
              </button>
            ) : (
              <div className="w-full h-32 flex flex-col items-center justify-center gap-2 text-muted-foreground">
                <GitCompare className="h-8 w-8" />
                <span>Select Player 1 first</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Search Modal */}
      {showSearch && (
        <Card className="glass">
          <CardHeader className="border-b border-border">
            <CardTitle className="flex items-center justify-between">
              <span>Search Players</span>
              <Button variant="ghost" size="icon" onClick={() => setShowSearch(false)}>
                <X className="h-4 w-4" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by player name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-input border-border h-11"
                autoFocus
              />
              {isSearching && (
                <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-primary" />
              )}
            </div>

            {searchResults.length > 0 && (
              <div className="space-y-2">
                {searchResults.map((player) => (
                  <button
                    key={`${player.name}-${player.school}`}
                    onClick={() => addPlayer(player)}
                    disabled={players.some((p) => p.searchResult.name === player.name)}
                    className={cn(
                      "w-full p-4 flex items-center gap-4 rounded-lg border border-border hover:bg-card transition-colors text-left",
                      players.some((p) => p.searchResult.name === player.name) && "opacity-50 cursor-not-allowed"
                    )}
                  >
                    {player.headshot_url ? (
                      <img
                        src={player.headshot_url}
                        alt={player.name}
                        className="w-10 h-10 rounded-lg object-cover"
                      />
                    ) : (
                      <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                        <User className="h-5 w-5 text-primary" />
                      </div>
                    )}
                    <div className="flex-1">
                      <p className="font-semibold">{player.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {player.position} • {player.school}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-primary">{formatNILValue(player.nil_value)}</p>
                      {player.stars && (
                        <div className="flex justify-end text-yellow-500">
                          {Array.from({ length: player.stars }).map((_, i) => (
                            <Star key={i} className="h-3 w-3 fill-yellow-500" />
                          ))}
                        </div>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            )}

            {searchQuery.length >= 2 && !isSearching && searchResults.length === 0 && (
              <p className="text-center text-muted-foreground py-8">
                No players found matching &quot;{searchQuery}&quot;
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Radar Chart Visualization */}
      {player1 && player2 && player1.stats?.pff && player2.stats?.pff && (
        <Card className="glass">
          <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
            <CardTitle className="text-sm font-bold uppercase tracking-wider flex items-center gap-2">
              <GitCompare className="h-4 w-4 text-primary" />
              Performance Grade Comparison
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <PlayerRadarChart
              player1Name={player1.searchResult.name}
              player2Name={player2.searchResult.name}
              player1Stats={player1.stats.pff}
              player2Stats={player2.stats.pff}
            />
            <div className="flex justify-center gap-8 mt-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-primary" />
                <span className="text-muted-foreground">{player1.searchResult.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500" />
                <span className="text-muted-foreground">{player2.searchResult.name}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Comparison Tables */}
      {player1 && player2 && (
        <div className="space-y-6">
          {/* Core Stats */}
          <Card className="glass overflow-hidden">
            <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
              <CardTitle className="text-sm font-bold uppercase tracking-wider">
                Core Comparison
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent border-border">
                    <TableHead className="text-muted-foreground">Stat</TableHead>
                    <TableHead className="text-right text-primary">{player1.searchResult.name}</TableHead>
                    <TableHead className="text-center w-10">vs</TableHead>
                    <TableHead className="text-left text-primary">{player2.searchResult.name}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <StatComparison
                    label="NIL Value"
                    value1={player1.searchResult.nil_value}
                    value2={player2.searchResult.nil_value}
                    format="currency"
                  />
                  <StatComparison
                    label="PIQ Overall"
                    value1={player1.stats?.pff?.overall}
                    value2={player2.stats?.pff?.overall}
                    format="grade"
                  />
                  <StatComparison
                    label="Stars"
                    value1={player1.searchResult.stars}
                    value2={player2.searchResult.stars}
                  />
                  <StatComparison
                    label="Height (in)"
                    value1={player1.stats?.height}
                    value2={player2.stats?.height}
                  />
                  <StatComparison
                    label="Weight (lbs)"
                    value1={player1.stats?.weight}
                    value2={player2.stats?.weight}
                  />
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Performance Grades */}
          {(player1.stats?.pff || player2.stats?.pff) && (
            <Card className="glass overflow-hidden">
              <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
                <CardTitle className="text-sm font-bold uppercase tracking-wider">
                  Performance Grades
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent border-border">
                      <TableHead className="text-muted-foreground">Grade</TableHead>
                      <TableHead className="text-right text-primary">{player1.searchResult.name}</TableHead>
                      <TableHead className="text-center w-10">vs</TableHead>
                      <TableHead className="text-left text-primary">{player2.searchResult.name}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <StatComparison
                      label="Overall"
                      value1={player1.stats?.pff?.overall}
                      value2={player2.stats?.pff?.overall}
                      format="grade"
                    />
                    <StatComparison
                      label="Offense"
                      value1={player1.stats?.pff?.offense}
                      value2={player2.stats?.pff?.offense}
                      format="grade"
                    />
                    <StatComparison
                      label="Defense"
                      value1={player1.stats?.pff?.defense}
                      value2={player2.stats?.pff?.defense}
                      format="grade"
                    />
                    <StatComparison
                      label="Pass Block"
                      value1={player1.stats?.pff?.pass_block}
                      value2={player2.stats?.pff?.pass_block}
                      format="grade"
                    />
                    <StatComparison
                      label="Run Block"
                      value1={player1.stats?.pff?.run_block}
                      value2={player2.stats?.pff?.run_block}
                      format="grade"
                    />
                    <StatComparison
                      label="Pass Rush"
                      value1={player1.stats?.pff?.pass_rush}
                      value2={player2.stats?.pff?.pass_rush}
                      format="grade"
                    />
                    <StatComparison
                      label="Run Defense"
                      value1={player1.stats?.pff?.run_defense}
                      value2={player2.stats?.pff?.run_defense}
                      format="grade"
                    />
                    <StatComparison
                      label="Coverage"
                      value1={player1.stats?.pff?.coverage}
                      value2={player2.stats?.pff?.coverage}
                      format="grade"
                    />
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {/* Position-Specific Stats */}
          {player1.stats?.passing && player2.stats?.passing && (
            <Card className="glass overflow-hidden">
              <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
                <CardTitle className="text-sm font-bold uppercase tracking-wider">
                  Passing Stats
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent border-border">
                      <TableHead className="text-muted-foreground">Stat</TableHead>
                      <TableHead className="text-right text-primary">{player1.searchResult.name}</TableHead>
                      <TableHead className="text-center w-10">vs</TableHead>
                      <TableHead className="text-left text-primary">{player2.searchResult.name}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <StatComparison
                      label="Passer Rating"
                      value1={player1.stats?.passing?.passer_rating}
                      value2={player2.stats?.passing?.passer_rating}
                    />
                    <StatComparison
                      label="Completion %"
                      value1={player1.stats?.passing?.completion_pct}
                      value2={player2.stats?.passing?.completion_pct}
                      format="percent"
                    />
                    <StatComparison
                      label="Big Time Throws"
                      value1={player1.stats?.passing?.big_time_throws}
                      value2={player2.stats?.passing?.big_time_throws}
                    />
                    <StatComparison
                      label="Turnover Worthy"
                      value1={player1.stats?.passing?.turnover_worthy_plays}
                      value2={player2.stats?.passing?.turnover_worthy_plays}
                      higherIsBetter={false}
                    />
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {player1.stats?.rushing && player2.stats?.rushing && (
            <Card className="glass overflow-hidden">
              <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
                <CardTitle className="text-sm font-bold uppercase tracking-wider">
                  Rushing Stats
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent border-border">
                      <TableHead className="text-muted-foreground">Stat</TableHead>
                      <TableHead className="text-right text-primary">{player1.searchResult.name}</TableHead>
                      <TableHead className="text-center w-10">vs</TableHead>
                      <TableHead className="text-left text-primary">{player2.searchResult.name}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <StatComparison
                      label="Elusive Rating"
                      value1={player1.stats?.rushing?.elusive_rating}
                      value2={player2.stats?.rushing?.elusive_rating}
                    />
                    <StatComparison
                      label="Yards After Contact"
                      value1={player1.stats?.rushing?.yards_after_contact}
                      value2={player2.stats?.rushing?.yards_after_contact}
                    />
                    <StatComparison
                      label="Breakaway %"
                      value1={player1.stats?.rushing?.breakaway_pct}
                      value2={player2.stats?.rushing?.breakaway_pct}
                      format="percent"
                    />
                    <StatComparison
                      label="YPC"
                      value1={player1.stats?.rushing?.yards_per_carry}
                      value2={player2.stats?.rushing?.yards_per_carry}
                    />
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Historical Comparisons - Show when player1 is selected */}
      {player1 && !player2 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* NFL Comparisons */}
          <Card className="glass">
            <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
              <CardTitle className="text-sm font-bold uppercase tracking-wider flex items-center gap-2">
                <Trophy className="h-4 w-4 text-primary" />
                NFL Comparisons
              </CardTitle>
              <p className="text-xs text-muted-foreground mt-1">
                Similar NFL players - predict draft value & career trajectory
              </p>
            </CardHeader>
            <CardContent className="p-4">
              {isLoadingComps ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : historicalComps?.nfl_comparisons?.length ? (
                <div className="space-y-3">
                  {historicalComps.nfl_comparisons.map((comp, idx) => (
                    <div
                      key={`nfl-${idx}`}
                      className="p-3 rounded-lg border border-border bg-card/50 hover:bg-card transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                            <Trophy className="h-5 w-5 text-primary" />
                          </div>
                          <div>
                            <p className="font-semibold">{comp.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {comp.school_or_team} • {comp.position}
                            </p>
                          </div>
                        </div>
                        <Badge className={cn("font-mono", getSimilarityColor(comp.similarity))}>
                          <Percent className="h-3 w-3 mr-1" />
                          {comp.similarity}%
                        </Badge>
                      </div>
                      {comp.nfl_outcome && (
                        <div className="mt-2 pt-2 border-t border-border/50">
                          <p className="text-xs text-muted-foreground">
                            {comp.nfl_outcome.draft_round && (
                              <span>Round {comp.nfl_outcome.draft_round}, Pick {comp.nfl_outcome.draft_pick} • </span>
                            )}
                            {comp.nfl_outcome.team}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  NFL comparison data not yet available
                </p>
              )}
            </CardContent>
          </Card>

          {/* College Comparisons */}
          <Card className="glass">
            <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
              <CardTitle className="text-sm font-bold uppercase tracking-wider flex items-center gap-2">
                <GraduationCap className="h-4 w-4 text-primary" />
                College Comparisons
              </CardTitle>
              <p className="text-xs text-muted-foreground mt-1">
                Similar current/recent college players
              </p>
            </CardHeader>
            <CardContent className="p-4">
              {isLoadingComps ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : historicalComps?.college_comparisons?.length ? (
                <div className="space-y-3">
                  {historicalComps.college_comparisons.map((comp, idx) => (
                    <div
                      key={`college-${idx}`}
                      className="p-3 rounded-lg border border-border bg-card/50 hover:bg-card transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                            <GraduationCap className="h-5 w-5 text-blue-500" />
                          </div>
                          <div>
                            <p className="font-semibold">{comp.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {comp.school_or_team} • {comp.position}
                            </p>
                          </div>
                        </div>
                        <Badge className={cn("font-mono", getSimilarityColor(comp.similarity))}>
                          <Percent className="h-3 w-3 mr-1" />
                          {comp.similarity}%
                        </Badge>
                      </div>
                      {comp.matching_stats && Object.keys(comp.matching_stats).length > 0 && (
                        <div className="mt-2 pt-2 border-t border-border/50">
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(comp.matching_stats).slice(0, 3).map(([key, val]) => (
                              <span key={key} className="text-xs bg-muted/50 px-2 py-0.5 rounded">
                                {key.replace(/_/g, " ")}: {val.comparison.toFixed(1)}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  College comparison data not yet available
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Empty State */}
      {players.length === 0 && !showSearch && (
        <Card className="glass">
          <CardContent className="p-12 text-center">
            <GitCompare className="h-16 w-16 text-primary mx-auto mb-4" />
            <h3 className="text-xl font-bold mb-2">Compare Players</h3>
            <p className="text-muted-foreground mb-6 max-w-md mx-auto">
              Select two players to compare their NIL values, performance grades, and position-specific stats side by side.
            </p>
            <Button onClick={() => setShowSearch(true)} className="bg-primary text-primary-foreground">
              <Plus className="h-4 w-4 mr-2" />
              Add First Player
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
