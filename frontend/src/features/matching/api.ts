import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import type { Match } from "@/api/types";

export function useMatches(minScore?: number) {
  return useQuery({
    queryKey: ["matches", minScore],
    queryFn: async () =>
      (await apiClient.get<Match[]>("/matches", { params: minScore ? { min_score: minScore } : {} })).data,
  });
}

export function useMatch(jobPostingId: string | undefined) {
  return useQuery({
    queryKey: ["match", jobPostingId],
    queryFn: async () => (await apiClient.get<Match | null>(`/matches/${jobPostingId}`)).data,
    enabled: !!jobPostingId,
  });
}

export function useRefreshMatches() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => apiClient.post("/matches/refresh"),
    onSuccess: () => {
      // Matching runs in the background; give it a moment before refetching.
      setTimeout(() => qc.invalidateQueries({ queryKey: ["matches"] }), 4000);
    },
  });
}
