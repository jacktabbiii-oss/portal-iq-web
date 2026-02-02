import { useQuery, useMutation } from "@tanstack/react-query";
import {
  getFlightRisk,
  getTeamReport,
  getPortalFit,
  getPortalRecommendations,
  type FlightRiskRequest,
  type PortalRecommendationsRequest,
} from "@/lib/api/portal";
import type { PlayerInput } from "@/lib/api/nil";

// Query keys
export const portalKeys = {
  all: ["portal"] as const,
  flightRisk: (player: PlayerInput) =>
    [...portalKeys.all, "flight-risk", player.name, player.school] as const,
  teamReport: (school: string) =>
    [...portalKeys.all, "team-report", school] as const,
  fit: (player: PlayerInput, targetSchool: string) =>
    [...portalKeys.all, "fit", player.name, targetSchool] as const,
  recommendations: (school: string) =>
    [...portalKeys.all, "recommendations", school] as const,
};

// Flight risk mutation
export function useFlightRisk() {
  return useMutation({
    mutationFn: ({
      player,
      teamContext,
    }: {
      player: PlayerInput;
      teamContext?: FlightRiskRequest["team_context"];
    }) => getFlightRisk(player, teamContext),
  });
}

// Team flight risk report query
export function useTeamReport(school: string | undefined) {
  return useQuery({
    queryKey: portalKeys.teamReport(school || ""),
    queryFn: () => getTeamReport(school!),
    enabled: !!school,
    staleTime: 5 * 60 * 1000,
  });
}

// Portal fit mutation
export function usePortalFit() {
  return useMutation({
    mutationFn: ({
      player,
      targetSchool,
    }: {
      player: PlayerInput;
      targetSchool: string;
    }) => getPortalFit(player, targetSchool),
  });
}

// Portal recommendations query
export function usePortalRecommendations(
  request: PortalRecommendationsRequest | undefined
) {
  return useQuery({
    queryKey: portalKeys.recommendations(request?.school || ""),
    queryFn: () => getPortalRecommendations(request!),
    enabled: !!request?.school && !!request?.budget,
    staleTime: 5 * 60 * 1000,
  });
}
