import apiClient from "./client";
import type {
  PlayerProfile,
  PlayerStats,
  SocialMedia,
  Recruiting,
  NILValuation,
  TransferImpact,
} from "@/types";

// =============================================================================
// NIL Leaderboard Types (Real Data)
// =============================================================================

export interface NILLeaderboardPlayer {
  rank: number;
  player_id: string;
  player_name: string;
  position: string;
  school: string;
  conference?: string | null;
  valuation: number;
  on3_value?: number | null;
  nil_tier: string;
  valuation_source?: string;
  social_followers?: number;
  headshot_url?: string;
  stars?: number | null;
  height?: number | null;
  weight?: number | null;
  pff_overall?: number | null;
  pff_offense?: number | null;
  pff_defense?: number | null;
  change?: number;
}

export interface NILLeaderboardResponse {
  players: NILLeaderboardPlayer[];
  total: number;
  total_count: number;  // Total matching players in database
  avg_value: number;    // Average NIL value across all filtered players
  market_cap: number;   // Sum of all NIL values across all filtered players
  offset: number;
  limit: number;
  has_more: boolean;
  filters_applied: Record<string, string | null>;
}

export interface NILLeaderboardParams {
  position?: string;
  school?: string;
  conference?: string;
  search?: string;  // Search player names
  limit?: number;
  offset?: number;  // For pagination
}

// Player search types
export interface PlayerSearchResult {
  player_id: string;
  player_name: string;
  position: string;
  school: string;
  valuation?: number;
  nil_tier?: string;
  headshot_url?: string;
  source: "nil" | "portal";
  destination_school?: string;
  status?: string;
  stars?: number;
}

export interface PlayerSearchResponse {
  players: PlayerSearchResult[];
  total: number;
  query: string;
  data_type: string;
}

export interface PlayerSearchParams {
  query: string;
  data_type?: "nil" | "portal" | "all";
  limit?: number;
}

// Request types
export interface PlayerInput {
  name: string;
  school: string;
  position: string;
  class_year?: string;
  eligibility_remaining?: number;
  overall_rating?: number;
  is_starter?: boolean;
  stats?: PlayerStats;
  social_media?: SocialMedia;
  recruiting?: Recruiting;
  measurables?: Record<string, number>;
}

export interface NILPredictRequest {
  player: PlayerInput;
}

export interface TransferImpactRequest {
  player: PlayerInput;
  target_school: string;
}

export interface MarketReportRequest {
  position?: string;
  conference?: string;
}

// Response types
export interface MarketReport {
  filters_applied: Record<string, string>;
  total_players: number;
  average_value: number;
  median_value: number;
  total_market_value: number;
  value_by_tier: Record<string, { count: number; avg_value: number }>;
  top_players: Array<{
    name: string;
    school: string;
    position: string;
    value: number;
  }>;
  market_trends: string[];
}

// =============================================================================
// NIL Leaderboard API (Real Data)
// =============================================================================

/**
 * Get NIL leaderboard with real data from the API.
 * This fetches actual player valuations from our proprietary ML models.
 * Supports pagination with offset/limit and full-text search.
 */
export async function getNILLeaderboard(
  params?: NILLeaderboardParams
): Promise<NILLeaderboardResponse> {
  const searchParams = new URLSearchParams();
  if (params?.position) searchParams.set("position", params.position);
  if (params?.school) searchParams.set("school", params.school);
  if (params?.conference) searchParams.set("conference", params.conference);
  if (params?.search) searchParams.set("search", params.search);
  if (params?.limit) searchParams.set("limit", params.limit.toString());
  if (params?.offset) searchParams.set("offset", params.offset.toString());

  const queryString = searchParams.toString();
  const url = queryString ? `/api/nil/leaderboard?${queryString}` : "/api/nil/leaderboard";

  const response = await apiClient.get(url);
  return response as unknown as NILLeaderboardResponse;
}

/**
 * Search players across all data (NIL and portal).
 * Returns quick results for autocomplete and search functionality.
 */
export async function searchPlayers(
  params: PlayerSearchParams
): Promise<PlayerSearchResponse> {
  const searchParams = new URLSearchParams();
  searchParams.set("query", params.query);
  if (params.data_type) searchParams.set("data_type", params.data_type);
  if (params.limit) searchParams.set("limit", params.limit.toString());

  const response = await apiClient.get(`/api/players/search?${searchParams.toString()}`);
  return response as unknown as PlayerSearchResponse;
}

/**
 * Get detailed stats for a specific player.
 */
export async function getPlayerStats(playerName: string): Promise<{
  profile?: {
    name: string;
    position: string;
    school: string;
    conference?: string;
    headshot_url?: string;
    height?: number;
    weight?: number;
    stars?: number;
  };
  nil?: {
    valuation: number;
    tier: string;
    valuation_source?: string;
  };
  pff?: Record<string, number | null>;
  portal?: {
    status: string;
    origin_school: string;
    destination_school?: string;
    entry_date?: string;
  };
}> {
  const response = await apiClient.get(`/api/players/${encodeURIComponent(playerName)}/stats`);
  return response as unknown as ReturnType<typeof getPlayerStats>;
}

/**
 * Get NIL tier definitions and thresholds.
 */
export async function getNILTiers(): Promise<Record<string, { min: number; label: string }>> {
  const response = await apiClient.get("/api/nil/tiers");
  return response as unknown as Record<string, { min: number; label: string }>;
}

// =============================================================================
// Custom NIL Valuation API
// =============================================================================

// API Functions
export async function predictNIL(player: PlayerInput): Promise<NILValuation> {
  const response = await apiClient.post("/api/nil/predict", { player });
  return response as unknown as NILValuation;
}

export async function getTransferImpact(
  player: PlayerInput,
  targetSchool: string
): Promise<TransferImpact> {
  const response = await apiClient.post("/api/nil/transfer-impact", {
    player,
    target_school: targetSchool,
  });
  return response as unknown as TransferImpact;
}

export async function getMarketReport(
  options?: MarketReportRequest
): Promise<MarketReport> {
  const response = await apiClient.post("/api/nil/market-report", options || {});
  return response as unknown as MarketReport;
}

// Helper to build player input from form data
export function buildPlayerInput(formData: {
  name: string;
  school: string;
  position: string;
  classYear?: string;
  stars?: string;
  overallRating?: string;
  instagramFollowers?: string;
  twitterFollowers?: string;
}): PlayerInput {
  return {
    name: formData.name,
    school: formData.school,
    position: formData.position,
    class_year: formData.classYear,
    overall_rating: formData.overallRating
      ? parseFloat(formData.overallRating)
      : undefined,
    social_media: {
      instagram_followers: formData.instagramFollowers
        ? parseInt(formData.instagramFollowers)
        : undefined,
      twitter_followers: formData.twitterFollowers
        ? parseInt(formData.twitterFollowers)
        : undefined,
    },
    recruiting: {
      stars: formData.stars ? parseInt(formData.stars) : undefined,
    },
  };
}
