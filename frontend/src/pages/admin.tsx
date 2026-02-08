import { useTranslation } from "react-i18next";
import { Server, Database, HardDrive, Users, FileText, Building2, Shield } from "lucide-react";

import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { useSystemInfo, useBackupInfo } from "@/hooks/use-admin";
import { formatDateTime } from "@/lib/utils";

export default function AdminPage() {
  const { t } = useTranslation();
  const { data: sysInfo, isLoading: sysLoading } = useSystemInfo();
  const { data: backupInfo, isLoading: backupLoading } = useBackupInfo();

  const isLoading = sysLoading || backupLoading;

  if (isLoading) {
    return (
      <>
        <Header title={t("admin.title")} />
        <div className="p-4 md:p-6 space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="rounded-lg border bg-card p-6 animate-pulse h-32" />
          ))}
        </div>
      </>
    );
  }

  return (
    <>
      <Header title={t("admin.title")} />
      <div className="p-4 md:p-6 space-y-6">
        {/* System Info */}
        {sysInfo && (
          <div className="rounded-lg border bg-card p-6 space-y-4">
            <h3 className="font-semibold flex items-center gap-2">
              <Server className="h-4 w-4" />
              {t("admin.system_info")}
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">{t("admin.app_version")}:</span>
                <Badge variant="secondary">{sysInfo.app_version}</Badge>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">{t("admin.debug_mode")}:</span>
                <Badge variant={sysInfo.debug_mode ? "warning" : "success"}>
                  {sysInfo.debug_mode ? t("admin.yes") : t("admin.no")}
                </Badge>
              </div>
              <div className="text-xs text-muted-foreground">
                {formatDateTime(sysInfo.timestamp)}
              </div>
            </div>

            {/* Database */}
            <div className="pt-2 border-t space-y-2">
              <h4 className="text-sm font-medium flex items-center gap-2">
                <Database className="h-4 w-4" />
                {t("admin.database")}
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-sm">
                <div><span className="text-muted-foreground">{t("admin.db_engine")}:</span> {sysInfo.database.engine}</div>
                {sysInfo.database.version && (
                  <div className="truncate"><span className="text-muted-foreground">{t("admin.db_version")}:</span> {sysInfo.database.version.slice(0, 30)}</div>
                )}
                {sysInfo.database.size && (
                  <div><span className="text-muted-foreground">{t("admin.db_size")}:</span> {sysInfo.database.size}</div>
                )}
                {sysInfo.database.active_connections != null && (
                  <div><span className="text-muted-foreground">{t("admin.connections")}:</span> {sysInfo.database.active_connections}</div>
                )}
              </div>
            </div>

            {/* Record Counts */}
            <div className="pt-2 border-t space-y-2">
              <h4 className="text-sm font-medium">{t("admin.record_counts")}</h4>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {[
                  { label: t("admin.companies"), value: sysInfo.record_counts.companies, icon: Building2 },
                  { label: t("admin.users"), value: sysInfo.record_counts.users, icon: Users },
                  { label: t("nav.clients"), value: sysInfo.record_counts.clients, icon: Users },
                  { label: t("nav.products"), value: sysInfo.record_counts.products, icon: HardDrive },
                  { label: t("nav.documents"), value: sysInfo.record_counts.documents, icon: FileText },
                ].map((item) => (
                  <div key={item.label} className="rounded-md border p-3 text-center">
                    <item.icon className="h-4 w-4 mx-auto mb-1 text-muted-foreground" />
                    <p className="text-2xl font-bold">{item.value}</p>
                    <p className="text-xs text-muted-foreground">{item.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Backup Info */}
        {backupInfo && (
          <div className="rounded-lg border bg-card p-6 space-y-4">
            <h3 className="font-semibold flex items-center gap-2">
              <HardDrive className="h-4 w-4" />
              {t("admin.backup_info")}
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">{t("admin.provider")}:</span> {backupInfo.provider}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">{t("admin.auto_backups")}:</span>
                <Badge variant={backupInfo.automatic_backups ? "success" : "destructive"}>
                  {backupInfo.automatic_backups ? t("admin.yes") : t("admin.no")}
                </Badge>
              </div>
            </div>
            <p className="text-sm text-muted-foreground">{backupInfo.backup_note}</p>

            {backupInfo.recent_maintenance && backupInfo.recent_maintenance.length > 0 && (
              <div className="pt-2 border-t space-y-2">
                <h4 className="text-sm font-medium">{t("admin.maintenance")}</h4>
                <div className="space-y-1">
                  {backupInfo.recent_maintenance.map((m) => (
                    <div key={m.table} className="flex flex-wrap gap-4 text-xs rounded-md border p-2">
                      <span className="font-mono">{m.table}</span>
                      <span className="text-muted-foreground">{t("admin.last_vacuum")}: {m.last_vacuum ? formatDateTime(m.last_vacuum) : "—"}</span>
                      <span className="text-muted-foreground">{t("admin.last_analyze")}: {m.last_analyze ? formatDateTime(m.last_analyze) : "—"}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
