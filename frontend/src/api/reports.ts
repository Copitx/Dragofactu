import api from "./client";
import type { PeriodReport, AnnualReport } from "@/types/report";

export async function getMonthlyReport(year: number, month: number): Promise<PeriodReport> {
  const response = await api.get<PeriodReport>("/reports/monthly", { params: { year, month } });
  return response.data;
}

export async function getQuarterlyReport(year: number, quarter: number): Promise<PeriodReport> {
  const response = await api.get<PeriodReport>("/reports/quarterly", { params: { year, quarter } });
  return response.data;
}

export async function getAnnualReport(year: number): Promise<AnnualReport> {
  const response = await api.get<AnnualReport>("/reports/annual", { params: { year } });
  return response.data;
}
