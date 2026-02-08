import api from "./client";
import type { Client, ClientCreate, ClientUpdate, ClientListParams } from "@/types/client";
import type { PaginatedResponse, MessageResponse } from "@/types/common";

export async function listClients(params?: ClientListParams): Promise<PaginatedResponse<Client>> {
  const response = await api.get<PaginatedResponse<Client>>("/clients", { params });
  return response.data;
}

export async function getClient(id: string): Promise<Client> {
  const response = await api.get<Client>(`/clients/${id}`);
  return response.data;
}

export async function createClient(data: ClientCreate): Promise<Client> {
  const response = await api.post<Client>("/clients", data);
  return response.data;
}

export async function updateClient(id: string, data: ClientUpdate): Promise<Client> {
  const response = await api.put<Client>(`/clients/${id}`, data);
  return response.data;
}

export async function deleteClient(id: string): Promise<MessageResponse> {
  const response = await api.delete<MessageResponse>(`/clients/${id}`);
  return response.data;
}
