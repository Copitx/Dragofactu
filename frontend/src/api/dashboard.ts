import api from "./client";

export interface RecentDocument {
  id: string;
  code: string;
  client_name: string;
  total: number;
  status: string;
  type: string;
}

export interface DashboardStats {
  clients_count: number;
  suppliers_count: number;
  products_count: number;
  pending_documents: number;
  low_stock_count: number;
  unpaid_invoices: number;
  month_total: number;
  pending_total: number;
  month_invoices: number;
  pending_reminders: number;
  recent_pending_docs: RecentDocument[];
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const response = await api.get<DashboardStats>("/dashboard/stats");
  return response.data;
}
