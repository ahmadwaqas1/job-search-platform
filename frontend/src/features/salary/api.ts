import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import type { SalarySnapshot } from "@/api/types";

export function useSalaryInsights(role: string, location: string) {
  return useQuery({
    queryKey: ["salary", role, location],
    queryFn: async () =>
      (await apiClient.get<SalarySnapshot[]>("/salary", { params: { role, location } })).data,
    enabled: !!role,
  });
}

export function useSalarySuggestions() {
  return useQuery({
    queryKey: ["salary-suggestions"],
    queryFn: async () =>
      (await apiClient.get<{ roles: string[]; locations: string[] }>("/salary/suggestions")).data,
  });
}
