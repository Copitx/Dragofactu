import { useTranslation } from "react-i18next";
import { Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatCurrency } from "@/lib/utils";
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

export function LineEditor({ lines, onChange, products, disabled }: LineEditorProps) {
  const { t } = useTranslation();

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
    });
  };

  const addLine = () => onChange([...lines, { ...emptyLine }]);

  const removeLine = (index: number) => {
    const next = lines.filter((_, i) => i !== index);
    onChange(next);
  };

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="hidden sm:grid sm:grid-cols-[1fr_2fr_80px_100px_80px_100px_32px] gap-2 text-xs font-medium text-muted-foreground px-1">
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
          className="grid grid-cols-1 sm:grid-cols-[1fr_2fr_80px_100px_80px_100px_32px] gap-2 items-start p-2 rounded-md border bg-muted/30"
        >
          {/* Product selector */}
          <Select
            value={line.product_id || undefined}
            onValueChange={(v) => selectProduct(i, v)}
            disabled={disabled}
          >
            <SelectTrigger className="h-9 text-xs">
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
    </div>
  );
}

export { calcLineSubtotal };
