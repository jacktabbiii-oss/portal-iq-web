// Player types
export interface PlayerProfile {
  id?: string;
  name: string;
  school: string;
  position: string;
  class_year?: string;
  eligibility_remaining?: number;
  hometown?: string;
  state?: string;
  overall_rating?: number;
  is_starter?: boolean;
}

export interface PlayerStats {
  games_played?: number;
  games_started?: number;
  passing_yards?: number;
  passing_tds?: number;
  interceptions?: number;
  completion_pct?: number;
  qbr?: number;
  rushing_yards?: number;
  rushing_tds?: number;
  receiving_yards?: number;
  receiving_tds?: number;
  receptions?: number;
  tackles?: number;
  sacks?: number;
  pff_grade?: number;
}

export interface SocialMedia {
  instagram_followers?: number;
  twitter_followers?: number;
  tiktok_followers?: number;
  total_followers?: number;
  engagement_rate?: number;
}

export interface Recruiting {
  stars?: number;
  national_rank?: number;
  position_rank?: number;
  state_rank?: number;
}

// NIL types
export type NILTier = "mega" | "premium" | "solid" | "moderate" | "entry";

export interface NILValuation {
  player_name: string;
  school: string;
  position: string;
  predicted_value: number;
  value_tier: NILTier;
  tier_probabilities?: Record<NILTier, number>;
  confidence: number;
  value_breakdown?: {
    base_value: number;
    social_media_premium: number;
    school_brand_factor: number;
    position_market_factor: number;
    draft_potential_premium: number;
  };
  comparable_players?: Array<{
    name: string;
    school: string;
    value: number;
  }>;
  percentile?: number;
}

export interface TransferImpact {
  player_name: string;
  current_school: string;
  target_school: string;
  current_value: number;
  projected_value: number;
  value_change: number;
  value_change_pct: number;
  factors?: Record<string, string>;
  recommendation?: string;
}

// Portal types
export type RiskLevel = "critical" | "high" | "moderate" | "low";

export interface FlightRisk {
  player_name: string;
  school: string;
  flight_risk_probability: number;
  risk_level: RiskLevel;
  risk_factors?: Array<{
    factor: string;
    impact: number;
  }>;
  retention_recommendations?: string[];
  estimated_replacement_cost?: number;
}

export interface PortalPlayer {
  id: string;
  name: string;
  position: string;
  origin_school: string;
  destination_school?: string;
  stars: number;
  overall_rating: number;
  nil_estimate?: number;
  entry_date: string;
  status: "active" | "committed" | "withdrawn";
}

export interface PortalFit {
  player_name: string;
  target_school: string;
  fit_score: number;
  fit_grade: string;
  projected_nil: number;
  projected_role: string;
  fit_breakdown?: {
    positional_need: number;
    production_upgrade: number;
    tier_match: number;
    nil_budget_fit: number;
    geographic_proximity: number;
    scheme_fit: number;
  };
  strengths?: string[];
  concerns?: string[];
}

// Draft types
export type DraftGrade = "A+" | "A" | "A-" | "B+" | "B" | "B-" | "C+" | "C" | "C-" | "D" | "F";

export interface DraftProjection {
  player_name: string;
  position: string;
  draft_eligible: boolean;
  projected_round: number;
  projected_pick_range: string;
  draft_probability: number;
  draft_grade: DraftGrade;
  expected_draft_value?: number;
  rookie_contract_estimate?: number;
  career_earnings_estimate?: number;
  strengths?: string[];
  weaknesses?: string[];
  comparable_prospects?: Array<{
    name: string;
    draft_position: number;
  }>;
  stock_trend: "rising" | "stable" | "falling";
}

// Roster types
export interface RosterPlayer {
  id: string;
  name: string;
  position: string;
  class_year: string;
  overall_rating: number;
  nil_value: number;
  flight_risk?: number;
  is_starter: boolean;
  stars?: number;
}

export interface RosterOptimization {
  school: string;
  total_budget: number;
  total_allocated: number;
  budget_remaining: number;
  expected_wins: number;
  optimization_status: string;
  allocations: Array<{
    player: string;
    position: string;
    recommended_nil: number;
    current_nil?: number;
  }>;
  position_breakdown: Record<string, number>;
  retention_priorities: string[];
  efficiency_score: number;
}

export interface ScenarioAnalysis {
  school: string;
  changes_analyzed: number;
  current_projected_wins: number;
  new_projected_wins: number;
  win_delta: number;
  total_nil_cost: number;
  cost_per_win: number;
  position_impacts: Record<string, number>;
  recommendation: string;
  risks: string[];
}

// Utility types
export interface SelectOption {
  value: string;
  label: string;
}

export interface FilterState {
  position?: string;
  conference?: string;
  school?: string;
  tier?: NILTier;
  riskLevel?: RiskLevel;
  minStars?: number;
  maxStars?: number;
  search?: string;
}
