import apiClient from "./client";
import type { PlayerInput } from "./nil";
import type { DraftProjection, DraftGrade } from "@/types";

// Request types
export interface DraftProjectRequest {
  player: PlayerInput;
}

export interface MockDraftRequest {
  season_year: number;
  num_rounds?: number;
}

// Response types
export interface MockDraftPick {
  pick: number;
  round: number;
  player: string;
  position: string;
  school: string;
  grade: string;
}

export interface MockDraft {
  season_year: number;
  num_rounds: number;
  total_picks: number;
  draft_board: MockDraftPick[];
  position_distribution: Record<string, number>;
  top_prospects_by_position: Record<string, Array<{ name: string; grade: string }>>;
  generated_at: string;
}

// API Functions
export async function getDraftProjection(
  player: PlayerInput
): Promise<DraftProjection> {
  const response = await apiClient.post("/api/draft/project", { player });
  return response as unknown as DraftProjection;
}

export async function getMockDraft(
  seasonYear: number,
  numRounds: number = 3
): Promise<MockDraft> {
  const response = await apiClient.post("/api/draft/mock", {
    season_year: seasonYear,
    num_rounds: numRounds,
  });
  return response as unknown as MockDraft;
}
