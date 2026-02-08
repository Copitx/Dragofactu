export interface DatabaseInfo {
  engine: string;
  version?: string;
  size?: string;
  active_connections?: number;
  error?: string;
}

export interface RecordCounts {
  companies: number;
  users: number;
  clients: number;
  products: number;
  documents: number;
}

export interface SystemInfo {
  app_version: string;
  debug_mode: boolean;
  database: DatabaseInfo;
  record_counts: RecordCounts;
  timestamp: string;
}

export interface MaintenanceEntry {
  table: string;
  last_vacuum: string | null;
  last_analyze: string | null;
}

export interface BackupInfo {
  provider: string;
  automatic_backups: boolean;
  backup_note: string;
  recent_maintenance?: MaintenanceEntry[];
}
