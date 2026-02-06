import apiClient from "./client";

// =============================================================================
// AI Search Types
// =============================================================================

export interface SearchRequest {
  query: string;
  context?: string;
}

export interface SearchResponse {
  response: string;
  sources?: string[];
  players_mentioned?: string[];
  data_used?: string[];
}

export interface SearchStatusResponse {
  available: boolean;
  anthropic_configured: boolean;
  datasets_loaded: number;
  datasets: Record<string, { loaded: boolean; records: number }>;
}

// =============================================================================
// AI Search API
// =============================================================================

/**
 * Send a query to the AI search endpoint
 */
export async function searchAI(query: string, context?: string): Promise<SearchResponse> {
  const response = await apiClient.post("/api/search", {
    query,
    context,
  });

  return response as unknown as SearchResponse;
}

/**
 * Check AI search status and available datasets
 */
export async function getSearchStatus(): Promise<SearchStatusResponse> {
  const response = await apiClient.get("/api/search/status");
  return response as unknown as SearchStatusResponse;
}
