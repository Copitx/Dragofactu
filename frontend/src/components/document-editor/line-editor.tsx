import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Plus, X, BookOpen, Search } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatCurrency } from "@/lib/utils";
import { supplierCatalogApi } from "@/api/supplier-catalog";
import type { Product } from "@/types/product";

export interface LineRow {
  line_type: string;
  product_id: string;
  description: string;
  quantity: number;
  unit_price: number;
  discount_percent: number;
}

interface LineEditorProps {
  lines: LineRow[];
  onChange: (lines: LineRow[]) => void;
  products: Product[];
  disabled?: boolean;
  defaultDiscount?: number;
}

function calcLineSubtotal(line: LineRow): number {
  return line.quantity * line.unit_price * (1 - line.discount_percent / 100);
}

const emptyLine: LineRow = {
  line_type: "product",
  product_id: "",
  description: "",
  quantity: 1,
  unit_price: 0,
  discount_percent: 0,
};

export function LineEditor({ lines, onChange, products, disabled, defaultDiscount = 0 }: LineEditorProps) {
  const { t } = useTranslation();
  const [catalogOpen, setCatalogOpen] = useState(false);
  const [catalogLineIdx, setCatalogLineIdx] = useState<number>(-1);
  const [catalogSearch, setCatalogSearch] = useState("");

  const { data: catalogResults } = useQuery({
    queryKey: ["catalog-search-inline", catalogSearch],
    queryFn: () => supplierCatalogApi.search({ q: catalogSearch || undefined, limit: 20 }),
    enabled: catalogOpen && catalogSearch.length >= 2,
    staleTime: 30_000,
  });

  const updateLine = (index: number, updates: Partial<LineRow>) => {
    const next = lines.map((l, i) => (i === index ? { ...l, ...updates } : l));
    onChange(next);
  };

  const selectProduct = (index: number, productId: string) => {
    const product = products.find((p) => p.id === productId);
    if (!product) return;
    updateLine(index, {
      product_id: productId,
      description: product.name,
      unit_price: product.sale_price,
      discount_percent: defaultDiscount,
    });
  };

  const selectCatalogEntry = (entry: { product_id: string; product_name: string; sale_price: number }) => {
    if (catalogLineIdx < 0) return;
    updateLine(catalogLineIdx, {
      product_id: entry.product_id,
      description: entry.product_name,
      unit_price: entry.sale_price,
      discount_percent: defaultDiscount,
    });
    setCatalogOpen(false);
    setCatalogSearch("");
  };

  const openCatalog = (index: number) => {
    setCatalogLineIdx(index);
    setCatalogSearch("");
    setCatalogOpen(true);
  };

  const addLine = () => onChange([...lines, { ...emptyLine }]);

  const removeLine = (index: number) => {
    const next = lines.filter((_, i) => i !== index);
    onChange(next);
  };

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="hidden sm:grid sm:grid-cols-[1fr_2fr_80px_100px_80px_100px_56px] gap-2 text-xs font-medium text-muted-foreground px-1">
        <span>{t("documents.lines.product")}</span>
        <span>{t("documents.lines.description")}</span>
        <span>{t("documents.lines.quantity")}</span>
        <span>{t("documents.lines.price")}</span>
        <span>{t("documents.lines.discount")}</span>
        <span>{t("documents.lines.line_total")}</span>
        <span />
      </div>

      {/* Lines */}
      {lines.map((line, i) => (
        <div
          key={i}
          className="grid grid-cols-1 sm:grid-cols-[1fr_2fr_80px_100px_80px_100px_56px] gap-2 items-start p-2 rounded-md border bg-muted/30"
        >
          {/* Product selector + catalog button */}
          <div className="flex gap-1">
            <Select
              value={line.product_id || undefined}
              onValueChange={(v) => selectProduct(i, v)}
              disabled={disabled}
            >
              <SelectTrigger className="h-9 text-xs flex-1 min-w-0">
                <SelectValue placeholder={t("documents.lines.product")} />
              </SelectTrigger>
              <SelectContent>
                {products.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.code} - {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {!disabled && (
              <Button
                type="button"
                variant="outline"
                size="icon"
                className="h-9 w-9 shrink-0"
                onClick={() => openCatalog(i)}
                title={t("catalog.search_in_catalog")}
              >
                <BookOpen className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>

          {/* Description */}
          <Input
            value={line.description}
            onChange={(e) => updateLine(i, { description: e.target.value })}
            placeholder={t("documents.lines.description")}
            className="h-9 text-xs"
            disabled={disabled}
          />

          {/* Quantity */}
          <Input
            type="number"
            min="0.01"
            step="0.01"
            value={line.quantity}
            onChange={(e) => updateLine(i, { quantity: parseFloat(e.target.value) || 0 })}
            className="h-9 text-xs"
            disabled={disabled}
          />

          {/* Price */}
          <Input
            type="number"
            min="0"
            step="0.01"
            value={line.unit_price}
            onChange={(e) => updateLine(i, { unit_price: parseFloat(e.target.value) || 0 })}
            className="h-9 text-xs"
            disabled={disabled}
          />

          {/* Discount */}
          <Input
            type="number"
            min="0"
            max="100"
            step="0.5"
            value={line.discount_percent}
            onChange={(e) => updateLine(i, { discount_percent: parseFloat(e.target.value) || 0 })}
            className="h-9 text-xs"
            disabled={disabled}
          />

          {/* Subtotal (read-only) */}
          <div className="flex items-center h-9 text-xs font-medium px-2">
            {formatCurrency(calcLineSubtotal(line))}
          </div>

          {/* Remove */}
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-9 w-9 text-destructive"
            onClick={() => removeLine(i)}
            disabled={disabled || lines.length <= 1}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>
      ))}

      {/* Add line button */}
      {!disabled && (
        <Button type="button" variant="outline" size="sm" onClick={addLine}>
          <Plus className="h-4 w-4 mr-1" />
          {t("documents.lines.add_line")}
        </Button>
      )}

      {/* Catalog search dialog */}
      <Dialog
        open={catalogOpen}
        onOpenChange={(open) => {
          setCatalogOpen(open);
          if (!open) setCatalogSearch("");
        }}
      >
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{t("catalog.search_in_catalog")}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder={t("catalog.search_placeholder")}
                value={catalogSearch}
                onChange={(e) => setCatalogSearch(e.target.value)}
                autoFocus
              />
            </div>
            {catalogSearch.length < 2 ? (
              <p className="text-sm text-muted-foreground text-center py-6">
                {t("catalog.type_to_search")}
              </p>
            ) : !catalogResults || catalogResults.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-6">
                {t("catalog.empty_global")}
              </p>
            ) : (
              <div className="space-y-1 max-h-72 overflow-y-auto">
                {catalogResults.map((entry) => (
                  <button
                    key={entry.id}
                    type="button"
                    className="w-full text-left px-3 py-2 rounded-md hover:bg-accent transition-colors border"
                    onClick={() =>
                      selectCatalogEntry({
                        product_id: entry.product_id,
                        product_name: entry.product_name,
                        sale_price: entry.sale_price,
                      })
                    }
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{entry.product_name}</span>
                      <span className="text-sm font-semibold text-primary">
                        {formatCurrency(entry.sale_price)}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                      <span className="text-xs text-muted-foreground">{entry.supplier_name}</span>
                      {entry.supplier_ref && (
                        <span className="text-xs text-muted-foreground">· Ref: {entry.supplier_ref}</span>
                      )}
                      <span className="text-xs text-muted-foreground ml-auto">
                        {t("catalog.purchase_price")}: {formatCurrency(entry.purchase_price)}
                        {entry.margin_pct != null && (
                          <span className={entry.margin_pct >= 0 ? " text-green-600 font-medium" : " text-red-600 font-medium"}>
                            {" "}({entry.margin_pct >= 0 ? "+" : ""}{entry.margin_pct.toFixed(1)}%)
                          </span>
                        )}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export { calcLineSubtotal };
