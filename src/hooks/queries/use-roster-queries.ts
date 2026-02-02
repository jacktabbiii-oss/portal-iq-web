import { useQuery, useMutation } from "@tanstack/react-query";
import {
  optimizeRoster,
  analyzeScenario,
  getRosterReport,
  type RosterOptimizeRequest,
  type ScenarioRequest,
} from "@/lib/api/roster";

// Query keys
export const rosterKeys = {
  all: ["roster"] as const,
  optimization: (school: string) =>
    [...rosterKeys.all, "optimization", school] as const,
  scenario: (school: string) =>
    [...rosterKeys.all, "scenario", school] as const,
  report: (school: string) =>
    [...rosterKeys.all, "report", school] as const,
};

// Roster optimization mutation
export function useRosterOptimization() {
  return useMutation({
    mutationFn: (request: RosterOptimizeRequest) => optimizeRoster(request),
  });
}

// Scenario analysis mutation
export function useScenarioAnalysis() {
  return useMutation({
    mutationFn: (request: ScenarioRequest) => analyzeScenario(request),
  });
}

// Roster report query
export function useRosterReport(school: string | undefined) {
  return useQuery({
    queryKey: rosterKeys.report(school || ""),
    queryFn: () => getRosterReport(school!),
    enabled: !!school,
    staleTime: 5 * 60 * 1000,
  });
}
