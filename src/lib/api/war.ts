import apiClient from "./client";

// =============================================================================
// Win Impact / WAR Types
// =============================================================================

export interface WARPlayer {
  rank: number;
  player_id: string;
  player_name: string;
  position: string;
  school: string;
  nil_valuation: number;
  war: number;
  war_low?: number;
  war_high?: number;
  win_prob_added: number;
  value_per_win: number;
  grade: "Elite" | "Premium" | "Solid" | "Average";
  confidence?: "high" | "medium" | "low";
  headshot_url?: string;
  stars?: number;
  origin_school?: string;
}

export interface WARBreakdown {
  base_war: number;
  position_scarcity: number;
  performance_multiplier: number;
  star_adjustment: number;
  school_tier: string;
  school_multiplier: number;
  nil_bonus: number;
  confidence_type: "measured" | "projected";
}

export interface DetailedWARResult {
  war: number;
  war_low: number;
  war_high: number;
  confidence: "high" | "medium" | "low";
  breakdown: WARBreakdown;
}

export interface TransferValueAnalysis {
  cost_per_war: number;
  fair_value_per_war: number;
  value_ratio: number;
  value_rating: string;
  roi_projection: string;
  market_comparison: string;
}

export interface TransferImpactProjection {
  current_baseline: number;
  projected_wins_added: number;
  new_projected_wins: number;
  diminishing_factor: number;
  playoff_impact: string;
}

export interface TeamPortalScore {
  team: string;
  portal_score: number;
  war_added: number;
  war_lost: number;
  net_war: number;
  avg_war_per_transfer: number;
  total_nil_invested: number;
  nil_efficiency: number;
  grade: string;
  breakdown: {
    transfers_in: number;
    position_balance: number;
    star_quality: number;
    star_distribution: Record<number, number>;
    position_distribution: Record<string, number>;
  };
  incoming_players?: WARPlayer[];
}

export interface WARLeaderboardParams {
  position?: string;
  school?: string;
  limit?: number;
}

// =============================================================================
// PORTAL IQ PROPRIETARY WAR ALGORITHM
// Must match dashboard/utils/win_impact_calculator.py exactly
// =============================================================================

// Base position WAR values (expected wins above replacement for elite player)
const POSITION_BASE_WAR: Record<string, number> = {
  // Offense - Premium positions
  QB: 3.0,      // Quarterbacks have highest single-player impact
  WR: 1.2,      // Top receivers create big plays
  RB: 0.9,      // Running backs still valuable but committee approach
  TE: 0.8,      // Receiving TEs more valuable
  // Offensive Line
  OT: 1.0,      // Tackles protect blind side
  OG: 0.7,      // Guards important for run game
  C: 0.6,       // Center controls line
  IOL: 0.7,     // Generic interior line
  // Defense - Premium positions
  EDGE: 1.5,    // Pass rushers change games
  CB: 1.2,      // Corners lock down receivers
  S: 0.9,       // Safeties cover deep
  LB: 1.0,      // Linebackers versatile
  DT: 0.8,      // Interior disruption
  DL: 0.9,      // Generic defensive line
  // Special Teams
  K: 0.4,       // Kickers can swing close games
  P: 0.3,       // Punters flip field position
  // Default
  ATH: 0.8,     // Athletes can play anywhere
};

// Position scarcity multiplier (harder to find quality = higher value)
const POSITION_SCARCITY: Record<string, number> = {
  QB: 1.4,      // Elite QBs are rare
  EDGE: 1.3,    // Pass rushers always in demand
  OT: 1.2,      // Good tackles hard to find
  CB: 1.2,      // Lockdown corners scarce
  WR: 1.0,      // More available
  RB: 0.8,      // Running backs replaceable
};

// NIL-to-star tier mapping (used when we only have NIL data)
// These thresholds help estimate player tier from market value
const NIL_STAR_THRESHOLDS: Record<string, { min: number; stars: number }[]> = {
  QB: [
    { min: 500000, stars: 5 },
    { min: 150000, stars: 4 },
    { min: 40000, stars: 3 },
    { min: 10000, stars: 2 },
  ],
  DEFAULT: [
    { min: 200000, stars: 5 },
    { min: 60000, stars: 4 },
    { min: 15000, stars: 3 },
    { min: 5000, stars: 2 },
  ],
};

// Star adjustment REDUCED: secondary indicator, not primary driver
// Old range: 0.3 to 2.0 (6.7x swing). New: 0.85 to 1.15 (1.35x swing)
const STAR_MULTIPLIERS: Record<number, number> = {
  5: 1.15,   // 5-star = slight boost, not defining factor
  4: 1.08,   // 4-star
  3: 1.0,    // 3-star = baseline
  2: 0.93,   // 2-star
  1: 0.85,   // Walk-on level
};

// PFF estimate from star rating (fallback when no PFF data available)
const STAR_PFF_ESTIMATE: Record<number, number> = {
  5: 82, 4: 72, 3: 62, 2: 55, 1: 48,
};
const FBS_AVG_STARTER_GRADE = 65;

// PFF data interface for performance calculation
export interface PFFData {
  pff_overall?: number;
  pff_passing?: number;
  pff_rushing?: number;
  pff_receiving?: number;
  pff_offense?: number;
  pff_defense?: number;
  pff_pass_rush?: number;
  pff_coverage?: number;
  pff_pass_block?: number;
  pff_run_block?: number;
  pff_run_defense?: number;
  completion_pct?: number;
  big_time_throw_pct?: number;
  turnover_worthy_play_pct?: number;
  elusive_rating?: number;
  yaco_per_attempt?: number;
  yards_per_route_run?: number;
  drop_rate?: number;
  pass_rush_win_rate?: number;
  pass_rushing_productivity?: number;
  forced_incompletion_rate?: number;
  passer_rating_allowed?: number;
  pass_blocking_efficiency?: number;
}

/**
 * Calculate position-specific performance multiplier from PFF data.
 * This is the PRIMARY differentiator in WAR v2.
 * Must match backend calculate_position_performance_score().
 */
function calculatePerformanceMultiplier(
  position: string,
  pffData?: PFFData | null,
  stars?: number,
): { multiplier: number; confidence: "measured" | "projected" } {
  const pos = position.toUpperCase();

  if (!pffData || !pffData.pff_overall) {
    const estGrade = STAR_PFF_ESTIMATE[stars || 2] || 55;
    return { multiplier: estGrade / FBS_AVG_STARTER_GRADE, confidence: "projected" };
  }

  const g = (key: keyof PFFData, fallback: number): number =>
    (pffData[key] as number) ?? fallback;

  let grade: number;

  if (pos === "QB") {
    const pffPass = g("pff_passing", g("pff_offense", g("pff_overall", 60)));
    const pffRush = g("pff_rushing", 60);
    const compPct = g("completion_pct", 58);
    const btt = g("big_time_throw_pct", 3.5);
    const twp = g("turnover_worthy_play_pct", 3.5);
    const compScore = Math.min(compPct / 65.0, 1.5) * 65;
    const decisionBonus = Math.max(0, btt - twp) * 3;
    grade = 0.50 * pffPass + 0.15 * pffRush + 0.20 * compScore + 0.15 * Math.min(80, 60 + decisionBonus);
  } else if (pos === "WR" || pos === "TE") {
    const pffRec = g("pff_receiving", g("pff_offense", g("pff_overall", 60)));
    const yprr = g("yards_per_route_run", 1.2);
    const drop = g("drop_rate", 8.0);
    const yprrScore = Math.min(yprr / 1.5, 1.5) * 65;
    const dropScore = Math.max(40, 80 - drop * 3);
    grade = 0.50 * pffRec + 0.30 * yprrScore + 0.20 * dropScore;
  } else if (pos === "RB") {
    const pffRush = g("pff_rushing", g("pff_offense", g("pff_overall", 60)));
    const elusive = g("elusive_rating", 40);
    const yaco = g("yaco_per_attempt", 2.0);
    const elusiveScore = Math.min(elusive / 50, 1.5) * 65;
    const yacoScore = Math.min(yaco / 2.5, 1.5) * 65;
    grade = 0.50 * pffRush + 0.25 * elusiveScore + 0.25 * yacoScore;
  } else if (pos === "EDGE" || pos === "DL" || pos === "DE") {
    const pffPR = g("pff_pass_rush", g("pff_defense", g("pff_overall", 60)));
    const prwr = g("pass_rush_win_rate", 10);
    const prp = g("pass_rushing_productivity", 5);
    const prwrScore = Math.min(prwr / 12.0, 1.5) * 65;
    const prpScore = Math.min(prp / 6.0, 1.5) * 65;
    grade = 0.50 * pffPR + 0.30 * prwrScore + 0.20 * prpScore;
  } else if (pos === "DT") {
    const pffDef = g("pff_run_defense", g("pff_defense", g("pff_overall", 60)));
    const pffPR = g("pff_pass_rush", 55);
    grade = 0.50 * pffDef + 0.50 * pffPR;
  } else if (pos === "CB" || pos === "S") {
    const pffCov = g("pff_coverage", g("pff_defense", g("pff_overall", 60)));
    const fi = g("forced_incompletion_rate", 8);
    const pra = g("passer_rating_allowed", 90);
    const fiScore = Math.min(fi / 10.0, 1.5) * 65;
    const praScore = Math.max(40, 90 - (pra - 70) * 0.8);
    grade = 0.50 * pffCov + 0.25 * fiScore + 0.25 * praScore;
  } else if (["OT", "OG", "C", "OL", "IOL"].includes(pos)) {
    const pffPB = g("pff_pass_block", g("pff_offense", g("pff_overall", 60)));
    const pffRB = g("pff_run_block", g("pff_offense", g("pff_overall", 60)));
    const pbe = g("pass_blocking_efficiency", 95);
    const pbeScore = Math.min(pbe / 96.0, 1.3) * 65;
    grade = 0.40 * pffPB + 0.35 * pffRB + 0.25 * pbeScore;
  } else if (pos === "LB") {
    const pffDef = g("pff_defense", g("pff_overall", 60));
    const pffCov = g("pff_coverage", 55);
    const pffRD = g("pff_run_defense", 55);
    grade = 0.40 * pffDef + 0.30 * pffCov + 0.30 * pffRD;
  } else {
    grade = g("pff_overall", 60);
  }

  return { multiplier: grade / FBS_AVG_STARTER_GRADE, confidence: "measured" };
}

/**
 * Estimate star rating from NIL value when actual stars not available
 */
function estimateStarsFromNIL(nilValue: number, position: string): number {
  const thresholds = NIL_STAR_THRESHOLDS[position.toUpperCase()] || NIL_STAR_THRESHOLDS.DEFAULT;
  for (const tier of thresholds) {
    if (nilValue >= tier.min) return tier.stars;
  }
  return 2; // Default to 2-star if below all thresholds
}

/**
 * Calculate NIL market signal bonus (must match backend get_nil_market_signal)
 */
function getNILMarketSignal(nilValue: number, position: string): number {
  if (!nilValue || nilValue <= 0) return 0;

  // Position-adjusted baselines (calibrated to real On3 market data)
  const positionNILBaseline: Record<string, number> = {
    QB: 50000,
    WR: 20000,
    RB: 15000,
    EDGE: 15000,
    CB: 12000,
  };

  const baseline = positionNILBaseline[position.toUpperCase()] || 10000;
  const ratio = nilValue / baseline;

  // REDUCED: NIL is minor signal (max 0.15, was 0.5) — avoid circularity
  if (ratio >= 10) return 0.15;     // 10x = superstar
  if (ratio >= 5) return 0.10;      // 5x = premium
  if (ratio >= 2) return 0.06;      // 2x = above average
  if (ratio >= 1) return 0.03;      // At baseline
  return 0;
}

/**
 * Calculate WAR using Portal IQ's proprietary algorithm (v2 — Performance-First)
 * IMPORTANT: This must match ml-engine/src/utils/data_loader.py calculate_player_war()
 */
export function calculateWAR(
  nilValue: number,
  position: string,
  stars?: number,
  school?: string,
  pffData?: PFFData | null,
): number {
  const pos = position?.toUpperCase() || "ATH";

  // 1. Base WAR from position
  const baseWAR = POSITION_BASE_WAR[pos] || 0.8;
  const scarcity = POSITION_SCARCITY[pos] || 1.0;

  // 2. Star adjustment (SECONDARY — reduced from primary)
  const effectiveStars = stars || estimateStarsFromNIL(nilValue, pos);
  const starAdj = STAR_MULTIPLIERS[effectiveStars] || 1.0;

  // 3. School tier factor (competition level context)
  const { multiplier: schoolMult } = getSchoolTier(school || "");

  // 4. Performance multiplier (THE PRIMARY DIFFERENTIATOR)
  const { multiplier: perfMult } = calculatePerformanceMultiplier(pos, pffData, effectiveStars);

  // 5. NIL market signal (MINOR bonus — avoid circularity)
  const nilBonus = getNILMarketSignal(nilValue, pos);

  // WAR = Base × Scarcity × Performance × School × Stars + NIL
  const rawWAR = baseWAR * scarcity * perfMult * schoolMult * starAdj + nilBonus;

  return Math.round(Math.max(0, rawWAR) * 100) / 100;
}

/**
 * Calculate win probability added from WAR
 */
function calculateWinProbAdded(war: number): number {
  // Each WAR adds roughly 6-8% win probability
  return war * 7;
}

/**
 * Get grade based on WAR
 */
function getGrade(war: number): "Elite" | "Premium" | "Solid" | "Average" {
  if (war >= 2.0) return "Elite";
  if (war >= 1.2) return "Premium";
  if (war >= 0.6) return "Solid";
  return "Average";
}

/**
 * Get WAR leaderboard by fetching NIL data and calculating WAR metrics
 */
export async function getWARLeaderboard(
  params?: WARLeaderboardParams
): Promise<WARPlayer[]> {
  // Ensure school tiers are loaded for WAR calculation
  await loadSchoolTiers();

  // Fetch NIL leaderboard data
  const searchParams = new URLSearchParams();
  if (params?.position) searchParams.set("position", params.position);
  if (params?.school) searchParams.set("school", params.school);
  searchParams.set("limit", (params?.limit || 100).toString());

  const queryString = searchParams.toString();
  const url = queryString ? `/api/nil/leaderboard?${queryString}` : "/api/nil/leaderboard";

  const response = await apiClient.get(url);
  // The response interceptor extracts data.data, so we cast through unknown
  const data = response as unknown as { players: Array<{
    rank?: number;
    player_id?: string;
    player_name: string;
    position: string;
    school: string;
    valuation: number;
    headshot_url?: string;
    stars?: number;
    origin_school?: string;
    pff_overall?: number;
  }>; total: number };

  // Transform NIL data to WAR metrics
  // Use pre-computed WAR from API when available (unified cache), fallback to client-side calculation
  const warPlayers: WARPlayer[] = data.players.map((player, index) => {
    const nilValue = player.valuation || 0;
    const playerWithWAR = player as Record<string, unknown>;

    // Check if API provided pre-computed WAR (from unified_players.csv)
    let war: number;
    if (typeof playerWithWAR.war === "number" && playerWithWAR.war > 0) {
      // Use pre-computed WAR from backend
      war = playerWithWAR.war;
    } else {
      // Fallback: calculate WAR client-side (legacy behavior)
      const pffData: PFFData | undefined = player.pff_overall ? {
        pff_overall: player.pff_overall,
        pff_offense: playerWithWAR.pff_offense as number | undefined,
        pff_defense: playerWithWAR.pff_defense as number | undefined,
      } : undefined;
      war = calculateWAR(nilValue, player.position, player.stars, player.school, pffData);
    }

    const winProbAdded = calculateWinProbAdded(war);
    const valuePerWin = war > 0 ? nilValue / war : 0;

    return {
      rank: index + 1,
      player_id: player.player_id || `player_${index}`,
      player_name: player.player_name,
      position: player.position,
      school: player.school,
      nil_valuation: nilValue,
      war: Math.round(war * 100) / 100,
      win_prob_added: Math.round(winProbAdded * 10) / 10,
      value_per_win: Math.round(valuePerWin),
      grade: getGrade(war),
      headshot_url: player.headshot_url,
      stars: player.stars,
      origin_school: player.origin_school,
    };
  });

  // Sort by WAR descending
  warPlayers.sort((a, b) => b.war - a.war);

  // Re-rank after sorting
  warPlayers.forEach((player, index) => {
    player.rank = index + 1;
  });

  return warPlayers;
}

/**
 * Calculate WAR for a custom player input (v2 — uses PFF data)
 */
export async function calculatePlayerWAR(input: {
  name: string;
  position: string;
  school: string;
  nil_valuation: number;
  stars?: number;
  pffData?: PFFData | null;
}): Promise<WARPlayer> {
  const war = calculateWAR(
    input.nil_valuation, input.position, input.stars, input.school, input.pffData,
  );
  const winProbAdded = calculateWinProbAdded(war);
  const valuePerWin = war > 0 ? input.nil_valuation / war : 0;

  return {
    rank: 0,
    player_id: input.name.toLowerCase().replace(/\s+/g, "_"),
    player_name: input.name,
    position: input.position,
    school: input.school,
    nil_valuation: input.nil_valuation,
    war: Math.round(war * 100) / 100,
    win_prob_added: Math.round(winProbAdded * 10) / 10,
    value_per_win: Math.round(valuePerWin),
    grade: getGrade(war),
    stars: input.stars,
  };
}

// =============================================================================
// School Tiers (loaded from API, cached locally)
// Multipliers match backend school_tiers.py TIER_DEFINITIONS
// =============================================================================

// Cache of school → { tier, multiplier } loaded from API
let _schoolTierCache: Record<string, { tier: string; multiplier: number }> | null = null;
let _cacheLoading = false;

/**
 * Load school tiers from the API and cache them.
 * Called on first use; subsequent calls return from cache.
 */
export async function loadSchoolTiers(): Promise<void> {
  if (_schoolTierCache || _cacheLoading) return;
  _cacheLoading = true;

  try {
    const response = await apiClient.get("/api/schools/tiers");
    const data = response as unknown as {
      tiers: Record<string, Array<{ school: string; tier: string; multiplier: number }>>;
      all_schools?: Array<{ school: string; tier: string; multiplier: number }>;
    };

    const cache: Record<string, { tier: string; multiplier: number }> = {};

    // Build cache from all_schools or from tiers buckets
    if (data.all_schools) {
      for (const s of data.all_schools) {
        cache[s.school.toLowerCase()] = { tier: s.tier, multiplier: s.multiplier };
      }
    } else if (data.tiers) {
      for (const [, schools] of Object.entries(data.tiers)) {
        for (const s of schools) {
          cache[s.school.toLowerCase()] = { tier: s.tier, multiplier: s.multiplier };
        }
      }
    }

    if (Object.keys(cache).length > 0) {
      _schoolTierCache = cache;
    }
  } catch {
    // Silently fail — getSchoolTier will use default multiplier
  } finally {
    _cacheLoading = false;
  }
}

/**
 * Get school tier and multiplier.
 * Uses API-cached data when available, defaults to 1.0 multiplier otherwise.
 */
export function getSchoolTier(school: string): { tier: string; multiplier: number } {
  if (!school) return { tier: "g5_mid", multiplier: 0.8 };

  const schoolLower = school.toLowerCase().trim();

  // Check API cache first
  if (_schoolTierCache) {
    const cached = _schoolTierCache[schoolLower];
    if (cached) return cached;

    // Try partial match (e.g. "Alabama" matching "alabama")
    for (const [key, info] of Object.entries(_schoolTierCache)) {
      if (key.includes(schoolLower) || schoolLower.includes(key)) {
        return info;
      }
    }
  }

  // Default for unknown/uncached schools
  return { tier: "g5_mid", multiplier: 0.8 };
}

/**
 * Calculate detailed WAR with full breakdown (v2 — Performance-First)
 * Must match backend calculate_player_war() exactly.
 */
export function calculateDetailedWAR(input: {
  position: string;
  stars?: number;
  nil_value?: number;
  destination_school?: string;
  pffData?: PFFData | null;
}): DetailedWARResult {
  const position = input.position?.toUpperCase() || "ATH";
  const stars = input.stars || 3;

  // 1. Base WAR from position
  const baseWAR = POSITION_BASE_WAR[position] || 0.8;
  const scarcity = POSITION_SCARCITY[position] || 1.0;

  // 2. Star adjustment (secondary)
  const starAdj = STAR_MULTIPLIERS[stars] || 1.0;

  // 3. School tier factor
  const { tier: tierName, multiplier: schoolMult } = getSchoolTier(input.destination_school || "");

  // 4. Performance multiplier (PRIMARY)
  const { multiplier: perfMult, confidence: confType } = calculatePerformanceMultiplier(
    position, input.pffData, stars,
  );

  // 5. NIL market signal (minor)
  const nilBonus = input.nil_value ? getNILMarketSignal(input.nil_value, position) : 0;

  // Calculate final WAR
  const finalWAR = Math.round(
    Math.max(0, baseWAR * scarcity * perfMult * schoolMult * starAdj + nilBonus) * 100
  ) / 100;

  // Confidence based on data quality
  let confidence: "high" | "medium" | "low" = "low";
  if (confType === "measured") {
    confidence = "high";
  } else if (stars > 0 && input.destination_school) {
    confidence = "medium";
  }

  // Confidence-based range
  const rangeFactor = confType === "measured" ? 0.15 : 0.4;

  return {
    war: finalWAR,
    war_low: Math.round(finalWAR * (1 - rangeFactor) * 100) / 100,
    war_high: Math.round(finalWAR * (1 + rangeFactor) * 100) / 100,
    confidence,
    breakdown: {
      base_war: Math.round(baseWAR * 100) / 100,
      position_scarcity: Math.round(scarcity * 100) / 100,
      performance_multiplier: Math.round(perfMult * 100) / 100,
      star_adjustment: Math.round(starAdj * 100) / 100,
      school_tier: tierName,
      school_multiplier: Math.round(schoolMult * 100) / 100,
      nil_bonus: Math.round(nilBonus * 100) / 100,
      confidence_type: confType,
    },
  };
}

/**
 * Analyze transfer value (cost per WAR, ROI projection)
 */
export function analyzeTransferValue(
  playerWAR: number,
  nilValue: number,
  position: string
): TransferValueAnalysis {
  if (!nilValue || nilValue <= 0 || !playerWAR || playerWAR <= 0) {
    return {
      cost_per_war: 0,
      fair_value_per_war: 30000,
      value_ratio: 0,
      value_rating: "unknown",
      roi_projection: "Insufficient data",
      market_comparison: "N/A",
    };
  }

  const costPerWAR = nilValue / playerWAR;

  // Position-adjusted fair value per WAR (calibrated to real On3 market data)
  const positionFairValue: Record<string, number> = {
    QB: 80000, WR: 40000, RB: 35000, EDGE: 45000, CB: 38000,
    OT: 35000, LB: 32000, S: 30000, TE: 32000, DT: 30000,
  };

  const fairValue = positionFairValue[position.toUpperCase()] || 30000;
  const ratio = costPerWAR / fairValue;

  let valueRating: string;
  let roiProjection: string;

  if (ratio <= 0.6) {
    valueRating = "exceptional_value";
    roiProjection = "High ROI - significantly undervalued";
  } else if (ratio <= 0.85) {
    valueRating = "good_value";
    roiProjection = "Positive ROI - below market rate";
  } else if (ratio <= 1.15) {
    valueRating = "fair_value";
    roiProjection = "Market rate - standard ROI expected";
  } else if (ratio <= 1.4) {
    valueRating = "slight_overpay";
    roiProjection = "Marginal ROI - slightly above market";
  } else {
    valueRating = "significant_overpay";
    roiProjection = "Negative ROI - premium price for talent";
  }

  const marketComparison = ratio < 1
    ? `Below market by ${Math.round((1 - ratio) * 100)}%`
    : `Above market by ${Math.round((ratio - 1) * 100)}%`;

  return {
    cost_per_war: Math.round(costPerWAR),
    fair_value_per_war: fairValue,
    value_ratio: Math.round(ratio * 100) / 100,
    value_rating: valueRating,
    roi_projection: roiProjection,
    market_comparison: marketComparison,
  };
}

/**
 * Project team improvement from adding a player
 */
export function projectTransferImpact(
  playerWAR: number,
  schoolTier: string
): TransferImpactProjection {
  // Tier-based win expectations
  const tierBaselineWins: Record<string, number> = {
    elite: 10,
    power: 8,
    rising: 6,
    developmental: 4,
  };

  const current = tierBaselineWins[schoolTier] || 6;

  // Diminishing returns for good teams
  let diminishingFactor = 1.0;
  if (current >= 10) diminishingFactor = 0.6;
  else if (current >= 8) diminishingFactor = 0.8;

  const projectedImprovement = playerWAR * diminishingFactor;

  let playoffImpact: string;
  if (projectedImprovement >= 1.5) playoffImpact = "Significant";
  else if (projectedImprovement >= 0.8) playoffImpact = "Moderate";
  else playoffImpact = "Marginal";

  return {
    current_baseline: current,
    projected_wins_added: Math.round(projectedImprovement * 10) / 10,
    new_projected_wins: Math.round(Math.min(13, current + projectedImprovement) * 10) / 10,
    diminishing_factor: diminishingFactor,
    playoff_impact: playoffImpact,
  };
}

/**
 * Calculate team portal impact scores from portal players
 */
export function calculateTeamPortalScores(players: WARPlayer[]): TeamPortalScore[] {
  // Group players by destination school
  const schoolMap = new Map<string, WARPlayer[]>();

  for (const player of players) {
    const school = player.school;
    if (!school) continue;

    if (!schoolMap.has(school)) {
      schoolMap.set(school, []);
    }
    schoolMap.get(school)!.push(player);
  }

  const teamScores: TeamPortalScore[] = [];

  for (const [school, incoming] of schoolMap.entries()) {
    if (incoming.length < 1) continue;

    // Calculate WAR and metrics
    const wars = incoming.map(p => p.war);
    const totalWAR = wars.reduce((sum, w) => sum + w, 0);
    const avgWAR = totalWAR / incoming.length;
    const totalNIL = incoming.reduce((sum, p) => sum + (p.nil_valuation || 0), 0);

    // Position distribution
    const positionCounts: Record<string, number> = {};
    const starCounts: Record<number, number> = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 };

    for (const player of incoming) {
      const pos = player.position || "ATH";
      positionCounts[pos] = (positionCounts[pos] || 0) + 1;

      const stars = player.stars || 3;
      starCounts[stars] = (starCounts[stars] || 0) + 1;
    }

    // Position balance (diversification is good)
    const numPositions = Object.keys(positionCounts).length;
    const maxPositionCount = Math.max(...Object.values(positionCounts));
    const positionBalance = Math.min(1.0, numPositions / 8) * (1 - (maxPositionCount / incoming.length * 0.3));

    // Star quality score
    const starQuality = (
      starCounts[5] * 1.0 +
      starCounts[4] * 0.6 +
      starCounts[3] * 0.3 +
      starCounts[2] * 0.1
    ) / incoming.length;

    // NIL efficiency (WAR per $10K of NIL spent)
    const nilEfficiency = totalNIL > 0 ? totalWAR / (totalNIL / 10000) : 0;

    // Calculate composite score (0-100 scale)
    const rawScore = (
      totalWAR * 8 +
      positionBalance * 15 +
      starQuality * 20 +
      Math.min(nilEfficiency * 5, 15)
    );

    const portalScore = Math.min(100, Math.max(0, rawScore));

    // Grade assignment
    let grade: string;
    if (portalScore >= 85) grade = "A+";
    else if (portalScore >= 75) grade = "A";
    else if (portalScore >= 65) grade = "B+";
    else if (portalScore >= 55) grade = "B";
    else if (portalScore >= 45) grade = "C+";
    else if (portalScore >= 35) grade = "C";
    else grade = "D";

    teamScores.push({
      team: school,
      portal_score: Math.round(portalScore * 10) / 10,
      war_added: Math.round(totalWAR * 100) / 100,
      war_lost: 0, // Would need outgoing data
      net_war: Math.round(totalWAR * 100) / 100,
      avg_war_per_transfer: Math.round(avgWAR * 100) / 100,
      total_nil_invested: totalNIL,
      nil_efficiency: Math.round(nilEfficiency * 1000) / 1000,
      grade,
      breakdown: {
        transfers_in: incoming.length,
        position_balance: Math.round(positionBalance * 100) / 100,
        star_quality: Math.round(starQuality * 100) / 100,
        star_distribution: starCounts,
        position_distribution: positionCounts,
      },
      incoming_players: incoming,
    });
  }

  // Sort by portal score descending
  teamScores.sort((a, b) => b.portal_score - a.portal_score);

  return teamScores;
}

/**
 * Get list of schools for dropdown.
 * Returns cached schools from API if available, empty array otherwise.
 * Use SCHOOL_LIST from team.ts for a complete static fallback list.
 */
export function getSchoolList(): string[] {
  if (_schoolTierCache) {
    return Object.values(_schoolTierCache)
      .map((_, i) => Object.keys(_schoolTierCache!)[i])
      .sort();
  }
  return [];
}
