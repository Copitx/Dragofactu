import { useQuery } from "@tanstack/react-query";
import { getSystemInfo, getBackupInfo } from "@/api/admin";

export function useSystemInfo() {
  return useQuery({
    queryKey: ["admin", "system-info"],
    queryFn: getSystemInfo,
  });
}

export function useBackupInfo() {
  return useQuery({
    queryKey: ["admin", "backup-info"],
    queryFn: getBackupInfo,
  });
}
