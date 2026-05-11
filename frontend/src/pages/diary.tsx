import { useState, useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { format } from "date-fns";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Pencil,
  Trash2,
  Pin,
  PinOff,
  X,
  Upload,
  Plus,
  Check,
  ChevronDown,
  ChevronUp,
  BookOpen,
} from "lucide-react";

import { Header } from "@/components/layout/header";
import { DataTable, type Column } from "@/components/data-table/data-table";
import { DataTableToolbar } from "@/components/data-table/toolbar";
import { DataTablePagination } from "@/components/data-table/pagination";
import { ConfirmDialog } from "@/components/forms/confirm-dialog";
import { MonthCalendar } from "@/components/common/month-calendar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
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
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

import {
  useDiary,
  useCreateDiaryEntry,
  useUpdateDiaryEntry,
  useDeleteDiaryEntry,
} from "@/hooks/use-diary";
import { diarySchema, type DiaryFormData } from "@/lib/validators";
import { importCSV } from "@/api/export-import";
import { formatDate, formatCurrency } from "@/lib/utils";
import { expensesApi } from "@/api/expenses";
import { projectsApi } from "@/api/projects";
import type { DiaryEntry } from "@/types/diary";
import type {
  CompanyExpense,
  CompanyExpenseCreate,
  ExpenseCategory,
  ExpenseStatus,
  ExpenseMonthlySummary,
} from "@/types/expense";

// ── Expense ledger tab ────────────────────────────────────────────────────────

const PAYMENT_METHODS = [
  "Transferencia",
  "Efectivo",
  "Tarjeta",
  "Domiciliación",
  "Cheque",
];

const EXPENSE_CATEGORIES: ExpenseCategory[] = [
  "material",
  "labor",
  "payroll",
  "fuel",
  "utilities",
  "subcontract",
  "tax",
  "other",
];

const STATUS_COLORS: Record<ExpenseStatus, string> = {
  pending: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
  paid: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
  partial: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
};

function ExpenseLedger() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const today = new Date();
  const [activeYear, setActiveYear] = useState(today.getFullYear());
  const [activeMonth, setActiveMonth] = useState(today.getMonth() + 1);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [catFilter, setCatFilter] = useState<string>("all");
  const [page, setPage] = useState(0);
  const pageSize = 50;
  const [formOpen, setFormOpen] = useState(false);
  const [editingExpense, setEditingExpense] = useState<CompanyExpense | null>(null);
  const [deleteExpenseId, setDeleteExpenseId] = useState<string | null>(null);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [markPaidId, setMarkPaidId] = useState<string | null>(null);
  const [showMonthSummary, setShowMonthSummary] = useState(true);

  // Quick entry form state (inline)
  const [quickDate, setQuickDate] = useState(today.toISOString().slice(0, 10));
  const [quickSupplier, setQuickSupplier] = useState("");
  const [quickConcept, setQuickConcept] = useState("");
  const [quickTotal, setQuickTotal] = useState("");
  const [quickVatRate, setQuickVatRate] = useState("");
  const [quickCategory, setQuickCategory] = useState<string>("other");
  const [quickProject, setQuickProject] = useState<string>("none");
  const [quickSaving, setQuickSaving] = useState(false);

  // Projects for selector
  const { data: projectsData } = useQuery({
    queryKey: ["projects-list-short"],
    queryFn: () => projectsApi.list({ limit: 200, status: "active" }),
    staleTime: 60_000,
  });
  const projects = (projectsData as any)?.items ?? [];

  // Expenses list
  const params: Record<string, any> = {
    skip: page * pageSize,
    limit: pageSize,
    year: activeYear,
    month: activeMonth,
  };
  if (statusFilter !== "all") params.status = statusFilter;
  if (catFilter !== "all") params.category = catFilter;

  const { data: expenseData, isLoading } = useQuery({
    queryKey: ["expenses", params],
    queryFn: () => expensesApi.list(params),
    staleTime: 30_000,
  });

  // Monthly summary
  const { data: summary } = useQuery<ExpenseMonthlySummary>({
    queryKey: ["expenses-summary", activeYear, activeMonth],
    queryFn: () => expensesApi.monthlySummary(activeYear, activeMonth),
    staleTime: 30_000,
  });

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["expenses"] });
  };

  const createMutation = useMutation({
    mutationFn: expensesApi.create,
    onSuccess: () => { toast.success(t("expenses.created")); invalidate(); },
    onError: () => toast.error(t("common.error")),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => expensesApi.update(id, data),
    onSuccess: () => { toast.success(t("expenses.updated")); invalidate(); setFormOpen(false); },
    onError: () => toast.error(t("common.error")),
  });

  const deleteMutation = useMutation({
    mutationFn: expensesApi.delete,
    onSuccess: () => { toast.success(t("expenses.deleted")); invalidate(); setDeleteOpen(false); },
    onError: () => toast.error(t("common.error")),
  });

  const markPaidMutation = useMutation({
    mutationFn: ({ id }: { id: string }) =>
      expensesApi.markPaid(id, { payment_date: today.toISOString().slice(0, 10) }),
    onSuccess: () => { toast.success(t("expenses.marked_paid")); invalidate(); setMarkPaidId(null); },
    onError: () => toast.error(t("common.error")),
  });

  const handleQuickAdd = async () => {
    if (!quickSupplier || !quickConcept || !quickTotal) return;
    setQuickSaving(true);
    try {
      const total = parseFloat(quickTotal);
      const vatRate = quickVatRate ? parseFloat(quickVatRate) : undefined;
      const netAmount = vatRate ? total / (1 + vatRate / 100) : undefined;
      const vatAmount = vatRate && netAmount ? total - netAmount : undefined;

      await createMutation.mutateAsync({
        expense_date: quickDate,
        supplier: quickSupplier,
        concept: quickConcept,
        total_amount: total,
        net_amount: netAmount ? parseFloat(netAmount.toFixed(2)) : undefined,
        vat_rate: vatRate,
        vat_amount: vatAmount ? parseFloat(vatAmount.toFixed(2)) : undefined,
        category: quickCategory as ExpenseCategory,
        project_id: quickProject !== "none" ? quickProject : undefined,
        status: "pending",
      } as CompanyExpenseCreate);

      // Reset quick form
      setQuickSupplier("");
      setQuickConcept("");
      setQuickTotal("");
      setQuickVatRate("");
      setQuickCategory("other");
      setQuickProject("none");
    } finally {
      setQuickSaving(false);
    }
  };

  const prevMonth = () => {
    if (activeMonth === 1) { setActiveYear(y => y - 1); setActiveMonth(12); }
    else setActiveMonth(m => m - 1);
    setPage(0);
  };
  const nextMonth = () => {
    if (activeMonth === 12) { setActiveYear(y => y + 1); setActiveMonth(1); }
    else setActiveMonth(m => m + 1);
    setPage(0);
  };

  const MONTH_NAMES = [
    "Enero","Febrero","Marzo","Abril","Mayo","Junio",
    "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre",
  ];

  // Full-form dialog state
  const [fdDate, setFdDate] = useState(today.toISOString().slice(0, 10));
  const [fdSupplier, setFdSupplier] = useState("");
  const [fdConcept, setFdConcept] = useState("");
  const [fdInvoiceRef, setFdInvoiceRef] = useState("");
  const [fdTotal, setFdTotal] = useState("");
  const [fdNet, setFdNet] = useState("");
  const [fdVatRate, setFdVatRate] = useState("");
  const [fdCategory, setFdCategory] = useState<string>("other");
  const [fdStatus, setFdStatus] = useState<string>("pending");
  const [fdPayMethod, setFdPayMethod] = useState<string>("none");
  const [fdPayDate, setFdPayDate] = useState("");
  const [fdPaidBy, setFdPaidBy] = useState("");
  const [fdProject, setFdProject] = useState<string>("none");
  const [fdNotes, setFdNotes] = useState("");

  const openEditDialog = (exp: CompanyExpense) => {
    setEditingExpense(exp);
    setFdDate(exp.expense_date.slice(0, 10));
    setFdSupplier(exp.supplier);
    setFdConcept(exp.concept);
    setFdInvoiceRef(exp.invoice_ref ?? "");
    setFdTotal(String(exp.total_amount));
    setFdNet(exp.net_amount != null ? String(exp.net_amount) : "");
    setFdVatRate(exp.vat_rate != null ? String(exp.vat_rate) : "");
    setFdCategory(exp.category ?? "other");
    setFdStatus(exp.status);
    setFdPayMethod(exp.payment_method ?? "none");
    setFdPayDate(exp.payment_date?.slice(0, 10) ?? "");
    setFdPaidBy(exp.paid_by ?? "");
    setFdProject(exp.project_id ?? "none");
    setFdNotes(exp.notes ?? "");
    setFormOpen(true);
  };

  const openCreateDialog = () => {
    setEditingExpense(null);
    setFdDate(today.toISOString().slice(0, 10));
    setFdSupplier(""); setFdConcept(""); setFdInvoiceRef("");
    setFdTotal(""); setFdNet(""); setFdVatRate("");
    setFdCategory("other"); setFdStatus("pending"); setFdPayMethod("none");
    setFdPayDate(""); setFdPaidBy(""); setFdProject("none"); setFdNotes("");
    setFormOpen(true);
  };

  const handleFormSave = async () => {
    const payload: any = {
      expense_date: fdDate,
      supplier: fdSupplier,
      concept: fdConcept,
      invoice_ref: fdInvoiceRef || undefined,
      total_amount: parseFloat(fdTotal),
      net_amount: fdNet ? parseFloat(fdNet) : undefined,
      vat_rate: fdVatRate ? parseFloat(fdVatRate) : undefined,
      category: fdCategory as ExpenseCategory,
      status: fdStatus as ExpenseStatus,
      payment_method: fdPayMethod !== "none" ? fdPayMethod : undefined,
      payment_date: fdPayDate || undefined,
      paid_by: fdPaidBy || undefined,
      project_id: fdProject !== "none" ? fdProject : undefined,
      notes: fdNotes || undefined,
    };
    if (editingExpense) {
      await updateMutation.mutateAsync({ id: editingExpense.id, data: payload });
    } else {
      await createMutation.mutateAsync(payload);
      setFormOpen(false);
    }
  };

  const columns: Column<CompanyExpense>[] = [
    {
      key: "date",
      header: t("common.date"),
      className: "w-28",
      cell: (e) => <span className="text-sm">{formatDate(e.expense_date)}</span>,
    },
    {
      key: "supplier",
      header: t("expenses.supplier"),
      cell: (e) => (
        <div>
          <p className="font-medium text-sm">{e.supplier}</p>
          {e.invoice_ref && <p className="text-xs text-muted-foreground">Nº {e.invoice_ref}</p>}
        </div>
      ),
    },
    {
      key: "concept",
      header: t("expenses.concept"),
      className: "hidden md:table-cell",
      cell: (e) => (
        <div>
          <p className="text-sm">{e.concept}</p>
          {e.project_name && <p className="text-xs text-muted-foreground">{e.project_name}</p>}
        </div>
      ),
    },
    {
      key: "category",
      header: t("expenses.category"),
      className: "hidden lg:table-cell w-28",
      cell: (e) => e.category ? (
        <Badge variant="outline" className="text-xs capitalize">{t(`expenses.categories.${e.category}`)}</Badge>
      ) : "—",
    },
    {
      key: "total",
      header: t("expenses.total"),
      className: "w-28 text-right",
      cell: (e) => (
        <div className="text-right">
          <p className="font-semibold">{formatCurrency(e.total_amount)}</p>
          {e.vat_rate != null && <p className="text-xs text-muted-foreground">IVA {e.vat_rate}%</p>}
        </div>
      ),
    },
    {
      key: "status",
      header: t("common.status"),
      className: "w-28",
      cell: (e) => (
        <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_COLORS[e.status]}`}>
          {t(`expenses.statuses.${e.status}`)}
        </span>
      ),
    },
    {
      key: "actions",
      header: "",
      className: "w-28",
      cell: (e) => (
        <div className="flex gap-1" onClick={(ev) => ev.stopPropagation()}>
          {e.status !== "paid" && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-green-600"
              title={t("expenses.mark_paid")}
              onClick={() => { setMarkPaidId(e.id); markPaidMutation.mutate({ id: e.id }); }}
              disabled={markPaidMutation.isPending && markPaidId === e.id}
            >
              <Check className="h-4 w-4" />
            </Button>
          )}
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEditDialog(e)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost" size="icon" className="h-8 w-8 text-destructive"
            onClick={() => { setDeleteExpenseId(e.id); setDeleteOpen(true); }}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-4">
      {/* Month navigation */}
      <div className="flex items-center gap-3">
        <Button variant="outline" size="sm" onClick={prevMonth}>‹</Button>
        <span className="font-semibold text-base min-w-[160px] text-center">
          {MONTH_NAMES[activeMonth - 1]} {activeYear}
        </span>
        <Button variant="outline" size="sm" onClick={nextMonth}>›</Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => { setActiveYear(today.getFullYear()); setActiveMonth(today.getMonth() + 1); }}
          className="text-muted-foreground"
        >
          {t("expenses.this_month")}
        </Button>
      </div>

      {/* Monthly summary */}
      {summary && (
        <div>
          <button
            className="flex items-center gap-1 text-sm text-muted-foreground mb-2"
            onClick={() => setShowMonthSummary(v => !v)}
          >
            <BookOpen className="h-4 w-4" />
            {t("expenses.monthly_summary")}
            {showMonthSummary ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </button>
          {showMonthSummary && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-lg border bg-muted/30">
              <div>
                <p className="text-xs text-muted-foreground">{t("expenses.total_month")}</p>
                <p className="text-lg font-bold">{formatCurrency(summary.total_amount)}</p>
                <p className="text-xs text-muted-foreground">{summary.expense_count} {t("expenses.records")}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{t("expenses.pending_amount")}</p>
                <p className="text-lg font-semibold text-yellow-600">{formatCurrency(summary.pending_amount)}</p>
                <p className="text-xs text-muted-foreground">{summary.pending_count} {t("expenses.pending_records")}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{t("expenses.paid_amount")}</p>
                <p className="text-lg font-semibold text-green-600">{formatCurrency(summary.paid_amount)}</p>
                <p className="text-xs text-muted-foreground">{summary.paid_count} {t("expenses.paid_records")}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{t("expenses.by_category")}</p>
                <div className="space-y-0.5 mt-1">
                  {Object.entries(summary.by_category).slice(0, 4).map(([cat, amt]) => (
                    <div key={cat} className="flex justify-between text-xs">
                      <span className="capitalize text-muted-foreground">{t(`expenses.categories.${cat}`)}</span>
                      <span className="font-medium">{formatCurrency(amt)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Quick-add row */}
      <div className="rounded-lg border p-3 bg-card">
        <p className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
          {t("expenses.quick_add")}
        </p>
        <div className="flex flex-wrap gap-2 items-end">
          <div className="flex flex-col gap-1">
            <Label className="text-xs">{t("common.date")}</Label>
            <Input type="date" value={quickDate} onChange={e => setQuickDate(e.target.value)} className="h-8 text-sm w-36" />
          </div>
          <div className="flex flex-col gap-1 flex-1 min-w-[120px]">
            <Label className="text-xs">{t("expenses.supplier")} *</Label>
            <Input
              value={quickSupplier}
              onChange={e => setQuickSupplier(e.target.value)}
              placeholder={t("expenses.supplier")}
              className="h-8 text-sm"
            />
          </div>
          <div className="flex flex-col gap-1 flex-1 min-w-[150px]">
            <Label className="text-xs">{t("expenses.concept")} *</Label>
            <Input
              value={quickConcept}
              onChange={e => setQuickConcept(e.target.value)}
              placeholder={t("expenses.concept")}
              className="h-8 text-sm"
            />
          </div>
          <div className="flex flex-col gap-1 w-24">
            <Label className="text-xs">IVA %</Label>
            <Input
              type="number"
              value={quickVatRate}
              onChange={e => setQuickVatRate(e.target.value)}
              placeholder="21"
              className="h-8 text-sm"
            />
          </div>
          <div className="flex flex-col gap-1 w-28">
            <Label className="text-xs">{t("expenses.total")} * (€)</Label>
            <Input
              type="number"
              value={quickTotal}
              onChange={e => setQuickTotal(e.target.value)}
              placeholder="0.00"
              className="h-8 text-sm"
            />
          </div>
          <div className="flex flex-col gap-1 w-36">
            <Label className="text-xs">{t("expenses.category")}</Label>
            <Select value={quickCategory} onValueChange={setQuickCategory}>
              <SelectTrigger className="h-8 text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {EXPENSE_CATEGORIES.map(c => (
                  <SelectItem key={c} value={c}>{t(`expenses.categories.${c}`)}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {projects.length > 0 && (
            <div className="flex flex-col gap-1 w-40">
              <Label className="text-xs">{t("expenses.project")}</Label>
              <Select value={quickProject} onValueChange={setQuickProject}>
                <SelectTrigger className="h-8 text-sm">
                  <SelectValue placeholder={t("expenses.no_project")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">{t("expenses.no_project")}</SelectItem>
                  {projects.map((p: any) => (
                    <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          <Button
            size="sm"
            className="h-8"
            onClick={handleQuickAdd}
            disabled={quickSaving || !quickSupplier || !quickConcept || !quickTotal}
          >
            <Plus className="h-4 w-4 mr-1" />
            {t("expenses.add")}
          </Button>
          <Button size="sm" variant="outline" className="h-8" onClick={openCreateDialog}>
            {t("expenses.advanced")}
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <Select value={statusFilter} onValueChange={v => { setStatusFilter(v); setPage(0); }}>
          <SelectTrigger className="w-36 h-8 text-sm">
            <SelectValue placeholder={t("common.status")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("expenses.all_statuses")}</SelectItem>
            <SelectItem value="pending">{t("expenses.statuses.pending")}</SelectItem>
            <SelectItem value="paid">{t("expenses.statuses.paid")}</SelectItem>
            <SelectItem value="partial">{t("expenses.statuses.partial")}</SelectItem>
          </SelectContent>
        </Select>

        <Select value={catFilter} onValueChange={v => { setCatFilter(v); setPage(0); }}>
          <SelectTrigger className="w-40 h-8 text-sm">
            <SelectValue placeholder={t("expenses.category")} />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">{t("expenses.all_categories")}</SelectItem>
            {EXPENSE_CATEGORIES.map(c => (
              <SelectItem key={c} value={c}>{t(`expenses.categories.${c}`)}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Expense table */}
      <div className="rounded-md border">
        <DataTable
          columns={columns}
          data={expenseData?.items ?? []}
          isLoading={isLoading}
          keyExtractor={(e) => e.id}
        />
      </div>

      <DataTablePagination
        page={page}
        pageSize={pageSize}
        total={expenseData?.total ?? 0}
        onPageChange={setPage}
        onPageSizeChange={() => {}}
      />

      {/* Full form dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="sm:max-w-[640px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingExpense ? t("expenses.edit") : t("expenses.new")}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">{t("common.date")} *</Label>
                <Input type="date" value={fdDate} onChange={e => setFdDate(e.target.value)} />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">{t("expenses.invoice_ref")}</Label>
                <Input value={fdInvoiceRef} onChange={e => setFdInvoiceRef(e.target.value)} placeholder="Nº factura proveedor" />
              </div>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">{t("expenses.supplier")} *</Label>
              <Input value={fdSupplier} onChange={e => setFdSupplier(e.target.value)} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">{t("expenses.concept")} *</Label>
              <Input value={fdConcept} onChange={e => setFdConcept(e.target.value)} />
            </div>
            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">{t("expenses.net")}</Label>
                <Input type="number" value={fdNet} onChange={e => setFdNet(e.target.value)} placeholder="0.00" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">IVA %</Label>
                <Input type="number" value={fdVatRate} onChange={e => setFdVatRate(e.target.value)} placeholder="21" />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">{t("expenses.total")} * (€)</Label>
                <Input type="number" value={fdTotal} onChange={e => setFdTotal(e.target.value)} placeholder="0.00" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">{t("expenses.category")}</Label>
                <Select value={fdCategory} onValueChange={setFdCategory}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {EXPENSE_CATEGORIES.map(c => (
                      <SelectItem key={c} value={c}>{t(`expenses.categories.${c}`)}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">{t("common.status")}</Label>
                <Select value={fdStatus} onValueChange={setFdStatus}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">{t("expenses.statuses.pending")}</SelectItem>
                    <SelectItem value="paid">{t("expenses.statuses.paid")}</SelectItem>
                    <SelectItem value="partial">{t("expenses.statuses.partial")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">{t("expenses.payment_method")}</Label>
                <Select value={fdPayMethod} onValueChange={setFdPayMethod}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">—</SelectItem>
                    {PAYMENT_METHODS.map(m => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">{t("expenses.payment_date")}</Label>
                <Input type="date" value={fdPayDate} onChange={e => setFdPayDate(e.target.value)} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs">{t("expenses.paid_by")}</Label>
                <Input value={fdPaidBy} onChange={e => setFdPaidBy(e.target.value)} placeholder="Iniciales..." />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">{t("expenses.project")}</Label>
                <Select value={fdProject} onValueChange={setFdProject}>
                  <SelectTrigger><SelectValue placeholder="—" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">—</SelectItem>
                    {projects.map((p: any) => (
                      <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">{t("expenses.notes")}</Label>
              <Textarea value={fdNotes} onChange={e => setFdNotes(e.target.value)} rows={2} />
            </div>
          </div>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setFormOpen(false)}>{t("buttons.cancel")}</Button>
            <Button
              onClick={handleFormSave}
              disabled={!fdSupplier || !fdConcept || !fdTotal || createMutation.isPending || updateMutation.isPending}
            >
              {(createMutation.isPending || updateMutation.isPending) ? t("buttons.loading") : t("buttons.save")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete confirm */}
      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        description={t("expenses.delete_confirm")}
        onConfirm={() => deleteExpenseId && deleteMutation.mutate(deleteExpenseId)}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}

// ── Main page with tabs ───────────────────────────────────────────────────────

export default function DiaryPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [pinnedOnly, setPinnedOnly] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [importing, setImporting] = useState(false);
  const [editing, setEditing] = useState<DiaryEntry | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  const dateFrom = selectedDate ? format(selectedDate, "yyyy-MM-dd") : undefined;
  const dateTo = selectedDate ? format(selectedDate, "yyyy-MM-dd") : undefined;

  const { data, isLoading } = useDiary({
    skip: page * pageSize,
    limit: pageSize,
    pinned_only: pinnedOnly || undefined,
    date_from: dateFrom,
    date_to: dateTo,
  });

  const { data: monthData } = useDiary({
    skip: 0,
    limit: 200,
    date_from: format(new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1), "yyyy-MM-dd"),
    date_to: format(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0), "yyyy-MM-dd"),
  });

  const highlightedDates = useMemo(() => {
    const dates = new Set<string>();
    if (monthData?.items) {
      for (const entry of monthData.items) {
        dates.add(entry.entry_date.slice(0, 10));
      }
    }
    return dates;
  }, [monthData]);

  const createMutation = useCreateDiaryEntry();
  const updateMutation = useUpdateDiaryEntry();
  const deleteMutation = useDeleteDiaryEntry();

  const form = useForm<DiaryFormData>({
    resolver: zodResolver(diarySchema),
    defaultValues: {
      title: "", content: "", entry_date: new Date().toISOString().slice(0, 10), tags: "", is_pinned: false,
    },
  });

  const openCreate = useCallback(() => {
    setEditing(null);
    form.reset({
      title: "", content: "", entry_date: new Date().toISOString().slice(0, 10), tags: "", is_pinned: false,
    });
    setFormOpen(true);
  }, [form]);

  const openEdit = useCallback((entry: DiaryEntry) => {
    setEditing(entry);
    form.reset({
      title: entry.title,
      content: entry.content,
      entry_date: entry.entry_date.slice(0, 10),
      tags: entry.tags || "",
      is_pinned: entry.is_pinned,
    });
    setFormOpen(true);
  }, [form]);

  const onSubmit = form.handleSubmit(async (values) => {
    const cleaned = Object.fromEntries(
      Object.entries(values).map(([k, v]) => [k, v === "" ? undefined : v])
    );
    try {
      if (editing) {
        await updateMutation.mutateAsync({ id: editing.id, data: cleaned });
        toast.success(t("diary.updated"));
      } else {
        await createMutation.mutateAsync(cleaned as DiaryFormData);
        toast.success(t("diary.created"));
      }
      setFormOpen(false);
    } catch {
      toast.error(t("common.error"));
    }
  });

  const onDelete = async () => {
    if (!deletingId) return;
    try {
      await deleteMutation.mutateAsync(deletingId);
      toast.success(t("diary.deleted"));
      setDeleteOpen(false);
      setDeletingId(null);
    } catch {
      toast.error(t("common.error"));
    }
  };

  const togglePin = async (entry: DiaryEntry) => {
    try {
      await updateMutation.mutateAsync({ id: entry.id, data: { is_pinned: !entry.is_pinned } });
    } catch {
      toast.error(t("common.error"));
    }
  };

  const handleSelectDate = useCallback((date: Date) => {
    setSelectedDate((prev) => {
      if (prev && format(prev, "yyyy-MM-dd") === format(date, "yyyy-MM-dd")) return null;
      return date;
    });
    setPage(0);
  }, []);

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    try {
      const result = await importCSV("diary", file);
      toast.success(result.message || t("export_import.import_success"));
      setImportOpen(false);
    } catch {
      toast.error(t("common.error"));
    } finally {
      setImporting(false);
    }
  };

  const diaryColumns: Column<DiaryEntry>[] = [
    {
      key: "pin",
      header: "",
      className: "w-10",
      cell: (e) => (
        <button onClick={() => togglePin(e)} className="text-muted-foreground hover:text-foreground">
          {e.is_pinned ? <Pin className="h-4 w-4 text-primary" /> : <PinOff className="h-4 w-4" />}
        </button>
      ),
    },
    { key: "date", header: t("common.date"), cell: (e) => formatDate(e.entry_date), className: "w-32" },
    { key: "title", header: t("diary.entry_title"), cell: (e) => (
      <div>
        <span className="font-medium">{e.title}</span>
        {e.is_pinned && <Badge variant="secondary" className="ml-2 text-xs">{t("diary.pinned")}</Badge>}
      </div>
    )},
    { key: "content", header: t("diary.content"), cell: (e) => (
      <span className="text-sm text-muted-foreground line-clamp-1">{e.content}</span>
    ), className: "hidden md:table-cell max-w-xs" },
    { key: "tags", header: "Tags", cell: (e) => e.tags || "—", className: "hidden lg:table-cell" },
    {
      key: "actions",
      header: t("common.actions"),
      className: "w-24",
      cell: (e) => (
        <div className="flex gap-1" onClick={(ev) => ev.stopPropagation()}>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(e)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => { setDeletingId(e.id); setDeleteOpen(true); }}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <>
      <Header title={t("diary.title")} />
      <div className="p-4 md:p-6">
        <Tabs defaultValue="notes">
          <TabsList className="mb-4">
            <TabsTrigger value="notes">{t("diary.tab_notes")}</TabsTrigger>
            <TabsTrigger value="expenses">{t("diary.tab_expenses")}</TabsTrigger>
          </TabsList>

          {/* ── Notes tab ── */}
          <TabsContent value="notes">
            <div className="space-y-4">
              <div className="max-w-xs">
                <MonthCalendar
                  currentMonth={currentMonth}
                  onMonthChange={setCurrentMonth}
                  selectedDate={selectedDate}
                  onSelectDate={handleSelectDate}
                  highlightedDates={highlightedDates}
                />
              </div>
              {selectedDate && (
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">
                    {t("diary.entries_for")} {format(selectedDate, "dd/MM/yyyy")}
                  </Badge>
                  <Button variant="ghost" size="sm" className="h-6 px-2" onClick={() => { setSelectedDate(null); setPage(0); }}>
                    <X className="h-3 w-3 mr-1" />
                    {t("diary.clear_filter")}
                  </Button>
                </div>
              )}
              <DataTableToolbar
                searchValue=""
                onSearchChange={() => {}}
                searchPlaceholder={t("diary.search_placeholder")}
                onAdd={openCreate}
                addLabel={t("diary.new")}
              >
                <Button variant="outline" size="sm" onClick={() => setImportOpen(true)}>
                  <Upload className="h-4 w-4 mr-1" />
                  {t("buttons.import")}
                </Button>
                <Button
                  variant={pinnedOnly ? "default" : "outline"}
                  size="sm"
                  onClick={() => { setPinnedOnly(!pinnedOnly); setPage(0); }}
                >
                  <Pin className="h-4 w-4 mr-1" />
                  {t("diary.pinned")}
                </Button>
              </DataTableToolbar>
              <div className="rounded-md border">
                <DataTable columns={diaryColumns} data={data?.items || []} isLoading={isLoading} keyExtractor={(e) => e.id} />
              </div>
              <DataTablePagination page={page} pageSize={pageSize} total={data?.total || 0} onPageChange={setPage} onPageSizeChange={setPageSize} />
            </div>
          </TabsContent>

          {/* ── Expenses tab ── */}
          <TabsContent value="expenses">
            <ExpenseLedger />
          </TabsContent>
        </Tabs>
      </div>

      {/* Diary create/edit dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editing ? t("diary.edit") : t("diary.new")}</DialogTitle>
          </DialogHeader>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("diary.entry_title")} *</Label>
                <Input {...form.register("title")} />
                {form.formState.errors.title && <p className="text-xs text-destructive">{form.formState.errors.title.message}</p>}
              </div>
              <div className="space-y-2">
                <Label>{t("common.date")} *</Label>
                <Input type="date" {...form.register("entry_date")} />
                {form.formState.errors.entry_date && <p className="text-xs text-destructive">{form.formState.errors.entry_date.message}</p>}
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t("diary.content")} *</Label>
              <Textarea {...form.register("content")} rows={6} />
              {form.formState.errors.content && <p className="text-xs text-destructive">{form.formState.errors.content.message}</p>}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Tags</Label>
                <Input {...form.register("tags")} placeholder="tag1, tag2" />
              </div>
              <div className="flex items-center gap-2 pt-6">
                <input type="checkbox" id="is_pinned" {...form.register("is_pinned")} className="h-4 w-4" />
                <Label htmlFor="is_pinned">{t("diary.pinned")}</Label>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setFormOpen(false)}>{t("buttons.cancel")}</Button>
              <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
                {(createMutation.isPending || updateMutation.isPending) ? t("buttons.loading") : t("buttons.save")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <ConfirmDialog open={deleteOpen} onOpenChange={setDeleteOpen} description={t("diary.delete_confirm")} onConfirm={onDelete} isLoading={deleteMutation.isPending} />

      <Dialog open={importOpen} onOpenChange={setImportOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader><DialogTitle>{t("export_import.import_title")}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">{t("export_import.file_hint")}</p>
            <Input type="file" accept=".csv" onChange={handleImport} disabled={importing} />
            {importing && <p className="text-sm">{t("buttons.loading")}</p>}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
