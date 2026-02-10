"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { School, Search, Trophy, TrendingUp, Zap, Building2, Loader2, Star } from "lucide-react";
import { cn } from "@/lib/utils";
import { SCHOOL_LIST } from "@/lib/api/team";
import { getSchoolTiers, type SchoolTierInfo, type SchoolTiersResponse } from "@/lib/api/team";

// Tier display configuration
const TIER_DISPLAY: Record<string, { color: string; bgColor: string; label: string; icon: typeof Trophy }> = {
  blue_blood: { color: "text-primary", bgColor: "bg-primary/10 border-primary/20", label: "Blue Blood", icon: Trophy },
  elite: { color: "text-primary", bgColor: "bg-primary/10 border-primary/20", label: "Elite", icon: Trophy },
  power_strong: { color: "text-blue-500", bgColor: "bg-blue-500/10 border-blue-500/20", label: "Strong P4", icon: TrendingUp },
  power_mid: { color: "text-blue-400", bgColor: "bg-blue-400/10 border-blue-400/20", label: "Mid P4", icon: TrendingUp },
  power_low: { color: "text-cyan-500", bgColor: "bg-cyan-500/10 border-cyan-500/20", label: "Lower P4", icon: TrendingUp },
  g5_strong: { color: "text-green-500", bgColor: "bg-green-500/10 border-green-500/20", label: "Strong G5", icon: Zap },
  g5_mid: { color: "text-green-400", bgColor: "bg-green-400/10 border-green-400/20", label: "Mid G5", icon: Zap },
  fcs: { color: "text-muted-foreground", bgColor: "bg-muted/10 border-border", label: "FCS", icon: Building2 },
};

// Display groups (combine similar tiers for UI)
const DISPLAY_GROUPS = [
  { key: "elite", label: "Elite Programs", tiers: ["blue_blood", "elite"], icon: Trophy, color: "text-primary", bg: "bg-primary/20" },
  { key: "power", label: "Power Programs", tiers: ["power_strong", "power_mid"], icon: TrendingUp, color: "text-blue-500", bg: "bg-blue-500/20" },
  { key: "rising", label: "Rising Programs", tiers: ["power_low", "g5_strong"], icon: Zap, color: "text-green-500", bg: "bg-green-500/20" },
  { key: "other", label: "Other Programs", tiers: ["g5_mid", "fcs"], icon: Building2, color: "text-muted-foreground", bg: "bg-muted/20" },
];

const conferences: Record<string, string> = {
  all: "All Schools",
  sec: "SEC",
  bigten: "Big Ten",
  acc: "ACC",
  big12: "Big 12",
  g5: "Group of 5",
};

const G5_CONFERENCES = new Set(["American", "Mountain West", "Sun Belt", "MAC", "Conference USA"]);

function formatRecord(wins?: number | null, losses?: number | null): string {
  if (wins == null && losses == null) return "";
  return `${wins ?? "?"}-${losses ?? "?"}`;
}

function formatSPPlus(sp?: number | null): string {
  if (sp == null) return "";
  const sign = sp >= 0 ? "+" : "";
  return `SP${sign}${sp.toFixed(1)}`;
}

export default function SchoolsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedConference, setSelectedConference] = useState("all");
  const [tiersData, setTiersData] = useState<SchoolTiersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function loadTiers() {
      try {
        const data = await getSchoolTiers();
        if (!cancelled) {
          setTiersData(data);
          setLoading(false);
        }
      } catch {
        if (!cancelled) {
          setError(true);
          setLoading(false);
        }
      }
    }
    loadTiers();
    return () => { cancelled = true; };
  }, []);

  // Build flat list of all schools from API data (or fallback to SCHOOL_LIST)
  const allSchools: SchoolTierInfo[] = tiersData?.all_schools
    ? tiersData.all_schools
    : SCHOOL_LIST.map((name) => ({
        school: name,
        tier: "g5_mid",
        multiplier: 1.0,
        label: "Unknown",
        score: 0,
      }));

  // Filter schools
  const filteredSchools = allSchools.filter((s) => {
    const matchesSearch = s.school.toLowerCase().includes(searchQuery.toLowerCase());
    if (!matchesSearch) return false;
    if (selectedConference === "all") return true;
    if (selectedConference === "g5") return G5_CONFERENCES.has(s.conference || "");
    const confMap: Record<string, string> = {
      sec: "SEC",
      bigten: "Big Ten",
      acc: "ACC",
      big12: "Big 12",
    };
    return s.conference === confMap[selectedConference];
  });

  // Group filtered schools by display group
  const groupedSchools = DISPLAY_GROUPS.map((group) => ({
    ...group,
    schools: filteredSchools
      .filter((s) => group.tiers.includes(s.tier))
      .sort((a, b) => b.score - a.score),
  }));

  // Count stats from real data
  const tierCounts = {
    elite: allSchools.filter((s) => s.tier === "blue_blood" || s.tier === "elite").length,
    power: allSchools.filter((s) => s.tier === "power_strong" || s.tier === "power_mid").length,
    rising: allSchools.filter((s) => s.tier === "power_low" || s.tier === "g5_strong").length,
    total: allSchools.length,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center space-y-4">
          <Loader2 className="h-8 w-8 text-primary animate-spin mx-auto" />
          <p className="text-muted-foreground">Loading school tiers from CFBD data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <School className="h-8 w-8 text-primary" />
            Schools
          </h1>
          <p className="text-muted-foreground mt-1">
            {tiersData
              ? `${tiersData.total_schools} FBS schools ranked by wins, SP+, talent, and conference strength`
              : `Browse ${SCHOOL_LIST.length} schools and analyze their transfer portal activity`}
          </p>
        </div>
        {error && (
          <Badge variant="outline" className="text-yellow-500 border-yellow-500/30">
            Using fallback data
          </Badge>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                <Trophy className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Elite</p>
                <p className="text-2xl font-bold">{tierCounts.elite}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                <TrendingUp className="h-5 w-5 text-blue-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Power</p>
                <p className="text-2xl font-bold">{tierCounts.power}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                <Zap className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Rising</p>
                <p className="text-2xl font-bold">{tierCounts.rising}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="glass">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-muted/20 flex items-center justify-center">
                <Building2 className="h-5 w-5 text-muted-foreground" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase">Total</p>
                <p className="text-2xl font-bold">{tierCounts.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="glass">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search schools..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 bg-input border-border h-11"
                />
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              {Object.entries(conferences).map(([key, label]) => (
                <Button
                  key={key}
                  variant={selectedConference === key ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedConference(key)}
                  className={cn(
                    "transition-all",
                    selectedConference === key && "bg-primary text-primary-foreground"
                  )}
                >
                  {label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Schools Grid by Tier Group */}
      {groupedSchools.map(
        (group) =>
          group.schools.length > 0 && (
            <div key={group.key} className="space-y-4">
              <div className="flex items-center gap-3">
                <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center", group.bg)}>
                  <group.icon className={cn("h-4 w-4", group.color)} />
                </div>
                <h2 className={cn("text-lg font-bold", group.color)}>
                  {group.label}
                </h2>
                <Badge variant="secondary" className="text-xs">
                  {group.schools.length}
                </Badge>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {group.schools.map((school) => {
                  const display = TIER_DISPLAY[school.tier] || TIER_DISPLAY.g5_mid;
                  const record = formatRecord(school.wins, school.losses);
                  const sp = formatSPPlus(school.sp_plus);
                  return (
                    <Link
                      key={school.school}
                      href={`/team-analysis?school=${encodeURIComponent(school.school)}`}
                    >
                      <Card
                        className={cn(
                          "glass cursor-pointer transition-all hover:border-primary/50 hover:shadow-lg hover:-translate-y-0.5 group h-full",
                          "border",
                          display.bgColor
                        )}
                      >
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0 flex-1">
                              <p className="font-medium group-hover:text-primary transition-colors truncate">
                                {school.school}
                              </p>
                              {school.conference && (
                                <p className="text-xs text-muted-foreground mt-0.5">{school.conference}</p>
                              )}
                            </div>
                            <Badge variant="outline" className={cn("text-xs shrink-0", display.color)}>
                              {display.label}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-3 mt-3 text-xs text-muted-foreground">
                            {record && <span className="font-mono">{record}</span>}
                            {sp && <span className="font-mono">{sp}</span>}
                            {school.multiplier > 0 && (
                              <span className={cn("font-mono", display.color)}>
                                {school.multiplier.toFixed(1)}x
                              </span>
                            )}
                          </div>
                          {school.score > 0 && (
                            <div className="mt-2">
                              <div className="h-1.5 bg-muted/30 rounded-full overflow-hidden">
                                <div
                                  className={cn(
                                    "h-full rounded-full transition-all",
                                    school.score >= 65 ? "bg-primary" :
                                    school.score >= 38 ? "bg-blue-500" :
                                    school.score >= 15 ? "bg-green-500" :
                                    "bg-muted-foreground"
                                  )}
                                  style={{ width: `${Math.min(100, school.score)}%` }}
                                />
                              </div>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    </Link>
                  );
                })}
              </div>
            </div>
          )
      )}

      {/* Empty State */}
      {filteredSchools.length === 0 && (
        <Card className="glass">
          <CardContent className="p-12 text-center">
            <School className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No schools found</h3>
            <p className="text-muted-foreground">
              Try adjusting your search or conference filter.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
