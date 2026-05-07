import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Building2, Users, FileText, UserCheck, KeyRound, Trash2, ArrowRightLeft, ShieldAlert } from "lucide-react";
import { toast } from "sonner";

import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAuthStore } from "@/stores/auth-store";
import api from "@/api/client";

// ─── Types ───────────────────────────────────────────────────────────────────

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

interface UserRow {
  id: string;
  username: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
  is_superadmin: boolean;
  company_id: string;
  company_name: string;
  company_code: string;
  created_at?: string;
}

// ─── API calls ───────────────────────────────────────────────────────────────

const fetchCompanies = () => api.get("/superadmin/companies").then(r => r.data);
const fetchUsers = (companyId?: string) =>
  api.get("/superadmin/users" + (companyId ? `?company_id=${companyId}` : "")).then(r => r.data);
const fetchAudit = () => api.get("/superadmin/audit?limit=50").then(r => r.data);

// ─── Main guard ──────────────────────────────────────────────────────────────

export default function SuperadminPage() {
  const user = useAuthStore((s) => s.user);
  if (!user?.is_superadmin) {
    return (
      <>
        <Header title="Superadmin" />
        <div className="p-6">
          <p className="text-destructive font-medium">Acceso denegado. Se requiere superadmin.</p>
        </div>
      </>
    );
  }
  return <SuperadminContent />;
}

// ─── Main content ─────────────────────────────────────────────────────────────

function SuperadminContent() {
  const [tab, setTab] = useState<"companies" | "users" | "audit">("companies");
  const [companyFilter, setCompanyFilter] = useState<string>("");

  const { data: companiesData, isLoading: cLoading } = useQuery({
    queryKey: ["sa-companies"],
    queryFn: fetchCompanies,
  });
  const { data: usersData, isLoading: uLoading } = useQuery({
    queryKey: ["sa-users", companyFilter],
    queryFn: () => fetchUsers(companyFilter || undefined),
  });
  const { data: auditData, isLoading: aLoading } = useQuery({
    queryKey: ["sa-audit"],
    queryFn: fetchAudit,
    enabled: tab === "audit",
  });

  const companies: CompanyRow[] = companiesData?.items ?? [];
  const users: UserRow[] = usersData?.items ?? [];
  const auditLogs: any[] = auditData?.items ?? [];

  const totalUsers = companies.reduce((s, c) => s + c.user_count, 0);
  const totalDocs = companies.reduce((s, c) => s + c.document_count, 0);

  return (
    <>
      <Header title="Superadmin — Panel de Plataforma" />
      <div className="p-4 md:p-6 space-y-6">

        {/* KPIs */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: "Empresas", value: companies.length, icon: Building2 },
            { label: "Usuarios totales", value: totalUsers, icon: Users },
            { label: "Documentos totales", value: totalDocs, icon: FileText },
            { label: "Empresas activas", value: companies.filter(c => c.is_active).length, icon: UserCheck },
          ].map(kpi => (
            <div key={kpi.label} className="rounded-lg border bg-card p-4 text-center">
              <kpi.icon className="h-5 w-5 mx-auto mb-2 text-muted-foreground" />
              <p className="text-2xl font-bold">{kpi.value}</p>
              <p className="text-xs text-muted-foreground">{kpi.label}</p>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b">
          {(["companies", "users", "audit"] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                tab === t
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {t === "companies" ? "Empresas" : t === "users" ? "Usuarios" : "Audit Log"}
            </button>
          ))}
        </div>

        {/* ── Empresas tab ── */}
        {tab === "companies" && (
          <CompaniesTab companies={companies} loading={cLoading} />
        )}

        {/* ── Usuarios tab ── */}
        {tab === "users" && (
          <UsersTab
            users={users}
            companies={companies}
            loading={uLoading}
            companyFilter={companyFilter}
            setCompanyFilter={setCompanyFilter}
          />
        )}

        {/* ── Audit tab ── */}
        {tab === "audit" && (
          <div className="rounded-lg border bg-card p-6 space-y-3">
            <h3 className="font-semibold">Audit Log Global (últimas 50 acciones)</h3>
            {aLoading ? (
              <div className="animate-pulse h-24 rounded bg-muted" />
            ) : (
              <div className="space-y-1 max-h-[600px] overflow-y-auto">
                {auditLogs.map(log => (
                  <div key={log.id} className="flex flex-wrap gap-2 text-xs rounded border p-2 font-mono">
                    <span className="text-muted-foreground">{log.created_at?.slice(0, 19).replace("T", " ")}</span>
                    <Badge variant="outline" className="text-xs">{log.action}</Badge>
                    <span>{log.entity_type}</span>
                    {log.details && <span className="text-muted-foreground truncate max-w-xs">{log.details}</span>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

      </div>
    </>
  );
}

// ─── Empresas Tab ─────────────────────────────────────────────────────────────

function CompaniesTab({ companies, loading }: { companies: CompanyRow[]; loading: boolean }) {
  const qc = useQueryClient();
  const [deleteTarget, setDeleteTarget] = useState<CompanyRow | null>(null);
  const [confirmName, setConfirmName] = useState("");

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.delete(`/superadmin/companies/${id}`).then(r => r.data),
    onSuccess: () => {
      toast.success("Empresa desactivada correctamente.");
      qc.invalidateQueries({ queryKey: ["sa-companies"] });
      qc.invalidateQueries({ queryKey: ["sa-users"] });
      setDeleteTarget(null);
      setConfirmName("");
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Error al eliminar empresa"),
  });

  return (
    <div className="rounded-lg border bg-card p-6 space-y-4">
      <h3 className="font-semibold flex items-center gap-2">
        <Building2 className="h-4 w-4" />
        Todas las empresas
      </h3>

      {loading ? (
        <div className="animate-pulse h-32 rounded bg-muted" />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-muted-foreground text-left">
                <th className="pb-2 pr-3">Código</th>
                <th className="pb-2 pr-3">Empresa</th>
                <th className="pb-2 pr-3">CIF</th>
                <th className="pb-2 pr-3 text-center">Usuarios</th>
                <th className="pb-2 pr-3 text-center">Docs</th>
                <th className="pb-2 pr-3 text-center">Clientes</th>
                <th className="pb-2 pr-3">Estado</th>
                <th className="pb-2">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {companies.map(c => (
                <tr key={c.id} className="border-b last:border-0 hover:bg-muted/30">
                  <td className="py-2 pr-3 font-mono text-xs">{c.code}</td>
                  <td className="py-2 pr-3">
                    <div className="font-medium">{c.name}</div>
                    {c.trade_name && c.trade_name !== c.name && (
                      <div className="text-xs text-muted-foreground">{c.trade_name}</div>
                    )}
                    {c.email && <div className="text-xs text-muted-foreground">{c.email}</div>}
                  </td>
                  <td className="py-2 pr-3 text-muted-foreground text-xs">{c.tax_id || "—"}</td>
                  <td className="py-2 pr-3 text-center">{c.user_count}</td>
                  <td className="py-2 pr-3 text-center">{c.document_count}</td>
                  <td className="py-2 pr-3 text-center">{c.client_count}</td>
                  <td className="py-2 pr-3">
                    <Badge variant={c.is_active ? "success" : "destructive"}>
                      {c.is_active ? "Activa" : "Inactiva"}
                    </Badge>
                  </td>
                  <td className="py-2">
                    <Button
                      size="sm"
                      variant="destructive"
                      className="h-7 text-xs"
                      onClick={() => { setDeleteTarget(c); setConfirmName(""); }}
                    >
                      <Trash2 className="h-3 w-3 mr-1" />
                      Eliminar
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Delete company dialog */}
      <Dialog open={!!deleteTarget} onOpenChange={open => { if (!open) { setDeleteTarget(null); setConfirmName(""); } }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <ShieldAlert className="h-5 w-5" />
              Eliminar empresa — Acción irreversible
            </DialogTitle>
            <DialogDescription className="space-y-2 pt-2">
              <p>
                Esto <strong>desactivará permanentemente</strong> la empresa{" "}
                <strong>{deleteTarget?.name}</strong> y todos sus usuarios.
              </p>
              <p className="text-destructive font-medium">
                Esta acción NO se puede deshacer. Los datos quedan inaccesibles.
              </p>
              <p>
                Para confirmar, escribe el nombre exacto de la empresa:{" "}
                <strong>{deleteTarget?.name}</strong>
              </p>
            </DialogDescription>
          </DialogHeader>
          <Input
            placeholder={`Escribe: ${deleteTarget?.name}`}
            value={confirmName}
            onChange={e => setConfirmName(e.target.value)}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => { setDeleteTarget(null); setConfirmName(""); }}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              disabled={confirmName !== deleteTarget?.name || deleteMut.isPending}
              onClick={() => deleteTarget && deleteMut.mutate(deleteTarget.id)}
            >
              {deleteMut.isPending ? "Eliminando..." : "Confirmar eliminación"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ─── Usuarios Tab ─────────────────────────────────────────────────────────────

const ROLES = ["ADMIN", "MANAGEMENT", "WAREHOUSE", "READ_ONLY"];

function UsersTab({
  users, companies, loading, companyFilter, setCompanyFilter,
}: {
  users: UserRow[];
  companies: CompanyRow[];
  loading: boolean;
  companyFilter: string;
  setCompanyFilter: (v: string) => void;
}) {
  const qc = useQueryClient();

  // Reset password dialog
  const [pwdTarget, setPwdTarget] = useState<UserRow | null>(null);
  const [newPwd, setNewPwd] = useState("");
  const [showPwd, setShowPwd] = useState(false);

  // Change company dialog
  const [moveTarget, setMoveTarget] = useState<UserRow | null>(null);
  const [targetCompany, setTargetCompany] = useState("");

  // Delete user dialog
  const [deleteTarget, setDeleteTarget] = useState<UserRow | null>(null);

  // Change role inline
  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, any> }) =>
      api.patch(`/superadmin/users/${id}`, data).then(r => r.data),
    onSuccess: () => {
      toast.success("Usuario actualizado.");
      qc.invalidateQueries({ queryKey: ["sa-users"] });
      qc.invalidateQueries({ queryKey: ["sa-companies"] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Error"),
  });

  const resetPwdMut = useMutation({
    mutationFn: ({ id, pwd }: { id: string; pwd: string }) =>
      api.post(`/superadmin/users/${id}/reset-password`, { new_password: pwd }).then(r => r.data),
    onSuccess: () => {
      toast.success("Contraseña restablecida.");
      setPwdTarget(null);
      setNewPwd("");
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Error"),
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.delete(`/superadmin/users/${id}`).then(r => r.data),
    onSuccess: () => {
      toast.success("Usuario desactivado.");
      qc.invalidateQueries({ queryKey: ["sa-users"] });
      qc.invalidateQueries({ queryKey: ["sa-companies"] });
      setDeleteTarget(null);
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Error"),
  });

  return (
    <div className="rounded-lg border bg-card p-6 space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="font-semibold flex items-center gap-2">
          <Users className="h-4 w-4" />
          Todos los usuarios ({users.length})
        </h3>
        <Select
          value={companyFilter || "all"}
          onValueChange={v => setCompanyFilter(v === "all" ? "" : v)}
        >
          <SelectTrigger className="w-[220px]">
            <SelectValue placeholder="Filtrar por empresa" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todas las empresas</SelectItem>
            {companies.map(c => (
              <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {loading ? (
        <div className="animate-pulse h-32 rounded bg-muted" />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-muted-foreground text-left">
                <th className="pb-2 pr-3">Usuario</th>
                <th className="pb-2 pr-3">Email</th>
                <th className="pb-2 pr-3">Empresa</th>
                <th className="pb-2 pr-3">Rol</th>
                <th className="pb-2 pr-3">Estado</th>
                <th className="pb-2">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id} className="border-b last:border-0 hover:bg-muted/30">
                  <td className="py-2 pr-3">
                    <div className="font-medium">{u.full_name}</div>
                    <div className="text-xs text-muted-foreground font-mono">{u.username}</div>
                    {u.is_superadmin && (
                      <Badge variant="default" className="text-xs mt-0.5">superadmin</Badge>
                    )}
                  </td>
                  <td className="py-2 pr-3 text-muted-foreground text-xs">{u.email || "—"}</td>
                  <td className="py-2 pr-3 text-xs">
                    <div>{u.company_name}</div>
                    <div className="text-muted-foreground font-mono">{u.company_code}</div>
                  </td>
                  <td className="py-2 pr-3">
                    {u.is_superadmin ? (
                      <Badge variant="outline" className="text-xs">SUPERADMIN</Badge>
                    ) : (
                      <Select
                        value={u.role}
                        onValueChange={role => updateMut.mutate({ id: u.id, data: { role } })}
                      >
                        <SelectTrigger className="h-7 w-[120px] text-xs">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {ROLES.map(r => (
                            <SelectItem key={r} value={r} className="text-xs">{r}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  </td>
                  <td className="py-2 pr-3">
                    <Badge variant={u.is_active ? "success" : "destructive"}>
                      {u.is_active ? "Activo" : "Inactivo"}
                    </Badge>
                  </td>
                  <td className="py-2">
                    <div className="flex gap-1 flex-wrap">
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-7 text-xs"
                        onClick={() => { setPwdTarget(u); setNewPwd(""); setShowPwd(false); }}
                        title="Cambiar contraseña"
                      >
                        <KeyRound className="h-3 w-3 mr-1" />
                        Contraseña
                      </Button>
                      {!u.is_superadmin && (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 text-xs"
                            onClick={() => { setMoveTarget(u); setTargetCompany(u.company_id); }}
                            title="Cambiar empresa"
                          >
                            <ArrowRightLeft className="h-3 w-3 mr-1" />
                            Empresa
                          </Button>
                          <Button
                            size="sm"
                            variant="destructive"
                            className="h-7 text-xs"
                            onClick={() => setDeleteTarget(u)}
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── Reset password dialog ── */}
      <Dialog open={!!pwdTarget} onOpenChange={open => { if (!open) setPwdTarget(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="h-4 w-4" />
              Cambiar contraseña — {pwdTarget?.username}
            </DialogTitle>
            <DialogDescription>
              Esta acción cambiará la contraseña del usuario inmediatamente.
              El usuario deberá usar la nueva contraseña en su próximo inicio de sesión.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label>Nueva contraseña (mín. 8 caracteres)</Label>
            <div className="relative">
              <Input
                type={showPwd ? "text" : "password"}
                value={newPwd}
                onChange={e => setNewPwd(e.target.value)}
                placeholder="Nueva contraseña..."
                minLength={8}
              />
              <button
                type="button"
                className="absolute right-3 top-2.5 text-xs text-muted-foreground"
                onClick={() => setShowPwd(v => !v)}
              >
                {showPwd ? "Ocultar" : "Ver"}
              </button>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPwdTarget(null)}>Cancelar</Button>
            <Button
              disabled={newPwd.length < 8 || resetPwdMut.isPending}
              onClick={() => pwdTarget && resetPwdMut.mutate({ id: pwdTarget.id, pwd: newPwd })}
            >
              {resetPwdMut.isPending ? "Guardando..." : "Cambiar contraseña"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── Move to company dialog ── */}
      <Dialog open={!!moveTarget} onOpenChange={open => { if (!open) setMoveTarget(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ArrowRightLeft className="h-4 w-4" />
              Cambiar empresa — {moveTarget?.username}
            </DialogTitle>
            <DialogDescription>
              El usuario dejará de tener acceso a los datos de su empresa actual y pasará a
              la empresa seleccionada. Esta acción queda registrada en el audit log.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label>Empresa destino</Label>
            <Select value={targetCompany} onValueChange={setTargetCompany}>
              <SelectTrigger>
                <SelectValue placeholder="Selecciona empresa..." />
              </SelectTrigger>
              <SelectContent>
                {companies.map(c => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.name} ({c.code})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setMoveTarget(null)}>Cancelar</Button>
            <Button
              disabled={!targetCompany || targetCompany === moveTarget?.company_id || updateMut.isPending}
              onClick={() => moveTarget && updateMut.mutate(
                { id: moveTarget.id, data: { company_id: targetCompany } },
                { onSuccess: () => setMoveTarget(null) }
              )}
            >
              {updateMut.isPending ? "Moviendo..." : "Confirmar cambio"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ── Delete user dialog ── */}
      <Dialog open={!!deleteTarget} onOpenChange={open => { if (!open) setDeleteTarget(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <ShieldAlert className="h-4 w-4" />
              Eliminar usuario
            </DialogTitle>
            <DialogDescription>
              El usuario <strong>{deleteTarget?.full_name}</strong> ({deleteTarget?.username}) será
              desactivado y no podrá iniciar sesión. Sus datos históricos se conservan.
              Esta acción se puede revertir contactando al administrador de la plataforma.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>Cancelar</Button>
            <Button
              variant="destructive"
              disabled={deleteMut.isPending}
              onClick={() => deleteTarget && deleteMut.mutate(deleteTarget.id)}
            >
              {deleteMut.isPending ? "Eliminando..." : "Eliminar usuario"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
