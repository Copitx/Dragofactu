import api from "./client";
import type {
  LoginRequest,
  LoginResponse,
  RegisterCompanyRequest,
  UserResponse,
  CreateUserRequest,
} from "@/types/auth";
import type { MessageResponse } from "@/types/common";

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await api.post<LoginResponse>("/auth/login", data);
  return response.data;
}

export async function register(data: RegisterCompanyRequest): Promise<UserResponse> {
  const response = await api.post<UserResponse>("/auth/register", data);
  return response.data;
}

export async function getMe(): Promise<UserResponse> {
  const response = await api.get<UserResponse>("/auth/me");
  return response.data;
}

export async function logout(): Promise<MessageResponse> {
  const response = await api.post<MessageResponse>("/auth/logout", {});
  return response.data;
}

export async function listCompanyUsers(): Promise<UserResponse[]> {
  const response = await api.get<UserResponse[]>("/auth/users");
  return response.data;
}

export async function createCompanyUser(data: CreateUserRequest): Promise<UserResponse> {
  const response = await api.post<UserResponse>("/auth/users", data);
  return response.data;
}

export async function deactivateCompanyUser(userId: string): Promise<MessageResponse> {
  const response = await api.delete<MessageResponse>(`/auth/users/${userId}`);
  return response.data;
}
