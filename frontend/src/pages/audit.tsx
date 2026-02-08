import { useState } from "react";
import { useTranslation } from "react-i18next";

import { Header } from "@/components/layout/header";
import { DataTable, type Column } from "@/components/data-table/data-table";
import { DataTablePagination } from "@/components/data-table/pagination";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { useAuditLogs } from "@/hooks/use-audit";
import { formatDateTime } from "@/lib/utils";
import type { AuditLogEntry } from "@/types/audit";

const ACTION_VARIANTS: Record<string, "default" | "success" | "warning" | "destructive"> = {
  create: "success",
  update: "warning",
  delete: "destructive",
};

const ENTITY_TYPES = ["client", "product", "supplier", "document", "worker", "diary", "reminder"];

export default function AuditPage() {
  const { t } = useTranslation();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(50);
  const [action, setAction] = useState<string>("all");
  const [entityType, setEntityType] = useState<string>("all");

  const { data, isLoading } = useAuditLogs({
    skip: page * pageSize,
    limit: pageSize,
    action: action !== "all" ? action : undefined,
    entity_type: entityType !== "all" ? entityType : undefined,
  });

  const parseDetails = (details: string | null): string => {
    if (!details) return "—";
    try {
      const obj = JSON.parse(details);
      return Object.entries(obj)
        .slice(0, 3)
        .map(([k, v]) => `${k}: ${v}`)
        .join(", ");
    } catch {
      return details.slice(0, 100);
    }
  };

  const columns: Column<AuditLogEntry>[] = [
    {
      key: "timestamp",
      header: t("audit.timestamp"),
      cell: (e) => <span className="text-xs">{formatDateTime(e.created_at)}</span>,
      className: "w-40",
    },
    {
      key: "action",
      header: t("audit.action"),
      cell: (e) => (
        <Badge variant={ACTION_VARIANTS[e.action] || "default"}>
          {t(`audit.actions.${e.action}`, e.action)}
        </Badge>
      ),
      className: "w-28",
    },
    {
      key: "entity_type",
      header: t("audit.entity_type"),
      cell: (e) => <span className="capitalize">{e.entity_type}</span>,
      className: "w-28",
    },
    {
      key: "entity_id",
      header: t("audit.entity_id"),
      cell: (e) => e.entity_id ? <span className="font-mono text-xs">{e.entity_id.slice(0, 8)}...</span> : "—",
      className: "hidden md:table-cell w-28",
    },
    {
      key: "details",
      header: t("audit.details"),
      cell: (e) => (
        <span className="text-xs text-muted-foreground line-clamp-1">{parseDetails(e.details)}</span>
      ),
      className: "hidden lg:table-cell",
    },
  ];

  return (
    <>
      <Header title={t("audit.title")} />
      <div className="p-4 md:p-6 space-y-4">
        {/* Filters */}
        <div className="flex flex-wrap gap-3">
          <Select value={action} onValueChange={(v) => { setAction(v); setPage(0); }}>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder={t("audit.filter_action")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("audit.filter_all")}</SelectItem>
              <SelectItem value="create">{t("audit.actions.create")}</SelectItem>
              <SelectItem value="update">{t("audit.actions.update")}</SelectItem>
              <SelectItem value="delete">{t("audit.actions.delete")}</SelectItem>
            </SelectContent>
          </Select>
          <Select value={entityType} onValueChange={(v) => { setEntityType(v); setPage(0); }}>
            <SelectTrigger className="w-[160px]">
              <SelectValue placeholder={t("audit.filter_entity")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{t("audit.filter_all")}</SelectItem>
              {ENTITY_TYPES.map((et) => (
                <SelectItem key={et} value={et} className="capitalize">{et}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

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
    </>
  );
}
