import api from "@/api/client";

export interface SupplierCatalogEntry {
  id: string;
  company_id: string;
  supplier_id: string;
  product_id: string;
  supplier_ref?: string;
  purchase_price: number;
  lead_time_days: number;
  min_order_qty: number;
  notes?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
  // Denormalized
  product_code?: string;
  product_name?: string;
  product_sale_price?: number;
  product_category?: string;
}

export interface CatalogSearchResult {
  id: string;
  supplier_id: string;
  supplier_name: string;
  supplier_code: string;
  product_id: string;
  product_code: string;
  product_name: string;
  supplier_ref?: string;
  purchase_price: number;
  sale_price: number;
  margin_pct?: number;
  lead_time_days: number;
}

export interface SupplierCatalogEntryCreate {
  product_id: string;
  supplier_ref?: string;
  purchase_price?: number;
  lead_time_days?: number;
  min_order_qty?: number;
  notes?: string;
}

export interface SupplierCatalogEntryUpdate {
  supplier_ref?: string;
  purchase_price?: number;
  lead_time_days?: number;
  min_order_qty?: number;
  notes?: string;
  is_active?: boolean;
}

export const supplierCatalogApi = {
  list: (supplierId: string) =>
    api.get<SupplierCatalogEntry[]>(`/suppliers/${supplierId}/catalog`).then((r) => r.data),

  add: (supplierId: string, data: SupplierCatalogEntryCreate) =>
    api.post<SupplierCatalogEntry>(`/suppliers/${supplierId}/catalog`, data).then((r) => r.data),

  update: (supplierId: string, entryId: string, data: SupplierCatalogEntryUpdate) =>
    api.put<SupplierCatalogEntry>(`/suppliers/${supplierId}/catalog/${entryId}`, data).then((r) => r.data),

  remove: (supplierId: string, entryId: string) =>
    api.delete(`/suppliers/${supplierId}/catalog/${entryId}`),

  search: (params?: { q?: string; supplier_id?: string; limit?: number }) =>
    api.get<CatalogSearchResult[]>("/catalog/search", { params }).then((r) => r.data),
};
