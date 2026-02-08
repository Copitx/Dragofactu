import { useState } from "react";
import { useTranslation } from "react-i18next";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { TrendingUp, Receipt, CreditCard, Clock } from "lucide-react";

import { Header } from "@/components/layout/header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { useMonthlyReport, useQuarterlyReport, useAnnualReport } from "@/hooks/use-reports";
import { formatCurrency } from "@/lib/utils";

type ReportType = "monthly" | "quarterly" | "annual";

const currentYear = new Date().getFullYear();
const currentMonth = new Date().getMonth() + 1;
const currentQuarter = Math.ceil(currentMonth / 3);

export default function ReportsPage() {
  const { t } = useTranslation();
  const [reportType, setReportType] = useState<ReportType>("monthly");
  const [year, setYear] = useState(currentYear);
  const [month, setMonth] = useState(currentMonth);
  const [quarter, setQuarter] = useState(currentQuarter);

  const monthlyQuery = useMonthlyReport(
    reportType === "monthly" ? year : 0,
    reportType === "monthly" ? month : 0
  );
  const quarterlyQuery = useQuarterlyReport(
    reportType === "quarterly" ? year : 0,
    reportType === "quarterly" ? quarter : 0
  );
  const annualQuery = useAnnualReport(
    reportType === "annual" ? year : 0
  );

  const isLoading = monthlyQuery.isLoading || quarterlyQuery.isLoading || annualQuery.isLoading;

  // Get the period data based on report type
  const periodData = reportType === "monthly" ? monthlyQuery.data
    : reportType === "quarterly" ? quarterlyQuery.data
    : null;

  const annualData = reportType === "annual" ? annualQuery.data : null;

  // Summary cards data
  const totalInvoiced = annualData?.total_invoiced ?? periodData?.total_invoiced ?? 0;
  const totalPaid = annualData?.total_paid ?? periodData?.total_paid ?? 0;
  const totalPending = annualData?.total_pending ?? periodData?.total_pending ?? 0;
  const docCount = periodData?.document_count ?? 0;

  // Chart data
  const chartData = annualData
    ? annualData.months.map((m, i) => ({
        name: `${i + 1}`,
        invoiced: m.total_invoiced,
        paid: m.total_paid,
        pending: m.total_pending,
      }))
    : periodData?.by_type.map((bt) => ({
        name: bt.type === "quote" ? t("documents.types.quote") :
              bt.type === "invoice" ? t("documents.types.invoice") :
              t("documents.types.delivery_note"),
        count: bt.count,
        total: bt.total,
      })) || [];

  const stats = [
    { label: t("reports.total_invoiced"), value: formatCurrency(totalInvoiced), icon: Receipt, color: "text-blue-500" },
    { label: t("reports.total_collected"), value: formatCurrency(totalPaid), icon: CreditCard, color: "text-green-500" },
    { label: t("reports.pending_amount"), value: formatCurrency(totalPending), icon: Clock, color: "text-orange-500" },
    ...(periodData ? [{ label: "Documentos", value: String(docCount), icon: TrendingUp, color: "text-purple-500" }] : []),
  ];

  return (
    <>
      <Header title={t("reports.title")} />
      <div className="p-4 md:p-6 space-y-6">
        {/* Controls */}
        <div className="flex flex-wrap items-end gap-4">
          <div className="space-y-2">
            <Label>Tipo</Label>
            <div className="flex gap-1">
              {(["monthly", "quarterly", "annual"] as const).map((rt) => (
                <Button
                  key={rt}
                  variant={reportType === rt ? "default" : "outline"}
                  size="sm"
                  onClick={() => setReportType(rt)}
                >
                  {t(`reports.${rt}`)}
                </Button>
              ))}
            </div>
          </div>
          <div className="space-y-2">
            <Label>{t("reports.year")}</Label>
            <Input
              type="number"
              value={year}
              onChange={(e) => setYear(Number(e.target.value))}
              min={2020}
              max={2100}
              className="w-24"
            />
          </div>
          {reportType === "monthly" && (
            <div className="space-y-2">
              <Label>{t("reports.month")}</Label>
              <Select value={String(month)} onValueChange={(v) => setMonth(Number(v))}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Array.from({ length: 12 }, (_, i) => (
                    <SelectItem key={i + 1} value={String(i + 1)}>{i + 1}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
          {reportType === "quarterly" && (
            <div className="space-y-2">
              <Label>{t("reports.quarter")}</Label>
              <Select value={String(quarter)} onValueChange={(v) => setQuarter(Number(v))}>
                <SelectTrigger className="w-[100px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {[1, 2, 3, 4].map((q) => (
                    <SelectItem key={q} value={String(q)}>Q{q}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        {/* Stats Cards */}
        {isLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="rounded-lg border bg-card p-4 animate-pulse h-20" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
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
        )}

        {/* Chart */}
        {!isLoading && chartData.length > 0 && (
          <div className="rounded-lg border bg-card p-4">
            <ResponsiveContainer width="100%" height={350}>
              {annualData ? (
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="name" className="text-xs" />
                  <YAxis className="text-xs" />
                  <Tooltip
                    contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
                    labelStyle={{ color: "hsl(var(--foreground))" }}
                  />
                  <Legend />
                  <Bar dataKey="invoiced" fill="hsl(var(--primary))" name={t("reports.total_invoiced")} />
                  <Bar dataKey="paid" fill="hsl(142 76% 36%)" name={t("reports.total_collected")} />
                  <Bar dataKey="pending" fill="hsl(38 92% 50%)" name={t("reports.pending_amount")} />
                </BarChart>
              ) : (
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis dataKey="name" className="text-xs" />
                  <YAxis className="text-xs" />
                  <Tooltip
                    contentStyle={{ backgroundColor: "hsl(var(--card))", border: "1px solid hsl(var(--border))" }}
                    labelStyle={{ color: "hsl(var(--foreground))" }}
                  />
                  <Bar dataKey="total" fill="hsl(var(--primary))" name="Total" />
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </>
  );
}
