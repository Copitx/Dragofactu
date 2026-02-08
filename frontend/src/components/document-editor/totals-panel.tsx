import { useTranslation } from "react-i18next";
import { formatCurrency } from "@/lib/utils";
import { TAX_RATE } from "@/lib/constants";

interface TotalsPanelProps {
  subtotal: number;
  taxAmount?: number;
  total?: number;
}

export function TotalsPanel({ subtotal, taxAmount, total }: TotalsPanelProps) {
  const { t } = useTranslation();
  const tax = taxAmount ?? subtotal * TAX_RATE;
  const grandTotal = total ?? subtotal + tax;

  return (
    <div className="flex flex-col items-end gap-1 pt-4 border-t">
      <div className="flex justify-between w-64 text-sm">
        <span className="text-muted-foreground">{t("documents.subtotal")}</span>
        <span>{formatCurrency(subtotal)}</span>
      </div>
      <div className="flex justify-between w-64 text-sm">
        <span className="text-muted-foreground">{t("documents.tax")} (21%)</span>
        <span>{formatCurrency(tax)}</span>
      </div>
      <div className="flex justify-between w-64 text-base font-semibold pt-1 border-t">
        <span>{t("documents.total")}</span>
        <span>{formatCurrency(grandTotal)}</span>
      </div>
    </div>
  );
}
