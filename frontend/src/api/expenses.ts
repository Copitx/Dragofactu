import apiClient from "@/api/client";
import type {
  CompanyExpense,
  CompanyExpenseCreate,
  CompanyExpenseUpdate,
  ExpenseListParams,
  ExpenseListResponse,
  ExpenseMonthlySummary,
  MarkExpensePaidRequest,
  SupplierSuggestion,
} from "@/types/expense";

export const expensesApi = {
  list: async (params: ExpenseListParams = {}): Promise<ExpenseListResponse> => {
    const res = await apiClient.get("/expenses", { params });
    return res.data;
  },

  create: async (data: CompanyExpenseCreate): Promise<CompanyExpense> => {
    const res = await apiClient.post("/expenses", data);
    return res.data;
  },

  get: async (id: string): Promise<CompanyExpense> => {
    const res = await apiClient.get(`/expenses/${id}`);
    return res.data;
  },

  update: async (id: string, data: CompanyExpenseUpdate): Promise<CompanyExpense> => {
    const res = await apiClient.put(`/expenses/${id}`, data);
    return res.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/expenses/${id}`);
  },

  markPaid: async (id: string, data: MarkExpensePaidRequest): Promise<CompanyExpense> => {
    const res = await apiClient.post(`/expenses/${id}/mark-paid`, data);
    return res.data;
  },

  monthlySummary: async (year: number, month: number): Promise<ExpenseMonthlySummary> => {
    const res = await apiClient.get("/expenses/summary/monthly", { params: { year, month } });
    return res.data;
  },

  supplierSuggestions: async (q: string): Promise<SupplierSuggestion[]> => {
    const res = await apiClient.get("/expenses/suppliers/suggestions", { params: { q } });
    return res.data;
  },
};
