import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Pencil, Trash2, Download } from "lucide-react";

import { Header } from "@/components/layout/header";
import { DataTable, type Column } from "@/components/data-table/data-table";
import { DataTableToolbar } from "@/components/data-table/toolbar";
import { DataTablePagination } from "@/components/data-table/pagination";
import { ConfirmDialog } from "@/components/forms/confirm-dialog";
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

import { useSuppliers, useCreateSupplier, useUpdateSupplier, useDeleteSupplier } from "@/hooks/use-suppliers";
import { supplierSchema, type SupplierFormData } from "@/lib/validators";
import { exportCSV, downloadBlob } from "@/api/export-import";
import type { Supplier } from "@/types/supplier";

export default function SuppliersPage() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [formOpen, setFormOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [editing, setEditing] = useState<Supplier | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data, isLoading } = useSuppliers({
    skip: page * pageSize,
    limit: pageSize,
    search: search || undefined,
  });

  const createMutation = useCreateSupplier();
  const updateMutation = useUpdateSupplier();
  const deleteMutation = useDeleteSupplier();

  const form = useForm<SupplierFormData>({
    resolver: zodResolver(supplierSchema),
    defaultValues: {
      code: "", name: "", tax_id: "", address: "", city: "",
      postal_code: "", province: "", country: "", phone: "",
      email: "", website: "", notes: "",
    },
  });

  const openCreate = useCallback(() => {
    setEditing(null);
    form.reset({
      code: "", name: "", tax_id: "", address: "", city: "",
      postal_code: "", province: "", country: "", phone: "",
      email: "", website: "", notes: "",
    });
    setFormOpen(true);
  }, [form]);

  const openEdit = useCallback((supplier: Supplier) => {
    setEditing(supplier);
    form.reset({
      code: supplier.code,
      name: supplier.name,
      tax_id: supplier.tax_id || "",
      address: supplier.address || "",
      city: supplier.city || "",
      postal_code: supplier.postal_code || "",
      province: supplier.province || "",
      country: supplier.country || "",
      phone: supplier.phone || "",
      email: supplier.email || "",
      website: supplier.website || "",
      notes: supplier.notes || "",
    });
    setFormOpen(true);
  }, [form]);

  const openDelete = useCallback((id: string) => {
    setDeletingId(id);
    setDeleteOpen(true);
  }, []);

  const onSubmit = form.handleSubmit(async (values) => {
    const cleaned = Object.fromEntries(
      Object.entries(values).map(([k, v]) => [k, v === "" ? undefined : v])
    );
    try {
      if (editing) {
        await updateMutation.mutateAsync({ id: editing.id, data: cleaned });
        toast.success(t("suppliers.updated"));
      } else {
        await createMutation.mutateAsync(cleaned as SupplierFormData);
        toast.success(t("suppliers.created"));
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
      toast.success(t("suppliers.deleted"));
      setDeleteOpen(false);
      setDeletingId(null);
    } catch {
      toast.error(t("common.error"));
    }
  };

  const handleExport = async () => {
    try {
      const blob = await exportCSV("suppliers");
      downloadBlob(blob, "suppliers.csv");
      toast.success(t("export_import.export_success"));
    } catch {
      toast.error(t("common.error"));
    }
  };

  const columns: Column<Supplier>[] = [
    { key: "code", header: t("suppliers.code"), cell: (s) => (
      <span className="font-mono text-xs">{s.code}</span>
    )},
    { key: "name", header: t("suppliers.name"), cell: (s) => (
      <span className="font-medium">{s.name}</span>
    )},
    { key: "tax_id", header: t("suppliers.tax_id"), cell: (s) => s.tax_id || "—", className: "hidden lg:table-cell" },
    { key: "email", header: t("suppliers.email"), cell: (s) => s.email || "—", className: "hidden md:table-cell" },
    { key: "phone", header: t("suppliers.phone"), cell: (s) => s.phone || "—", className: "hidden md:table-cell" },
    { key: "city", header: t("suppliers.city"), cell: (s) => s.city || "—", className: "hidden xl:table-cell" },
    {
      key: "actions",
      header: t("common.actions"),
      className: "w-24",
      cell: (s) => (
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(s)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => openDelete(s.id)}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  const isSaving = createMutation.isPending || updateMutation.isPending;

  return (
    <>
      <Header title={t("suppliers.title")} />
      <div className="p-4 md:p-6 space-y-4">
        <DataTableToolbar
          searchValue={search}
          onSearchChange={(v) => { setSearch(v); setPage(0); }}
          searchPlaceholder={t("suppliers.search_placeholder")}
          onAdd={openCreate}
          addLabel={t("suppliers.new")}
        >
          <Button variant="outline" size="sm" onClick={handleExport}>
            <Download className="h-4 w-4 mr-1" />
            CSV
          </Button>
        </DataTableToolbar>

        <div className="rounded-md border">
          <DataTable
            columns={columns}
            data={data?.items || []}
            isLoading={isLoading}
            keyExtractor={(s) => s.id}
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
            <DialogTitle>{editing ? t("suppliers.edit") : t("suppliers.new")}</DialogTitle>
          </DialogHeader>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("suppliers.code")} *</Label>
                <Input {...form.register("code")} disabled={!!editing} />
                {form.formState.errors.code && (
                  <p className="text-xs text-destructive">{form.formState.errors.code.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>{t("suppliers.name")} *</Label>
                <Input {...form.register("name")} />
                {form.formState.errors.name && (
                  <p className="text-xs text-destructive">{form.formState.errors.name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>{t("suppliers.tax_id")}</Label>
                <Input {...form.register("tax_id")} />
              </div>
              <div className="space-y-2">
                <Label>{t("suppliers.email")}</Label>
                <Input type="email" {...form.register("email")} />
              </div>
              <div className="space-y-2">
                <Label>{t("suppliers.phone")}</Label>
                <Input {...form.register("phone")} />
              </div>
              <div className="space-y-2">
                <Label>{t("suppliers.city")}</Label>
                <Input {...form.register("city")} />
              </div>
              <div className="space-y-2">
                <Label>{t("suppliers.postal_code")}</Label>
                <Input {...form.register("postal_code")} />
              </div>
              <div className="space-y-2">
                <Label>{t("suppliers.country")}</Label>
                <Input {...form.register("country")} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t("suppliers.address")}</Label>
              <Input {...form.register("address")} />
            </div>
            <div className="space-y-2">
              <Label>{t("suppliers.notes")}</Label>
              <Textarea {...form.register("notes")} rows={3} />
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

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        description={t("suppliers.delete_confirm")}
        onConfirm={onDelete}
        isLoading={deleteMutation.isPending}
      />
    </>
  );
}
