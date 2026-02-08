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
}

export interface DocumentLineCreate {
  line_type?: string;
  product_id?: string;
  description: string;
  quantity?: number;
  unit_price?: number;
  discount_percent?: number;
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
  lines: DocumentLineCreate[];
}

export interface DocumentUpdate {
  client_id?: string;
  due_date?: string;
  notes?: string;
  internal_notes?: string;
  terms?: string;
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
}

export interface StatusChange {
  new_status: string;
}
