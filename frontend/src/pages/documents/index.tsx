import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Plus, Eye, Trash2 } from "lucide-react";

import { Header } from "@/components/layout/header";
import { DataTable, type Column } from "@/components/data-table/data-table";
import { DataTablePagination } from "@/components/data-table/pagination";
import { ConfirmDialog } from "@/components/forms/confirm-dialog";
import { StatusBadge } from "@/components/document-editor/status-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { useDocuments, useDeleteDocument } from "@/hooks/use-documents";
import { formatCurrency, formatDate } from "@/lib/utils";
import { DOC_TYPES, TYPE_I18N_MAP, DOC_STATUSES, STATUS_I18N_MAP } from "@/lib/constants";
import type { DocumentSummary } from "@/types/document";

const ALL = "__all__";

export default function DocumentsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(25);
  const [typeFilter, setTypeFilter] = useState(ALL);
  const [statusFilter, setStatusFilter] = useState(ALL);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const { data, isLoading } = useDocuments({
    skip: page * pageSize,
    limit: pageSize,
    doc_type: typeFilter !== ALL ? typeFilter : undefined,
    doc_status: statusFilter !== ALL ? statusFilter : undefined,
  });

  const deleteMutation = useDeleteDocument();

  const onDelete = async () => {
    if (!deletingId) return;
    try {
      await deleteMutation.mutateAsync(deletingId);
      toast.success(t("documents.deleted"));
      setDeleteOpen(false);
      setDeletingId(null);
    } catch {
      toast.error(t("common.error"));
    }
  };

  const typeVariant = (type: string): "default" | "secondary" | "outline" => {
    if (type === DOC_TYPES.INVOICE) return "default";
    if (type === DOC_TYPES.DELIVERY_NOTE) return "secondary";
    return "outline";
  };

  const columns: Column<DocumentSummary>[] = [
    {
      key: "code",
      header: t("documents.code"),
      cell: (d) => <span className="font-mono text-xs">{d.code}</span>,
    },
    {
      key: "type",
      header: t("documents.type"),
      cell: (d) => (
        <Badge variant={typeVariant(d.type)}>
          {t(`documents.types.${TYPE_I18N_MAP[d.type]}`)}
        </Badge>
      ),
    },
    {
      key: "client",
      header: t("documents.client"),
      cell: (d) => <span className="font-medium">{d.client_name || "—"}</span>,
    },
    {
      key: "date",
      header: t("documents.date"),
      cell: (d) => formatDate(d.issue_date),
      className: "hidden md:table-cell",
    },
    {
      key: "total",
      header: t("documents.total"),
      cell: (d) => <span className="font-medium">{formatCurrency(d.total)}</span>,
    },
    {
      key: "status",
      header: t("documents.status"),
      cell: (d) => <StatusBadge status={d.status} />,
    },
    {
      key: "actions",
      header: t("common.actions"),
      className: "w-24",
      cell: (d) => (
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => navigate(`/documents/${d.id}`)}
          >
            <Eye className="h-4 w-4" />
          </Button>
          {d.status === DOC_STATUSES.DRAFT && (
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-destructive"
              onClick={() => {
                setDeletingId(d.id);
                setDeleteOpen(true);
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      ),
    },
  ];

  return (
    <>
      <Header title={t("documents.title")} />
      <div className="p-4 md:p-6 space-y-4">
        {/* Toolbar */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-2">
            {/* Type filter */}
            <Select value={typeFilter} onValueChange={(v) => { setTypeFilter(v); setPage(0); }}>
              <SelectTrigger className="h-9 w-[160px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>{t("documents.type")}: All</SelectItem>
                {Object.entries(DOC_TYPES).map(([key, val]) => (
                  <SelectItem key={val} value={val}>
                    {t(`documents.types.${key}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Status filter */}
            <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v); setPage(0); }}>
              <SelectTrigger className="h-9 w-[160px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL}>{t("documents.status")}: All</SelectItem>
                {Object.entries(DOC_STATUSES).map(([, val]) => (
                  <SelectItem key={val} value={val}>
                    {t(`documents.statuses.${STATUS_I18N_MAP[val]}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button size="sm" onClick={() => navigate("/documents/new")}>
            <Plus className="h-4 w-4 mr-1" />
            {t("documents.new")}
          </Button>
        </div>

        {/* Table */}
        <div className="rounded-md border">
          <DataTable
            columns={columns}
            data={data?.items || []}
            isLoading={isLoading}
            keyExtractor={(d) => d.id}
            onRowClick={(d) => navigate(`/documents/${d.id}`)}
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

      <ConfirmDialog
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        description={t("documents.delete_confirm")}
        onConfirm={onDelete}
        isLoading={deleteMutation.isPending}
      />
    </>
  );
}
