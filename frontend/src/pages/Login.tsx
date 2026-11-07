import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../features/auth/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      await login({ email, password });
      navigate("/dashboard");
    } catch {
      setError("Invalid email or password. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#080b16] px-4 text-white">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md space-y-5 rounded-2xl border border-gray-800 bg-[#111827] p-8"
      >
        <div>
          <h1 className="text-3xl font-bold">Welcome back</h1>
          <p className="mt-2 text-gray-400">
            Sign in to your SpendWise account.
          </p>
        </div>

        {error && (
          <p role="alert" className="text-sm text-red-400">
            {error}
          </p>
        )}

        <div>
          <label htmlFor="email" className="mb-2 block text-sm">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-lg border border-gray-700 bg-[#080b16] p-3 outline-none focus:border-cyan-400"
          />
        </div>

        <div>
          <label htmlFor="password" className="mb-2 block text-sm">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-lg border border-gray-700 bg-[#080b16] p-3 outline-none focus:border-cyan-400"
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-cyan-500 p-3 font-semibold text-black hover:bg-cyan-400 disabled:opacity-50"
        >
          {submitting ? "Signing in..." : "Sign in"}
        </button>

        <p className="text-center text-sm text-gray-400">
          Don't have an account?{" "}
          <Link to="/register" className="text-cyan-400">
            Register
          </Link>
        </p>
      </form>
    </main>
  );
}