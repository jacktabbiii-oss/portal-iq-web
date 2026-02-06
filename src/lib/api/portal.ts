import apiClient from "./client";
import type { PlayerInput } from "./nil";
import type { FlightRisk, PortalFit, RiskLevel } from "@/types";

// =============================================================================
// Portal Players Types (Real Data)
// =============================================================================

export interface PortalPlayer {
  player_id: string;
  player_name: string;
  position: string;
  origin_school: string;
  origin_conference?: string;
  destination_school?: string;
  stars?: number;
  entry_date?: string;
  status: "available" | "committed" | "withdrawn";
  nil_valuation?: number;
  days_in_portal?: number;
  headshot_url?: string;
}

export interface PortalPlayersParams {
  position?: string;
  origin_school?: string;
  origin_conference?: string;
  min_stars?: number;
  status?: "available" | "committed" | "all";
  search?: string;  // Search player names
  limit?: number;
  offset?: number;  // For pagination
}

// Request types
export interface FlightRiskRequest {
  player: PlayerInput;
  team_context?: {
    recent_coaching_change?: boolean;
    scheme_change?: boolean;
    nil_budget?: number;
  };
}

export interface TeamReportRequest {
  school: string;
  include_scholarship_players_only?: boolean;
}

export interface PortalFitRequest {
  player: PlayerInput;
  target_school: string;
}

export interface PortalRecommendationsRequest {
  school: string;
  budget: number;
  positions_of_need?: string[];
  max_targets?: number;
}

// Response types
export interface TeamReport {
  school: string;
  analysis_date: string;
  total_roster_size: number;
  total_at_risk: number;
  critical_risk_players: Array<{
    name: string;
    position: string;
    risk: number;
    nil_value: number;
  }>;
  high_risk_players: Array<{
    name: string;
    position: string;
    risk: number;
    nil_value: number;
  }>;
  estimated_wins_at_risk: number;
  total_retention_budget_needed: number;
  position_vulnerability: Record<string, { count: number; avg_risk: number }>;
  recommendations: string[];
}

export interface PortalTarget {
  name: string;
  position: string;
  origin_school: string;
  projected_nil: number;
  fit_score: number;
  win_impact: number;
  value_rating: number;
}

export interface PortalRecommendations {
  school: string;
  budget: number;
  targets: PortalTarget[];
  positions_prioritized: string[];
  budget_allocation_suggestion: Record<string, number>;
  projected_roster_improvement: number;
  acquisition_strategy: string;
}

// =============================================================================
// Portal Players API (Real Data)
// =============================================================================

export interface PortalPlayersResponse {
  players: PortalPlayer[];
  total: number;
  total_count: number;  // Total matching players in database
  offset: number;
  limit: number;
  has_more: boolean;
  filters_applied: Record<string, string | null>;
}

/**
 * Get active transfer portal players with real data from the API.
 * This fetches actual player data from On3 transfer portal.
 * Supports pagination with offset/limit and full-text search.
 */
export async function getActivePortalPlayers(
  params?: PortalPlayersParams
): Promise<PortalPlayersResponse> {
  const searchParams = new URLSearchParams();
  if (params?.position) searchParams.set("position", params.position);
  if (params?.origin_school) searchParams.set("origin_school", params.origin_school);
  if (params?.origin_conference) searchParams.set("origin_conference", params.origin_conference);
  if (params?.min_stars) searchParams.set("min_stars", params.min_stars.toString());
  if (params?.status) searchParams.set("status", params.status);
  if (params?.search) searchParams.set("search", params.search);
  if (params?.limit) searchParams.set("limit", params.limit.toString());
  if (params?.offset) searchParams.set("offset", params.offset.toString());

  const queryString = searchParams.toString();
  const url = queryString ? `/api/portal/active?${queryString}` : "/api/portal/active";

  const response = await apiClient.get(url);
  // Response interceptor extracts data.data, which contains { players: [...], total: N, total_count: N, ... }
  const data = response as unknown as PortalPlayersResponse;
  return {
    players: data.players || [],
    total: data.total || 0,
    total_count: data.total_count || data.total || 0,
    offset: data.offset || 0,
    limit: data.limit || 200,
    has_more: data.has_more || false,
    filters_applied: data.filters_applied || {},
  };
}

/**
 * Get team portal activity (incoming/outgoing transfers).
 */
export async function getTeamPortalActivity(
  team: string,
  season: number = 2026
): Promise<{
  team: string;
  season: number;
  incoming: PortalPlayer[];
  outgoing: PortalPlayer[];
  net_talent_change: number;
}> {
  const response = await apiClient.get(`/api/portal/team/${encodeURIComponent(team)}?season=${season}`);
  return response as unknown as {
    team: string;
    season: number;
    incoming: PortalPlayer[];
    outgoing: PortalPlayer[];
    net_talent_change: number;
  };
}

// =============================================================================
// Portal Analysis API
// =============================================================================

// API Functions
export async function getFlightRisk(
  player: PlayerInput,
  teamContext?: FlightRiskRequest["team_context"]
): Promise<FlightRisk> {
  const response = await apiClient.post("/api/portal/at-risk", {
    player,
    team_context: teamContext,
  });
  return response as unknown as FlightRisk;
}

export async function getTeamReport(school: string): Promise<TeamReport> {
  const response = await apiClient.post("/api/portal/team-report", { school });
  return response as unknown as TeamReport;
}

export async function getPortalFit(
  player: PlayerInput,
  targetSchool: string
): Promise<PortalFit> {
  const response = await apiClient.post("/api/portal/fit-score", {
    player,
    target_school: targetSchool,
  });
  return response as unknown as PortalFit;
}

export async function getPortalRecommendations(
  request: PortalRecommendationsRequest
): Promise<PortalRecommendations> {
  const response = await apiClient.post("/api/portal/recommendations", request);
  return response as unknown as PortalRecommendations;
}
