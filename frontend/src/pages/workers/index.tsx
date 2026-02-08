import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Pencil, Trash2, GraduationCap, Plus, X } from "lucide-react";

import { Header } from "@/components/layout/header";
import { DataTable, type Column } from "@/components/data-table/data-table";
import { DataTableToolbar } from "@/components/data-table/toolbar";
import { DataTablePagination } from "@/components/data-table/pagination";
import { ConfirmDialog } from "@/components/forms/confirm-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
  useWorkers,
  useWorker,
  useCreateWorker,
  useUpdateWorker,
  useDeleteWorker,
  useAddCourse,
  useDeleteCourse,
} from "@/hooks/use-workers";
import { workerSchema, courseSchema, type WorkerFormData, type CourseFormData } from "@/lib/validators";
import { formatCurrency, formatDate } from "@/lib/utils";
import type { WorkerSummary } from "@/types/worker";

export default function WorkersPage() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [department, setDepartment] = useState<string>("all");
  const [formOpen, setFormOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);
  const [courseOpen, setCourseOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | undefined>(undefined);

  const { data, isLoading } = useWorkers({
    skip: page * pageSize,
    limit: pageSize,
    search: search || undefined,
    department: department !== "all" ? department : undefined,
  });

  const { data: selectedWorker } = useWorker(selectedId);

  const createMutation = useCreateWorker();
  const updateMutation = useUpdateWorker();
  const deleteMutation = useDeleteWorker();
  const addCourseMutation = useAddCourse();
  const deleteCourseMutation = useDeleteCourse();

  const form = useForm<WorkerFormData>({
    resolver: zodResolver(workerSchema),
    defaultValues: {
      code: "", first_name: "", last_name: "", phone: "", email: "",
      address: "", position: "", department: "", hire_date: "",
    },
  });

  const courseForm = useForm<CourseFormData>({
    resolver: zodResolver(courseSchema),
    defaultValues: { name: "", description: "", provider: "", issue_date: "", expiration_date: "" },
  });

  // Extract unique departments for filter
  const departments = Array.from(new Set((data?.items || []).map((w) => w.department).filter(Boolean))) as string[];

  const openCreate = useCallback(() => {
    setEditingId(null);
    form.reset({
      code: "", first_name: "", last_name: "", phone: "", email: "",
      address: "", position: "", department: "", hire_date: "",
    });
    setFormOpen(true);
  }, [form]);

  const openEdit = useCallback((worker: WorkerSummary) => {
    setEditingId(worker.id);
    setSelectedId(worker.id);
    form.reset({
      code: worker.code,
      first_name: worker.first_name,
      last_name: worker.last_name,
      position: worker.position || "",
      department: worker.department || "",
      phone: "", email: "", address: "", hire_date: "",
    });
    setFormOpen(true);
  }, [form]);

  const openDetail = useCallback((worker: WorkerSummary) => {
    setSelectedId(worker.id);
    setDetailOpen(true);
  }, []);

  const onSubmit = form.handleSubmit(async (values) => {
    const cleaned = Object.fromEntries(
      Object.entries(values).map(([k, v]) => [k, v === "" ? undefined : v])
    );
    try {
      if (editingId) {
        await updateMutation.mutateAsync({ id: editingId, data: cleaned });
        toast.success(t("workers.updated"));
      } else {
        await createMutation.mutateAsync(cleaned as WorkerFormData);
        toast.success(t("workers.created"));
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
      toast.success(t("workers.deleted"));
      setDeleteOpen(false);
      setDeletingId(null);
    } catch {
      toast.error(t("common.error"));
    }
  };

  const onAddCourse = courseForm.handleSubmit(async (values) => {
    if (!selectedId) return;
    const cleaned = Object.fromEntries(
      Object.entries(values).map(([k, v]) => [k, v === "" ? undefined : v])
    );
    try {
      await addCourseMutation.mutateAsync({ workerId: selectedId, data: cleaned as CourseFormData });
      toast.success(t("workers.course_added"));
      setCourseOpen(false);
      courseForm.reset();
    } catch {
      toast.error(t("common.error"));
    }
  });

  const onDeleteCourse = async (courseId: string) => {
    if (!selectedId) return;
    try {
      await deleteCourseMutation.mutateAsync({ workerId: selectedId, courseId });
      toast.success(t("workers.course_deleted"));
    } catch {
      toast.error(t("common.error"));
    }
  };

  const columns: Column<WorkerSummary>[] = [
    { key: "code", header: t("workers.code"), cell: (w) => (
      <span className="font-mono text-xs">{w.code}</span>
    )},
    { key: "name", header: t("workers.name"), cell: (w) => (
      <button className="font-medium text-left hover:underline" onClick={() => openDetail(w)}>
        {w.full_name}
      </button>
    )},
    { key: "position", header: t("workers.position"), cell: (w) => w.position || "—", className: "hidden md:table-cell" },
    { key: "department", header: t("workers.department"), cell: (w) => w.department || "—", className: "hidden lg:table-cell" },
    { key: "active", header: "Status", cell: (w) => w.is_active ? <Badge variant="success">Active</Badge> : <Badge variant="secondary">Inactive</Badge>, className: "hidden xl:table-cell" },
    {
      key: "actions",
      header: t("common.actions"),
      className: "w-24",
      cell: (w) => (
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(w)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => { setDeletingId(w.id); setDeleteOpen(true); }}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  const isSaving = createMutation.isPending || updateMutation.isPending;

  return (
    <>
      <Header title={t("workers.title")} />
      <div className="p-4 md:p-6 space-y-4">
        <DataTableToolbar
          searchValue={search}
          onSearchChange={(v) => { setSearch(v); setPage(0); }}
          searchPlaceholder={t("workers.search_placeholder")}
          onAdd={openCreate}
          addLabel={t("workers.new")}
        >
          {departments.length > 0 && (
            <Select value={department} onValueChange={(v) => { setDepartment(v); setPage(0); }}>
              <SelectTrigger className="w-[160px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{t("inventory.filter_all")}</SelectItem>
                {departments.map((d) => (
                  <SelectItem key={d} value={d}>{d}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        </DataTableToolbar>

        <div className="rounded-md border">
          <DataTable
            columns={columns}
            data={data?.items || []}
            isLoading={isLoading}
            keyExtractor={(w) => w.id}
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

      {/* Create/Edit Worker Dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingId ? t("workers.edit") : t("workers.new")}</DialogTitle>
          </DialogHeader>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("workers.code")} *</Label>
                <Input {...form.register("code")} disabled={!!editingId} />
                {form.formState.errors.code && (
                  <p className="text-xs text-destructive">{form.formState.errors.code.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>{t("workers.first_name")} *</Label>
                <Input {...form.register("first_name")} />
                {form.formState.errors.first_name && (
                  <p className="text-xs text-destructive">{form.formState.errors.first_name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>{t("workers.last_name")} *</Label>
                <Input {...form.register("last_name")} />
                {form.formState.errors.last_name && (
                  <p className="text-xs text-destructive">{form.formState.errors.last_name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>{t("workers.email")}</Label>
                <Input type="email" {...form.register("email")} />
              </div>
              <div className="space-y-2">
                <Label>{t("workers.phone")}</Label>
                <Input {...form.register("phone")} />
              </div>
              <div className="space-y-2">
                <Label>{t("workers.position")}</Label>
                <Input {...form.register("position")} />
              </div>
              <div className="space-y-2">
                <Label>{t("workers.department")}</Label>
                <Input {...form.register("department")} />
              </div>
              <div className="space-y-2">
                <Label>{t("workers.hire_date")}</Label>
                <Input type="date" {...form.register("hire_date")} />
              </div>
              <div className="space-y-2">
                <Label>{t("workers.salary")}</Label>
                <Input type="number" step="0.01" min="0" {...form.register("salary")} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t("workers.address")}</Label>
              <Input {...form.register("address")} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setFormOpen(false)}>
                {t("buttons.cancel")}
              </Button>
              <Button type="submit" disabled={isSaving}>
                {isSaving ? t("buttons.loading") : t("buttons.save")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Worker Detail / Courses Dialog */}
      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedWorker?.full_name}</DialogTitle>
          </DialogHeader>
          {selectedWorker && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><span className="text-muted-foreground">{t("workers.code")}:</span> {selectedWorker.code}</div>
                <div><span className="text-muted-foreground">{t("workers.email")}:</span> {selectedWorker.email || "—"}</div>
                <div><span className="text-muted-foreground">{t("workers.phone")}:</span> {selectedWorker.phone || "—"}</div>
                <div><span className="text-muted-foreground">{t("workers.position")}:</span> {selectedWorker.position || "—"}</div>
                <div><span className="text-muted-foreground">{t("workers.department")}:</span> {selectedWorker.department || "—"}</div>
                <div><span className="text-muted-foreground">{t("workers.hire_date")}:</span> {selectedWorker.hire_date ? formatDate(selectedWorker.hire_date) : "—"}</div>
                {selectedWorker.salary != null && (
                  <div><span className="text-muted-foreground">{t("workers.salary")}:</span> {formatCurrency(selectedWorker.salary)}</div>
                )}
              </div>

              {/* Courses */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium flex items-center gap-2">
                    <GraduationCap className="h-4 w-4" />
                    {t("workers.courses")}
                  </h4>
                  <Button size="sm" variant="outline" onClick={() => { courseForm.reset(); setCourseOpen(true); }}>
                    <Plus className="h-3 w-3 mr-1" />
                    {t("buttons.add")}
                  </Button>
                </div>
                {selectedWorker.courses.length === 0 ? (
                  <p className="text-sm text-muted-foreground py-2">—</p>
                ) : (
                  <div className="space-y-2">
                    {selectedWorker.courses.map((course) => (
                      <div key={course.id} className="flex items-center justify-between rounded-md border p-3">
                        <div>
                          <p className="font-medium text-sm">{course.name}</p>
                          {course.provider && <p className="text-xs text-muted-foreground">{course.provider}</p>}
                          <div className="flex items-center gap-2 mt-1">
                            {course.issue_date && <span className="text-xs">{formatDate(course.issue_date)}</span>}
                            <Badge variant={course.is_valid ? "success" : "destructive"} className="text-xs">
                              {course.is_valid ? "Valid" : "Expired"}
                            </Badge>
                          </div>
                        </div>
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive" onClick={() => onDeleteCourse(course.id)}>
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Add Course Dialog */}
      <Dialog open={courseOpen} onOpenChange={setCourseOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>{t("workers.courses")}</DialogTitle>
          </DialogHeader>
          <form onSubmit={onAddCourse} className="space-y-4">
            <div className="space-y-2">
              <Label>{t("workers.course_name")} *</Label>
              <Input {...courseForm.register("name")} />
              {courseForm.formState.errors.name && (
                <p className="text-xs text-destructive">{courseForm.formState.errors.name.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label>{t("workers.course_provider")}</Label>
              <Input {...courseForm.register("provider")} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("workers.hire_date")}</Label>
                <Input type="date" {...courseForm.register("issue_date")} />
              </div>
              <div className="space-y-2">
                <Label>{t("reminders.due_date")}</Label>
                <Input type="date" {...courseForm.register("expiration_date")} />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCourseOpen(false)}>
                {t("buttons.cancel")}
              </Button>
              <Button type="submit" disabled={addCourseMutation.isPending}>
                {addCourseMutation.isPending ? t("buttons.loading") : t("buttons.save")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        description={t("workers.delete_confirm")}
        onConfirm={onDelete}
        isLoading={deleteMutation.isPending}
      />
    </>
  );
}
