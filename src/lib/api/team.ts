import apiClient from "./client";

// =============================================================================
// Team Analysis Types
// =============================================================================

export interface TeamPlayer {
  player_name: string;
  position: string;
  origin_school?: string;
  destination_school?: string;
  stars: number;
  nil_valuation: number;
  war: number;
  status: string;
}

export interface TeamPortalActivity {
  team: string;
  season: number;
  incoming: TeamPlayer[];
  outgoing: TeamPlayer[];
  net_war: number;
  total_nil_invested: number;
  summary: {
    incoming_count: number;
    outgoing_count: number;
    net_count: number;
    incoming_war: number;
    outgoing_war: number;
  };
}

export interface PositionNeed {
  incoming: number;
  outgoing: number;
  net: number;
  need_level: "none" | "low" | "moderate" | "critical";
}

export interface TeamRosterNeeds {
  team: string;
  needs: Record<string, PositionNeed>;
  priority_positions: string[];
  analysis: string;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get team portal activity (incoming/outgoing transfers)
 */
export async function getTeamPortalActivity(
  team: string,
  season: number = 2025
): Promise<TeamPortalActivity> {
  const response = await apiClient.get(`/api/portal/team/${encodeURIComponent(team)}`, {
    params: { season },
  });

  const data = response as unknown as TeamPortalActivity;
  return data;
}

/**
 * Get team roster needs analysis
 */
export async function getTeamRosterNeeds(team: string): Promise<TeamRosterNeeds> {
  const response = await apiClient.get(`/api/roster/${encodeURIComponent(team)}/needs`);
  const data = response as unknown as TeamRosterNeeds;
  return data;
}

/**
 * Get comprehensive team outlook
 */
export async function getTeamOutlook(team: string, season: number = 2025) {
  const [activity, needs] = await Promise.all([
    getTeamPortalActivity(team, season),
    getTeamRosterNeeds(team),
  ]);

  // Calculate grade based on net WAR and needs addressed
  const netWar = activity.net_war;
  const priorityNeeds = needs.priority_positions.length;

  let grade = "C";
  if (netWar >= 5 && priorityNeeds <= 2) grade = "A+";
  else if (netWar >= 3 && priorityNeeds <= 3) grade = "A";
  else if (netWar >= 2 && priorityNeeds <= 4) grade = "B+";
  else if (netWar >= 1) grade = "B";
  else if (netWar >= 0) grade = "C+";
  else if (netWar >= -2) grade = "C";
  else grade = "D";

  return {
    activity,
    needs,
    grade,
    summary: {
      net_war: netWar,
      total_nil: activity.total_nil_invested,
      transfers_in: activity.summary.incoming_count,
      transfers_out: activity.summary.outgoing_count,
      priority_needs: priorityNeeds,
    },
  };
}

// =============================================================================
// School List (for dropdowns)
// =============================================================================

export const SCHOOL_LIST = [
  // SEC
  "Alabama", "Arkansas", "Auburn", "Florida", "Georgia", "Kentucky", "LSU",
  "Mississippi State", "Missouri", "Oklahoma", "Ole Miss", "South Carolina",
  "Tennessee", "Texas", "Texas A&M", "Vanderbilt",
  // Big Ten
  "Illinois", "Indiana", "Iowa", "Maryland", "Michigan", "Michigan State",
  "Minnesota", "Nebraska", "Northwestern", "Ohio State", "Oregon", "Penn State",
  "Purdue", "Rutgers", "UCLA", "USC", "Washington", "Wisconsin",
  // ACC
  "Boston College", "California", "Clemson", "Duke", "Florida State",
  "Georgia Tech", "Louisville", "Miami", "NC State", "North Carolina",
  "Notre Dame", "Pittsburgh", "SMU", "Stanford", "Syracuse", "Virginia",
  "Virginia Tech", "Wake Forest",
  // Big 12
  "Arizona", "Arizona State", "Baylor", "BYU", "Cincinnati", "Colorado",
  "Houston", "Iowa State", "Kansas", "Kansas State", "Oklahoma State", "TCU",
  "Texas Tech", "UCF", "Utah", "West Virginia",
  // AAC
  "Army", "Charlotte", "East Carolina", "FAU", "Memphis", "Navy",
  "North Texas", "Rice", "South Florida", "Temple", "Tulane", "Tulsa",
  "UAB", "UTSA",
  // Sun Belt
  "App State", "Arkansas State", "Coastal Carolina", "Georgia Southern",
  "Georgia State", "James Madison", "Louisiana", "Marshall", "Old Dominion",
  "South Alabama", "Southern Miss", "Texas State", "Troy", "UL Monroe",
  // Mountain West
  "Air Force", "Boise State", "Colorado State", "Fresno State", "Hawaii",
  "Nevada", "New Mexico", "San Diego State", "San Jose State", "UNLV",
  "Utah State", "Wyoming",
  // MAC
  "Akron", "Ball State", "Bowling Green", "Buffalo", "Central Michigan",
  "Eastern Michigan", "Kent State", "Miami (OH)", "Northern Illinois",
  "Ohio", "Toledo", "Western Michigan",
  // C-USA
  "FIU", "Jacksonville State", "Kennesaw State", "Liberty", "Louisiana Tech",
  "Middle Tennessee", "New Mexico State", "Sam Houston", "UTEP", "Western Kentucky",
  // Independents
  "Connecticut", "UMass",
].sort();
