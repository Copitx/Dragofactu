import api from "./client";
import type {
  LoginRequest,
  LoginResponse,
  RegisterCompanyRequest,
  UserResponse,
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
  const response = await api.post<MessageResponse>("/auth/logout");
  return response.data;
}
