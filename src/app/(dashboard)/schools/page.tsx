"use client";

import { useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { School, Search, Trophy, TrendingUp, Zap, Building2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { SCHOOL_LIST } from "@/lib/api/team";

// School tiers for display
const SCHOOL_TIERS: Record<string, { schools: string[]; color: string; bgColor: string; label: string }> = {
  elite: {
    schools: ["Alabama", "Georgia", "Ohio State", "Michigan", "Texas", "Oregon", "Penn State", "Notre Dame", "USC", "Clemson"],
    color: "text-primary",
    bgColor: "bg-primary/10 border-primary/20",
    label: "Elite",
  },
  power: {
    schools: ["LSU", "Oklahoma", "Florida", "Miami", "Tennessee", "Auburn", "Texas A&M", "Wisconsin", "UCLA", "Washington", "Utah", "Ole Miss", "Missouri", "Florida State", "Louisville", "Kentucky", "Arkansas"],
    color: "text-blue-500",
    bgColor: "bg-blue-500/10 border-blue-500/20",
    label: "Power",
  },
  rising: {
    schools: ["Colorado", "Indiana", "Illinois", "Iowa State", "Kansas State", "Arizona", "NC State", "Virginia Tech", "Baylor", "Pittsburgh", "SMU", "Syracuse", "Duke", "California", "Nebraska"],
    color: "text-green-500",
    bgColor: "bg-green-500/10 border-green-500/20",
    label: "Rising",
  },
};

function getSchoolTier(school: string): { tier: string; color: string; bgColor: string; label: string } {
  for (const [tierName, tierData] of Object.entries(SCHOOL_TIERS)) {
    if (tierData.schools.some((s) => s.toLowerCase() === school.toLowerCase())) {
      return { tier: tierName, ...tierData };
    }
  }
  return { tier: "other", color: "text-muted-foreground", bgColor: "bg-muted/10 border-border", label: "Other" };
}

const conferences: Record<string, string> = {
  all: "All Schools",
  sec: "SEC",
  bigten: "Big Ten",
  acc: "ACC",
  big12: "Big 12",
};

const conferenceSchools: Record<string, string[]> = {
  sec: ["Alabama", "Arkansas", "Auburn", "Florida", "Georgia", "Kentucky", "LSU", "Mississippi State", "Missouri", "Oklahoma", "Ole Miss", "South Carolina", "Tennessee", "Texas", "Texas A&M", "Vanderbilt"],
  bigten: ["Illinois", "Indiana", "Iowa", "Maryland", "Michigan", "Michigan State", "Minnesota", "Nebraska", "Northwestern", "Ohio State", "Oregon", "Penn State", "Purdue", "Rutgers", "UCLA", "USC", "Washington", "Wisconsin"],
  acc: ["Boston College", "California", "Clemson", "Duke", "Florida State", "Georgia Tech", "Louisville", "Miami", "NC State", "North Carolina", "Notre Dame", "Pittsburgh", "SMU", "Stanford", "Syracuse", "Virginia", "Virginia Tech", "Wake Forest"],
  big12: ["Arizona", "Arizona State", "Baylor", "BYU", "Cincinnati", "Colorado", "Houston", "Iowa State", "Kansas", "Kansas State", "Oklahoma State", "TCU", "Texas Tech", "UCF", "Utah", "West Virginia"],
};

const tierIcons = {
  elite: Trophy,
  power: TrendingUp,
  rising: Zap,
  other: Building2,
};

const tierLabels = {
  elite: "Elite Programs",
  power: "Power Programs",
  rising: "Rising Programs",
  other: "Other Programs",
};

export default function SchoolsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedConference, setSelectedConference] = useState("all");

  const filteredSchools = SCHOOL_LIST.filter((school) => {
    const matchesSearch = school.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesConference =
      selectedConference === "all" ||
      conferenceSchools[selectedConference]?.includes(school);
    return matchesSearch && matchesConference;
  });

  // Group by tier
  const groupedSchools = {
    elite: filteredSchools.filter((s) => SCHOOL_TIERS.elite.schools.includes(s)),
    power: filteredSchools.filter((s) => SCHOOL_TIERS.power.schools.includes(s)),
    rising: filteredSchools.filter((s) => SCHOOL_TIERS.rising.schools.includes(s)),
    other: filteredSchools.filter(
      (s) =>
        !SCHOOL_TIERS.elite.schools.includes(s) &&
        !SCHOOL_TIERS.power.schools.includes(s) &&
        !SCHOOL_TIERS.rising.schools.includes(s)
    ),
  };

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
            Browse {SCHOOL_LIST.length} schools and analyze their transfer portal activity
          </p>
        </div>
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
                <p className="text-2xl font-bold">{SCHOOL_TIERS.elite.schools.length}</p>
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
                <p className="text-2xl font-bold">{SCHOOL_TIERS.power.schools.length}</p>
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
                <p className="text-2xl font-bold">{SCHOOL_TIERS.rising.schools.length}</p>
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
                <p className="text-2xl font-bold">{SCHOOL_LIST.length}</p>
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

      {/* Schools Grid by Tier */}
      {(Object.entries(groupedSchools) as [keyof typeof tierLabels, string[]][]).map(
        ([tier, schools]) =>
          schools.length > 0 && (
            <div key={tier} className="space-y-4">
              <div className="flex items-center gap-3">
                {(() => {
                  const Icon = tierIcons[tier];
                  return (
                    <>
                      <div className={cn(
                        "w-8 h-8 rounded-lg flex items-center justify-center",
                        tier === "elite" && "bg-primary/20",
                        tier === "power" && "bg-blue-500/20",
                        tier === "rising" && "bg-green-500/20",
                        tier === "other" && "bg-muted/20"
                      )}>
                        <Icon className={cn(
                          "h-4 w-4",
                          tier === "elite" && "text-primary",
                          tier === "power" && "text-blue-500",
                          tier === "rising" && "text-green-500",
                          tier === "other" && "text-muted-foreground"
                        )} />
                      </div>
                      <h2 className={cn(
                        "text-lg font-bold",
                        tier === "elite" && "text-primary",
                        tier === "power" && "text-blue-500",
                        tier === "rising" && "text-green-500",
                        tier === "other" && "text-muted-foreground"
                      )}>
                        {tierLabels[tier]}
                      </h2>
                      <Badge variant="secondary" className="text-xs">
                        {schools.length}
                      </Badge>
                    </>
                  );
                })()}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {schools.map((school) => {
                  const tierInfo = getSchoolTier(school);
                  return (
                    <Link
                      key={school}
                      href={`/team-analysis?school=${encodeURIComponent(school)}`}
                    >
                      <Card className={cn(
                        "glass cursor-pointer transition-all hover:border-primary/50 hover:shadow-lg hover:-translate-y-0.5 group h-full",
                        "border",
                        tierInfo.bgColor
                      )}>
                        <CardContent className="p-4">
                          <p className="font-medium group-hover:text-primary transition-colors truncate">
                            {school}
                          </p>
                          <Badge
                            variant="outline"
                            className={cn("text-xs mt-2", tierInfo.color)}
                          >
                            {tierInfo.label}
                          </Badge>
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
