import { useTranslation } from "react-i18next";
import {
  Users,
  Truck,
  Package,
  FileText,
  AlertTriangle,
  CreditCard,
} from "lucide-react";
import { Header } from "@/components/layout/header";
import { MetricCard } from "@/components/common/metric-card";
import { PageSkeleton } from "@/components/common/loading";
import { useDashboardStats } from "@/hooks/use-dashboard";

export default function DashboardPage() {
  const { t } = useTranslation();
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
      <div className="p-6">
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
      </div>
    </>
  );
}
