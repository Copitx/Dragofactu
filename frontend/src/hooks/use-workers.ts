import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listWorkers, getWorker, createWorker, updateWorker, deleteWorker, addCourse, deleteCourse } from "@/api/workers";
import type { WorkerListParams, WorkerCreate, WorkerUpdate, CourseCreate } from "@/types/worker";

export function useWorkers(params?: WorkerListParams) {
  return useQuery({
    queryKey: ["workers", params],
    queryFn: () => listWorkers(params),
  });
}

export function useWorker(id: string | undefined) {
  return useQuery({
    queryKey: ["workers", id],
    queryFn: () => getWorker(id!),
    enabled: !!id,
  });
}

export function useCreateWorker() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: WorkerCreate) => createWorker(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workers"] }),
  });
}

export function useUpdateWorker() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WorkerUpdate }) => updateWorker(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workers"] }),
  });
}

export function useDeleteWorker() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteWorker(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workers"] }),
  });
}

export function useAddCourse() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ workerId, data }: { workerId: string; data: CourseCreate }) => addCourse(workerId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workers"] }),
  });
}

export function useDeleteCourse() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ workerId, courseId }: { workerId: string; courseId: string }) => deleteCourse(workerId, courseId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["workers"] }),
  });
}
