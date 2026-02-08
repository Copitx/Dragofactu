import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Pencil, Trash2, CheckCircle2, Clock, AlertCircle } from "lucide-react";

import { Header } from "@/components/layout/header";
import { DataTable, type Column } from "@/components/data-table/data-table";
import { DataTableToolbar } from "@/components/data-table/toolbar";
import { DataTablePagination } from "@/components/data-table/pagination";
import { ConfirmDialog } from "@/components/forms/confirm-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import {
  useReminders,
  useCreateReminder,
  useUpdateReminder,
  useCompleteReminder,
  useDeleteReminder,
} from "@/hooks/use-reminders";
import { reminderSchema, type ReminderFormData } from "@/lib/validators";
import { formatDate } from "@/lib/utils";
import type { Reminder } from "@/types/reminder";

const PRIORITY_VARIANTS: Record<string, "default" | "warning" | "destructive"> = {
  low: "default",
  normal: "warning",
  high: "destructive",
};

export default function RemindersPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [pendingOnly, setPendingOnly] = useState(true);
  const [priority, setPriority] = useState<string>("all");
  const [formOpen, setFormOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [editing, setEditing] = useState<Reminder | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data, isLoading } = useReminders({
    skip: page * pageSize,
    limit: pageSize,
    pending_only: pendingOnly || undefined,
    priority: priority !== "all" ? priority : undefined,
  });

  const createMutation = useCreateReminder();
  const updateMutation = useUpdateReminder();
  const completeMutation = useCompleteReminder();
  const deleteMutation = useDeleteReminder();

  const form = useForm<ReminderFormData>({
    resolver: zodResolver(reminderSchema),
    defaultValues: { title: "", description: "", due_date: "", priority: "normal" },
  });

  const openCreate = useCallback(() => {
    setEditing(null);
    form.reset({ title: "", description: "", due_date: "", priority: "normal" });
    setFormOpen(true);
  }, [form]);

  const openEdit = useCallback((reminder: Reminder) => {
    setEditing(reminder);
    form.reset({
      title: reminder.title,
      description: reminder.description || "",
      due_date: reminder.due_date?.slice(0, 10) || "",
      priority: reminder.priority,
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
        toast.success(t("reminders.updated"));
      } else {
        await createMutation.mutateAsync(cleaned as ReminderFormData);
        toast.success(t("reminders.created"));
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
      toast.success(t("reminders.deleted"));
      setDeleteOpen(false);
      setDeletingId(null);
    } catch {
      toast.error(t("common.error"));
    }
  };

  const onComplete = async (id: string) => {
    try {
      await completeMutation.mutateAsync(id);
      toast.success(t("reminders.completed_msg"));
    } catch {
      toast.error(t("common.error"));
    }
  };

  const columns: Column<Reminder>[] = [
    {
      key: "status",
      header: "",
      className: "w-10",
      cell: (r) => (
        r.is_completed
          ? <CheckCircle2 className="h-4 w-4 text-green-500" />
          : r.is_overdue
            ? <AlertCircle className="h-4 w-4 text-destructive" />
            : <Clock className="h-4 w-4 text-muted-foreground" />
      ),
    },
    { key: "title", header: t("reminders.reminder_title"), cell: (r) => (
      <div className="flex items-center gap-2">
        <span className={r.is_completed ? "line-through text-muted-foreground" : "font-medium"}>{r.title}</span>
        {r.is_overdue && !r.is_completed && <Badge variant="destructive" className="text-xs">{t("reminders.overdue")}</Badge>}
      </div>
    )},
    { key: "priority", header: t("reminders.priority"), cell: (r) => (
      <Badge variant={PRIORITY_VARIANTS[r.priority] || "default"}>
        {t(`reminders.priorities.${r.priority}`)}
      </Badge>
    ), className: "hidden sm:table-cell" },
    { key: "due_date", header: t("reminders.due_date"), cell: (r) => r.due_date ? formatDate(r.due_date) : "—", className: "hidden md:table-cell" },
    { key: "description", header: t("reminders.description"), cell: (r) => (
      <span className="text-sm text-muted-foreground line-clamp-1">{r.description || "—"}</span>
    ), className: "hidden lg:table-cell max-w-xs" },
    {
      key: "actions",
      header: t("common.actions"),
      className: "w-32",
      cell: (r) => (
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          {!r.is_completed && (
            <Button variant="ghost" size="icon" className="h-8 w-8 text-green-600" onClick={() => onComplete(r.id)} title={t("reminders.complete")}>
              <CheckCircle2 className="h-4 w-4" />
            </Button>
          )}
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(r)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => { setDeletingId(r.id); setDeleteOpen(true); }}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  return (
    <>
      <Header title={t("reminders.title")} />
      <div className="p-4 md:p-6 space-y-4">
        <DataTableToolbar
          searchValue=""
          onSearchChange={() => {}}
          searchPlaceholder=""
          onAdd={openCreate}
          addLabel={t("reminders.new")}
        >
          <div className="flex gap-2">
            <Button
              variant={pendingOnly ? "default" : "outline"}
              size="sm"
              onClick={() => { setPendingOnly(true); setPage(0); }}
            >
              {t("reminders.filter_pending")}
            </Button>
            <Button
              variant={!pendingOnly ? "default" : "outline"}
              size="sm"
              onClick={() => { setPendingOnly(false); setPage(0); }}
            >
              {t("reminders.filter_completed")}
            </Button>
          </div>
          <Select value={priority} onValueChange={(v) => { setPriority(v); setPage(0); }}>
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("inventory.filter_all")}</SelectItem>
              <SelectItem value="low">{t("reminders.priorities.low")}</SelectItem>
              <SelectItem value="normal">{t("reminders.priorities.normal")}</SelectItem>
              <SelectItem value="high">{t("reminders.priorities.high")}</SelectItem>
            </SelectContent>
          </Select>
        </DataTableToolbar>

        <div className="rounded-md border">
          <DataTable
            columns={columns}
            data={data?.items || []}
            isLoading={isLoading}
            keyExtractor={(r) => r.id}
          />
        </div>

        <DataTablePagination
          page={page}
          pageSize={pageSize}
          total={data?.total || 0}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
        />
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>{editing ? t("reminders.title") : t("reminders.new")}</DialogTitle>
          </DialogHeader>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label>{t("reminders.reminder_title")} *</Label>
              <Input {...form.register("title")} />
              {form.formState.errors.title && (
                <p className="text-xs text-destructive">{form.formState.errors.title.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label>{t("reminders.description")}</Label>
              <Textarea {...form.register("description")} rows={3} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("reminders.due_date")}</Label>
                <Input type="date" {...form.register("due_date")} />
              </div>
              <div className="space-y-2">
                <Label>{t("reminders.priority")}</Label>
                <Select
                  value={form.watch("priority")}
                  onValueChange={(v) => form.setValue("priority", v)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">{t("reminders.priorities.low")}</SelectItem>
                    <SelectItem value="normal">{t("reminders.priorities.normal")}</SelectItem>
                    <SelectItem value="high">{t("reminders.priorities.high")}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setFormOpen(false)}>
                {t("buttons.cancel")}
              </Button>
              <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
                {(createMutation.isPending || updateMutation.isPending) ? t("buttons.loading") : t("buttons.save")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        description={t("reminders.delete_confirm")}
        onConfirm={onDelete}
        isLoading={deleteMutation.isPending}
      />
    </>
  );
}
