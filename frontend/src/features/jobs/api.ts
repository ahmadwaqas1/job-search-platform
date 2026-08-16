import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/api/client";
import type { JobPosting, JobSource } from "@/api/types";

export function useJobs(filters: { q?: string; location?: string; remote_type?: string }) {
  return useQuery({
    queryKey: ["jobs", filters],
    queryFn: async () => (await apiClient.get<JobPosting[]>("/jobs", { params: filters })).data,
  });
}

export function useJob(id: string | undefined) {
  return useQuery({
    queryKey: ["job", id],
    queryFn: async () => (await apiClient.get<JobPosting>(`/jobs/${id}`)).data,
    enabled: !!id,
  });
}

export function useJobSources() {
  return useQuery({
    queryKey: ["job-sources"],
    queryFn: async () => (await apiClient.get<JobSource[]>("/jobs/sources/list")).data,
  });
}

export function useCreateJobSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: {
      type: string;
      name: string;
      config: Record<string, unknown>;
      poll_interval_minutes?: number;
    }) => (await apiClient.post<JobSource>("/jobs/sources", payload)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["job-sources"] }),
  });
}

export function useSetSourceActive() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, isActive }: { id: string; isActive: boolean }) =>
      (await apiClient.patch<JobSource>(`/jobs/sources/${id}/active`, null, { params: { is_active: isActive } })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["job-sources"] }),
  });
}

export function useDeleteJobSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => apiClient.delete(`/jobs/sources/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["job-sources"] }),
  });
}

export function usePollSourceNow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => apiClient.post(`/jobs/sources/${id}/poll-now`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["job-sources"] }),
  });
}
