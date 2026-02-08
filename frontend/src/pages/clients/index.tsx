import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Pencil, Trash2 } from "lucide-react";

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

import { useClients, useCreateClient, useUpdateClient, useDeleteClient } from "@/hooks/use-clients";
import { clientSchema, type ClientFormData } from "@/lib/validators";
import type { Client } from "@/types/client";

export default function ClientsPage() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [formOpen, setFormOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [editing, setEditing] = useState<Client | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data, isLoading } = useClients({
    skip: page * pageSize,
    limit: pageSize,
    search: search || undefined,
  });

  const createMutation = useCreateClient();
  const updateMutation = useUpdateClient();
  const deleteMutation = useDeleteClient();

  const form = useForm<ClientFormData>({
    resolver: zodResolver(clientSchema),
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

  const openEdit = useCallback((client: Client) => {
    setEditing(client);
    form.reset({
      code: client.code,
      name: client.name,
      tax_id: client.tax_id || "",
      address: client.address || "",
      city: client.city || "",
      postal_code: client.postal_code || "",
      province: client.province || "",
      country: client.country || "",
      phone: client.phone || "",
      email: client.email || "",
      website: client.website || "",
      notes: client.notes || "",
    });
    setFormOpen(true);
  }, [form]);

  const openDelete = useCallback((id: string) => {
    setDeletingId(id);
    setDeleteOpen(true);
  }, []);

  const onSubmit = form.handleSubmit(async (values) => {
    // Clean empty strings to undefined
    const cleaned = Object.fromEntries(
      Object.entries(values).map(([k, v]) => [k, v === "" ? undefined : v])
    );
    try {
      if (editing) {
        await updateMutation.mutateAsync({ id: editing.id, data: cleaned });
        toast.success(t("clients.updated"));
      } else {
        await createMutation.mutateAsync(cleaned as ClientFormData);
        toast.success(t("clients.created"));
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
      toast.success(t("clients.deleted"));
      setDeleteOpen(false);
      setDeletingId(null);
    } catch {
      toast.error(t("common.error"));
    }
  };

  const columns: Column<Client>[] = [
    { key: "code", header: t("clients.code"), cell: (c) => (
      <span className="font-mono text-xs">{c.code}</span>
    )},
    { key: "name", header: t("clients.name"), cell: (c) => (
      <span className="font-medium">{c.name}</span>
    )},
    { key: "tax_id", header: t("clients.tax_id"), cell: (c) => c.tax_id || "—", className: "hidden lg:table-cell" },
    { key: "email", header: t("clients.email"), cell: (c) => c.email || "—", className: "hidden md:table-cell" },
    { key: "phone", header: t("clients.phone"), cell: (c) => c.phone || "—", className: "hidden md:table-cell" },
    { key: "city", header: t("clients.city"), cell: (c) => c.city || "—", className: "hidden xl:table-cell" },
    {
      key: "actions",
      header: t("common.actions"),
      className: "w-24",
      cell: (c) => (
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(c)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => openDelete(c.id)}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  const isSaving = createMutation.isPending || updateMutation.isPending;

  return (
    <>
      <Header title={t("clients.title")} />
      <div className="p-4 md:p-6 space-y-4">
        <DataTableToolbar
          searchValue={search}
          onSearchChange={(v) => { setSearch(v); setPage(0); }}
          searchPlaceholder={t("clients.search_placeholder")}
          onAdd={openCreate}
          addLabel={t("clients.new")}
        />

        <div className="rounded-md border">
          <DataTable
            columns={columns}
            data={data?.items || []}
            isLoading={isLoading}
            keyExtractor={(c) => c.id}
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
            <DialogTitle>{editing ? t("clients.edit") : t("clients.new")}</DialogTitle>
          </DialogHeader>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("clients.code")} *</Label>
                <Input {...form.register("code")} disabled={!!editing} />
                {form.formState.errors.code && (
                  <p className="text-xs text-destructive">{form.formState.errors.code.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>{t("clients.name")} *</Label>
                <Input {...form.register("name")} />
                {form.formState.errors.name && (
                  <p className="text-xs text-destructive">{form.formState.errors.name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>{t("clients.tax_id")}</Label>
                <Input {...form.register("tax_id")} />
              </div>
              <div className="space-y-2">
                <Label>{t("clients.email")}</Label>
                <Input type="email" {...form.register("email")} />
              </div>
              <div className="space-y-2">
                <Label>{t("clients.phone")}</Label>
                <Input {...form.register("phone")} />
              </div>
              <div className="space-y-2">
                <Label>{t("clients.city")}</Label>
                <Input {...form.register("city")} />
              </div>
              <div className="space-y-2">
                <Label>{t("clients.postal_code")}</Label>
                <Input {...form.register("postal_code")} />
              </div>
              <div className="space-y-2">
                <Label>{t("clients.country")}</Label>
                <Input {...form.register("country")} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t("clients.address")}</Label>
              <Input {...form.register("address")} />
            </div>
            <div className="space-y-2">
              <Label>{t("clients.notes")}</Label>
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
        description={t("clients.delete_confirm")}
        onConfirm={onDelete}
        isLoading={deleteMutation.isPending}
      />
    </>
  );
}
