import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient, downloadAuthedFile } from "@/api/client";
import type { CVDocument, Profile } from "@/api/types";

export function useProfile() {
  return useQuery({
    queryKey: ["profile"],
    queryFn: async () => (await apiClient.get<Profile>("/profile")).data,
  });
}

export function useSaveProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Omit<Profile, "id" | "has_embedding">) =>
      (await apiClient.put<Profile>("/profile", payload)).data,
    onSuccess: (data) => {
      qc.setQueryData(["profile"], data);
      qc.invalidateQueries({ queryKey: ["matches"] });
    },
  });
}

export function useUploadCV() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return (await apiClient.post<CVDocument>("/cv/upload", form)).data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["cv-documents"] }),
  });
}

export function useCVDocuments() {
  return useQuery({
    queryKey: ["cv-documents"],
    queryFn: async () => (await apiClient.get<CVDocument[]>("/cv/documents")).data,
  });
}

/** Polls a single CV document until it finishes parsing (or fails). */
export function useCVDocument(id: string | null) {
  return useQuery({
    queryKey: ["cv-document", id],
    queryFn: async () => (await apiClient.get<CVDocument>(`/cv/documents/${id}`)).data,
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.parse_status;
      return status === "pending" || status === "processing" ? 1500 : false;
    },
  });
}

export function useDownloadCV() {
  return useMutation({
    mutationFn: async (template: "modern" | "classic") =>
      downloadAuthedFile(`/cv/export?template=${template}`, `resume-${template}.pdf`),
  });
}
