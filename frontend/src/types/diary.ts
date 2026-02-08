export interface DiaryEntry {
  id: string;
  company_id: string;
  title: string;
  content: string;
  entry_date: string;
  user_id: string;
  tags?: string;
  related_document_id?: string;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
}

export interface DiaryEntryCreate {
  title: string;
  content: string;
  entry_date: string;
  tags?: string;
  related_document_id?: string;
  is_pinned?: boolean;
}

export type DiaryEntryUpdate = Partial<DiaryEntryCreate>;

export interface DiaryListParams {
  skip?: number;
  limit?: number;
  date_from?: string;
  date_to?: string;
  pinned_only?: boolean;
}
