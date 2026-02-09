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
  star_multiplier: number;
  rating_bonus: number;
  school_tier: string;
  school_multiplier: number;
  measurables_factor: number;
  experience_factor: number;
  nil_bonus: number;
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
    { min: 2000000, stars: 5 },
    { min: 800000, stars: 4 },
    { min: 200000, stars: 3 },
    { min: 50000, stars: 2 },
  ],
  DEFAULT: [
    { min: 500000, stars: 5 },
    { min: 200000, stars: 4 },
    { min: 75000, stars: 3 },
    { min: 25000, stars: 2 },
  ],
};

// Star rating multipliers (must match backend)
const STAR_MULTIPLIERS: Record<number, number> = {
  5: 2.0,    // 5-star = proven elite talent
  4: 1.5,    // 4-star = high upside
  3: 1.0,    // 3-star = baseline
  2: 0.6,    // 2-star = developmental
  1: 0.3,    // Walk-on level
};

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

  // Position-adjusted baselines
  const positionNILBaseline: Record<string, number> = {
    QB: 500000,
    WR: 200000,
    RB: 150000,
    EDGE: 150000,
    CB: 120000,
  };

  const baseline = positionNILBaseline[position.toUpperCase()] || 100000;
  const ratio = nilValue / baseline;

  if (ratio >= 10) return 0.5;      // 10x = superstar
  if (ratio >= 5) return 0.35;      // 5x = premium
  if (ratio >= 2) return 0.2;       // 2x = above average
  if (ratio >= 1) return 0.1;       // At baseline
  return 0;
}

/**
 * Calculate WAR using Portal IQ's proprietary algorithm
 * IMPORTANT: This must match dashboard/utils/win_impact_calculator.py
 */
export function calculateWAR(nilValue: number, position: string, stars?: number, school?: string): number {
  const pos = position?.toUpperCase() || "ATH";

  // 1. Base WAR from position
  const baseWAR = POSITION_BASE_WAR[pos] || 0.8;
  const scarcity = POSITION_SCARCITY[pos] || 1.0;

  // 2. Star rating multiplier
  const effectiveStars = stars || estimateStarsFromNIL(nilValue, pos);
  const starMult = STAR_MULTIPLIERS[effectiveStars] || 1.0;

  // 3. School tier factor (if school provided)
  const { multiplier: schoolMult } = getSchoolTier(school || "");

  // 4. NIL market signal (bonus, not multiplier)
  // Treat all NIL from leaderboard as predicted (0.7 discount)
  const nilBonus = getNILMarketSignal(nilValue, pos) * 0.7;

  // Calculate final WAR (simplified - no measurables/experience without full data)
  const rawWAR = baseWAR * scarcity;
  const adjustedWAR = rawWAR * starMult;
  const schoolAdjusted = adjustedWAR * schoolMult;
  const finalWAR = schoolAdjusted + nilBonus;

  return Math.round(finalWAR * 100) / 100;
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
  }>; total: number };

  // Transform NIL data to WAR metrics using Portal IQ's proprietary algorithm
  const warPlayers: WARPlayer[] = data.players.map((player, index) => {
    const nilValue = player.valuation || 0;
    // Pass school for school tier adjustment in WAR calculation
    const war = calculateWAR(nilValue, player.position, undefined, player.school);
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
 * Calculate WAR for a custom player input
 */
export async function calculatePlayerWAR(input: {
  name: string;
  position: string;
  school: string;
  nil_valuation: number;
  pff_grade?: number;
}): Promise<WARPlayer> {
  // Use NIL value for base calculation
  let nilValue = input.nil_valuation;

  // Adjust based on performance grade if provided (65-95 range)
  if (input.pff_grade) {
    const gradeMultiplier = (input.pff_grade - 60) / 30; // 0-1.17 range
    nilValue = nilValue * (0.7 + gradeMultiplier * 0.6);
  }

  const war = calculateWAR(nilValue, input.position);
  const winProbAdded = calculateWinProbAdded(war);
  const valuePerWin = war > 0 ? input.nil_valuation / war : 0;

  return {
    rank: 0,
    player_id: input.name.toLowerCase().replace(/\s+/g, "_"),
    player_name: input.name,
    position: input.position,
    school: input.school,
    nil_valuation: input.nil_valuation,
    war: Math.round(war * 10) / 10,
    win_prob_added: Math.round(winProbAdded * 10) / 10,
    value_per_win: Math.round(valuePerWin),
    grade: getGrade(war),
  };
}

// =============================================================================
// School Tiers (matching Streamlit algorithm)
// =============================================================================

const SCHOOL_TIERS: Record<string, { schools: string[]; multiplier: number }> = {
  elite: {
    schools: ["Alabama", "Georgia", "Ohio State", "Michigan", "Texas",
              "Oregon", "Penn State", "Notre Dame", "USC", "Clemson"],
    multiplier: 1.3,
  },
  power: {
    schools: ["LSU", "Oklahoma", "Florida", "Miami", "Tennessee", "Auburn",
              "Texas A&M", "Wisconsin", "UCLA", "Washington", "Utah", "Ole Miss",
              "Missouri", "Florida State", "Louisville", "Kentucky", "Arkansas"],
    multiplier: 1.15,
  },
  rising: {
    schools: ["Colorado", "Indiana", "Illinois", "Iowa State", "Kansas State",
              "Arizona", "NC State", "Virginia Tech", "Baylor", "Pittsburgh",
              "SMU", "Syracuse", "Duke", "Cal", "Nebraska"],
    multiplier: 1.0,
  },
  developmental: {
    schools: [],
    multiplier: 0.85,
  }
};

/**
 * Get school tier and multiplier
 */
export function getSchoolTier(school: string): { tier: string; multiplier: number } {
  if (!school) return { tier: "developmental", multiplier: 0.85 };

  const schoolLower = school.toLowerCase();

  for (const [tierName, tierData] of Object.entries(SCHOOL_TIERS)) {
    if (tierName === "developmental") continue;
    for (const s of tierData.schools) {
      if (s.toLowerCase().includes(schoolLower) || schoolLower.includes(s.toLowerCase())) {
        return { tier: tierName, multiplier: tierData.multiplier };
      }
    }
  }

  return { tier: "developmental", multiplier: 0.85 };
}

/**
 * Calculate detailed WAR with full breakdown (matching Streamlit algorithm)
 */
export function calculateDetailedWAR(input: {
  position: string;
  stars?: number;
  nil_value?: number;
  destination_school?: string;
  is_predicted_nil?: boolean;
}): DetailedWARResult {
  const position = input.position?.toUpperCase() || "ATH";
  const stars = input.stars || 3;

  // 1. Base WAR from position (using same weights as POSITION_WAR_WEIGHTS)
  const positionBaseWAR: Record<string, number> = {
    QB: 3.0, WR: 1.2, RB: 0.9, TE: 0.8,
    OT: 1.0, OG: 0.7, C: 0.6, IOL: 0.7,
    EDGE: 1.5, CB: 1.2, S: 0.9, LB: 1.0, DT: 0.8, DL: 0.9,
    K: 0.4, P: 0.3, ATH: 0.8,
  };

  const positionScarcity: Record<string, number> = {
    QB: 1.4, EDGE: 1.3, OT: 1.2, CB: 1.2, WR: 1.0, RB: 0.8,
  };

  const baseWAR = positionBaseWAR[position] || 0.8;
  const scarcity = positionScarcity[position] || 1.0;

  // 2. Star rating multiplier
  const starMult = STAR_MULTIPLIERS[stars] || 1.0;

  // 3. School tier factor
  const { tier: tierName, multiplier: schoolMult } = getSchoolTier(input.destination_school || "");

  // 4. NIL market signal (bonus, not multiplier)
  let nilBonus = 0;
  if (input.nil_value && input.nil_value > 0) {
    const positionNILBaseline: Record<string, number> = {
      QB: 500000, WR: 200000, RB: 150000, EDGE: 150000, CB: 120000,
    };
    const baseline = positionNILBaseline[position] || 100000;
    const ratio = input.nil_value / baseline;

    if (ratio >= 10) nilBonus = 0.5;
    else if (ratio >= 5) nilBonus = 0.35;
    else if (ratio >= 2) nilBonus = 0.2;
    else if (ratio >= 1) nilBonus = 0.1;

    // Reduce confidence in predicted NIL
    if (input.is_predicted_nil) {
      nilBonus *= 0.7;
    }
  }

  // Calculate final WAR
  const rawWAR = baseWAR * scarcity;
  const adjustedWAR = rawWAR * starMult;
  const schoolAdjusted = adjustedWAR * schoolMult;
  const finalWAR = Math.round((schoolAdjusted + nilBonus) * 100) / 100;

  // Confidence level
  let confidence: "high" | "medium" | "low" = "low";
  let confidenceScore = 0;
  if (stars > 0) confidenceScore += 30;
  if (input.nil_value && input.nil_value > 0) confidenceScore += input.is_predicted_nil ? 15 : 25;
  if (input.destination_school && tierName !== "developmental") confidenceScore += 15;

  if (confidenceScore >= 60) confidence = "high";
  else if (confidenceScore >= 35) confidence = "medium";

  return {
    war: finalWAR,
    war_low: Math.round(finalWAR * 0.7 * 100) / 100,
    war_high: Math.round(finalWAR * 1.3 * 100) / 100,
    confidence,
    breakdown: {
      base_war: Math.round(baseWAR * 100) / 100,
      position_scarcity: Math.round(scarcity * 100) / 100,
      star_multiplier: Math.round(starMult * 100) / 100,
      rating_bonus: 0,
      school_tier: tierName,
      school_multiplier: Math.round(schoolMult * 100) / 100,
      measurables_factor: 1.0,
      experience_factor: 1.0,
      nil_bonus: Math.round(nilBonus * 100) / 100,
    }
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
      fair_value_per_war: 300000,
      value_ratio: 0,
      value_rating: "unknown",
      roi_projection: "Insufficient data",
      market_comparison: "N/A",
    };
  }

  const costPerWAR = nilValue / playerWAR;

  // Position-adjusted fair value per WAR
  const positionFairValue: Record<string, number> = {
    QB: 800000, WR: 400000, RB: 350000, EDGE: 450000, CB: 380000,
    OT: 350000, LB: 320000, S: 300000, TE: 320000, DT: 300000,
  };

  const fairValue = positionFairValue[position.toUpperCase()] || 300000;
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

    // NIL efficiency
    const nilEfficiency = totalNIL > 0 ? totalWAR / (totalNIL / 100000) : 0;

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
 * Get list of schools for dropdown
 */
export function getSchoolList(): string[] {
  const allSchools: string[] = [];
  for (const tierData of Object.values(SCHOOL_TIERS)) {
    allSchools.push(...tierData.schools);
  }
  return allSchools.sort();
}
