import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import type { ChatSession, ChatSessionSummary } from "@/api/types";

export function useChatSessions() {
  return useQuery({
    queryKey: ["chat-sessions"],
    queryFn: async () => (await apiClient.get<ChatSessionSummary[]>("/chat/sessions")).data,
  });
}

export function useChatSession(id: string | undefined) {
  return useQuery({
    queryKey: ["chat-session", id],
    queryFn: async () => (await apiClient.get<ChatSession>(`/chat/sessions/${id}`)).data,
    enabled: !!id,
  });
}

export function useCreateChatSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { title?: string; job_posting_id?: string }) =>
      (await apiClient.post<ChatSession>("/chat/sessions", payload)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["chat-sessions"] }),
  });
}

export function useDeleteChatSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => apiClient.delete(`/chat/sessions/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["chat-sessions"] }),
  });
}
