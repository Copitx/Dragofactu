import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listDocuments,
  getDocument,
  createDocument,
  updateDocument,
  deleteDocument,
  changeDocumentStatus,
  convertDocument,
} from "@/api/documents";
import type {
  DocumentListParams,
  DocumentCreate,
  DocumentUpdate,
  StatusChange,
} from "@/types/document";

export function useDocuments(params?: DocumentListParams) {
  return useQuery({
    queryKey: ["documents", params],
    queryFn: () => listDocuments(params),
  });
}

export function useDocument(id: string | undefined) {
  return useQuery({
    queryKey: ["documents", id],
    queryFn: () => getDocument(id!),
    enabled: !!id,
  });
}

export function useCreateDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: DocumentCreate) => createDocument(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useUpdateDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: DocumentUpdate }) => updateDocument(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteDocument(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useChangeStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: StatusChange }) =>
      changeDocumentStatus(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useConvertDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, targetType }: { id: string; targetType: string }) =>
      convertDocument(id, targetType),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
