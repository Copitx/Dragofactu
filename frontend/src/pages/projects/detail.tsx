import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Building2, ArrowLeft, Plus, Trash2, Link, Unlink,
  TrendingUp, TrendingDown, Euro, Receipt, FileText
} from "lucide-react";

import { Header } from "@/components/layout/header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";

import { projectsApi, type ProjectExpenseCreate } from "@/api/projects";
import { formatCurrency } from "@/lib/utils";

const CATEGORY_LABELS: Record<string, string> = {
  material: "Material",
  labor: "Mano de obra",
  subcontract: "Subcontrata",
  other: "Otros",
};

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  paused: "bg-yellow-100 text-yellow-800",
  completed: "bg-blue-100 text-blue-800",
  cancelled: "bg-gray-100 text-gray-800",
};

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();

  const [expenseOpen, setExpenseOpen] = useState(false);
  const [linkDocOpen, setLinkDocOpen] = useState(false);
  const [linkDocId, setLinkDocId] = useState("");

  const [expForm, setExpForm] = useState<ProjectExpenseCreate>({
    date: new Date().toISOString().slice(0, 10),
    description: "",
    supplier: "",
    document_ref: "",
    amount: 0,
    category: "material",
    notes: "",
  });

  const { data: project, isLoading } = useQuery({
    queryKey: ["project", id],
    queryFn: () => projectsApi.get(id!),
    enabled: !!id,
  });

  const { data: kpis } = useQuery({
    queryKey: ["project-summary", id],
    queryFn: () => projectsApi.summary(id!),
    enabled: !!id,
  });

  const addExpenseMutation = useMutation({
    mutationFn: (data: ProjectExpenseCreate) => projectsApi.addExpense(id!, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["project", id] });
      qc.invalidateQueries({ queryKey: ["project-summary", id] });
      toast.success(t("projects.expense_added"));
      setExpenseOpen(false);
      setExpForm({ date: new Date().toISOString().slice(0, 10), description: "", supplier: "", document_ref: "", amount: 0, category: "material", notes: "" });
    },
    onError: () => toast.error(t("common.error")),
  });

  const deleteExpenseMutation = useMutation({
    mutationFn: (expenseId: string) => projectsApi.deleteExpense(id!, expenseId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["project", id] });
      qc.invalidateQueries({ queryKey: ["project-summary", id] });
      toast.success(t("projects.expense_deleted"));
    },
    onError: () => toast.error(t("common.error")),
  });

  const linkDocMutation = useMutation({
    mutationFn: (docId: string) => projectsApi.linkDocument(id!, docId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["project", id] });
      qc.invalidateQueries({ queryKey: ["project-summary", id] });
      toast.success(t("projects.document_linked"));
      setLinkDocOpen(false);
      setLinkDocId("");
    },
    onError: () => toast.error(t("common.error")),
  });

  const unlinkDocMutation = useMutation({
    mutationFn: (docId: string) => projectsApi.unlinkDocument(id!, docId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["project", id] });
      qc.invalidateQueries({ queryKey: ["project-summary", id] });
      toast.success(t("projects.document_unlinked"));
    },
    onError: () => toast.error(t("common.error")),
  });

  if (isLoading || !project) {
    return (
      <>
        <Header title={t("projects.title")} />
        <div className="p-6 text-muted-foreground">{t("buttons.loading")}</div>
      </>
    );
  }

  return (
    <>
      <Header title={project.code} />
      <div className="p-4 md:p-6 space-y-6 max-w-5xl">
        {/* Back + title */}
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate("/projects")}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-xl font-semibold flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              {project.name}
            </h1>
            {project.client_name && (
              <p className="text-sm text-muted-foreground">{project.client_name}</p>
            )}
          </div>
          <Badge className={`ml-auto ${STATUS_COLORS[project.status] || ""}`} variant="outline">
            {t(`projects.statuses.${project.status}`)}
          </Badge>
        </div>

        {/* KPI cards */}
        {kpis && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="border rounded-md p-4 space-y-1">
              <p className="text-xs text-muted-foreground">{t("projects.estimated_value")}</p>
              <p className="text-lg font-semibold">{formatCurrency(kpis.estimated_value)}</p>
            </div>
            <div className="border rounded-md p-4 space-y-1">
              <p className="text-xs text-muted-foreground">{t("projects.total_expenses")}</p>
              <p className={`text-lg font-semibold ${kpis.total_expenses > kpis.estimated_value && kpis.estimated_value > 0 ? "text-red-600" : ""}`}>
                {formatCurrency(kpis.total_expenses)}
              </p>
            </div>
            <div className="border rounded-md p-4 space-y-1">
              <p className="text-xs text-muted-foreground">{t("projects.total_invoiced")}</p>
              <p className="text-lg font-semibold">{formatCurrency(kpis.total_invoiced)}</p>
            </div>
            <div className="border rounded-md p-4 space-y-1">
              <p className="text-xs text-muted-foreground">{t("projects.margin")}</p>
              <p className={`text-lg font-semibold flex items-center gap-1 ${kpis.margin >= 0 ? "text-green-600" : "text-red-600"}`}>
                {kpis.margin >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                {formatCurrency(kpis.margin)}
                {kpis.margin_pct != null && (
                  <span className="text-sm font-normal">({kpis.margin_pct.toFixed(1)}%)</span>
                )}
              </p>
            </div>
          </div>
        )}

        {/* Project info */}
        {project.address && (
          <p className="text-sm text-muted-foreground">
            📍 {project.address}
          </p>
        )}
        {project.notes && (
          <p className="text-sm text-muted-foreground border-l-2 pl-3">{project.notes}</p>
        )}

        {/* Expenses */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold flex items-center gap-2">
              <Euro className="h-4 w-4" />
              {t("projects.expenses")} ({project.expenses.length})
            </h2>
            <Button size="sm" onClick={() => setExpenseOpen(true)}>
              <Plus className="h-4 w-4 mr-1" />
              {t("projects.add_expense")}
            </Button>
          </div>

          {project.expenses.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4 border rounded-md">
              {t("projects.no_expenses")}
            </p>
          ) : (
            <div className="border rounded-md overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-muted text-muted-foreground">
                  <tr>
                    <th className="text-left px-3 py-2">{t("projects.expense_date")}</th>
                    <th className="text-left px-3 py-2">{t("projects.expense_description")}</th>
                    <th className="text-left px-3 py-2 hidden md:table-cell">{t("projects.expense_supplier")}</th>
                    <th className="text-left px-3 py-2 hidden lg:table-cell">{t("projects.expense_category")}</th>
                    <th className="text-right px-3 py-2">{t("projects.expense_amount")}</th>
                    <th className="px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {project.expenses.map((e) => (
                    <tr key={e.id} className="border-t">
                      <td className="px-3 py-2 whitespace-nowrap">{e.date}</td>
                      <td className="px-3 py-2">
                        {e.description}
                        {e.document_ref && (
                          <span className="text-xs text-muted-foreground ml-1">({e.document_ref})</span>
                        )}
                      </td>
                      <td className="px-3 py-2 hidden md:table-cell">{e.supplier || "—"}</td>
                      <td className="px-3 py-2 hidden lg:table-cell">
                        <Badge variant="outline" className="text-xs">
                          {CATEGORY_LABELS[e.category] || e.category}
                        </Badge>
                      </td>
                      <td className="px-3 py-2 text-right font-medium">{formatCurrency(e.amount)}</td>
                      <td className="px-3 py-2 text-right">
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive"
                          onClick={() => deleteExpenseMutation.mutate(e.id)}>
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t bg-muted/30">
                    <td colSpan={4} className="px-3 py-2 font-medium">{t("projects.total_expenses")}</td>
                    <td className="px-3 py-2 text-right font-bold">
                      {formatCurrency(project.expenses.reduce((s, e) => s + (e.amount || 0), 0))}
                    </td>
                    <td />
                  </tr>
                </tfoot>
              </table>
            </div>
          )}
        </div>

        {/* Linked documents */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold flex items-center gap-2">
              <FileText className="h-4 w-4" />
              {t("projects.linked_documents")} ({project.documents.length})
            </h2>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => setLinkDocOpen(true)}>
                <Link className="h-4 w-4 mr-1" />
                {t("projects.link_document")}
              </Button>
              <Button size="sm" variant="outline"
                onClick={() => navigate(`/documents/new`)}>
                <Receipt className="h-4 w-4 mr-1" />
                {t("projects.new_document")}
              </Button>
            </div>
          </div>

          {project.documents.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4 border rounded-md">
              {t("projects.no_documents")}
            </p>
          ) : (
            <div className="border rounded-md overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-muted text-muted-foreground">
                  <tr>
                    <th className="text-left px-3 py-2">{t("documents.code")}</th>
                    <th className="text-left px-3 py-2">{t("documents.type")}</th>
                    <th className="text-left px-3 py-2">{t("documents.status")}</th>
                    <th className="text-right px-3 py-2">{t("documents.total")}</th>
                    <th className="px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {project.documents.map((pd) => (
                    <tr key={pd.id} className="border-t">
                      <td className="px-3 py-2">
                        <button className="font-mono text-xs hover:underline"
                          onClick={() => navigate(`/documents/${pd.document_id}`)}>
                          {pd.doc_code}
                        </button>
                      </td>
                      <td className="px-3 py-2">{pd.doc_type}</td>
                      <td className="px-3 py-2">{pd.doc_status}</td>
                      <td className="px-3 py-2 text-right">{pd.doc_total != null ? formatCurrency(pd.doc_total) : "—"}</td>
                      <td className="px-3 py-2 text-right">
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive"
                          onClick={() => unlinkDocMutation.mutate(pd.document_id)}>
                          <Unlink className="h-3 w-3" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Add expense dialog */}
      <Dialog open={expenseOpen} onOpenChange={setExpenseOpen}>
        <DialogContent className="sm:max-w-[480px]">
          <DialogHeader>
            <DialogTitle>{t("projects.add_expense")}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("projects.expense_date")} *</Label>
                <Input type="date" value={expForm.date}
                  onChange={(e) => setExpForm((f) => ({ ...f, date: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label>{t("projects.expense_amount")} (€) *</Label>
                <Input type="number" min={0} step="0.01"
                  value={expForm.amount}
                  onChange={(e) => setExpForm((f) => ({ ...f, amount: parseFloat(e.target.value) || 0 }))} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t("projects.expense_description")} *</Label>
              <Input value={expForm.description}
                onChange={(e) => setExpForm((f) => ({ ...f, description: e.target.value }))} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("projects.expense_supplier")}</Label>
                <Input value={expForm.supplier}
                  onChange={(e) => setExpForm((f) => ({ ...f, supplier: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label>{t("projects.expense_ref")}</Label>
                <Input value={expForm.document_ref}
                  onChange={(e) => setExpForm((f) => ({ ...f, document_ref: e.target.value }))}
                  placeholder="Nº albarán/factura" />
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t("projects.expense_category")}</Label>
              <select className="w-full border rounded px-2 py-1.5 text-sm bg-background"
                value={expForm.category}
                onChange={(e) => setExpForm((f) => ({ ...f, category: e.target.value }))}>
                <option value="material">Material</option>
                <option value="labor">Mano de obra</option>
                <option value="subcontract">Subcontrata</option>
                <option value="other">Otros</option>
              </select>
            </div>
            <div className="space-y-2">
              <Label>{t("projects.notes")}</Label>
              <Textarea rows={2} value={expForm.notes}
                onChange={(e) => setExpForm((f) => ({ ...f, notes: e.target.value }))} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setExpenseOpen(false)}>{t("buttons.cancel")}</Button>
            <Button
              disabled={!expForm.description || !expForm.date || addExpenseMutation.isPending}
              onClick={() => addExpenseMutation.mutate(expForm)}>
              {addExpenseMutation.isPending ? t("buttons.loading") : t("buttons.save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Link document dialog */}
      <Dialog open={linkDocOpen} onOpenChange={setLinkDocOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>{t("projects.link_document")}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">{t("projects.link_document_hint")}</p>
            <Input
              placeholder={t("projects.document_id_placeholder")}
              value={linkDocId}
              onChange={(e) => setLinkDocId(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setLinkDocOpen(false)}>{t("buttons.cancel")}</Button>
            <Button
              disabled={!linkDocId || linkDocMutation.isPending}
              onClick={() => linkDocMutation.mutate(linkDocId)}>
              {linkDocMutation.isPending ? t("buttons.loading") : t("projects.link")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
