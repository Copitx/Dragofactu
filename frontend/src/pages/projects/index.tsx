import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useForm } from "react-hook-form";
import { Building2, ExternalLink, TrendingUp, TrendingDown } from "lucide-react";

import { Header } from "@/components/layout/header";
import { DataTable, type Column } from "@/components/data-table/data-table";
import { DataTableToolbar } from "@/components/data-table/toolbar";
import { DataTablePagination } from "@/components/data-table/pagination";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";

import { projectsApi, type Project } from "@/api/projects";
import { useClients } from "@/hooks/use-clients";
import { formatCurrency } from "@/lib/utils";

const STATUS_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  paused: "bg-yellow-100 text-yellow-800",
  completed: "bg-blue-100 text-blue-800",
  cancelled: "bg-gray-100 text-gray-800",
};

export default function ProjectsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize] = useState(25);
  const [statusFilter, setStatusFilter] = useState("");
  const [formOpen, setFormOpen] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ["projects", { search, page, pageSize, status: statusFilter }],
    queryFn: () => projectsApi.list({
      skip: page * pageSize,
      limit: pageSize,
      search: search || undefined,
      status: statusFilter || undefined,
    }),
  });

  const { data: clientsData } = useClients({ limit: 500 });
  const clients = clientsData?.items || [];

  type ProjectFormValues = {
    name: string;
    client_id: string;
    address: string;
    start_date: string;
    estimated_value: string;
    notes: string;
  };

  const form = useForm<ProjectFormValues>({
    defaultValues: {
      name: "",
      client_id: "",
      address: "",
      start_date: "",
      estimated_value: "",
      notes: "",
    },
  });

  const createMutation = useMutation({
    mutationFn: (values: ProjectFormValues) =>
      projectsApi.create({
        name: values.name,
        client_id: values.client_id || undefined,
        address: values.address || undefined,
        start_date: values.start_date || undefined,
        estimated_value: values.estimated_value ? parseFloat(values.estimated_value) : 0,
        notes: values.notes || undefined,
      }),
    onSuccess: (project) => {
      qc.invalidateQueries({ queryKey: ["projects"] });
      toast.success(t("projects.created"));
      setFormOpen(false);
      form.reset();
      navigate(`/projects/${project.id}`);
    },
    onError: () => toast.error(t("common.error")),
  });

  const columns: Column<Project>[] = [
    {
      key: "code",
      header: t("projects.code"),
      cell: (p) => <span className="font-mono text-xs">{p.code}</span>,
    },
    {
      key: "name",
      header: t("projects.name"),
      cell: (p) => (
        <div>
          <span className="font-medium">{p.name}</span>
          {p.client_name && (
            <span className="text-xs text-muted-foreground ml-2">• {p.client_name}</span>
          )}
        </div>
      ),
    },
    {
      key: "status",
      header: t("projects.status"),
      cell: (p) => (
        <Badge className={STATUS_COLORS[p.status] || ""} variant="outline">
          {t(`projects.statuses.${p.status}`)}
        </Badge>
      ),
      className: "hidden sm:table-cell",
    },
    {
      key: "estimated_value",
      header: t("projects.estimated_value"),
      cell: (p) => formatCurrency(p.estimated_value),
      className: "hidden md:table-cell text-right",
    },
    {
      key: "total_expenses",
      header: t("projects.total_expenses"),
      cell: (p) => {
        const expenses = p.total_expenses || 0;
        const estimated = p.estimated_value || 0;
        const over = expenses > estimated && estimated > 0;
        return (
          <span className={over ? "text-red-600" : ""}>
            {formatCurrency(expenses)}
          </span>
        );
      },
      className: "hidden lg:table-cell text-right",
    },
    {
      key: "margin",
      header: t("projects.margin"),
      cell: (p) => {
        const estimated = p.estimated_value || 0;
        const expenses = p.total_expenses || 0;
        if (estimated === 0) return "—";
        const margin = estimated - expenses;
        const pct = (margin / estimated * 100).toFixed(0);
        return (
          <span className={`flex items-center gap-1 justify-end ${margin >= 0 ? "text-green-600" : "text-red-600"}`}>
            {margin >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {pct}%
          </span>
        );
      },
      className: "hidden xl:table-cell text-right",
    },
    {
      key: "actions",
      header: "",
      className: "w-10",
      cell: (p) => (
        <Button variant="ghost" size="icon" className="h-8 w-8"
          onClick={(e) => { e.stopPropagation(); navigate(`/projects/${p.id}`); }}>
          <ExternalLink className="h-4 w-4" />
        </Button>
      ),
    },
  ];

  return (
    <>
      <Header title={t("projects.title")} />
      <div className="p-4 md:p-6 space-y-4">
        <DataTableToolbar
          searchValue={search}
          onSearchChange={(v) => { setSearch(v); setPage(0); }}
          searchPlaceholder={t("projects.search_placeholder")}
          onAdd={() => setFormOpen(true)}
          addLabel={t("projects.new")}
        >
          <Select value={statusFilter} onValueChange={(v) => { setStatusFilter(v === "_all" ? "" : v); setPage(0); }}>
            <SelectTrigger className="w-36 h-8 text-xs">
              <SelectValue placeholder={t("projects.all_statuses")} />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="_all">{t("projects.all_statuses")}</SelectItem>
              <SelectItem value="active">{t("projects.statuses.active")}</SelectItem>
              <SelectItem value="paused">{t("projects.statuses.paused")}</SelectItem>
              <SelectItem value="completed">{t("projects.statuses.completed")}</SelectItem>
              <SelectItem value="cancelled">{t("projects.statuses.cancelled")}</SelectItem>
            </SelectContent>
          </Select>
        </DataTableToolbar>

        <div className="rounded-md border">
          <DataTable
            columns={columns}
            data={data?.items || []}
            isLoading={isLoading}
            keyExtractor={(p) => p.id}
            onRowClick={(p) => navigate(`/projects/${p.id}`)}
          />
        </div>

        <DataTablePagination
          page={page}
          pageSize={pageSize}
          total={data?.total || 0}
          onPageChange={setPage}
          onPageSizeChange={() => {}}
        />
      </div>

      {/* Create Dialog */}
      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>
              <Building2 className="inline h-4 w-4 mr-2" />
              {t("projects.new")}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={form.handleSubmit((v) => createMutation.mutate(v))} className="space-y-4">
            <div className="space-y-2">
              <Label>{t("projects.name")} *</Label>
              <Input {...form.register("name", { required: true })} placeholder="Piscina Familia García..." />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t("projects.client")}</Label>
                <select className="w-full border rounded px-2 py-1.5 text-sm bg-background"
                  {...form.register("client_id")}>
                  <option value="">{t("projects.no_client")}</option>
                  {clients.map((c) => (
                    <option key={c.id} value={c.id}>{c.code} — {c.name}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-2">
                <Label>{t("projects.estimated_value")} (€)</Label>
                <Input type="number" {...form.register("estimated_value")} min={0} step="0.01" />
              </div>
            </div>
            <div className="space-y-2">
              <Label>{t("projects.address")}</Label>
              <Input {...form.register("address")} placeholder="Calle, número, municipio..." />
            </div>
            <div className="space-y-2">
              <Label>{t("projects.start_date")}</Label>
              <Input type="date" {...form.register("start_date")} />
            </div>
            <div className="space-y-2">
              <Label>{t("projects.notes")}</Label>
              <Textarea {...form.register("notes")} rows={2} />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setFormOpen(false)}>
                {t("buttons.cancel")}
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? t("buttons.loading") : t("buttons.save")}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </>
  );
}
