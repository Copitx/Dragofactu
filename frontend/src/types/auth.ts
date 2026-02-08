export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: UserResponse;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterCompanyRequest {
  company_code: string;
  company_name: string;
  company_tax_id?: string;
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export interface UserResponse {
  id: string;
  company_id: string;
  username: string;
  email: string;
  full_name: string;
  first_name?: string;
  last_name?: string;
  role: string;
  is_active: boolean;
  company_name?: string;
}
