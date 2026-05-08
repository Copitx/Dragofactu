export interface DocumentLine {
  id: string;
  document_id: string;
  line_type: "product" | "text";
  product_id?: string;
  description: string;
  quantity: number;
  unit_price: number;
  discount_percent: number;
  subtotal: number;
  order_index: number;
  measurements?: string;
}

export interface DocumentLineCreate {
  line_type?: string;
  product_id?: string;
  description: string;
  quantity?: number;
  unit_price?: number;
  discount_percent?: number;
  measurements?: string;
}

export interface Document {
  id: string;
  company_id: string;
  code: string;
  type: string;
  status: string;
  issue_date: string;
  due_date?: string;
  client_id: string;
  parent_document_id?: string;
  subtotal: number;
  tax_amount: number;
  total: number;
  notes?: string;
  internal_notes?: string;
  terms?: string;
  // Business fields
  client_reference?: string;
  payment_method?: string;
  execution_location?: string;
  payment_date?: string;
  created_by: string;
  lines: DocumentLine[];
  created_at: string;
  updated_at: string;
}

export interface DocumentSummary {
  id: string;
  code: string;
  type: string;
  status: string;
  issue_date: string;
  due_date?: string;
  client_id: string;
  client_name?: string;
  total: number;
  created_at?: string;
}

export interface DocumentCreate {
  type: string;
  client_id: string;
  issue_date: string;
  due_date?: string;
  notes?: string;
  internal_notes?: string;
  terms?: string;
  client_reference?: string;
  payment_method?: string;
  execution_location?: string;
  lines: DocumentLineCreate[];
}

export interface DocumentUpdate {
  client_id?: string;
  due_date?: string;
  notes?: string;
  internal_notes?: string;
  terms?: string;
  client_reference?: string;
  payment_method?: string;
  execution_location?: string;
  payment_date?: string;
  lines?: DocumentLineCreate[];
}

export interface DocumentListParams {
  skip?: number;
  limit?: number;
  doc_type?: string;
  doc_status?: string;
  client_id?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
}

export interface StatusChange {
  new_status: string;
}
