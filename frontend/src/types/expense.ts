export type ExpenseStatus = "pending" | "paid" | "partial";

export type ExpenseCategory =
  | "material"
  | "labor"
  | "payroll"
  | "fuel"
  | "utilities"
  | "subcontract"
  | "tax"
  | "other";

export interface CompanyExpense {
  id: string;
  company_id: string;
  expense_date: string;
  supplier: string;
  concept: string;
  invoice_ref?: string;
  net_amount?: number;
  vat_rate?: number;
  vat_amount?: number;
  total_amount: number;
  category?: ExpenseCategory;
  status: ExpenseStatus;
  payment_method?: string;
  payment_date?: string;
  paid_by?: string;
  project_id?: string;
  project_name?: string;
  notes?: string;
  user_id: string;
  created_at?: string;
  updated_at?: string;
}

export interface CompanyExpenseCreate {
  expense_date: string;
  supplier: string;
  concept: string;
  invoice_ref?: string;
  net_amount?: number;
  vat_rate?: number;
  vat_amount?: number;
  total_amount: number;
  category?: ExpenseCategory;
  status?: ExpenseStatus;
  payment_method?: string;
  payment_date?: string;
  paid_by?: string;
  project_id?: string;
  notes?: string;
}

export interface CompanyExpenseUpdate extends Partial<CompanyExpenseCreate> {}

export interface ExpenseListParams {
  skip?: number;
  limit?: number;
  status?: ExpenseStatus;
  category?: ExpenseCategory;
  project_id?: string;
  date_from?: string;
  date_to?: string;
  supplier?: string;
  search?: string;
  year?: number;
  month?: number;
}

export interface ExpenseListResponse {
  items: CompanyExpense[];
  total: number;
  skip: number;
  limit: number;
}

export interface MarkExpensePaidRequest {
  payment_method?: string;
  payment_date?: string;
  paid_by?: string;
}

export interface ExpenseMonthlySummary {
  year: number;
  month: number;
  total_amount: number;
  pending_amount: number;
  paid_amount: number;
  partial_amount: number;
  by_category: Record<string, number>;
  expense_count: number;
  pending_count: number;
  paid_count: number;
}

export interface SupplierSuggestion {
  name: string;
  last_used?: string;
}
