export interface Reminder {
  id: string;
  company_id: string;
  title: string;
  description?: string;
  due_date?: string;
  priority: string;
  is_completed: boolean;
  is_overdue: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface ReminderCreate {
  title: string;
  description?: string;
  due_date?: string;
  priority?: string;
}

export interface ReminderUpdate {
  title?: string;
  description?: string;
  due_date?: string;
  priority?: string;
  is_completed?: boolean;
}

export interface ReminderListParams {
  skip?: number;
  limit?: number;
  pending_only?: boolean;
  priority?: string;
}
