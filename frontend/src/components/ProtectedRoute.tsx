import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../features/auth/AuthContextValue";

// Wait for session restoration before deciding whether to render a private page.
export default function ProtectedRoute() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#080b16] text-white">
        Loading SpendWise...
      </div>
    );
  }

  return user ? <Outlet /> : <Navigate to="/login" replace />;
}