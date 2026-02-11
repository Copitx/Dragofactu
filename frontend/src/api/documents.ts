import api from "./client";
import type {
  Document,
  DocumentSummary,
  DocumentCreate,
  DocumentUpdate,
  DocumentListParams,
  StatusChange,
} from "@/types/document";
import type { PaginatedResponse, MessageResponse } from "@/types/common";

export async function listDocuments(
  params?: DocumentListParams
): Promise<PaginatedResponse<DocumentSummary>> {
  const response = await api.get<PaginatedResponse<DocumentSummary>>("/documents", { params });
  return response.data;
}

export async function getDocument(id: string): Promise<Document> {
  const response = await api.get<Document>(`/documents/${id}`);
  return response.data;
}

export async function createDocument(data: DocumentCreate): Promise<Document> {
  const response = await api.post<Document>("/documents", data);
  return response.data;
}

export async function updateDocument(id: string, data: DocumentUpdate): Promise<Document> {
  const response = await api.put<Document>(`/documents/${id}`, data);
  return response.data;
}

export async function deleteDocument(id: string): Promise<MessageResponse> {
  const response = await api.delete<MessageResponse>(`/documents/${id}`);
  return response.data;
}

export async function changeDocumentStatus(
  id: string,
  data: StatusChange
): Promise<Document> {
  const response = await api.post<Document>(`/documents/${id}/change-status`, data);
  return response.data;
}

export async function convertDocument(
  id: string,
  targetType: string
): Promise<Document> {
  const response = await api.post<Document>(`/documents/${id}/convert`, null, {
    params: { target_type: targetType },
  });
  return response.data;
}

export async function downloadDocumentPdf(id: string, code: string): Promise<void> {
  const response = await api.get(`/documents/${id}/pdf`, {
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", `${code}.pdf`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export async function getEmailStatus(): Promise<{ configured: boolean }> {
  const response = await api.get<{ configured: boolean }>("/documents/email/status");
  return response.data;
}

export async function sendDocumentEmail(
  id: string,
  recipientEmail: string
): Promise<MessageResponse> {
  const response = await api.post<MessageResponse>(
    `/documents/${id}/send-email`,
    null,
    { params: { recipient_email: recipientEmail } }
  );
  return response.data;
}
