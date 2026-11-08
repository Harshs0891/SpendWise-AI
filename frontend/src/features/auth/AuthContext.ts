import { createContext, useContext } from "react";
import type { LoginRequest, User } from "../../types/auth";

export interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined,
);

// Keep the hook in a non-component module so React Fast Refresh can safely
// preserve component state in AuthContext.tsx.
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
}
