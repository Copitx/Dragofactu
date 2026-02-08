import api from "./client";
import type { SystemInfo, BackupInfo } from "@/types/admin";

export async function getSystemInfo(): Promise<SystemInfo> {
  const response = await api.get<SystemInfo>("/admin/system-info");
  return response.data;
}

export async function getBackupInfo(): Promise<BackupInfo> {
  const response = await api.get<BackupInfo>("/admin/backup-info");
  return response.data;
}
