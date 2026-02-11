import api from "./client";

export interface CompanySettings {
  id: string;
  code: string;
  name: string;
  legal_name?: string;
  tax_id?: string;
  address?: string;
  city?: string;
  postal_code?: string;
  province?: string;
  country?: string;
  phone?: string;
  email?: string;
  website?: string;
  logo_path?: string;
  logo_base64?: string;
  pdf_footer_text?: string;
  default_language: string;
  default_currency: string;
  tax_rate: number;
}

export type CompanySettingsUpdate = Partial<Omit<CompanySettings, "id" | "code">>;

export async function getCompanySettings(): Promise<CompanySettings> {
  const response = await api.get<CompanySettings>("/company/settings");
  return response.data;
}

export async function updateCompanySettings(data: CompanySettingsUpdate): Promise<CompanySettings> {
  const response = await api.put<CompanySettings>("/company/settings", data);
  return response.data;
}
