import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { authApi } from "./AuthApi";
import type { LoginRequest, User } from "../../types/auth";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(
  undefined
);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = sessionStorage.getItem("access_token");

    if (!token) {
      setLoading(false);
      return;
    }

    authApi
      .getCurrentUser()
      .then(setUser)
      .catch(() => {
        sessionStorage.removeItem("access_token");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (data: LoginRequest) => {
    const result = await authApi.login(data);

    sessionStorage.setItem("access_token", result.access_token);

    try {
      const currentUser = await authApi.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      sessionStorage.removeItem("access_token");
      throw error;
    }
  };

  const logout = () => {
    sessionStorage.removeItem("access_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
}