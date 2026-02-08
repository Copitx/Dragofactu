import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listReminders, createReminder, updateReminder, completeReminder, deleteReminder } from "@/api/reminders";
import type { ReminderListParams, ReminderCreate, ReminderUpdate } from "@/types/reminder";

export function useReminders(params?: ReminderListParams) {
  return useQuery({
    queryKey: ["reminders", params],
    queryFn: () => listReminders(params),
  });
}

export function useCreateReminder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ReminderCreate) => createReminder(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reminders"] }),
  });
}

export function useUpdateReminder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ReminderUpdate }) => updateReminder(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reminders"] }),
  });
}

export function useCompleteReminder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => completeReminder(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reminders"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDeleteReminder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteReminder(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reminders"] }),
  });
}
