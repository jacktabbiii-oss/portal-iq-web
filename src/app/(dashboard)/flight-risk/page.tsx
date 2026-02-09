"use client";

import { useState, useCallback, useMemo } from "react";
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
import {
  AlertTriangle,
  Search,
  Shield,
  Users,
  TrendingDown,
  DollarSign,
  Loader2,
  ChevronRight,
  Target,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { SCHOOL_LIST } from "@/lib/api/team";
import {
  getTeamPortalActivity,
  getActivePortalPlayers,
  type PortalPlayer,
} from "@/lib/api/portal";
import { calculateWAR } from "@/lib/api/war";

// Position WAR weights for estimating impact of losing a player
const POSITION_WIN_IMPACT: Record<string, number> = {
  QB: 2.5,
  WR: 0.8,
  RB: 0.8,
  TE: 0.6,
  OT: 0.7,
  OG: 0.6,
  C: 0.6,
  EDGE: 1.2,
  DL: 0.9,
  DT: 0.9,
  DE: 1.0,
  LB: 0.8,
  CB: 0.9,
  S: 0.7,
  K: 0.3,
  P: 0.2,
  ATH: 0.6,
};

function getRiskLevel(
  outgoingCount: number,
  positionCount: number
): { level: string; color: string; bgColor: string } {
  const ratio = positionCount > 0 ? outgoingCount / Math.max(positionCount, 1) : 0;
  if (outgoingCount >= 3 || ratio >= 0.5)
    return { level: "Critical", color: "text-red-500", bgColor: "bg-red-500/10 border-red-500/30" };
  if (outgoingCount >= 2 || ratio >= 0.3)
    return { level: "High", color: "text-orange-500", bgColor: "bg-orange-500/10 border-orange-500/30" };
  if (outgoingCount >= 1)
    return { level: "Moderate", color: "text-yellow-500", bgColor: "bg-yellow-500/10 border-yellow-500/30" };
  return { level: "Low", color: "text-green-500", bgColor: "bg-green-500/10 border-green-500/30" };
}

function formatCurrency(value: number): string {
  if (value >= 1000000000) return `$${(value / 1000000000).toFixed(1)}B`;
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`;
  return `$${value.toLocaleString()}`;
}

export default function FlightRiskPage() {
  const [selectedSchool, setSelectedSchool] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [outgoing, setOutgoing] = useState<PortalPlayer[]>([]);
  const [incoming, setIncoming] = useState<PortalPlayer[]>([]);
  const [netTalentChange, setNetTalentChange] = useState(0);

  const filteredSchools = useMemo(
    () =>
      SCHOOL_LIST.filter((s) =>
        s.toLowerCase().includes(searchQuery.toLowerCase())
      ),
    [searchQuery]
  );

  const handleAnalyze = useCallback(async () => {
    if (!selectedSchool) return;
    setLoading(true);
    setError(null);

    try {
      const activity = await getTeamPortalActivity(selectedSchool);
      setOutgoing(activity.outgoing || []);
      setIncoming(activity.incoming || []);
      setNetTalentChange(activity.net_talent_change || 0);
    } catch (err) {
      console.error("Failed to fetch flight risk data:", err);
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [selectedSchool]);

  // Calculate position vulnerability from real outgoing data
  const positionVulnerability = useMemo(() => {
    const groups: Record<
      string,
      { players: PortalPlayer[]; totalNIL: number; totalWAR: number }
    > = {};

    for (const player of outgoing) {
      const pos = player.position || "ATH";
      if (!groups[pos]) {
        groups[pos] = { players: [], totalNIL: 0, totalWAR: 0 };
      }
      groups[pos].players.push(player);
      groups[pos].totalNIL += player.nil_valuation || player.on3_value || 0;
      const war = calculateWAR(
        player.nil_valuation || player.on3_value || 0,
        pos,
        player.stars,
        player.origin_school
      );
      groups[pos].totalWAR += war;
    }

    return Object.entries(groups)
      .map(([pos, data]) => ({
        position: pos,
        count: data.players.length,
        totalNIL: data.totalNIL,
        totalWAR: data.totalWAR,
        players: data.players,
        risk: getRiskLevel(data.players.length, data.players.length),
        winImpact: data.players.length * (POSITION_WIN_IMPACT[pos] || 0.5),
      }))
      .sort((a, b) => b.totalWAR - a.totalWAR);
  }, [outgoing]);

  // Summary stats from real data
  const summary = useMemo(() => {
    const totalWARLost = positionVulnerability.reduce(
      (sum, pv) => sum + pv.totalWAR,
      0
    );
    const totalNILAtRisk = outgoing.reduce(
      (sum, p) => sum + (p.nil_valuation || p.on3_value || 0),
      0
    );
    const totalWARGained = incoming.reduce((sum, p) => {
      const war = calculateWAR(
        p.nil_valuation || p.on3_value || 0,
        p.position,
        p.stars,
        p.origin_school
      );
      return sum + war;
    }, 0);
    const criticalPositions = positionVulnerability.filter(
      (pv) => pv.risk.level === "Critical" || pv.risk.level === "High"
    );

    return {
      playersLost: outgoing.length,
      playersGained: incoming.length,
      totalWARLost: Math.round(totalWARLost * 100) / 100,
      totalWARGained: Math.round(totalWARGained * 100) / 100,
      netWAR: Math.round((totalWARGained - totalWARLost) * 100) / 100,
      totalNILAtRisk,
      criticalPositions: criticalPositions.map((p) => p.position),
      estimatedWinsAtRisk:
        Math.round(
          positionVulnerability.reduce((sum, pv) => sum + pv.winImpact, 0) * 10
        ) / 10,
    };
  }, [outgoing, incoming, positionVulnerability]);

  const hasData = outgoing.length > 0 || incoming.length > 0;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <AlertTriangle className="h-8 w-8 text-primary" />
          Flight Risk Analysis
        </h1>
        <p className="text-muted-foreground mt-1">
          Analyze roster vulnerability from transfer portal activity using real
          portal data
        </p>
      </div>

      {/* School Selector */}
      <Card className="glass">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <label className="block text-xs text-muted-foreground uppercase tracking-wider mb-2">
                Search School
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Type to search..."
                  className="pl-10 bg-input border-border h-11"
                />
              </div>
            </div>
            <div className="flex-1">
              <label className="block text-xs text-muted-foreground uppercase tracking-wider mb-2">
                Select School
              </label>
              <Select
                value={selectedSchool}
                onValueChange={setSelectedSchool}
              >
                <SelectTrigger className="bg-input border-border h-11">
                  <SelectValue placeholder="Choose a school..." />
                </SelectTrigger>
                <SelectContent>
                  {filteredSchools.map((school) => (
                    <SelectItem key={school} value={school}>
                      {school}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button
                onClick={handleAnalyze}
                disabled={!selectedSchool || loading}
                className="bg-primary text-primary-foreground hover:bg-primary/90 h-11 px-6"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  "Analyze"
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {error && (
        <Card className="border-red-500/30 bg-red-500/5">
          <CardContent className="p-4 text-red-400">{error}</CardContent>
        </Card>
      )}

      {hasData && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card className="glass">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-red-500/20 flex items-center justify-center">
                    <TrendingDown className="h-5 w-5 text-red-500" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground uppercase">
                      Players Lost
                    </p>
                    <p className="text-2xl font-bold text-red-400">
                      {summary.playersLost}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="glass">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                    <Target className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground uppercase">
                      WAR Lost
                    </p>
                    <p className="text-2xl font-bold text-red-400">
                      -{summary.totalWARLost}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="glass">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                    <Users className="h-5 w-5 text-green-500" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground uppercase">
                      Players Added
                    </p>
                    <p className="text-2xl font-bold text-green-400">
                      +{summary.playersGained}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="glass">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                    <DollarSign className="h-5 w-5 text-blue-500" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground uppercase">
                      NIL at Risk
                    </p>
                    <p className="text-2xl font-bold">
                      {formatCurrency(summary.totalNILAtRisk)}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Net Impact Banner */}
          <Card
            className={cn(
              "glass border",
              summary.netWAR >= 0
                ? "border-green-500/30"
                : "border-red-500/30"
            )}
          >
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Shield
                    className={cn(
                      "h-6 w-6",
                      summary.netWAR >= 0
                        ? "text-green-500"
                        : "text-red-500"
                    )}
                  />
                  <div>
                    <p className="text-sm text-muted-foreground">
                      Net Portal Impact
                    </p>
                    <p
                      className={cn(
                        "text-xl font-bold",
                        summary.netWAR >= 0
                          ? "text-green-400"
                          : "text-red-400"
                      )}
                    >
                      {summary.netWAR >= 0 ? "+" : ""}
                      {summary.netWAR} WAR
                    </p>
                  </div>
                </div>
                {summary.criticalPositions.length > 0 && (
                  <div className="text-right">
                    <p className="text-xs text-muted-foreground mb-1">
                      Critical Needs
                    </p>
                    <div className="flex gap-1 flex-wrap justify-end">
                      {summary.criticalPositions.map((pos) => (
                        <Badge
                          key={pos}
                          variant="outline"
                          className="border-red-500/50 text-red-400 text-xs"
                        >
                          {pos}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Position Vulnerability */}
            <Card className="glass">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-primary" />
                  Position Vulnerability
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {positionVulnerability.length > 0 ? (
                  positionVulnerability.map((pv) => (
                    <div
                      key={pv.position}
                      className={cn(
                        "rounded-lg p-3 border",
                        pv.risk.bgColor
                      )}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-white">
                            {pv.position}
                          </span>
                          <Badge
                            variant="outline"
                            className={cn("text-xs", pv.risk.color)}
                          >
                            {pv.risk.level}
                          </Badge>
                        </div>
                        <span className="text-sm text-muted-foreground">
                          {pv.count} player{pv.count !== 1 ? "s" : ""} lost
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>
                          WAR Lost:{" "}
                          <span className="text-red-400 font-medium">
                            -{pv.totalWAR.toFixed(1)}
                          </span>
                        </span>
                        <span>
                          NIL:{" "}
                          <span className="text-white font-medium">
                            {formatCurrency(pv.totalNIL)}
                          </span>
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground text-center py-8">
                    No outgoing transfers found
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Outgoing Players */}
            <Card className="glass">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <TrendingDown className="h-5 w-5 text-red-500" />
                  Players Lost ({outgoing.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
                  {outgoing.length > 0 ? (
                    outgoing
                      .sort(
                        (a, b) =>
                          (b.nil_valuation || b.on3_value || 0) -
                          (a.nil_valuation || a.on3_value || 0)
                      )
                      .map((player, i) => {
                        const nil =
                          player.nil_valuation || player.on3_value || 0;
                        const war = calculateWAR(
                          nil,
                          player.position,
                          player.stars,
                          player.origin_school
                        );
                        return (
                          <div
                            key={`${player.player_name}-${i}`}
                            className="flex items-center justify-between p-3 rounded-lg bg-card hover:bg-card/80 transition-colors"
                          >
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center text-xs font-bold text-red-400">
                                {player.position}
                              </div>
                              <div>
                                <p className="font-medium text-sm">
                                  {player.player_name}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  {player.destination_school
                                    ? `To ${player.destination_school}`
                                    : "Uncommitted"}
                                  {player.stars
                                    ? ` · ${"★".repeat(player.stars)}`
                                    : ""}
                                </p>
                              </div>
                            </div>
                            <div className="text-right">
                              <p className="text-primary font-bold text-sm">
                                {war.toFixed(1)} WAR
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {formatCurrency(nil)}
                              </p>
                            </div>
                          </div>
                        );
                      })
                  ) : (
                    <p className="text-muted-foreground text-center py-8">
                      No outgoing transfers
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Incoming Replacements */}
          {incoming.length > 0 && (
            <Card className="glass">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <ChevronRight className="h-5 w-5 text-green-500" />
                  Incoming Replacements ({incoming.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {incoming
                    .sort(
                      (a, b) =>
                        (b.nil_valuation || b.on3_value || 0) -
                        (a.nil_valuation || a.on3_value || 0)
                    )
                    .map((player, i) => {
                      const nil =
                        player.nil_valuation || player.on3_value || 0;
                      const war = calculateWAR(
                        nil,
                        player.position,
                        player.stars,
                        player.origin_school
                      );
                      return (
                        <div
                          key={`${player.player_name}-${i}`}
                          className="flex items-center justify-between p-3 rounded-lg bg-card"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center text-xs font-bold text-green-400">
                              {player.position}
                            </div>
                            <div>
                              <p className="font-medium text-sm">
                                {player.player_name}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                From {player.origin_school}
                                {player.stars
                                  ? ` · ${"★".repeat(player.stars)}`
                                  : ""}
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-green-400 font-bold text-sm">
                              +{war.toFixed(1)} WAR
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {formatCurrency(nil)}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {!hasData && !loading && (
        <Card className="glass">
          <CardContent className="p-12 text-center">
            <AlertTriangle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">
              Select a School to Analyze
            </h3>
            <p className="text-muted-foreground">
              Choose a school above to see their roster vulnerability from
              portal activity. All data comes from real transfer portal records.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
