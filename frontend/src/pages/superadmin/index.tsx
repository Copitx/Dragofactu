import { useTranslation } from "react-i18next";
import { useQuery } from "@tanstack/react-query";
import { Building2, Users, FileText, UserCheck } from "lucide-react";

import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { useAuthStore } from "@/stores/auth-store";
import api from "@/api/client";

interface CompanyRow {
  id: string;
  code: string;
  name: string;
  trade_name?: string;
  tax_id?: string;
  email?: string;
  is_active: boolean;
  created_at?: string;
  user_count: number;
  document_count: number;
  client_count: number;
}

async function fetchAllCompanies(): Promise<{ items: CompanyRow[]; total: number }> {
  const res = await api.get("/superadmin/companies");
  return res.data;
}

async function fetchGlobalAudit(): Promise<{ items: any[]; total: number }> {
  const res = await api.get("/superadmin/audit?limit=50");
  return res.data;
}

export default function SuperadminPage() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);

  // Guard: only superadmin
  if (!user?.is_superadmin) {
    return (
      <>
        <Header title={t("admin.superadmin_title")} />
        <div className="p-6">
          <p className="text-destructive font-medium">Acceso denegado. Se requiere superadmin.</p>
        </div>
      </>
    );
  }

  return <SuperadminContent />;
}

function SuperadminContent() {
  const { t } = useTranslation();

  const { data: companiesData, isLoading: companiesLoading } = useQuery({
    queryKey: ["superadmin-companies"],
    queryFn: fetchAllCompanies,
  });

  const { data: auditData, isLoading: auditLoading } = useQuery({
    queryKey: ["superadmin-audit"],
    queryFn: fetchGlobalAudit,
  });

  const companies = companiesData?.items ?? [];
  const auditLogs = auditData?.items ?? [];

  const totalUsers = companies.reduce((s, c) => s + c.user_count, 0);
  const totalDocs = companies.reduce((s, c) => s + c.document_count, 0);

  return (
    <>
      <Header title={t("admin.superadmin_title")} />
      <div className="p-4 md:p-6 space-y-6">

        {/* Platform KPIs */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: "Empresas", value: companies.length, icon: Building2 },
            { label: "Usuarios totales", value: totalUsers, icon: Users },
            { label: "Documentos totales", value: totalDocs, icon: FileText },
            { label: "Activas", value: companies.filter((c) => c.is_active).length, icon: UserCheck },
          ].map((kpi) => (
            <div key={kpi.label} className="rounded-lg border bg-card p-4 text-center">
              <kpi.icon className="h-5 w-5 mx-auto mb-2 text-muted-foreground" />
              <p className="text-2xl font-bold">{kpi.value}</p>
              <p className="text-xs text-muted-foreground">{kpi.label}</p>
            </div>
          ))}
        </div>

        {/* Companies table */}
        <div className="rounded-lg border bg-card p-6 space-y-4">
          <h3 className="font-semibold flex items-center gap-2">
            <Building2 className="h-4 w-4" />
            {t("admin.all_companies")}
          </h3>
          {companiesLoading ? (
            <div className="animate-pulse h-32 rounded bg-muted" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-muted-foreground text-left">
                    <th className="pb-2 pr-4">Código</th>
                    <th className="pb-2 pr-4">Empresa</th>
                    <th className="pb-2 pr-4">CIF</th>
                    <th className="pb-2 pr-4 text-center">Usuarios</th>
                    <th className="pb-2 pr-4 text-center">Documentos</th>
                    <th className="pb-2 pr-4 text-center">Clientes</th>
                    <th className="pb-2">Estado</th>
                  </tr>
                </thead>
                <tbody>
                  {companies.map((c) => (
                    <tr key={c.id} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-2 pr-4 font-mono text-xs">{c.code}</td>
                      <td className="py-2 pr-4">
                        <div className="font-medium">{c.name}</div>
                        {c.trade_name && c.trade_name !== c.name && (
                          <div className="text-xs text-muted-foreground">{c.trade_name}</div>
                        )}
                      </td>
                      <td className="py-2 pr-4 text-muted-foreground">{c.tax_id || "—"}</td>
                      <td className="py-2 pr-4 text-center">{c.user_count}</td>
                      <td className="py-2 pr-4 text-center">{c.document_count}</td>
                      <td className="py-2 pr-4 text-center">{c.client_count}</td>
                      <td className="py-2">
                        <Badge variant={c.is_active ? "success" : "destructive"}>
                          {c.is_active ? "Activa" : "Inactiva"}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Global audit log */}
        <div className="rounded-lg border bg-card p-6 space-y-4">
          <h3 className="font-semibold">{t("admin.global_audit")} (últimas 50 acciones)</h3>
          {auditLoading ? (
            <div className="animate-pulse h-24 rounded bg-muted" />
          ) : (
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {auditLogs.map((log) => (
                <div
                  key={log.id}
                  className="flex flex-wrap gap-2 text-xs rounded border p-2 font-mono"
                >
                  <span className="text-muted-foreground">{log.created_at?.slice(0, 19).replace("T", " ")}</span>
                  <Badge variant="outline" className="text-xs">{log.action}</Badge>
                  <span>{log.entity_type}</span>
                  {log.details && (
                    <span className="text-muted-foreground truncate max-w-xs">{log.details}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

      </div>
    </>
  );
}
