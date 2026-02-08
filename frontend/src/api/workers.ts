import api from "./client";
import type { Worker, WorkerSummary, WorkerCreate, WorkerUpdate, WorkerListParams, Course, CourseCreate } from "@/types/worker";
import type { PaginatedResponse, MessageResponse } from "@/types/common";

export async function listWorkers(params?: WorkerListParams): Promise<PaginatedResponse<WorkerSummary>> {
  const response = await api.get<PaginatedResponse<WorkerSummary>>("/workers", { params });
  return response.data;
}

export async function getWorker(id: string): Promise<Worker> {
  const response = await api.get<Worker>(`/workers/${id}`);
  return response.data;
}

export async function createWorker(data: WorkerCreate): Promise<Worker> {
  const response = await api.post<Worker>("/workers", data);
  return response.data;
}

export async function updateWorker(id: string, data: WorkerUpdate): Promise<Worker> {
  const response = await api.put<Worker>(`/workers/${id}`, data);
  return response.data;
}

export async function deleteWorker(id: string): Promise<MessageResponse> {
  const response = await api.delete<MessageResponse>(`/workers/${id}`);
  return response.data;
}

export async function addCourse(workerId: string, data: CourseCreate): Promise<Course> {
  const response = await api.post<Course>(`/workers/${workerId}/courses`, data);
  return response.data;
}

export async function deleteCourse(workerId: string, courseId: string): Promise<MessageResponse> {
  const response = await api.delete<MessageResponse>(`/workers/${workerId}/courses/${courseId}`);
  return response.data;
}
