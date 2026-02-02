import apiClient from "./client";
import type {
  PlayerProfile,
  PlayerStats,
  SocialMedia,
  Recruiting,
  NILValuation,
  TransferImpact,
} from "@/types";

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
