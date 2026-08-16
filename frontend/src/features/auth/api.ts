import { useMutation, useQuery } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import type { User } from "@/api/types";
import { useAuthStore } from "@/store/authStore";

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export function useRegister() {
  const setToken = useAuthStore((s) => s.setToken);
  return useMutation({
    mutationFn: async (payload: { email: string; password: string }) => {
      const { data } = await apiClient.post<TokenResponse>("/auth/register", payload);
      return data;
    },
    onSuccess: (data) => setToken(data.access_token),
  });
}

export function useLogin() {
  const setToken = useAuthStore((s) => s.setToken);
  return useMutation({
    mutationFn: async (payload: { email: string; password: string }) => {
      const { data } = await apiClient.post<TokenResponse>("/auth/login", payload);
      return data;
    },
    onSuccess: (data) => setToken(data.access_token),
  });
}

export function useMe() {
  const token = useAuthStore((s) => s.token);
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => (await apiClient.get<User>("/auth/me")).data,
    enabled: !!token,
    retry: false,
  });
}
