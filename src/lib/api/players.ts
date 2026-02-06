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
