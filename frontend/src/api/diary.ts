import api from "./client";
import type { DiaryEntry, DiaryEntryCreate, DiaryEntryUpdate, DiaryListParams } from "@/types/diary";
import type { PaginatedResponse, MessageResponse } from "@/types/common";

export async function listDiaryEntries(params?: DiaryListParams): Promise<PaginatedResponse<DiaryEntry>> {
  const response = await api.get<PaginatedResponse<DiaryEntry>>("/diary", { params });
  return response.data;
}

export async function getDiaryEntry(id: string): Promise<DiaryEntry> {
  const response = await api.get<DiaryEntry>(`/diary/${id}`);
  return response.data;
}

export async function createDiaryEntry(data: DiaryEntryCreate): Promise<DiaryEntry> {
  const response = await api.post<DiaryEntry>("/diary", data);
  return response.data;
}

export async function updateDiaryEntry(id: string, data: DiaryEntryUpdate): Promise<DiaryEntry> {
  const response = await api.put<DiaryEntry>(`/diary/${id}`, data);
  return response.data;
}

export async function deleteDiaryEntry(id: string): Promise<MessageResponse> {
  const response = await api.delete<MessageResponse>(`/diary/${id}`);
  return response.data;
}
