import api from "./client";
import type { Product, ProductCreate, ProductUpdate, ProductListParams, StockAdjustment } from "@/types/product";
import type { PaginatedResponse, MessageResponse } from "@/types/common";

export async function listProducts(params?: ProductListParams): Promise<PaginatedResponse<Product>> {
  const response = await api.get<PaginatedResponse<Product>>("/products", { params });
  return response.data;
}

export async function getProduct(id: string): Promise<Product> {
  const response = await api.get<Product>(`/products/${id}`);
  return response.data;
}

export async function createProduct(data: ProductCreate): Promise<Product> {
  const response = await api.post<Product>("/products", data);
  return response.data;
}

export async function updateProduct(id: string, data: ProductUpdate): Promise<Product> {
  const response = await api.put<Product>(`/products/${id}`, data);
  return response.data;
}

export async function deleteProduct(id: string): Promise<MessageResponse> {
  const response = await api.delete<MessageResponse>(`/products/${id}`);
  return response.data;
}

export async function adjustStock(id: string, data: StockAdjustment): Promise<Product> {
  const response = await api.post<Product>(`/products/${id}/adjust-stock`, data);
  return response.data;
}
