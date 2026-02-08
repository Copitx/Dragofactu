export interface DocumentTypeSummary {
  type: string;
  count: number;
  total: number;
}

export interface PeriodReport {
  period_start: string;
  period_end: string;
  total_invoiced: number;
  total_quotes: number;
  total_paid: number;
  total_pending: number;
  document_count: number;
  by_type: DocumentTypeSummary[];
}

export interface AnnualReport {
  year: number;
  total_invoiced: number;
  total_paid: number;
  total_pending: number;
  months: PeriodReport[];
}
