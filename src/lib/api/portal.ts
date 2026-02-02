import apiClient from "./client";
import type { PlayerInput } from "./nil";
import type { FlightRisk, PortalFit, RiskLevel } from "@/types";

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

// API Functions
export async function getFlightRisk(
  player: PlayerInput,
  teamContext?: FlightRiskRequest["team_context"]
): Promise<FlightRisk> {
  const response = await apiClient.post("/api/portal/flight-risk", {
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
