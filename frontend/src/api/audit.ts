import api from "./client";
import type { AuditLogEntry, AuditListParams } from "@/types/audit";
import type { PaginatedResponse } from "@/types/common";

export async function listAuditLogs(params?: AuditListParams): Promise<PaginatedResponse<AuditLogEntry>> {
  const response = await api.get<PaginatedResponse<AuditLogEntry>>("/audit", { params });
  return response.data;
}
