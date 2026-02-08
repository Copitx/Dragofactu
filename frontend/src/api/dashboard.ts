import api from "./client";

export interface DashboardStats {
  clients_count: number;
  suppliers_count: number;
  products_count: number;
  pending_documents: number;
  low_stock_count: number;
  unpaid_invoices: number;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await api.get<DashboardStats>("/dashboard/stats");
  return response.data;
}
