import apiClient from "./client";

// =============================================================================
// Player Types
// =============================================================================

export interface PlayerSearchResult {
  name: string;
  position: string;
  school: string;
  nil_value?: number;
  stars?: number;
  headshot_url?: string;
  pff_overall?: number;
  status?: string;
  destination_school?: string;
  data_source: "nil" | "portal";
}

export interface PlayerSearchResponse {
  players: PlayerSearchResult[];
  total: number;
  query: string;
}

export interface PFFGrades {
  overall?: number;
  offense?: number;
  defense?: number;
  passing?: number;
  rushing?: number;
  receiving?: number;
  pass_block?: number;
  run_block?: number;
  pass_rush?: number;
  run_defense?: number;
  tackling?: number;
  coverage?: number;
}

export interface PassingStats {
  passer_rating?: number;
  completion_pct?: number;
  big_time_throws?: number;
  big_time_throw_pct?: number;
  turnover_worthy_plays?: number;
  pressure_completion_pct?: number;
  pressure_qb_rating?: number;
  yards?: number;
  touchdowns?: number;
}

export interface RushingStats {
  elusive_rating?: number;
  yards_after_contact?: number;
  yaco_per_attempt?: number;
  breakaway_pct?: number;
  missed_tackles_forced?: number;
  yards?: number;
  touchdowns?: number;
  yards_per_carry?: number;
}

export interface ReceivingStats {
  yards_per_route_run?: number;
  drop_rate?: number;
  contested_catch_rate?: number;
  yards_after_catch?: number;
  targets?: number;
  receptions?: number;
  yards?: number;
  touchdowns?: number;
}

export interface PassRushStats {
  pass_rushing_productivity?: number;
  pass_rush_win_rate?: number;
  pressures?: number;
  sacks?: number;
  hurries?: number;
  hits?: number;
}

export interface CoverageStats {
  passer_rating_allowed?: number;
  yards_per_coverage_snap?: number;
  forced_incompletes?: number;
  interceptions?: number;
  pass_breakups?: number;
  missed_tackle_rate?: number;
}

export interface BlockingStats {
  pass_blocking_efficiency?: number;
  pressures_allowed?: number;
  sacks_allowed?: number;
  run_block_percent?: number;
}

export interface ValueBreakdown {
  position_base: number;
  performance_multiplier: number;
  school_multiplier: number;
  social_value: number;
  potential_value: number;
  starter_bonus: number;
}

export interface DualValuation {
  on3_value: number | null;
  portal_iq_value: number;
  portal_iq_tier: string;
  confidence: string;
  has_on3_data: boolean;
  breakdown: ValueBreakdown | null;
  reasoning: string[];
}

export interface PlayerStats {
  name: string;
  position: string;
  school: string;
  headshot_url?: string;
  season: number;
  nil_value?: number;
  nil_tier?: string;
  stars?: number;
  height?: number;
  weight?: number;
  pff: PFFGrades;
  passing?: PassingStats;
  rushing?: RushingStats;
  receiving?: ReceivingStats;
  pass_rush?: PassRushStats;
  coverage?: CoverageStats;
  blocking?: BlockingStats;
  valuation?: DualValuation;
}

// =============================================================================
// Comparison Types
// =============================================================================

export interface NFLOutcome {
  team?: string;
  seasons_played?: number;
  draft_round?: number;
  draft_pick?: number;
  career_highlights?: string[];
}

export interface MatchingStats {
  [key: string]: {
    target: number;
    comparison: number;
  };
}

export interface PlayerComparison {
  name: string;
  school_or_team: string;
  position: string;
  seasons: number[];
  similarity: number;
  league: "NFL" | "NCAA";
  matching_stats: MatchingStats;
  nfl_outcome?: NFLOutcome;
  headshot_url?: string;
}

export interface PlayerComparisonsResponse {
  player: string;
  position: string;
  nfl_comparisons: PlayerComparison[];
  college_comparisons: PlayerComparison[];
  message?: string;
}

export interface EliteProfile {
  player: string;
  position: string;
  elite_traits: string[];
  elite_trait_count: number;
  elite_bonus: number;
  draft_adjustment: number;
  measurables: {
    height?: number;
    weight?: number;
    forty?: number;
    vertical?: number;
    broad_jump?: number;
    bench?: number;
    three_cone?: number;
    shuttle?: number;
  };
  thresholds: { [key: string]: number };
}

export interface CareerStats {
  player_name: string;
  college_seasons: Record<string, unknown>[];
  nfl_seasons: Record<string, unknown>[];
  combine_data?: Record<string, unknown>;
  total_seasons: number;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Search for players by name across NIL and portal data.
 */
export async function searchPlayers(
  query: string,
  dataType: "nil" | "portal" | "all" = "all",
  limit: number = 25
): Promise<PlayerSearchResponse> {
  const params = new URLSearchParams({
    query,
    data_type: dataType,
    limit: limit.toString(),
  });

  const response = await apiClient.get(`/api/players/search?${params}`);
  return response as unknown as PlayerSearchResponse;
}

/**
 * Get comprehensive stats for a specific player.
 */
export async function getPlayerStats(
  playerName: string,
  season: number = 2025
): Promise<PlayerStats> {
  const encodedName = encodeURIComponent(playerName);
  const response = await apiClient.get(
    `/api/players/${encodedName}/stats?season=${season}`
  );
  return response as unknown as PlayerStats;
}

/**
 * Format height in inches to display string (e.g., 76 -> "6'4\"")
 */
export function formatHeight(inches: number | undefined): string {
  if (!inches) return "-";
  const feet = Math.floor(inches / 12);
  const remainingInches = Math.round(inches % 12);
  return `${feet}'${remainingInches}"`;
}

/**
 * Format NIL value to currency string
 */
export function formatNILValue(value: number | undefined): string {
  if (!value) return "$0";
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `$${Math.round(value / 1000)}K`;
  }
  return `$${value.toLocaleString()}`;
}

/**
 * Get PFF grade color based on value
 */
export function getPFFGradeColor(grade: number | undefined): string {
  if (!grade) return "text-muted-foreground";
  if (grade >= 90) return "text-green-500";
  if (grade >= 80) return "text-emerald-400";
  if (grade >= 70) return "text-yellow-500";
  if (grade >= 60) return "text-orange-500";
  return "text-red-500";
}

/**
 * Get PFF grade label based on value
 */
export function getPFFGradeLabel(grade: number | undefined): string {
  if (!grade) return "N/A";
  if (grade >= 90) return "Elite";
  if (grade >= 80) return "High Quality";
  if (grade >= 70) return "Above Average";
  if (grade >= 60) return "Average";
  if (grade >= 50) return "Below Average";
  return "Poor";
}

/**
 * Get comparable players (NFL and college) for a player.
 */
export async function getPlayerComparisons(
  playerName: string,
  includeNfl: boolean = true,
  includeCollege: boolean = true,
  limit: number = 5
): Promise<PlayerComparisonsResponse> {
  const encodedName = encodeURIComponent(playerName);
  const params = new URLSearchParams({
    include_nfl: includeNfl.toString(),
    include_college: includeCollege.toString(),
    limit: limit.toString(),
  });

  const response = await apiClient.get(
    `/api/players/${encodedName}/comparisons?${params}`
  );
  return response as unknown as PlayerComparisonsResponse;
}

/**
 * Get elite athlete profile with measurables and bonuses.
 */
export async function getPlayerEliteProfile(
  playerName: string
): Promise<EliteProfile> {
  const encodedName = encodeURIComponent(playerName);
  const response = await apiClient.get(
    `/api/players/${encodedName}/elite-profile`
  );
  return response as unknown as EliteProfile;
}

/**
 * Get career stats across multiple seasons.
 */
export async function getPlayerCareer(playerName: string): Promise<CareerStats> {
  const encodedName = encodeURIComponent(playerName);
  const response = await apiClient.get(`/api/players/${encodedName}/career`);
  return response as unknown as CareerStats;
}

/**
 * Get similarity score color based on percentage.
 */
export function getSimilarityColor(similarity: number): string {
  if (similarity >= 90) return "text-green-500";
  if (similarity >= 80) return "text-emerald-400";
  if (similarity >= 70) return "text-yellow-500";
  if (similarity >= 60) return "text-orange-400";
  return "text-muted-foreground";
}

/**
 * Format elite trait name for display.
 */
export function formatEliteTrait(trait: string): string {
  const traitNames: { [key: string]: string } = {
    height: "Height",
    weight: "Weight",
    forty: "40-Yard Dash",
    vertical: "Vertical Jump",
    broad_jump: "Broad Jump",
    bench: "Bench Press",
    three_cone: "3-Cone Drill",
    shuttle: "Shuttle",
    arm_length: "Arm Length",
    hand_size: "Hand Size",
  };
  return traitNames[trait] || trait;
}

// =============================================================================
// Draft Projection Types & API
// =============================================================================

export interface DraftProjection {
  player: string;
  position: string;
  draft_grade: number;
  draft_letter_grade: string;
  projected_round: number | null;
  projected_pick: number;
  pick_range: string;
  draft_probability: number;
  elite_bonus: number;
  elite_traits: string[];
  elite_adjustment: number;
  rookie_contract_estimate: number;
  career_earnings_estimate: number;
  expected_draft_value: number;
}

export interface DraftComparable {
  name: string;
  school: string;
  year: number;
  round: number;
  overall_pick: number;
  nfl_team: string;
  pre_draft_grade: number | null;
  position: string;
}

/**
 * Get draft projection for a player.
 */
export async function getDraftProjection(
  playerName: string
): Promise<DraftProjection> {
  const encodedName = encodeURIComponent(playerName);
  const response = await apiClient.get(
    `/api/draft/project/${encodedName}`
  );
  return response as unknown as DraftProjection;
}

/**
 * Get historical draft comparables for a player.
 */
export async function getDraftComparables(
  playerName: string,
  limit: number = 5
): Promise<DraftComparable[]> {
  const encodedName = encodeURIComponent(playerName);
  const params = new URLSearchParams({ limit: limit.toString() });
  const response = await apiClient.get(
    `/api/draft/comparables/${encodedName}?${params}`
  );
  return (response as unknown as { comparables: DraftComparable[] }).comparables || [];
}

/**
 * Format contract value to display string.
 */
export function formatContractValue(value: number | undefined): string {
  if (!value) return "$0";
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `$${Math.round(value / 1000)}K`;
  }
  return `$${value.toLocaleString()}`;
}

/**
 * Get draft grade color based on letter grade.
 */
export function getDraftGradeColor(grade: string): string {
  if (grade.startsWith("A")) return "text-green-500";
  if (grade.startsWith("B")) return "text-yellow-500";
  if (grade.startsWith("C")) return "text-orange-500";
  return "text-red-500";
}
