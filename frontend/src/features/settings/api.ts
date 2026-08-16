import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import type { EffectiveSettings } from "@/api/types";

export function useEffectiveSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: async () => (await apiClient.get<EffectiveSettings>("/settings")).data,
  });
}
