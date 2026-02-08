export interface Product {
  id: string;
  company_id: string;
  code: string;
  name: string;
  description?: string;
  category?: string;
  purchase_price: number;
  sale_price: number;
  current_stock: number;
  minimum_stock: number;
  stock_unit: string;
  supplier_id?: string;
  is_active: boolean;
  is_low_stock: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  code: string;
  name: string;
  description?: string;
  category?: string;
  purchase_price?: number;
  sale_price?: number;
  current_stock?: number;
  minimum_stock?: number;
  stock_unit?: string;
  supplier_id?: string;
}

export type ProductUpdate = Partial<ProductCreate>;

export interface ProductListParams {
  skip?: number;
  limit?: number;
  search?: string;
  category?: string;
  low_stock?: boolean;
  active_only?: boolean;
}

export interface StockAdjustment {
  quantity: number;
  reason?: string;
}
