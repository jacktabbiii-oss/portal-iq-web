import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  predictNIL,
  getTransferImpact,
  getMarketReport,
  type PlayerInput,
  type MarketReportRequest,
} from "@/lib/api/nil";

// Query keys
export const nilKeys = {
  all: ["nil"] as const,
  predictions: () => [...nilKeys.all, "predictions"] as const,
  prediction: (player: PlayerInput) =>
    [...nilKeys.predictions(), player.name, player.school] as const,
  transferImpact: (player: PlayerInput, targetSchool: string) =>
    [...nilKeys.all, "transfer-impact", player.name, targetSchool] as const,
  marketReport: (filters?: MarketReportRequest) =>
    [...nilKeys.all, "market-report", filters] as const,
};

// Predict NIL value mutation (use mutation since it's a POST with dynamic data)
export function useNILPrediction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (player: PlayerInput) => predictNIL(player),
    onSuccess: (data, player) => {
      // Cache the result
      queryClient.setQueryData(nilKeys.prediction(player), data);
    },
  });
}

// Transfer impact mutation
export function useTransferImpact() {
  return useMutation({
    mutationFn: ({
      player,
      targetSchool,
    }: {
      player: PlayerInput;
      targetSchool: string;
    }) => getTransferImpact(player, targetSchool),
  });
}

// Market report query (can be cached since filters are known)
export function useMarketReport(filters?: MarketReportRequest) {
  return useQuery({
    queryKey: nilKeys.marketReport(filters),
    queryFn: () => getMarketReport(filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
