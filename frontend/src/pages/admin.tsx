import { useTranslation } from "react-i18next";
import { useState } from "react";
import { Server, Database, HardDrive, Users, FileText, Building2, Shield, UserPlus, Trash2 } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useForm } from "react-hook-form";

import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useSystemInfo, useBackupInfo } from "@/hooks/use-admin";
import { listCompanyUsers, createCompanyUser, deactivateCompanyUser } from "@/api/auth";
import { formatDateTime } from "@/lib/utils";
import type { CreateUserRequest } from "@/types/auth";

export default function AdminPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [showCreateUser, setShowCreateUser] = useState(false);
  const { data: sysInfo, isLoading: sysLoading } = useSystemInfo();
  const { data: backupInfo, isLoading: backupLoading } = useBackupInfo();

  const { data: companyUsers = [] } = useQuery({
    queryKey: ["company-users"],
    queryFn: listCompanyUsers,
  });

  const createUserMutation = useMutation({
    mutationFn: createCompanyUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["company-users"] });
      setShowCreateUser(false);
      toast.success(t("admin.user_created"));
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || t("admin.user_create_error"));
    },
  });

  const deactivateUserMutation = useMutation({
    mutationFn: deactivateCompanyUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["company-users"] });
      toast.success(t("admin.user_deactivated"));
    },
    onError: () => toast.error(t("common.error")),
  });

  const userForm = useForm<CreateUserRequest>({
    defaultValues: { role: "read_only" },
  });

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

        {/* Company Users */}
        <div className="rounded-lg border bg-card p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold flex items-center gap-2">
              <Users className="h-4 w-4" />
              {t("admin.company_users")}
            </h3>
            <Button size="sm" onClick={() => setShowCreateUser(true)}>
              <UserPlus className="h-4 w-4 mr-2" />
              {t("admin.add_user")}
            </Button>
          </div>
          <div className="space-y-2">
            {companyUsers.length === 0 ? (
              <p className="text-sm text-muted-foreground">{t("common.no_results")}</p>
            ) : (
              companyUsers.map((u) => (
                <div key={u.id} className="flex items-center justify-between rounded-md border p-3 text-sm">
                  <div className="flex items-center gap-3">
                    <div>
                      <span className="font-medium">{u.full_name}</span>
                      <span className="text-muted-foreground ml-2">@{u.username}</span>
                    </div>
                    <Badge variant="secondary">{u.role}</Badge>
                    {u.is_superadmin && <Badge variant="destructive">Superadmin</Badge>}
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-destructive hover:text-destructive"
                    onClick={() => {
                      if (confirm(t("admin.confirm_deactivate_user"))) {
                        deactivateUserMutation.mutate(u.id);
                      }
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Create User Dialog */}
        <Dialog open={showCreateUser} onOpenChange={setShowCreateUser}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{t("admin.add_user")}</DialogTitle>
            </DialogHeader>
            <form
              onSubmit={userForm.handleSubmit((data) => createUserMutation.mutate(data))}
              className="space-y-4"
            >
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label>{t("admin.username")}</Label>
                  <Input {...userForm.register("username", { required: true })} />
                </div>
                <div className="space-y-1">
                  <Label>{t("admin.full_name")}</Label>
                  <Input {...userForm.register("full_name", { required: true })} />
                </div>
              </div>
              <div className="space-y-1">
                <Label>{t("admin.email")}</Label>
                <Input type="email" {...userForm.register("email", { required: true })} />
              </div>
              <div className="space-y-1">
                <Label>{t("admin.password")}</Label>
                <Input type="password" {...userForm.register("password", { required: true })} />
              </div>
              <div className="space-y-1">
                <Label>{t("admin.role")}</Label>
                <Select
                  defaultValue="read_only"
                  onValueChange={(v) => userForm.setValue("role", v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="admin">{t("admin.role_admin")}</SelectItem>
                    <SelectItem value="management">{t("admin.role_management")}</SelectItem>
                    <SelectItem value="warehouse">{t("admin.role_warehouse")}</SelectItem>
                    <SelectItem value="read_only">{t("admin.role_read_only")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex gap-2 justify-end pt-2">
                <Button type="button" variant="outline" onClick={() => setShowCreateUser(false)}>
                  {t("buttons.cancel")}
                </Button>
                <Button type="submit" disabled={createUserMutation.isPending}>
                  {createUserMutation.isPending ? t("buttons.loading") : t("buttons.add")}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

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
