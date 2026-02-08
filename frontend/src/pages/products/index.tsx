import { useState, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Pencil, Trash2, PackageMinus } from "lucide-react";

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
  useProducts,
  useCreateProduct,
  useUpdateProduct,
  useDeleteProduct,
  useAdjustStock,
} from "@/hooks/use-products";
import { productSchema, stockAdjustmentSchema, type ProductFormData, type StockAdjustmentFormData } from "@/lib/validators";
import { formatCurrency } from "@/lib/utils";
import type { Product } from "@/types/product";

export default function ProductsPage() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [formOpen, setFormOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [stockOpen, setStockOpen] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [stockProduct, setStockProduct] = useState<Product | null>(null);

  const { data, isLoading } = useProducts({
    skip: page * pageSize,
    limit: pageSize,
    search: search || undefined,
  });

  const createMutation = useCreateProduct();
  const updateMutation = useUpdateProduct();
  const deleteMutation = useDeleteProduct();
  const stockMutation = useAdjustStock();

  const form = useForm<ProductFormData>({
    resolver: zodResolver(productSchema),
    defaultValues: {
      code: "", name: "", description: "", category: "",
      purchase_price: 0, sale_price: 0, current_stock: 0,
      minimum_stock: 0, stock_unit: "unidades", supplier_id: "",
    },
  });

  const stockForm = useForm<StockAdjustmentFormData>({
    resolver: zodResolver(stockAdjustmentSchema),
    defaultValues: { quantity: 0, reason: "" },
  });

  const openCreate = useCallback(() => {
    setEditing(null);
    form.reset({
      code: "", name: "", description: "", category: "",
      purchase_price: 0, sale_price: 0, current_stock: 0,
      minimum_stock: 0, stock_unit: "unidades", supplier_id: "",
    });
    setFormOpen(true);
  }, [form]);

  const openEdit = useCallback((product: Product) => {
    setEditing(product);
    form.reset({
      code: product.code,
      name: product.name,
      description: product.description || "",
      category: product.category || "",
      purchase_price: product.purchase_price,
      sale_price: product.sale_price,
      current_stock: product.current_stock,
      minimum_stock: product.minimum_stock,
      stock_unit: product.stock_unit,
      supplier_id: product.supplier_id || "",
    });
    setFormOpen(true);
  }, [form]);

  const openStockAdjust = useCallback((product: Product) => {
    setStockProduct(product);
    stockForm.reset({ quantity: 0, reason: "" });
    setStockOpen(true);
  }, [stockForm]);

  const onSubmit = form.handleSubmit(async (values) => {
    const cleaned = Object.fromEntries(
      Object.entries(values).map(([k, v]) => [k, v === "" ? undefined : v])
    );
    try {
      if (editing) {
        await updateMutation.mutateAsync({ id: editing.id, data: cleaned });
        toast.success(t("products.updated"));
      } else {
        await createMutation.mutateAsync(cleaned as ProductFormData);
        toast.success(t("products.created"));
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
      toast.success(t("products.deleted"));
      setDeleteOpen(false);
      setDeletingId(null);
    } catch {
      toast.error(t("common.error"));
    }
  };

  const onStockAdjust = stockForm.handleSubmit(async (values) => {
    if (!stockProduct) return;
    try {
      await stockMutation.mutateAsync({ id: stockProduct.id, data: values });
      toast.success(t("products.updated"));
      setStockOpen(false);
    } catch {
      toast.error(t("common.error"));
    }
  });

  const columns: Column<Product>[] = [
    { key: "code", header: t("products.code"), cell: (p) => (
      <span className="font-mono text-xs">{p.code}</span>
    )},
    { key: "name", header: t("products.name"), cell: (p) => (
      <div>
        <span className="font-medium">{p.name}</span>
        {p.category && <span className="ml-2 text-xs text-muted-foreground">{p.category}</span>}
      </div>
    )},
    { key: "price", header: t("products.price"), cell: (p) => formatCurrency(p.sale_price), className: "hidden sm:table-cell" },
    { key: "cost", header: t("products.cost"), cell: (p) => formatCurrency(p.purchase_price), className: "hidden lg:table-cell" },
    {
      key: "stock",
      header: t("products.stock"),
      cell: (p) => (
        <div className="flex items-center gap-2">
          <span>{p.current_stock}</span>
          {p.is_low_stock && <Badge variant="warning">Low</Badge>}
        </div>
      ),
    },
    {
      key: "actions",
      header: t("common.actions"),
      className: "w-32",
      cell: (p) => (
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openStockAdjust(p)}>
            <PackageMinus className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(p)}>
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => { setDeletingId(p.id); setDeleteOpen(true); }}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  const isSaving = createMutation.isPending || updateMutation.isPending;

  return (
    <>
      <Header title={t("products.title")} />
      <div className="p-4 md:p-6 space-y-4">
        <DataTableToolbar
          searchValue={search}
          onSearchChange={(v) => { setSearch(v); setPage(0); }}
          searchPlaceholder={t("products.search_placeholder")}
          onAdd={openCreate}
          addLabel={t("products.new")}
        />

        <div className="rounded-md border">
          <DataTable
            columns={columns}
            data={data?.items || []}
            isLoading={isLoading}
            keyExtractor={(p) => p.id}
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
            <DialogTitle>{editing ? t("products.edit") : t("products.new")}</DialogTitle>
          </DialogHeader>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("products.code")} *</Label>
                <Input {...form.register("code")} disabled={!!editing} />
                {form.formState.errors.code && (
                  <p className="text-xs text-destructive">{form.formState.errors.code.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>{t("products.name")} *</Label>
                <Input {...form.register("name")} />
                {form.formState.errors.name && (
                  <p className="text-xs text-destructive">{form.formState.errors.name.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>{t("products.category")}</Label>
                <Input {...form.register("category")} />
              </div>
              <div className="space-y-2">
                <Label>{t("products.price")} (EUR)</Label>
                <Input type="number" step="0.01" min="0" {...form.register("sale_price")} />
              </div>
              <div className="space-y-2">
                <Label>{t("products.cost")} (EUR)</Label>
                <Input type="number" step="0.01" min="0" {...form.register("purchase_price")} />
              </div>
              <div className="space-y-2">
                <Label>{t("products.stock")}</Label>
                <Input type="number" min="0" {...form.register("current_stock")} />
              </div>
              <div className="space-y-2">
                <Label>{t("products.min_stock")}</Label>
                <Input type="number" min="0" {...form.register("minimum_stock")} />
              </div>
              <div className="space-y-2">
                <Label>Unidad</Label>
                <Input {...form.register("stock_unit")} />
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t("products.description")}</Label>
              <Textarea {...form.register("description")} rows={3} />
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

      {/* Stock Adjustment Dialog */}
      <Dialog open={stockOpen} onOpenChange={setStockOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>{t("products.adjust_stock")}</DialogTitle>
          </DialogHeader>
          {stockProduct && (
            <p className="text-sm text-muted-foreground">
              {stockProduct.name} — Stock: {stockProduct.current_stock} {stockProduct.stock_unit}
            </p>
          )}
          <form onSubmit={onStockAdjust} className="space-y-4">
            <div className="space-y-2">
              <Label>{t("inventory.quantity")} *</Label>
              <Input type="number" {...stockForm.register("quantity")} placeholder="+10 / -5" />
              {stockForm.formState.errors.quantity && (
                <p className="text-xs text-destructive">{stockForm.formState.errors.quantity.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label>{t("inventory.adjustment_reason")} *</Label>
              <Input {...stockForm.register("reason")} />
              {stockForm.formState.errors.reason && (
                <p className="text-xs text-destructive">{stockForm.formState.errors.reason.message}</p>
              )}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setStockOpen(false)}>
                {t("buttons.cancel")}
              </Button>
              <Button type="submit" disabled={stockMutation.isPending}>
                {stockMutation.isPending ? t("buttons.loading") : t("buttons.save")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        description={t("products.delete_confirm")}
        onConfirm={onDelete}
        isLoading={deleteMutation.isPending}
      />
    </>
  );
}
