import { useQuery, useMutation } from "@tanstack/react-query";
import { getDraftProjection, getMockDraft } from "@/lib/api/draft";
import type { PlayerInput } from "@/lib/api/nil";

// Query keys
export const draftKeys = {
  all: ["draft"] as const,
  projection: (player: PlayerInput) =>
    [...draftKeys.all, "projection", player.name, player.school] as const,
  mockDraft: (year: number, rounds: number) =>
    [...draftKeys.all, "mock", year, rounds] as const,
};

// Draft projection mutation
export function useDraftProjection() {
  return useMutation({
    mutationFn: (player: PlayerInput) => getDraftProjection(player),
  });
}

// Mock draft query
export function useMockDraft(seasonYear: number, numRounds: number = 3) {
  return useQuery({
    queryKey: draftKeys.mockDraft(seasonYear, numRounds),
    queryFn: () => getMockDraft(seasonYear, numRounds),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}
