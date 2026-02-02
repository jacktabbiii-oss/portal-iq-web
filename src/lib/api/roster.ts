import apiClient from "./client";
import type { RosterOptimization, ScenarioAnalysis } from "@/types";

// Request types
export interface RosterOptimizeRequest {
  school: string;
  total_budget: number;
  win_target?: number;
}

export interface ScenarioChange {
  name: string;
  position: string;
  action: "add" | "remove";
  overall_rating: number;
  nil_cost?: number;
}

export interface ScenarioRequest {
  school: string;
  changes: ScenarioChange[];
}

// Response types
export interface RosterReport {
  school: string;
  school_tier: string;
  generated_at: string;
  executive_summary: string[];
  roster_summary: Record<string, unknown>;
  nil_optimization: Record<string, unknown>;
  portal_shopping: Record<string, unknown>;
  flight_risk: Record<string, unknown>;
  win_projection: Record<string, unknown>;
  gap_analysis: Record<string, unknown>;
  output_files: Record<string, string>;
}

// API Functions
export async function optimizeRoster(
  request: RosterOptimizeRequest
): Promise<RosterOptimization> {
  const response = await apiClient.post("/api/roster/optimize", request);
  return response as unknown as RosterOptimization;
}

export async function analyzeScenario(
  request: ScenarioRequest
): Promise<ScenarioAnalysis> {
  const response = await apiClient.post("/api/roster/scenario", request);
  return response as unknown as ScenarioAnalysis;
}

export async function getRosterReport(school: string): Promise<RosterReport> {
  const response = await apiClient.get(`/api/roster/${encodeURIComponent(school)}/report`);
  return response as unknown as RosterReport;
}
