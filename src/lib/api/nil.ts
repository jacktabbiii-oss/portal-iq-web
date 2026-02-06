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
  valuation: number;
  nil_tier: string;
  social_followers?: number;
  headshot_url?: string;
  change?: number;
}

export interface NILLeaderboardResponse {
  players: NILLeaderboardPlayer[];
  total: number;
}

export interface NILLeaderboardParams {
  position?: string;
  school?: string;
  conference?: string;
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
 * This fetches actual player valuations from On3 and proprietary models.
 */
export async function getNILLeaderboard(
  params?: NILLeaderboardParams
): Promise<NILLeaderboardResponse> {
  const searchParams = new URLSearchParams();
  if (params?.position) searchParams.set("position", params.position);
  if (params?.school) searchParams.set("school", params.school);
  if (params?.conference) searchParams.set("conference", params.conference);
  if (params?.limit) searchParams.set("limit", params.limit.toString());

  const queryString = searchParams.toString();
  const url = queryString ? `/api/portal-iq/nil/leaderboard?${queryString}` : "/api/portal-iq/nil/leaderboard";

  const response = await apiClient.get(url);
  return response as unknown as NILLeaderboardResponse;
}

/**
 * Get NIL tier definitions and thresholds.
 */
export async function getNILTiers(): Promise<Record<string, { min: number; label: string }>> {
  const response = await apiClient.get("/api/portal-iq/nil/tiers");
  return response as unknown as Record<string, { min: number; label: string }>;
}

// =============================================================================
// Custom NIL Valuation API
// =============================================================================

// API Functions
export async function predictNIL(player: PlayerInput): Promise<NILValuation> {
  const response = await apiClient.post("/api/portal-iq/nil/valuate", { player });
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
