import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Package, AlertTriangle, DollarSign, PackageMinus } from "lucide-react";

import { Header } from "@/components/layout/header";
import { DataTable, type Column } from "@/components/data-table/data-table";
import { DataTableToolbar } from "@/components/data-table/toolbar";
import { DataTablePagination } from "@/components/data-table/pagination";
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

import { useProducts, useAdjustStock } from "@/hooks/use-products";
import { stockAdjustmentSchema, type StockAdjustmentFormData } from "@/lib/validators";
import { formatCurrency } from "@/lib/utils";
import type { Product } from "@/types/product";

type StockFilter = "all" | "in_stock" | "low_stock" | "no_stock";

export default function InventoryPage() {
  const { t } = useTranslation();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [stockFilter, setStockFilter] = useState<StockFilter>("all");
  const [stockOpen, setStockOpen] = useState(false);
  const [stockProduct, setStockProduct] = useState<Product | null>(null);

  const { data, isLoading } = useProducts({
    skip: page * pageSize,
    limit: pageSize,
    search: search || undefined,
  });

  const stockMutation = useAdjustStock();

  const stockForm = useForm<StockAdjustmentFormData>({
    resolver: zodResolver(stockAdjustmentSchema),
    defaultValues: { quantity: 0, reason: "" },
  });

  // Filter products based on stock filter
  const filteredItems = (data?.items || []).filter((p) => {
    switch (stockFilter) {
      case "in_stock": return p.current_stock > p.minimum_stock;
      case "low_stock": return p.current_stock > 0 && p.current_stock <= p.minimum_stock;
      case "no_stock": return p.current_stock === 0;
      default: return true;
    }
  });

  // Stats
  const allItems = data?.items || [];
  const totalProducts = data?.total || 0;
  const lowStockCount = allItems.filter((p) => p.is_low_stock).length;
  const totalValue = allItems.reduce((sum, p) => sum + p.sale_price * p.current_stock, 0);

  const openStockAdjust = (product: Product) => {
    setStockProduct(product);
    stockForm.reset({ quantity: 0, reason: "" });
    setStockOpen(true);
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
    {
      key: "stock",
      header: t("products.stock"),
      cell: (p) => (
        <div className="flex items-center gap-2">
          <span className="font-medium">{p.current_stock}</span>
          <span className="text-xs text-muted-foreground">/ {p.minimum_stock}</span>
          {p.current_stock === 0 && <Badge variant="destructive">0</Badge>}
          {p.current_stock > 0 && p.is_low_stock && <Badge variant="warning">Low</Badge>}
        </div>
      ),
    },
    { key: "unit", header: "Unidad", cell: (p) => p.stock_unit, className: "hidden md:table-cell" },
    { key: "value", header: t("inventory.total_value"), cell: (p) => formatCurrency(p.sale_price * p.current_stock), className: "hidden lg:table-cell" },
    {
      key: "actions",
      header: t("common.actions"),
      className: "w-20",
      cell: (p) => (
        <div onClick={(e) => e.stopPropagation()}>
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openStockAdjust(p)}>
            <PackageMinus className="h-4 w-4" />
          </Button>
        </div>
      ),
    },
  ];

  const stats = [
    { label: t("inventory.total_products"), value: totalProducts, icon: Package, color: "text-blue-500" },
    { label: t("inventory.low_stock_items"), value: lowStockCount, icon: AlertTriangle, color: "text-yellow-500" },
    { label: t("inventory.total_value"), value: formatCurrency(totalValue), icon: DollarSign, color: "text-green-500" },
  ];

  return (
    <>
      <Header title={t("inventory.title")} />
      <div className="p-4 md:p-6 space-y-4">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {stats.map((stat) => (
            <div key={stat.label} className="rounded-lg border bg-card p-4">
              <div className="flex items-center gap-3">
                <stat.icon className={`h-5 w-5 ${stat.color}`} />
                <div>
                  <p className="text-sm text-muted-foreground">{stat.label}</p>
                  <p className="text-2xl font-bold">{stat.value}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Toolbar with filter */}
        <DataTableToolbar
          searchValue={search}
          onSearchChange={(v) => { setSearch(v); setPage(0); }}
          searchPlaceholder={t("products.search_placeholder")}
        >
          <Select value={stockFilter} onValueChange={(v) => { setStockFilter(v as StockFilter); setPage(0); }}>
            <SelectTrigger className="w-[160px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("inventory.filter_all")}</SelectItem>
              <SelectItem value="in_stock">{t("inventory.filter_in_stock")}</SelectItem>
              <SelectItem value="low_stock">{t("inventory.filter_low_stock")}</SelectItem>
              <SelectItem value="no_stock">{t("inventory.filter_no_stock")}</SelectItem>
            </SelectContent>
          </Select>
        </DataTableToolbar>

        <div className="rounded-md border">
          <DataTable
            columns={columns}
            data={filteredItems}
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

      {/* Stock Adjustment Dialog */}
      <Dialog open={stockOpen} onOpenChange={setStockOpen}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>{t("inventory.adjust_stock")}</DialogTitle>
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
    </>
  );
}
