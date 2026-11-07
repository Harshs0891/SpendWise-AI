import { api } from "../../lib/api";
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
} from "../../types/auth";

// Keep authentication HTTP calls in one place with typed request and response contracts.
export const authApi = {
  async register(data: RegisterRequest): Promise<User> {
    const response = await api.post<User>(
      "/auth/register",
      data
    );

    return response.data;
  },

  async login(data: LoginRequest): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>(
      "/auth/login",
      data
    );

    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>("/users/me");

    return response.data;
  },
};