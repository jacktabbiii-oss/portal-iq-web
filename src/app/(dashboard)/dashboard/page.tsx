"use client";

import Link from "next/link";
import { useUser } from "@/stores/auth-store";
import { StatCard } from "@/components/cards/stat-card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  DollarSign,
  ArrowRightLeft,
  Trophy,
  Users,
  TrendingUp,
  ChevronRight,
  Clock,
} from "lucide-react";
import { formatCurrency, formatRelativeTime } from "@/lib/utils";
import { TierBadge, RiskBadge } from "@/components/cards/tier-badge";

// Demo data for the dashboard
const stats = {
  totalPlayers: 12847,
  portalEntries: 2156,
  nilValuations: 8523,
  draftProspects: 342,
};

const recentPortalEntries = [
  {
    name: "Marcus Johnson",
    position: "QB",
    fromSchool: "UCLA",
    time: "2024-01-15T10:30:00Z",
    rating: 0.89,
  },
  {
    name: "DeShawn Williams",
    position: "WR",
    fromSchool: "Florida State",
    time: "2024-01-15T09:15:00Z",
    rating: 0.85,
  },
  {
    name: "Tyler Brown",
    position: "CB",
    fromSchool: "Michigan State",
    time: "2024-01-15T08:00:00Z",
    rating: 0.82,
  },
];

const trendingPlayers = [
  { name: "Caleb Williams", school: "USC", position: "QB", nilValue: 3200000, tier: "mega" as const },
  { name: "Travis Hunter", school: "Colorado", position: "CB", nilValue: 2800000, tier: "mega" as const },
  { name: "Arch Manning", school: "Texas", position: "QB", nilValue: 2500000, tier: "mega" as const },
];

const atRiskPlayers = [
  { name: "Jordan Smith", school: "Tennessee", position: "WR", risk: "high" as const, flightRisk: 0.72 },
  { name: "Chris Davis", school: "Georgia", position: "RB", risk: "moderate" as const, flightRisk: 0.45 },
  { name: "Mike Johnson", school: "Alabama", position: "LB", risk: "low" as const, flightRisk: 0.18 },
];

const quickActions = [
  {
    title: "NIL Valuator",
    description: "Get instant valuations for any player",
    icon: DollarSign,
    href: "/nil-valuator",
    color: "bg-green-500/10 text-green-500",
  },
  {
    title: "Portal Intelligence",
    description: "Track portal movements and flight risk",
    icon: ArrowRightLeft,
    href: "/portal-intelligence",
    color: "bg-blue-500/10 text-blue-500",
  },
  {
    title: "Draft Tracker",
    description: "Project draft positions and earnings",
    icon: Trophy,
    href: "/draft-tracker",
    color: "bg-purple-500/10 text-purple-500",
  },
  {
    title: "Roster Builder",
    description: "Optimize your roster and NIL budget",
    icon: Users,
    href: "/roster-builder",
    color: "bg-orange-500/10 text-orange-500",
  },
];

export default function DashboardPage() {
  const user = useUser();

  return (
    <div className="space-y-6">
      {/* Welcome header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            Welcome back, {user?.name?.split(" ")[0] || "User"}
          </h1>
          <p className="text-muted-foreground mt-1">
            Here&apos;s what&apos;s happening in college football today
          </p>
        </div>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Clock className="h-4 w-4" />
          Last updated: {formatRelativeTime(new Date().toISOString())}
        </div>
      </div>

      {/* Stats overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Players"
          value={stats.totalPlayers.toLocaleString()}
          description="In database"
          change="+124"
          changeType="positive"
          icon={Users}
        />
        <StatCard
          title="Active Portal Entries"
          value={stats.portalEntries.toLocaleString()}
          description="This cycle"
          change="+37"
          changeType="positive"
          icon={ArrowRightLeft}
        />
        <StatCard
          title="NIL Valuations"
          value={stats.nilValuations.toLocaleString()}
          description="This month"
          change="+892"
          changeType="positive"
          icon={DollarSign}
        />
        <StatCard
          title="Draft Prospects"
          value={stats.draftProspects.toLocaleString()}
          description="2025 eligible"
          icon={Trophy}
        />
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {quickActions.map((action) => (
          <Link key={action.title} href={action.href}>
            <Card className="bg-card border-border/50 hover:border-primary/50 transition-colors cursor-pointer h-full">
              <CardContent className="pt-6">
                <div
                  className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${action.color}`}
                >
                  <action.icon className="h-6 w-6" />
                </div>
                <h3 className="font-semibold mb-1">{action.title}</h3>
                <p className="text-sm text-muted-foreground">
                  {action.description}
                </p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Three column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trending players */}
        <Card className="bg-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              Trending Players
            </CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/nil-valuator">
                View all
                <ChevronRight className="h-4 w-4 ml-1" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {trendingPlayers.map((player, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-3 rounded-lg bg-secondary/50"
              >
                <div>
                  <p className="font-medium">{player.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {player.position} • {player.school}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-semibold text-primary">
                    {formatCurrency(player.nilValue, { compact: true })}
                  </p>
                  <TierBadge tier={player.tier} className="mt-1" />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Recent portal entries */}
        <Card className="bg-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <ArrowRightLeft className="h-5 w-5 text-blue-500" />
              Recent Portal Entries
            </CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/portal-intelligence">
                View all
                <ChevronRight className="h-4 w-4 ml-1" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {recentPortalEntries.map((entry, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-3 rounded-lg bg-secondary/50"
              >
                <div>
                  <p className="font-medium">{entry.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {entry.position} • from {entry.fromSchool}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-muted-foreground">
                    {formatRelativeTime(entry.time)}
                  </p>
                  <p className="text-sm font-medium mt-1">
                    Rating: {(entry.rating * 100).toFixed(0)}
                  </p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* At-risk players */}
        <Card className="bg-card border-border/50">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-lg font-semibold flex items-center gap-2">
              <Users className="h-5 w-5 text-orange-500" />
              Flight Risk Watch
            </CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link href="/portal-intelligence">
                View all
                <ChevronRight className="h-4 w-4 ml-1" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            {atRiskPlayers.map((player, i) => (
              <div
                key={i}
                className="flex items-center justify-between p-3 rounded-lg bg-secondary/50"
              >
                <div>
                  <p className="font-medium">{player.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {player.position} • {player.school}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium mb-1">
                    {(player.flightRisk * 100).toFixed(0)}%
                  </p>
                  <RiskBadge level={player.risk} />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
