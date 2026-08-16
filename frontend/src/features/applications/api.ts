import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient, downloadAuthedFile } from "@/api/client";
import type { Application, ApplicationStatus } from "@/api/types";

export function useApplications() {
  return useQuery({
    queryKey: ["applications"],
    queryFn: async () => (await apiClient.get<Application[]>("/applications")).data,
  });
}

export function useApplication(id: string | undefined) {
  return useQuery({
    queryKey: ["application", id],
    queryFn: async () => (await apiClient.get<Application>(`/applications/${id}`)).data,
    enabled: !!id,
    refetchInterval: (query) => (query.state.data?.draft_status === "generating" ? 2000 : false),
  });
}

export function useCreateApplication() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: { job_posting_id: string; match_id?: string; auto_generate_draft?: boolean }) =>
      (await apiClient.post<Application>("/applications", payload)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["applications"] }),
  });
}

export function useUpdateApplicationStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status, note }: { id: string; status: ApplicationStatus; note?: string }) =>
      (await apiClient.patch<Application>(`/applications/${id}/status`, { status, note: note || "" })).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["applications"] });
    },
  });
}

export function useEditApplication() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      ...payload
    }: {
      id: string;
      cover_letter_text?: string;
      application_answers?: { question: string; answer: string }[];
      notes?: string;
    }) => (await apiClient.patch<Application>(`/applications/${id}`, payload)).data,
    onSuccess: (data) => qc.setQueryData(["application", data.id], data),
  });
}

export function useRegenerateDraft() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => apiClient.post(`/applications/${id}/generate-draft`),
    onSuccess: (_data, id) => qc.invalidateQueries({ queryKey: ["application", id] }),
  });
}

export function useDownloadTailoredResume() {
  return useMutation({
    mutationFn: async (id: string) =>
      downloadAuthedFile(`/applications/${id}/resume.pdf`, "tailored-resume.pdf"),
  });
}
