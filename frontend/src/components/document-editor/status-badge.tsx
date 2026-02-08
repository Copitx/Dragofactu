import { useTranslation } from "react-i18next";
import { Badge } from "@/components/ui/badge";
import { STATUS_I18N_MAP, DOC_STATUSES } from "@/lib/constants";

const STATUS_VARIANT: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
  [DOC_STATUSES.DRAFT]: "secondary",
  [DOC_STATUSES.NOT_SENT]: "outline",
  [DOC_STATUSES.SENT]: "default",
  [DOC_STATUSES.ACCEPTED]: "success",
  [DOC_STATUSES.REJECTED]: "destructive",
  [DOC_STATUSES.PAID]: "success",
  [DOC_STATUSES.PARTIALLY_PAID]: "warning",
  [DOC_STATUSES.CANCELLED]: "destructive",
};

export function StatusBadge({ status }: { status: string }) {
  const { t } = useTranslation();
  const i18nKey = STATUS_I18N_MAP[status] || status;
  const variant = STATUS_VARIANT[status] || "secondary";

  return (
    <Badge variant={variant}>
      {t(`documents.statuses.${i18nKey}`)}
    </Badge>
  );
}
