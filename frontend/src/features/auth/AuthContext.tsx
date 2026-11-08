import { useEffect, useState, type ReactNode } from "react";
import { AuthContext } from "./AuthContextValue";

import { authApi } from "./AuthApi";
import type { LoginRequest, User } from "../../types/auth";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(() =>
    Boolean(sessionStorage.getItem("access_token")),
  );

  // Restore the signed-in user after refresh using the token held in session storage.
  useEffect(() => {
    const token = sessionStorage.getItem("access_token");

    if (!token) return;

    authApi
      .getCurrentUser()
      .then(setUser)
      .catch(() => {
        sessionStorage.removeItem("access_token");
        setUser(null);
      })
      .finally(() => setLoading(false));
  }, []);

  // Save the token, then fetch the profile to populate shared authentication state.
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

  // Clear the browser session token and in-memory user state together.
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

