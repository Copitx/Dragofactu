import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import {
  Users,
  Truck,
  Package,
  FileText,
  AlertTriangle,
  CreditCard,
  Euro,
  Clock,
  Bell,
  Plus,
  FilePlus,
  UserPlus,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { MetricCard } from "@/components/common/metric-card";
import { PageSkeleton } from "@/components/common/loading";
import { useDashboardStats } from "@/hooks/use-dashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const statusColors: Record<string, string> = {
  draft: "bg-gray-500",
  not_sent: "bg-yellow-500",
  sent: "bg-blue-500",
  accepted: "bg-green-500",
  paid: "bg-emerald-600",
};

export default function DashboardPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data: stats, isLoading } = useDashboardStats();

  if (isLoading) {
    return (
      <>
        <Header title={t("dashboard.title")} />
        <PageSkeleton />
      </>
    );
  }

  return (
    <>
      <Header title={t("dashboard.title")} />
      <div className="p-6 space-y-6">
        {/* Metric cards */}
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
          <MetricCard
            title={t("dashboard.clients_count")}
            value={stats?.clients_count ?? 0}
            icon={Users}
          />
          <MetricCard
            title={t("dashboard.suppliers_count")}
            value={stats?.suppliers_count ?? 0}
            icon={Truck}
          />
          <MetricCard
            title={t("dashboard.products_count")}
            value={stats?.products_count ?? 0}
            icon={Package}
          />
          <MetricCard
            title={t("dashboard.pending_documents")}
            value={stats?.pending_documents ?? 0}
            icon={FileText}
            variant="warning"
          />
          <MetricCard
            title={t("dashboard.low_stock")}
            value={stats?.low_stock_count ?? 0}
            icon={AlertTriangle}
            variant={stats?.low_stock_count ? "destructive" : "default"}
          />
          <MetricCard
            title={t("dashboard.unpaid_invoices")}
            value={stats?.unpaid_invoices ?? 0}
            icon={CreditCard}
            variant={stats?.unpaid_invoices ? "warning" : "default"}
          />
        </div>

        {/* Financial summary + Quick Actions row */}
        <div className="grid gap-4 grid-cols-1 lg:grid-cols-3">
          {/* Financial Summary */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Euro className="h-5 w-5" />
                {t("dashboard.financial_summary")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 grid-cols-1 sm:grid-cols-3">
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">{t("dashboard.month_total")}</p>
                  <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {(stats?.month_total ?? 0).toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {stats?.month_invoices ?? 0} {t("dashboard.unpaid_invoices").toLowerCase()}
                  </p>
                </div>
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">{t("dashboard.pending_total")}</p>
                  <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                    {(stats?.pending_total ?? 0).toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                  </p>
                </div>
                <div className="rounded-lg border p-4">
                  <p className="text-sm text-muted-foreground">{t("dashboard.pending_reminders")}</p>
                  <div className="flex items-center gap-2">
                    <Bell className="h-5 w-5 text-muted-foreground" />
                    <p className="text-2xl font-bold">{stats?.pending_reminders ?? 0}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Plus className="h-5 w-5" />
                {t("dashboard.quick_actions")}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                className="w-full justify-start gap-2"
                variant="outline"
                onClick={() => navigate("/documents?new=invoice")}
              >
                <FilePlus className="h-4 w-4" />
                {t("dashboard.new_invoice")}
              </Button>
              <Button
                className="w-full justify-start gap-2"
                variant="outline"
                onClick={() => navigate("/documents?new=quote")}
              >
                <FileText className="h-4 w-4" />
                {t("dashboard.new_quote")}
              </Button>
              <Button
                className="w-full justify-start gap-2"
                variant="outline"
                onClick={() => navigate("/clients?new=true")}
              >
                <UserPlus className="h-4 w-4" />
                {t("dashboard.new_client")}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Recent Pending Documents */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Clock className="h-5 w-5" />
              {t("dashboard.recent_pending_title")}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.recent_pending_docs && stats.recent_pending_docs.length > 0 ? (
              <div className="space-y-3">
                {stats.recent_pending_docs.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between rounded-lg border p-3 hover:bg-muted/50 cursor-pointer transition-colors"
                    onClick={() => navigate(`/documents`)}
                  >
                    <div className="flex items-center gap-3">
                      <Badge variant="secondary" className="font-mono text-xs">
                        {doc.code}
                      </Badge>
                      <span className="text-sm">{doc.client_name || "—"}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium">
                        {doc.total.toLocaleString("es-ES", { style: "currency", currency: "EUR" })}
                      </span>
                      <Badge
                        variant="outline"
                        className={`text-xs text-white ${statusColors[doc.status] ?? "bg-gray-500"}`}
                      >
                        {doc.status}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">
                {t("dashboard.no_pending_docs")}
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
