export interface AuditLogEntry {
  id: string;
  company_id: string;
  user_id: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  details: string | null;
  created_at: string;
}

export interface AuditListParams {
  skip?: number;
  limit?: number;
  action?: string;
  entity_type?: string;
}
