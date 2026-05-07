import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Pencil, Trash2, Download, Upload, BookOpen, Plus, X } from "lucide-react";
import { supplierCatalogApi } from "@/api/supplier-catalog";

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
import { useProducts } from "@/hooks/use-products";
import { supplierSchema, type SupplierFormData } from "@/lib/validators";
import { exportCSV, importCSV, downloadBlob } from "@/api/export-import";
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
  const [importOpen, setImportOpen] = useState(false);
  const [importing, setImporting] = useState(false);

  // Catalog state
  const [catalogSupplier, setCatalogSupplier] = useState<Supplier | null>(null);
  const [catalogOpen, setCatalogOpen] = useState(false);
  const [addProductId, setAddProductId] = useState("");
  const [addSupplierRef, setAddSupplierRef] = useState("");
  const [addPurchasePrice, setAddPurchasePrice] = useState("");
  const qc = useQueryClient();

  const { data, isLoading } = useSuppliers({
    skip: page * pageSize,
    limit: pageSize,
    search: search || undefined,
  });

  const createMutation = useCreateSupplier();
  const updateMutation = useUpdateSupplier();
  const deleteMutation = useDeleteSupplier();

  // Catalog queries
  const { data: catalogEntries = [], isLoading: catalogLoading } = useQuery({
    queryKey: ["supplier-catalog", catalogSupplier?.id],
    queryFn: () => supplierCatalogApi.list(catalogSupplier!.id),
    enabled: !!catalogSupplier,
  });

  const addCatalogMutation = useMutation({
    mutationFn: (payload: { product_id: string; supplier_ref?: string; purchase_price?: number }) =>
      supplierCatalogApi.add(catalogSupplier!.id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["supplier-catalog", catalogSupplier?.id] });
      setAddProductId(""); setAddSupplierRef(""); setAddPurchasePrice("");
      toast.success(t("catalog.added"));
    },
    onError: () => toast.error(t("common.error")),
  });

  const removeCatalogMutation = useMutation({
    mutationFn: (entryId: string) => supplierCatalogApi.remove(catalogSupplier!.id, entryId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["supplier-catalog", catalogSupplier?.id] });
      toast.success(t("catalog.removed"));
    },
    onError: () => toast.error(t("common.error")),
  });

  const { data: productsData } = useProducts({ limit: 500 });
  const allProducts = productsData?.items || [];

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

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    try {
      const result = await importCSV("suppliers", file);
      toast.success(result.message || t("export_import.import_success"));
      setImportOpen(false);
    } catch {
      toast.error(t("common.error"));
    } finally {
      setImporting(false);
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
          <Button variant="ghost" size="icon" className="h-8 w-8" title={t("catalog.title")}
            onClick={() => { setCatalogSupplier(s); setCatalogOpen(true); }}>
            <BookOpen className="h-4 w-4" />
          </Button>
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
          <Button variant="outline" size="sm" onClick={() => setImportOpen(true)}>
            <Upload className="h-4 w-4 mr-1" />
            {t("buttons.import")}
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

      {/* Import Dialog */}
      <Dialog open={importOpen} onOpenChange={setImportOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>{t("export_import.import_title")}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">{t("export_import.file_hint")}</p>
            <Input type="file" accept=".csv" onChange={handleImport} disabled={importing} />
            {importing && <p className="text-sm">{t("buttons.loading")}</p>}
          </div>
        </DialogContent>
      </Dialog>

      {/* Supplier Catalog Dialog */}
      <Dialog open={catalogOpen} onOpenChange={(v) => { setCatalogOpen(v); if (!v) setCatalogSupplier(null); }}>
        <DialogContent className="sm:max-w-[700px] max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {t("catalog.title")} — {catalogSupplier?.name}
            </DialogTitle>
          </DialogHeader>

          {/* Add product row */}
          <div className="border rounded-md p-3 bg-muted/30 space-y-2">
            <p className="text-sm font-medium">{t("catalog.add_product")}</p>
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-2">
              <div className="sm:col-span-2">
                <select
                  className="w-full border rounded px-2 py-1.5 text-sm bg-background"
                  value={addProductId}
                  onChange={(e) => setAddProductId(e.target.value)}
                >
                  <option value="">{t("catalog.select_product")}</option>
                  {allProducts
                    .filter((p) => !catalogEntries.some((e) => e.product_id === p.id))
                    .map((p) => (
                      <option key={p.id} value={p.id}>{p.code} — {p.name}</option>
                    ))}
                </select>
              </div>
              <Input
                placeholder={t("catalog.supplier_ref")}
                value={addSupplierRef}
                onChange={(e) => setAddSupplierRef(e.target.value)}
              />
              <Input
                type="number"
                placeholder={t("catalog.purchase_price")}
                value={addPurchasePrice}
                onChange={(e) => setAddPurchasePrice(e.target.value)}
                min={0}
                step="0.01"
              />
            </div>
            <Button
              size="sm"
              disabled={!addProductId || addCatalogMutation.isPending}
              onClick={() => addCatalogMutation.mutate({
                product_id: addProductId,
                supplier_ref: addSupplierRef || undefined,
                purchase_price: addPurchasePrice ? parseFloat(addPurchasePrice) : 0,
              })}
            >
              <Plus className="h-4 w-4 mr-1" />
              {t("catalog.add")}
            </Button>
          </div>

          {/* Catalog entries table */}
          {catalogLoading ? (
            <p className="text-sm text-muted-foreground">{t("buttons.loading")}</p>
          ) : catalogEntries.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">{t("catalog.empty")}</p>
          ) : (
            <div className="border rounded-md overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-muted">
                  <tr>
                    <th className="text-left px-3 py-2">{t("catalog.product")}</th>
                    <th className="text-left px-3 py-2">{t("catalog.supplier_ref")}</th>
                    <th className="text-right px-3 py-2">{t("catalog.purchase_price")}</th>
                    <th className="text-right px-3 py-2">{t("catalog.sale_price")}</th>
                    <th className="text-right px-3 py-2">{t("catalog.margin")}</th>
                    <th className="px-3 py-2"></th>
                  </tr>
                </thead>
                <tbody>
                  {catalogEntries.map((entry) => {
                    const sale = entry.product_sale_price || 0;
                    const buy = entry.purchase_price || 0;
                    const margin = buy > 0 ? ((sale - buy) / buy * 100).toFixed(1) : "—";
                    return (
                      <tr key={entry.id} className="border-t">
                        <td className="px-3 py-2">
                          <span className="font-mono text-xs text-muted-foreground mr-1">{entry.product_code}</span>
                          {entry.product_name}
                        </td>
                        <td className="px-3 py-2">{entry.supplier_ref || "—"}</td>
                        <td className="px-3 py-2 text-right">€{buy.toFixed(2)}</td>
                        <td className="px-3 py-2 text-right">€{sale.toFixed(2)}</td>
                        <td className="px-3 py-2 text-right">
                          <span className={typeof margin === "string" ? "" : parseFloat(margin) >= 0 ? "text-green-600" : "text-red-600"}>
                            {typeof margin === "string" ? margin : `${margin}%`}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-right">
                          <Button
                            variant="ghost" size="icon" className="h-7 w-7 text-destructive"
                            onClick={() => removeCatalogMutation.mutate(entry.id)}
                            disabled={removeCatalogMutation.isPending}
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
