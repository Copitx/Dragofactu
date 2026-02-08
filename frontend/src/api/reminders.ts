import api from "./client";
import type { Reminder, ReminderCreate, ReminderUpdate, ReminderListParams } from "@/types/reminder";
import type { PaginatedResponse, MessageResponse } from "@/types/common";

export async function listReminders(params?: ReminderListParams): Promise<PaginatedResponse<Reminder>> {
  const response = await api.get<PaginatedResponse<Reminder>>("/reminders", { params });
  return response.data;
}

export async function getReminder(id: string): Promise<Reminder> {
  const response = await api.get<Reminder>(`/reminders/${id}`);
  return response.data;
}

export async function createReminder(data: ReminderCreate): Promise<Reminder> {
  const response = await api.post<Reminder>("/reminders", data);
  return response.data;
}

export async function updateReminder(id: string, data: ReminderUpdate): Promise<Reminder> {
  const response = await api.put<Reminder>(`/reminders/${id}`, data);
  return response.data;
}

export async function completeReminder(id: string): Promise<Reminder> {
  const response = await api.post<Reminder>(`/reminders/${id}/complete`);
  return response.data;
}

export async function deleteReminder(id: string): Promise<MessageResponse> {
  const response = await api.delete<MessageResponse>(`/reminders/${id}`);
  return response.data;
}
