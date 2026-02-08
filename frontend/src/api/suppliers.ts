import api from "./client";
import type { Supplier, SupplierCreate, SupplierUpdate, SupplierListParams } from "@/types/supplier";
import type { PaginatedResponse, MessageResponse } from "@/types/common";

export async function listSuppliers(params?: SupplierListParams): Promise<PaginatedResponse<Supplier>> {
  const response = await api.get<PaginatedResponse<Supplier>>("/suppliers", { params });
  return response.data;
}

export async function getSupplier(id: string): Promise<Supplier> {
  const response = await api.get<Supplier>(`/suppliers/${id}`);
  return response.data;
}

export async function createSupplier(data: SupplierCreate): Promise<Supplier> {
  const response = await api.post<Supplier>("/suppliers", data);
  return response.data;
}

export async function updateSupplier(id: string, data: SupplierUpdate): Promise<Supplier> {
  const response = await api.put<Supplier>(`/suppliers/${id}`, data);
  return response.data;
}

export async function deleteSupplier(id: string): Promise<MessageResponse> {
  const response = await api.delete<MessageResponse>(`/suppliers/${id}`);
  return response.data;
}
