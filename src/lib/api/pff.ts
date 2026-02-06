import apiClient from "./client";

// =============================================================================
// PFF Stats Types
// =============================================================================

export type PFFCategory =
  | "passing"
  | "rushing"
  | "receiving"
  | "defense"
  | "pass_rush"
  | "blocking"
  | "special";

export interface PFFPlayer {
  player?: string;
  name?: string;
  team?: string;
  position?: string;
  season: number;
  [key: string]: unknown; // Dynamic stats columns
}

export interface PFFStatsResponse {
  players: PFFPlayer[];
  total: number;
  category: string;
  season: number;
}

// =============================================================================
// Reference Data Types
// =============================================================================

export interface PositionPreset {
  min: number;
  ideal_min?: number;
  max?: number;
  tall?: number;
  label: string;
}

export interface PositionPresetsResponse {
  height: Record<string, PositionPreset>;
  weight: Record<string, PositionPreset>;
}

// =============================================================================
// API Functions
// =============================================================================

/**
 * Get PFF stats for a specific category.
 */
export async function getPFFStats(
  category: PFFCategory,
  season: number = 2025,
  limit: number = 100
): Promise<PFFStatsResponse> {
  const params = new URLSearchParams({
    season: season.toString(),
    limit: limit.toString(),
  });

  const response = await apiClient.get(`/api/pff/${category}?${params}`);
  return response as unknown as PFFStatsResponse;
}

/**
 * Get QB passing stats from PFF.
 */
export async function getPassingStats(
  season: number = 2025,
  limit: number = 100
): Promise<PFFStatsResponse> {
  return getPFFStats("passing", season, limit);
}

/**
 * Get RB rushing stats from PFF.
 */
export async function getRushingStats(
  season: number = 2025,
  limit: number = 100
): Promise<PFFStatsResponse> {
  return getPFFStats("rushing", season, limit);
}

/**
 * Get WR/TE receiving stats from PFF.
 */
export async function getReceivingStats(
  season: number = 2025,
  limit: number = 100
): Promise<PFFStatsResponse> {
  return getPFFStats("receiving", season, limit);
}

/**
 * Get defensive stats from PFF.
 */
export async function getDefenseStats(
  season: number = 2025,
  limit: number = 100
): Promise<PFFStatsResponse> {
  return getPFFStats("defense", season, limit);
}

/**
 * Get pass rush stats from PFF.
 */
export async function getPassRushStats(
  season: number = 2025,
  limit: number = 100
): Promise<PFFStatsResponse> {
  return getPFFStats("pass_rush", season, limit);
}

/**
 * Get O-line blocking stats from PFF.
 */
export async function getBlockingStats(
  season: number = 2025,
  limit: number = 100
): Promise<PFFStatsResponse> {
  return getPFFStats("blocking", season, limit);
}

// =============================================================================
// Reference Data Functions
// =============================================================================

/**
 * Get list of valid positions.
 */
export async function getPositions(): Promise<string[]> {
  const response = await apiClient.get("/api/reference/positions");
  const data = response as unknown as { positions: string[] };
  return data.positions;
}

/**
 * Get list of conferences.
 */
export async function getConferences(): Promise<string[]> {
  const response = await apiClient.get("/api/reference/conferences");
  const data = response as unknown as { conferences: string[] };
  return data.conferences;
}

/**
 * Get list of schools.
 */
export async function getSchools(): Promise<string[]> {
  const response = await apiClient.get("/api/reference/schools");
  const data = response as unknown as { schools: string[] };
  return data.schools;
}

/**
 * Get position presets for height and weight.
 */
export async function getPositionPresets(): Promise<PositionPresetsResponse> {
  const response = await apiClient.get("/api/reference/presets");
  return response as unknown as PositionPresetsResponse;
}
