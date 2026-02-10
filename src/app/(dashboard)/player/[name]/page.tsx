"use client";

import { useState, useEffect, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ArrowLeft,
  DollarSign,
  TrendingUp,
  Star,
  Ruler,
  Weight,
  Target,
  Shield,
  Zap,
  Trophy,
  Users,
  BarChart3,
  Info,
  Loader2,
  AlertCircle,
  ExternalLink,
  Heart,
  HeartOff,
  Share2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getPlayerStats,
  getPlayerComparisons,
  getDraftProjection,
  type PlayerStats,
  type PlayerComparisonsResponse,
  type DraftProjection,
  formatHeight,
  formatNILValue,
  getPFFGradeColor,
  getPFFGradeLabel,
  getDraftGradeColor,
  formatContractValue,
  getSimilarityColor,
} from "@/lib/api/players";
import { calculateDetailedWAR, analyzeTransferValue, getSchoolTier } from "@/lib/api/war";
import { useWatchlist } from "@/hooks/use-watchlist";

// Helper to format currency
function formatCurrency(value: number | undefined | null): string {
  if (value == null || isNaN(value)) return "$0";
  if (value >= 1000000000) {
    return `$${(value / 1000000000).toFixed(1)}B`;
  } else if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}K`;
  }
  return `$${value.toLocaleString()}`;
}

function getTierBadge(tier: string) {
  const styles: Record<string, string> = {
    mega: "bg-gradient-to-r from-yellow-500 to-amber-500 text-black",
    premium: "bg-gradient-to-r from-purple-500 to-pink-500 text-white",
    solid: "bg-gradient-to-r from-blue-500 to-cyan-500 text-white",
    moderate: "bg-gradient-to-r from-green-500 to-emerald-500 text-white",
    entry: "bg-gray-500 text-white",
  };
  return styles[tier?.toLowerCase()] || "bg-gray-500 text-white";
}

// Valuation factor explanations
const VALUATION_FACTORS = {
  position_base: {
    label: "Position Base Value",
    description: "Starting value based on position market demand. QBs command highest premiums.",
    icon: Target,
  },
  school_multiplier: {
    label: "School Brand Multiplier",
    description: "Boost from school's NIL market size, fan engagement, and media exposure.",
    icon: Trophy,
  },
  performance_multiplier: {
    label: "Performance Multiplier",
    description: "Based on performance grades and on-field production metrics.",
    icon: TrendingUp,
  },
  social_value: {
    label: "Social Media Value",
    description: "Value from social media following and engagement potential.",
    icon: Users,
  },
  starter_bonus: {
    label: "Starter Premium",
    description: "Additional value for projected starters with high playing time.",
    icon: Star,
  },
  potential_value: {
    label: "Potential Premium",
    description: "Extra value for high-ceiling recruits and breakout candidates.",
    icon: Zap,
  },
};

export default function PlayerDetailPage() {
  const params = useParams();
  const router = useRouter();
  const playerName = decodeURIComponent(params.name as string);

  // State
  const [playerStats, setPlayerStats] = useState<PlayerStats | null>(null);
  const [comparisons, setComparisons] = useState<PlayerComparisonsResponse | null>(null);
  const [draftProjection, setDraftProjection] = useState<DraftProjection | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("overview");

  // Watchlist
  const { isInWatchlist, toggleWatchlist } = useWatchlist();

  // Fetch player data
  useEffect(() => {
    async function fetchData() {
      setIsLoading(true);
      setError(null);

      try {
        // Fetch all data in parallel
        const [statsResult, comparisonsResult, draftResult] = await Promise.allSettled([
          getPlayerStats(playerName),
          getPlayerComparisons(playerName),
          getDraftProjection(playerName),
        ]);

        if (statsResult.status === "fulfilled") {
          setPlayerStats(statsResult.value);
        } else {
          setError("Player not found");
          return;
        }

        if (comparisonsResult.status === "fulfilled") {
          setComparisons(comparisonsResult.value);
        }

        if (draftResult.status === "fulfilled") {
          setDraftProjection(draftResult.value);
        }
      } catch (err) {
        console.error("Failed to fetch player data:", err);
        setError(err instanceof Error ? err.message : "Failed to load player data");
      } finally {
        setIsLoading(false);
      }
    }

    if (playerName) {
      fetchData();
    }
  }, [playerName]);

  // Calculate WAR
  const playerWAR = useMemo(() => {
    if (!playerStats) return null;

    const warResult = calculateDetailedWAR({
      position: playerStats.position,
      stars: playerStats.stars,
      nil_value: playerStats.nil_value,
      destination_school: playerStats.school,
      is_predicted_nil: true,
    });

    const transferValue = analyzeTransferValue(
      warResult.war,
      playerStats.nil_value || 0,
      playerStats.position
    );

    return {
      ...warResult,
      winProbAdded: warResult.war * 7,
      transferValue,
    };
  }, [playerStats]);

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto" />
          <p className="text-muted-foreground">Loading player data...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !playerStats) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Card className="glass max-w-md">
          <CardContent className="p-8 text-center">
            <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">Player Not Found</h2>
            <p className="text-muted-foreground mb-4">
              {error || `Could not find data for "${playerName}"`}
            </p>
            <Button onClick={() => router.back()}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const valuation = playerStats.valuation;

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Button variant="ghost" size="sm" onClick={() => router.back()}>
        <ArrowLeft className="h-4 w-4 mr-2" />
        Back
      </Button>

      {/* Player Header */}
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Player Info Card */}
        <Card className="glass flex-1">
          <CardContent className="p-6">
            <div className="flex items-start gap-6">
              {/* Photo */}
              {playerStats.headshot_url ? (
                <Image
                  src={playerStats.headshot_url}
                  alt={playerStats.name}
                  width={120}
                  height={120}
                  className="rounded-xl object-cover border-4 border-primary/20"
                  unoptimized
                />
              ) : (
                <div className="w-[120px] h-[120px] rounded-xl bg-primary/20 flex items-center justify-center border-4 border-primary/20">
                  <span className="text-3xl font-bold text-primary">
                    {playerStats.name?.split(" ").map(n => n[0]).join("").slice(0, 2)}
                  </span>
                </div>
              )}

              {/* Info */}
              <div className="flex-1">
                <div className="flex items-start justify-between">
                  <div>
                    <h1 className="text-3xl font-bold">{playerStats.name}</h1>
                    <div className="flex items-center gap-3 mt-2">
                      <Badge variant="outline" className="font-mono text-base px-3 py-1">
                        {playerStats.position}
                      </Badge>
                      <span className="text-lg text-muted-foreground">{playerStats.school}</span>
                    </div>
                    {playerStats.stars && (
                      <div className="flex mt-2 text-yellow-500">
                        {Array.from({ length: Math.min(playerStats.stars, 5) }).map((_, i) => (
                          <Star key={i} className="h-5 w-5 fill-yellow-500" />
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() =>
                        toggleWatchlist({
                          id: playerStats.name,
                          player_name: playerStats.name,
                          position: playerStats.position,
                          school: playerStats.school,
                          nil_valuation: playerStats.nil_value || 0,
                          stars: playerStats.stars,
                          headshot_url: playerStats.headshot_url,
                        })
                      }
                    >
                      {isInWatchlist(playerStats.name) ? (
                        <Heart className="h-4 w-4 fill-red-500 text-red-500" />
                      ) : (
                        <Heart className="h-4 w-4" />
                      )}
                    </Button>
                    <Button variant="outline" size="icon">
                      <Share2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                {/* Measurables */}
                {(playerStats.height || playerStats.weight) && (
                  <div className="flex gap-6 mt-4">
                    {playerStats.height && (
                      <div className="flex items-center gap-2">
                        <Ruler className="h-4 w-4 text-muted-foreground" />
                        <span className="font-semibold">{formatHeight(playerStats.height)}</span>
                      </div>
                    )}
                    {playerStats.weight && (
                      <div className="flex items-center gap-2">
                        <Weight className="h-4 w-4 text-muted-foreground" />
                        <span className="font-semibold">{playerStats.weight} lbs</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* NIL Valuation Card */}
        <Card className="glass lg:w-96">
          <CardContent className="p-6">
            <div className="text-center">
              <p className="text-sm text-muted-foreground uppercase tracking-wider mb-2">
                Portal IQ Valuation
              </p>
              <p className="text-5xl font-bold text-primary mb-3">
                {formatCurrency(valuation?.portal_iq_value || playerStats.nil_value)}
              </p>
              <Badge className={cn("text-sm px-4 py-1", getTierBadge(valuation?.portal_iq_tier || playerStats.nil_tier || ""))}>
                {valuation?.portal_iq_tier || playerStats.nil_tier || "EMERGING"} TIER
              </Badge>

              {/* On3 comparison if available */}
              {valuation?.has_on3_data && valuation.on3_value && (
                <div className="mt-4 pt-4 border-t border-border">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider mb-1">
                    On3 Market Reference
                  </p>
                  <p className="text-2xl font-bold text-blue-400">
                    {formatCurrency(valuation.on3_value)}
                  </p>

                  {/* Market comparison assessment */}
                  {valuation.market_comparison && (
                    <div className="mt-3">
                      <Badge
                        className={cn(
                          "text-xs px-3 py-1",
                          valuation.market_comparison.assessment === "undervalued"
                            ? "bg-green-500/20 text-green-400 border border-green-500/30"
                            : valuation.market_comparison.assessment === "overvalued"
                              ? "bg-red-500/20 text-red-400 border border-red-500/30"
                              : "bg-gray-500/20 text-gray-400 border border-gray-500/30"
                        )}
                      >
                        {valuation.market_comparison.assessment === "undervalued"
                          ? `+${valuation.market_comparison.difference_pct}% Undervalued`
                          : valuation.market_comparison.assessment === "overvalued"
                            ? `${valuation.market_comparison.difference_pct}% Overvalued`
                            : "Fair Value"}
                      </Badge>
                    </div>
                  )}
                </div>
              )}

              {valuation?.confidence && (
                <p className="text-sm text-muted-foreground mt-3">
                  Confidence: <span className="text-foreground font-medium">{valuation.confidence}</span>
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs for Different Sections */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-card border border-border">
          <TabsTrigger value="overview">
            <BarChart3 className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="valuation">
            <DollarSign className="h-4 w-4 mr-2" />
            Valuation
          </TabsTrigger>
          <TabsTrigger value="stats">
            <TrendingUp className="h-4 w-4 mr-2" />
            Stats
          </TabsTrigger>
          <TabsTrigger value="comparisons">
            <Users className="h-4 w-4 mr-2" />
            Comparisons
          </TabsTrigger>
          <TabsTrigger value="draft">
            <Trophy className="h-4 w-4 mr-2" />
            Draft
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Performance Grades Summary */}
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-primary" />
                  Performance Grades
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {playerStats.pff?.overall ? (
                  <>
                    <div className="text-center mb-6">
                      <div className="inline-flex items-center justify-center w-24 h-24 rounded-full border-4 border-primary bg-primary/10">
                        <span className={cn("text-3xl font-bold", getPFFGradeColor(playerStats.pff.overall))}>
                          {playerStats.pff.overall.toFixed(1)}
                        </span>
                      </div>
                      <p className="text-sm text-muted-foreground mt-2">
                        {getPFFGradeLabel(playerStats.pff.overall)}
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      {playerStats.pff.offense && (
                        <div className="p-3 bg-card rounded-lg">
                          <p className="text-xs text-muted-foreground">Offense</p>
                          <p className={cn("text-xl font-bold", getPFFGradeColor(playerStats.pff.offense))}>
                            {playerStats.pff.offense.toFixed(1)}
                          </p>
                        </div>
                      )}
                      {playerStats.pff.defense && (
                        <div className="p-3 bg-card rounded-lg">
                          <p className="text-xs text-muted-foreground">Defense</p>
                          <p className={cn("text-xl font-bold", getPFFGradeColor(playerStats.pff.defense))}>
                            {playerStats.pff.defense.toFixed(1)}
                          </p>
                        </div>
                      )}
                      {playerStats.pff.passing && (
                        <div className="p-3 bg-card rounded-lg">
                          <p className="text-xs text-muted-foreground">Passing</p>
                          <p className={cn("text-xl font-bold", getPFFGradeColor(playerStats.pff.passing))}>
                            {playerStats.pff.passing.toFixed(1)}
                          </p>
                        </div>
                      )}
                      {playerStats.pff.rushing && (
                        <div className="p-3 bg-card rounded-lg">
                          <p className="text-xs text-muted-foreground">Rushing</p>
                          <p className={cn("text-xl font-bold", getPFFGradeColor(playerStats.pff.rushing))}>
                            {playerStats.pff.rushing.toFixed(1)}
                          </p>
                        </div>
                      )}
                      {playerStats.pff.receiving && (
                        <div className="p-3 bg-card rounded-lg">
                          <p className="text-xs text-muted-foreground">Receiving</p>
                          <p className={cn("text-xl font-bold", getPFFGradeColor(playerStats.pff.receiving))}>
                            {playerStats.pff.receiving.toFixed(1)}
                          </p>
                        </div>
                      )}
                      {playerStats.pff.coverage && (
                        <div className="p-3 bg-card rounded-lg">
                          <p className="text-xs text-muted-foreground">Coverage</p>
                          <p className={cn("text-xl font-bold", getPFFGradeColor(playerStats.pff.coverage))}>
                            {playerStats.pff.coverage.toFixed(1)}
                          </p>
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Shield className="h-12 w-12 mx-auto mb-3 opacity-30" />
                    <p>No performance grades available</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Win Impact Summary */}
            {playerWAR && (
              <Card className="glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-primary" />
                    Win Impact (WAR)
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-center mb-6">
                    <div className="inline-flex items-center justify-center w-24 h-24 rounded-full border-4 border-green-500 bg-green-500/10">
                      <span className="text-3xl font-bold text-green-500">
                        {playerWAR.war.toFixed(2)}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-2">
                      Wins Above Replacement
                    </p>
                  </div>

                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Win Probability Added</span>
                      <span className="font-semibold text-green-500">+{playerWAR.winProbAdded.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Value Rating</span>
                      <Badge variant="outline">{playerWAR.transferValue.value_rating}</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">Cost per WAR</span>
                      <span className="font-semibold">{formatCurrency(playerWAR.transferValue.cost_per_war)}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Quick Valuation Reasoning */}
          {valuation?.reasoning && valuation.reasoning.length > 0 && (
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Info className="h-5 w-5 text-primary" />
                  Why This Valuation?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {valuation.reasoning.map((reason, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <span className="text-primary font-bold">•</span>
                      <span className="text-muted-foreground">{reason}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Valuation Breakdown Tab */}
        <TabsContent value="valuation" className="space-y-6">
          <Card className="glass">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-primary" />
                NIL Valuation Breakdown
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {valuation?.breakdown ? (
                <>
                  {/* Visual Breakdown */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(valuation.breakdown).map(([key, value]) => {
                      const factor = VALUATION_FACTORS[key as keyof typeof VALUATION_FACTORS];
                      if (!factor || !value) return null;
                      const Icon = factor.icon;
                      const isMultiplier = key.includes("multiplier") || key.includes("bonus");

                      return (
                        <Card key={key} className="bg-card/50">
                          <CardContent className="p-4">
                            <div className="flex items-start gap-3">
                              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                                <Icon className="h-5 w-5 text-primary" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="font-semibold text-sm">{factor.label}</p>
                                <p className="text-2xl font-bold text-primary">
                                  {isMultiplier ? `${value}x` : formatCurrency(value as number)}
                                </p>
                                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                  {factor.description}
                                </p>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>

                  {/* Formula Explanation */}
                  <div className="p-4 bg-card/50 rounded-lg border border-border">
                    <p className="text-sm font-semibold mb-2">How We Calculate:</p>
                    <p className="text-sm text-muted-foreground">
                      <span className="font-mono text-primary">Final Value</span> = Position Base ×
                      School Multiplier × Performance Multiplier × Starter Bonus + Social Value + Potential Premium
                    </p>
                  </div>
                </>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <DollarSign className="h-12 w-12 mx-auto mb-3 opacity-30" />
                  <p>Detailed breakdown not available</p>
                  <p className="text-sm mt-2">
                    Valuation: <span className="font-bold text-primary">{formatCurrency(playerStats.nil_value)}</span>
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Valuation Reasoning */}
          {valuation?.reasoning && valuation.reasoning.length > 0 && (
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Info className="h-5 w-5 text-primary" />
                  Valuation Analysis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {valuation.reasoning.map((reason, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-card/50 rounded-lg">
                      <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                        <span className="text-xs font-bold text-primary">{i + 1}</span>
                      </div>
                      <p className="text-sm">{reason}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Stats Tab */}
        <TabsContent value="stats" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Player Statistics - Always show if available */}
            {playerStats.pff?.overall && (
              <Card className="glass col-span-full">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-primary" />
                    Player Statistics
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    <div className="text-center p-4 bg-card rounded-lg border-2 border-primary">
                      <p className="text-xs text-muted-foreground uppercase tracking-wider">Overall</p>
                      <p className={cn("text-3xl font-bold", getPFFGradeColor(playerStats.pff.overall))}>
                        {playerStats.pff.overall.toFixed(1)}
                      </p>
                      <p className="text-xs text-muted-foreground">{getPFFGradeLabel(playerStats.pff.overall)}</p>
                    </div>
                    {playerStats.pff.offense && (
                      <div className="text-center p-4 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider">Offense</p>
                        <p className={cn("text-2xl font-bold", getPFFGradeColor(playerStats.pff.offense))}>
                          {playerStats.pff.offense.toFixed(1)}
                        </p>
                      </div>
                    )}
                    {playerStats.pff.defense && (
                      <div className="text-center p-4 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider">Defense</p>
                        <p className={cn("text-2xl font-bold", getPFFGradeColor(playerStats.pff.defense))}>
                          {playerStats.pff.defense.toFixed(1)}
                        </p>
                      </div>
                    )}
                    {playerStats.pff.passing && (
                      <div className="text-center p-4 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider">Passing</p>
                        <p className={cn("text-2xl font-bold", getPFFGradeColor(playerStats.pff.passing))}>
                          {playerStats.pff.passing.toFixed(1)}
                        </p>
                      </div>
                    )}
                    {playerStats.pff.rushing && (
                      <div className="text-center p-4 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider">Rushing</p>
                        <p className={cn("text-2xl font-bold", getPFFGradeColor(playerStats.pff.rushing))}>
                          {playerStats.pff.rushing.toFixed(1)}
                        </p>
                      </div>
                    )}
                    {playerStats.pff.receiving && (
                      <div className="text-center p-4 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider">Receiving</p>
                        <p className={cn("text-2xl font-bold", getPFFGradeColor(playerStats.pff.receiving))}>
                          {playerStats.pff.receiving.toFixed(1)}
                        </p>
                      </div>
                    )}
                    {playerStats.pff.pass_rush && (
                      <div className="text-center p-4 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider">Pass Rush</p>
                        <p className={cn("text-2xl font-bold", getPFFGradeColor(playerStats.pff.pass_rush))}>
                          {playerStats.pff.pass_rush.toFixed(1)}
                        </p>
                      </div>
                    )}
                    {playerStats.pff.coverage && (
                      <div className="text-center p-4 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider">Coverage</p>
                        <p className={cn("text-2xl font-bold", getPFFGradeColor(playerStats.pff.coverage))}>
                          {playerStats.pff.coverage.toFixed(1)}
                        </p>
                      </div>
                    )}
                    {playerStats.pff.run_block && (
                      <div className="text-center p-4 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider">Run Block</p>
                        <p className={cn("text-2xl font-bold", getPFFGradeColor(playerStats.pff.run_block))}>
                          {playerStats.pff.run_block.toFixed(1)}
                        </p>
                      </div>
                    )}
                    {playerStats.pff.pass_block && (
                      <div className="text-center p-4 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider">Pass Block</p>
                        <p className={cn("text-2xl font-bold", getPFFGradeColor(playerStats.pff.pass_block))}>
                          {playerStats.pff.pass_block.toFixed(1)}
                        </p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Position-Specific Stats - only show if has actual data */}
            {playerStats.passing && (playerStats.passing.yards || playerStats.passing.touchdowns || playerStats.passing.completion_pct || playerStats.passing.passer_rating) && (
              <Card className="glass">
                <CardHeader>
                  <CardTitle>Passing Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    {playerStats.passing.yards && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Yards</p>
                        <p className="text-2xl font-bold">{playerStats.passing.yards.toLocaleString()}</p>
                      </div>
                    )}
                    {playerStats.passing.touchdowns && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">TDs</p>
                        <p className="text-2xl font-bold">{playerStats.passing.touchdowns}</p>
                      </div>
                    )}
                    {playerStats.passing.completion_pct && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Comp %</p>
                        <p className="text-2xl font-bold">{playerStats.passing.completion_pct.toFixed(1)}%</p>
                      </div>
                    )}
                    {playerStats.passing.passer_rating && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Passer Rating</p>
                        <p className="text-2xl font-bold">{playerStats.passing.passer_rating.toFixed(1)}</p>
                      </div>
                    )}
                    {playerStats.passing.big_time_throw_pct && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Big Time %</p>
                        <p className="text-2xl font-bold">{playerStats.passing.big_time_throw_pct.toFixed(1)}%</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {playerStats.rushing && (playerStats.rushing.yards || playerStats.rushing.touchdowns || playerStats.rushing.yards_per_carry || playerStats.rushing.attempts || playerStats.rushing.elusive_rating) && (
              <Card className="glass">
                <CardHeader>
                  <CardTitle>Rushing Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {playerStats.rushing.attempts != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Attempts</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.rushing.attempts)}</p>
                      </div>
                    )}
                    {playerStats.rushing.yards != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Yards</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.rushing.yards).toLocaleString()}</p>
                      </div>
                    )}
                    {playerStats.rushing.touchdowns != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">TDs</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.rushing.touchdowns)}</p>
                      </div>
                    )}
                    {playerStats.rushing.yards_per_carry != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">YPC</p>
                        <p className="text-2xl font-bold">{playerStats.rushing.yards_per_carry.toFixed(1)}</p>
                      </div>
                    )}
                    {playerStats.rushing.yards_after_contact != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">YAC</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.rushing.yards_after_contact)}</p>
                      </div>
                    )}
                    {playerStats.rushing.missed_tackles_forced != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Broken Tackles</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.rushing.missed_tackles_forced)}</p>
                      </div>
                    )}
                    {playerStats.rushing.elusive_rating != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Elusive Rating</p>
                        <p className="text-2xl font-bold">{playerStats.rushing.elusive_rating.toFixed(1)}</p>
                      </div>
                    )}
                    {playerStats.rushing.breakaway_yards != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Breakaway Yds</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.rushing.breakaway_yards)}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {playerStats.receiving && (playerStats.receiving.receptions || playerStats.receiving.yards || playerStats.receiving.touchdowns || playerStats.receiving.targets || playerStats.receiving.yards_per_route_run) && (
              <Card className="glass">
                <CardHeader>
                  <CardTitle>Receiving Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {playerStats.receiving.targets != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Targets</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.receiving.targets)}</p>
                      </div>
                    )}
                    {playerStats.receiving.receptions != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Receptions</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.receiving.receptions)}</p>
                      </div>
                    )}
                    {playerStats.receiving.yards != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Yards</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.receiving.yards).toLocaleString()}</p>
                      </div>
                    )}
                    {playerStats.receiving.touchdowns != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">TDs</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.receiving.touchdowns)}</p>
                      </div>
                    )}
                    {playerStats.receiving.catch_rate != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Catch Rate</p>
                        <p className="text-2xl font-bold">{playerStats.receiving.catch_rate.toFixed(1)}%</p>
                      </div>
                    )}
                    {playerStats.receiving.yards_per_route_run != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Yds/Route</p>
                        <p className="text-2xl font-bold">{playerStats.receiving.yards_per_route_run.toFixed(2)}</p>
                      </div>
                    )}
                    {playerStats.receiving.yards_after_catch != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">YAC</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.receiving.yards_after_catch)}</p>
                      </div>
                    )}
                    {playerStats.receiving.drops != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Drops</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.receiving.drops)}</p>
                      </div>
                    )}
                    {playerStats.receiving.longest != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Longest</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.receiving.longest)}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {playerStats.pass_rush && (playerStats.pass_rush.sacks || playerStats.pass_rush.pressures || playerStats.pass_rush.pass_rush_win_rate) && (
              <Card className="glass">
                <CardHeader>
                  <CardTitle>Pass Rush Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    {playerStats.pass_rush.sacks && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Sacks</p>
                        <p className="text-2xl font-bold">{playerStats.pass_rush.sacks}</p>
                      </div>
                    )}
                    {playerStats.pass_rush.pressures && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Pressures</p>
                        <p className="text-2xl font-bold">{playerStats.pass_rush.pressures}</p>
                      </div>
                    )}
                    {playerStats.pass_rush.pass_rush_win_rate && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Win Rate</p>
                        <p className="text-2xl font-bold">{playerStats.pass_rush.pass_rush_win_rate.toFixed(1)}%</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {playerStats.coverage && (playerStats.coverage.interceptions || playerStats.coverage.pass_breakups || playerStats.coverage.passer_rating_allowed) && (
              <Card className="glass">
                <CardHeader>
                  <CardTitle>Coverage Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    {playerStats.coverage.interceptions && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">INTs</p>
                        <p className="text-2xl font-bold">{playerStats.coverage.interceptions}</p>
                      </div>
                    )}
                    {playerStats.coverage.pass_breakups && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">PBUs</p>
                        <p className="text-2xl font-bold">{playerStats.coverage.pass_breakups}</p>
                      </div>
                    )}
                    {playerStats.coverage.passer_rating_allowed && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Rating Allowed</p>
                        <p className="text-2xl font-bold">{playerStats.coverage.passer_rating_allowed.toFixed(1)}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {playerStats.blocking && (playerStats.blocking.pass_blocking_efficiency || playerStats.blocking.pressures_allowed) && (
              <Card className="glass">
                <CardHeader>
                  <CardTitle>Blocking Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    {playerStats.blocking.pass_blocking_efficiency && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Pass Block Eff</p>
                        <p className="text-2xl font-bold">{playerStats.blocking.pass_blocking_efficiency.toFixed(1)}</p>
                      </div>
                    )}
                    {playerStats.blocking.pressures_allowed !== undefined && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Press Allowed</p>
                        <p className="text-2xl font-bold">{playerStats.blocking.pressures_allowed}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Tackling Stats */}
            {playerStats.tackling && (playerStats.tackling.tackles || playerStats.tackling.tackles_for_loss || playerStats.tackling.forced_fumbles) && (
              <Card className="glass">
                <CardHeader>
                  <CardTitle>Tackling Stats</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {playerStats.tackling.tackles != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Tackles</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.tackling.tackles)}</p>
                      </div>
                    )}
                    {playerStats.tackling.assists != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Assists</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.tackling.assists)}</p>
                      </div>
                    )}
                    {playerStats.tackling.tackles_for_loss != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">TFLs</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.tackling.tackles_for_loss)}</p>
                      </div>
                    )}
                    {playerStats.tackling.missed_tackles != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Missed</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.tackling.missed_tackles)}</p>
                      </div>
                    )}
                    {playerStats.tackling.forced_fumbles != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Forced Fumbles</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.tackling.forced_fumbles)}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Games & Snaps */}
            {(playerStats.games_played || playerStats.snaps) && (
              <Card className="glass">
                <CardHeader>
                  <CardTitle>Usage</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {playerStats.games_played != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Games Played</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.games_played)}</p>
                      </div>
                    )}
                    {playerStats.snaps?.offensive != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Off. Snaps</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.snaps.offensive)}</p>
                      </div>
                    )}
                    {playerStats.snaps?.defensive != null && (
                      <div className="text-center p-3 bg-card rounded-lg">
                        <p className="text-xs text-muted-foreground">Def. Snaps</p>
                        <p className="text-2xl font-bold">{Math.round(playerStats.snaps.defensive)}</p>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* No Stats Available - only show if we have no PFF grades and no position stats */}
            {!playerStats.pff?.overall && !playerStats.passing && !playerStats.rushing && !playerStats.receiving &&
             !playerStats.pass_rush && !playerStats.coverage && !playerStats.blocking && !playerStats.tackling && (
              <Card className="glass col-span-full">
                <CardContent className="p-8 text-center">
                  <BarChart3 className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-30" />
                  <p className="text-muted-foreground">No detailed stats available for this player</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    Stats are loaded when available
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Comparisons Tab */}
        <TabsContent value="comparisons" className="space-y-6">
          {comparisons ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* NFL Comparisons */}
              <Card className="glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Trophy className="h-5 w-5 text-primary" />
                    NFL Comparisons
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {comparisons.nfl_comparisons && comparisons.nfl_comparisons.length > 0 ? (
                    <div className="space-y-3">
                      {comparisons.nfl_comparisons.map((comp, i) => (
                        <div key={i} className="p-3 bg-card rounded-lg flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                            <span className="text-sm font-bold">{comp.similarity}%</span>
                          </div>
                          <div className="flex-1">
                            <p className="font-semibold">{comp.name}</p>
                            <p className="text-sm text-muted-foreground">{comp.school_or_team}</p>
                          </div>
                          {comp.nfl_outcome?.draft_round && (
                            <Badge variant="outline">
                              Rd {comp.nfl_outcome.draft_round}
                            </Badge>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-center py-8 text-muted-foreground">
                      No NFL comparisons available
                    </p>
                  )}
                </CardContent>
              </Card>

              {/* College Comparisons */}
              <Card className="glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="h-5 w-5 text-primary" />
                    College Comparisons
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {comparisons.college_comparisons && comparisons.college_comparisons.length > 0 ? (
                    <div className="space-y-3">
                      {comparisons.college_comparisons.map((comp, i) => (
                        <div key={i} className="p-3 bg-card rounded-lg flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                            <span className="text-sm font-bold">{comp.similarity}%</span>
                          </div>
                          <div className="flex-1">
                            <p className="font-semibold">{comp.name}</p>
                            <p className="text-sm text-muted-foreground">{comp.school_or_team}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-center py-8 text-muted-foreground">
                      No college comparisons available
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card className="glass">
              <CardContent className="p-8 text-center">
                <Users className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-30" />
                <p className="text-muted-foreground">Player comparisons not available</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Draft Tab */}
        <TabsContent value="draft" className="space-y-6">
          {draftProjection ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Trophy className="h-5 w-5 text-primary" />
                    Draft Projection
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="text-center">
                    <Badge className={cn("text-2xl px-6 py-2", getDraftGradeColor(draftProjection.draft_letter_grade))}>
                      {draftProjection.draft_letter_grade}
                    </Badge>
                    <p className="text-sm text-muted-foreground mt-2">Draft Grade</p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-card rounded-lg">
                      <p className="text-xs text-muted-foreground">Projected Round</p>
                      <p className="text-2xl font-bold">{draftProjection.projected_round || "UDFA"}</p>
                    </div>
                    <div className="text-center p-3 bg-card rounded-lg">
                      <p className="text-xs text-muted-foreground">Pick Range</p>
                      <p className="text-2xl font-bold">{draftProjection.pick_range}</p>
                    </div>
                    <div className="text-center p-3 bg-card rounded-lg">
                      <p className="text-xs text-muted-foreground">Draft Probability</p>
                      <p className="text-2xl font-bold">{(draftProjection.draft_probability * 100).toFixed(0)}%</p>
                    </div>
                    <div className="text-center p-3 bg-card rounded-lg">
                      <p className="text-xs text-muted-foreground">Elite Traits</p>
                      <p className="text-2xl font-bold">{draftProjection.elite_traits?.length || 0}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="glass">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <DollarSign className="h-5 w-5 text-primary" />
                    Contract Projections
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="p-4 bg-card rounded-lg">
                    <p className="text-xs text-muted-foreground uppercase tracking-wider">Rookie Contract</p>
                    <p className="text-3xl font-bold text-primary">
                      {formatContractValue(draftProjection.rookie_contract_estimate)}
                    </p>
                  </div>
                  <div className="p-4 bg-card rounded-lg">
                    <p className="text-xs text-muted-foreground uppercase tracking-wider">Career Earnings (Est.)</p>
                    <p className="text-3xl font-bold text-green-500">
                      {formatContractValue(draftProjection.career_earnings_estimate)}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card className="glass">
              <CardContent className="p-8 text-center">
                <Trophy className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-30" />
                <p className="text-muted-foreground">Draft projection not available</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
