import api from "./client";
import type { MessageResponse } from "@/types/common";

export async function exportCSV(entity: "clients" | "products" | "suppliers"): Promise<Blob> {
  const response = await api.get(`/export/${entity}`, { responseType: "blob" });
  return response.data;
}

export async function importCSV(entity: "clients" | "products", file: File): Promise<MessageResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post<MessageResponse>(`/export/import/${entity}`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
