export interface Course {
  id: string;
  worker_id: string;
  name: string;
  description?: string;
  provider?: string;
  issue_date?: string;
  expiration_date?: string;
  is_valid: boolean;
  certificate_path?: string;
  created_at: string;
  updated_at: string;
}

export interface CourseCreate {
  name: string;
  description?: string;
  provider?: string;
  issue_date?: string;
  expiration_date?: string;
}

export interface Worker {
  id: string;
  company_id: string;
  code: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone?: string;
  email?: string;
  address?: string;
  position?: string;
  department?: string;
  hire_date?: string;
  salary?: number;
  is_active: boolean;
  courses: Course[];
  created_at: string;
  updated_at: string;
}

export interface WorkerSummary {
  id: string;
  code: string;
  first_name: string;
  last_name: string;
  full_name: string;
  position?: string;
  department?: string;
  is_active: boolean;
}

export interface WorkerCreate {
  code: string;
  first_name: string;
  last_name: string;
  phone?: string;
  email?: string;
  address?: string;
  position?: string;
  department?: string;
  hire_date?: string;
  salary?: number;
}

export type WorkerUpdate = Partial<WorkerCreate>;

export interface WorkerListParams {
  skip?: number;
  limit?: number;
  search?: string;
  department?: string;
  active_only?: boolean;
}
