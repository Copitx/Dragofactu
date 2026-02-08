import { useQuery } from "@tanstack/react-query";
import { listAuditLogs } from "@/api/audit";
import type { AuditListParams } from "@/types/audit";

export function useAuditLogs(params?: AuditListParams) {
  return useQuery({
    queryKey: ["audit", params],
    queryFn: () => listAuditLogs(params),
  });
}
