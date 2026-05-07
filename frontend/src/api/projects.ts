import api from "@/api/client";

export interface ProjectExpense {
  id: string;
  project_id: string;
  company_id: string;
  date: string;
  description: string;
  supplier?: string;
  document_ref?: string;
  amount: number;
  category: "material" | "labor" | "subcontract" | "other";
  worker_id?: string;
  notes?: string;
  created_at?: string;
  worker_name?: string;
}

export interface ProjectDocument {
  id: string;
  project_id: string;
  document_id: string;
  company_id: string;
  linked_at?: string;
  doc_code?: string;
  doc_type?: string;
  doc_status?: string;
  doc_total?: number;
}

export interface Project {
  id: string;
  company_id: string;
  code: string;
  name: string;
  client_id?: string;
  client_name?: string;
  address?: string;
  status: "active" | "paused" | "completed" | "cancelled";
  start_date?: string;
  end_date?: string;
  estimated_value: number;
  notes?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
  total_expenses?: number;
  total_invoiced?: number;
}

export interface ProjectDetail extends Project {
  expenses: ProjectExpense[];
  documents: ProjectDocument[];
}

export interface ProjectSummaryKPIs {
  estimated_value: number;
  total_expenses: number;
  total_invoiced: number;
  margin: number;
  margin_pct?: number;
}

export interface ProjectCreate {
  name: string;
  client_id?: string;
  address?: string;
  status?: string;
  start_date?: string;
  end_date?: string;
  estimated_value?: number;
  notes?: string;
}

export interface ProjectExpenseCreate {
  date: string;
  description: string;
  supplier?: string;
  document_ref?: string;
  amount?: number;
  category?: string;
  worker_id?: string;
  notes?: string;
}

export interface ProjectListParams {
  skip?: number;
  limit?: number;
  search?: string;
  status?: string;
  client_id?: string;
}

export interface ProjectList {
  items: Project[];
  total: number;
  skip: number;
  limit: number;
}

export const projectsApi = {
  list: (params?: ProjectListParams) =>
    api.get<ProjectList>("/projects", { params }).then((r) => r.data),

  get: (id: string) =>
    api.get<ProjectDetail>(`/projects/${id}`).then((r) => r.data),

  create: (data: ProjectCreate) =>
    api.post<Project>("/projects", data).then((r) => r.data),

  update: (id: string, data: Partial<ProjectCreate>) =>
    api.put<Project>(`/projects/${id}`, data).then((r) => r.data),

  delete: (id: string) =>
    api.delete(`/projects/${id}`),

  // Expenses
  addExpense: (projectId: string, data: ProjectExpenseCreate) =>
    api.post<ProjectExpense>(`/projects/${projectId}/expenses`, data).then((r) => r.data),

  deleteExpense: (projectId: string, expenseId: string) =>
    api.delete(`/projects/${projectId}/expenses/${expenseId}`),

  // Documents
  linkDocument: (projectId: string, documentId: string) =>
    api.post<ProjectDocument>(`/projects/${projectId}/documents/${documentId}`).then((r) => r.data),

  unlinkDocument: (projectId: string, documentId: string) =>
    api.delete(`/projects/${projectId}/documents/${documentId}`),

  // KPIs
  summary: (projectId: string) =>
    api.get<ProjectSummaryKPIs>(`/projects/${projectId}/summary`).then((r) => r.data),
};
