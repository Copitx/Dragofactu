import { useQuery } from "@tanstack/react-query";
import { getMonthlyReport, getQuarterlyReport, getAnnualReport } from "@/api/reports";

export function useMonthlyReport(year: number, month: number) {
  return useQuery({
    queryKey: ["reports", "monthly", year, month],
    queryFn: () => getMonthlyReport(year, month),
    enabled: year > 0 && month > 0,
  });
}

export function useQuarterlyReport(year: number, quarter: number) {
  return useQuery({
    queryKey: ["reports", "quarterly", year, quarter],
    queryFn: () => getQuarterlyReport(year, quarter),
    enabled: year > 0 && quarter > 0,
  });
}

export function useAnnualReport(year: number) {
  return useQuery({
    queryKey: ["reports", "annual", year],
    queryFn: () => getAnnualReport(year),
    enabled: year > 0,
  });
}
