"use client";

import { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  DollarSign,
  ArrowRightLeft,
  TrendingUp,
  Brain,
  Flame,
  Bell,
  Trophy,
  ArrowRight,
  Star,
  Users,
  Zap,
  RefreshCw,
  Loader2,
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { getNILLeaderboard, type NILLeaderboardPlayer } from "@/lib/api/nil";
import { getActivePortalPlayers, getPortalTeamRankings, type PortalPlayer, type TeamRanking } from "@/lib/api/portal";

// Feature cards (static content)
const features = [
  {
    title: "NIL Valuator",
    description:
      "Proprietary NIL valuations powered by our ML algorithm. Compare players, analyze value breakdowns, and track market trends instantly.",
    icon: DollarSign,
    href: "/nil-valuator",
    cta: "Predict player market value",
  },
  {
    title: "Portal Intelligence",
    description:
      "Real-time transfer portal tracking. Analyze commitments, team rankings, and find the best portal targets instantly.",
    icon: ArrowRightLeft,
    href: "/portal-intelligence",
    cta: "Transfer portal analytics",
  },
  {
    title: "Win Impact",
    description:
      "Understand how much value a player adds to their team. Win impact directly correlates to NIL valuation and transfer market value.",
    icon: TrendingUp,
    href: "/win-impact",
    cta: "Player value analytics",
  },
  {
    title: "AI Assistant",
    description:
      "Chat with AI about players, NIL values, and portal activity. Get instant insights and recommendations powered by real data.",
    icon: Brain,
    href: "/ai-assistant",
    cta: "Ask anything about the portal",
  },
];

function formatCurrency(value: number | undefined | null): string {
  if (value == null || isNaN(value)) return "$0";
  if (value >= 1000000000) {
    return `$${(value / 1000000000).toFixed(1)}B`;
  } else if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `$${Math.round(value / 1000)}K`;
  }
  return `$${value.toLocaleString()}`;
}

export default function DashboardPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    totalPlayers: 0,
    portalEntries: 0,
    nilValuations: 0,
    newToday: 0,
  });
  const [topNilPlayers, setTopNilPlayers] = useState<NILLeaderboardPlayer[]>([]);
  const [recentPortalActivity, setRecentPortalActivity] = useState<PortalPlayer[]>([]);
  const [topPortalClasses, setTopPortalClasses] = useState<TeamRanking[]>([]);

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      // Fetch all data in parallel - including server-side portal rankings
      const [nilResponse, portalResponse, rankingsResponse] = await Promise.all([
        getNILLeaderboard({ limit: 5 }).catch(() => ({ players: [], total: 0, total_count: 0 })),
        getActivePortalPlayers({ limit: 10, status: "all" }).catch(() => ({ players: [], total: 0, total_count: 0, active_in_portal: 0, committed: 0, schools_active: 0 })),
        getPortalTeamRankings(3).catch(() => ({ rankings: [], total_teams: 0 })),
      ]);

      // Set top NIL players
      setTopNilPlayers(nilResponse.players.slice(0, 3));

      // Set stats from API response (real numbers, not fabricated)
      const nilTotal = (nilResponse as { total_count?: number }).total_count || nilResponse.total || 0;
      const portalTotal = (portalResponse as { total_count?: number }).total_count || portalResponse.total || 0;

      setStats({
        totalPlayers: nilTotal,
        portalEntries: portalTotal,
        nilValuations: nilTotal,
        newToday: 0,
      });

      // Set recent portal activity (most recent committed players)
      const recentCommits = portalResponse.players
        .filter((p: PortalPlayer) => p.status === "committed" && p.destination_school)
        .slice(0, 3);
      setRecentPortalActivity(recentCommits);

      // Use server-side portal rankings (processes ALL portal entries)
      setTopPortalClasses(rankingsResponse.rankings.slice(0, 3));
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const currentDate = new Date().toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  const statsData = [
    {
      label: "Total Players",
      value: isLoading ? "..." : (stats.totalPlayers || 0).toLocaleString(),
      change: "Updated daily",
      changeType: "positive" as const,
      icon: Users,
    },
    {
      label: "Portal Entries",
      value: isLoading ? "..." : (stats.portalEntries || 0).toLocaleString(),
      change: "Current cycle",
      changeType: "neutral" as const,
      icon: ArrowRightLeft,
    },
    {
      label: "NIL Valuations",
      value: isLoading ? "..." : (stats.nilValuations || 0).toLocaleString(),
      change: "Real-time",
      changeType: "neutral" as const,
      icon: DollarSign,
    },
    {
      label: "Models Updated",
      value: currentDate,
      change: "Latest",
      changeType: "neutral" as const,
      icon: Zap,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <section className="relative py-8 text-center">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/10 to-transparent -z-10 blur-3xl opacity-30 rounded-3xl" />

        <div className="inline-flex items-center justify-center p-2 bg-card rounded-2xl mb-4 glow-gold">
          <img src="/logo.png" alt="Portal IQ" className="h-16 w-16 object-contain" />
        </div>

        <h1 className="text-5xl font-black tracking-tighter mb-2">
          PORTAL <span className="text-primary">IQ</span>
        </h1>

        <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
          The ultra-modern AI engine for elite athlete NIL valuation and transfer portal
          intelligence.
        </p>

        <Button
          variant="ghost"
          size="sm"
          onClick={fetchData}
          disabled={isLoading}
          className="mt-4"
        >
          <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
          Refresh Data
        </Button>
      </section>

      {/* Stats Grid */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statsData.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card
              key={stat.label}
              className="glass border-l-4 border-l-primary hover:-translate-y-1 transition-all duration-200"
            >
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                    {stat.label}
                  </p>
                  <Icon className="h-4 w-4 text-primary" />
                </div>
                <h3 className="text-3xl font-bold text-foreground">{stat.value}</h3>
                <div
                  className={cn(
                    "flex items-center gap-1 mt-2 text-sm font-semibold",
                    stat.changeType === "positive" && "text-green-500",
                    stat.changeType === "neutral" && "text-muted-foreground"
                  )}
                >
                  {stat.changeType === "positive" && <TrendingUp className="h-3 w-3" />}
                  {stat.changeType === "neutral" && <Zap className="h-3 w-3" />}
                  {stat.change}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </section>

      {/* Feature Cards */}
      <section className="space-y-6">
        <div className="flex items-center gap-3">
          <Zap className="h-6 w-6 text-primary" />
          <h2 className="text-2xl font-bold">Explore Our Tools</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="gold-gradient-border rounded-2xl group cursor-pointer overflow-hidden"
              >
                <Link href={feature.href}>
                  <div className="inner bg-background p-8 h-full flex flex-col justify-between transition-all group-hover:bg-card rounded-[calc(1rem-1px)]">
                    <div>
                      <div className="w-14 h-14 bg-primary/10 rounded-xl flex items-center justify-center mb-6 group-hover:bg-primary/20 transition-colors">
                        <Icon className="h-7 w-7 text-primary" />
                      </div>
                      <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                      <p className="text-muted-foreground leading-relaxed mb-6">
                        {feature.description}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 text-primary font-semibold group-hover:translate-x-2 transition-transform">
                      {feature.cta}
                      <ArrowRight className="h-4 w-4" />
                    </div>
                  </div>
                </Link>
              </div>
            );
          })}
        </div>
      </section>

      {/* Live Portal Feed */}
      <section className="space-y-6">
        <div className="flex items-center gap-3">
          <Zap className="h-6 w-6 text-primary" />
          <h2 className="text-2xl font-bold">Live Portal Feed</h2>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Top NIL Players */}
          <Card className="glass overflow-hidden">
            <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
              <CardTitle className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider">
                <Flame className="h-4 w-4 text-orange-500" />
                Top NIL Players
              </CardTitle>
            </CardHeader>
            <CardContent className="p-2">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : topNilPlayers.length > 0 ? (
                topNilPlayers.map((player, i) => (
                  <div
                    key={i}
                    className="p-4 flex justify-between items-center hover:bg-card rounded-xl transition-colors cursor-pointer"
                  >
                    <div>
                      <p className="font-bold">
                        {player.player_name}{" "}
                        <span className="text-xs font-medium text-muted-foreground">
                          ({player.position})
                        </span>
                      </p>
                      <p className="text-xs text-muted-foreground">{player.school}</p>
                    </div>
                    <span className="font-bold text-primary">
                      {formatCurrency(player.valuation)}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-center text-muted-foreground py-8 text-sm">
                  No data available
                </p>
              )}
            </CardContent>
          </Card>

          {/* Recent Portal Activity */}
          <Card className="glass overflow-hidden">
            <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
              <CardTitle className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider">
                <Bell className="h-4 w-4 text-blue-500" />
                Recent Portal Activity
              </CardTitle>
            </CardHeader>
            <CardContent className="p-2">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : recentPortalActivity.length > 0 ? (
                recentPortalActivity.map((player, i) => (
                  <div
                    key={i}
                    className="p-4 flex items-center gap-4 hover:bg-card rounded-xl transition-colors cursor-pointer"
                  >
                    <div className="flex text-yellow-500 text-xs">
                      {Array.from({ length: player.stars || 3 }).map((_, j) => (
                        <Star key={j} className="h-3 w-3 fill-yellow-500" />
                      ))}
                    </div>
                    <p className="text-sm font-medium flex-1">
                      <span className="font-bold">{player.player_name}</span>{" "}
                      <span className="text-muted-foreground">({player.position})</span> to{" "}
                      <span className="text-primary font-bold">{player.destination_school}</span>
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-center text-muted-foreground py-8 text-sm">
                  No recent activity
                </p>
              )}
            </CardContent>
          </Card>

          {/* Top Portal Classes */}
          <Card className="glass overflow-hidden">
            <CardHeader className="border-b border-border bg-primary/5 px-6 py-4">
              <CardTitle className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider">
                <Trophy className="h-4 w-4 text-yellow-500" />
                Top Portal Classes (2026)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-2">
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              ) : topPortalClasses.length > 0 ? (
                topPortalClasses.map((team, index) => (
                  <div
                    key={team.team}
                    className="p-4 flex justify-between items-center hover:bg-card rounded-xl transition-colors cursor-pointer"
                  >
                    <div>
                      <span className="font-bold">
                        {index + 1}. {team.team}
                      </span>
                      <p className="text-xs text-muted-foreground">
                        {team.breakdown.transfers_in} transfers
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="font-bold">
                        {team.grade}
                      </Badge>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-muted-foreground py-8 text-sm">
                  No data available
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Quick Actions */}
      <section className="flex flex-wrap gap-4 justify-center pt-4">
        <Button asChild className="bg-primary text-primary-foreground hover:bg-primary/90 glow-gold">
          <Link href="/nil-valuator">
            <DollarSign className="mr-2 h-4 w-4" />
            Start NIL Valuation
          </Link>
        </Button>
        <Button asChild variant="outline" className="border-primary text-primary hover:bg-primary hover:text-primary-foreground">
          <Link href="/portal-intelligence">
            <ArrowRightLeft className="mr-2 h-4 w-4" />
            Explore Portal
          </Link>
        </Button>
        <Button asChild variant="outline" className="border-primary text-primary hover:bg-primary hover:text-primary-foreground">
          <Link href="/ai-assistant">
            <Brain className="mr-2 h-4 w-4" />
            Ask AI Assistant
          </Link>
        </Button>
      </section>
    </div>
  );
}
