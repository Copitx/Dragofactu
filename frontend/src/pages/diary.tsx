import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Pencil, Trash2, Pin, PinOff } from "lucide-react";

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
  useDiary,
  useCreateDiaryEntry,
  useUpdateDiaryEntry,
  useDeleteDiaryEntry,
} from "@/hooks/use-diary";
import { diarySchema, type DiaryFormData } from "@/lib/validators";
import { formatDate } from "@/lib/utils";
import type { DiaryEntry } from "@/types/diary";

export default function DiaryPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [pinnedOnly, setPinnedOnly] = useState(false);
  const [formOpen, setFormOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [editing, setEditing] = useState<DiaryEntry | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data, isLoading } = useDiary({
    skip: page * pageSize,
    limit: pageSize,
    pinned_only: pinnedOnly || undefined,
  });

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
      await updateMutation.mutateAsync({
        id: entry.id,
        data: { is_pinned: !entry.is_pinned },
      });
    } catch {
      toast.error(t("common.error"));
    }
  };

  const columns: Column<DiaryEntry>[] = [
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
      <div className="p-4 md:p-6 space-y-4">
        <DataTableToolbar
          searchValue=""
          onSearchChange={() => {}}
          searchPlaceholder={t("diary.search_placeholder")}
          onAdd={openCreate}
          addLabel={t("diary.new")}
        >
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
          <DataTable
            columns={columns}
            data={data?.items || []}
            isLoading={isLoading}
            keyExtractor={(e) => e.id}
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
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editing ? t("diary.edit") : t("diary.new")}</DialogTitle>
          </DialogHeader>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("diary.entry_title")} *</Label>
                <Input {...form.register("title")} />
                {form.formState.errors.title && (
                  <p className="text-xs text-destructive">{form.formState.errors.title.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>{t("common.date")} *</Label>
                <Input type="date" {...form.register("entry_date")} />
                {form.formState.errors.entry_date && (
                  <p className="text-xs text-destructive">{form.formState.errors.entry_date.message}</p>
                )}
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t("diary.content")} *</Label>
              <Textarea {...form.register("content")} rows={6} />
              {form.formState.errors.content && (
                <p className="text-xs text-destructive">{form.formState.errors.content.message}</p>
              )}
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
        description={t("diary.delete_confirm")}
        onConfirm={onDelete}
        isLoading={deleteMutation.isPending}
      />
    </>
  );
}
