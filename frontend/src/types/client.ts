export interface Client {
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

export interface ClientCreate {
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

export type ClientUpdate = Partial<ClientCreate>;

export interface ClientListParams {
  skip?: number;
  limit?: number;
  search?: string;
  active_only?: boolean;
}
