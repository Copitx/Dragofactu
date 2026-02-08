export interface Supplier {
  id: string;
  company_id: string;
  code: string;
  name: string;
  tax_id?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  province?: string;
  country?: string;
  phone?: string;
  email?: string;
  website?: string;
  notes?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SupplierCreate {
  code: string;
  name: string;
  tax_id?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  province?: string;
  country?: string;
  phone?: string;
  email?: string;
  website?: string;
  notes?: string;
}

export type SupplierUpdate = Partial<SupplierCreate>;

export interface SupplierListParams {
  skip?: number;
  limit?: number;
  search?: string;
  active_only?: boolean;
}
