import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listDiaryEntries, createDiaryEntry, updateDiaryEntry, deleteDiaryEntry } from "@/api/diary";
import type { DiaryListParams, DiaryEntryCreate, DiaryEntryUpdate } from "@/types/diary";

export function useDiary(params?: DiaryListParams) {
  return useQuery({
    queryKey: ["diary", params],
    queryFn: () => listDiaryEntries(params),
  });
}

export function useCreateDiaryEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: DiaryEntryCreate) => createDiaryEntry(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["diary"] }),
  });
}

export function useUpdateDiaryEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: DiaryEntryUpdate }) => updateDiaryEntry(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["diary"] }),
  });
}

export function useDeleteDiaryEntry() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteDiaryEntry(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["diary"] }),
  });
}
