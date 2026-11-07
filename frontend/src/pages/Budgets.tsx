import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { budgetApi } from "../features/budgets/BudgetApi";
import { categoryApi } from "../features/categories/CategoryApi";

// Return the first day of the current month in YYYY-MM-DD format.
const getCurrentMonth = () => {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`;
};

// Format monetary values using the selected currency.
const formatMoney = (value: number | string, currency: string) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(Number(value));

export default function Budgets() {
  const queryClient = useQueryClient();

  const [periodStart, setPeriodStart] = useState(getCurrentMonth());
  const [categoryId, setCategoryId] = useState("");
  const [amount, setAmount] = useState("");
  const [threshold, setThreshold] = useState("80");
  const [error, setError] = useState("");

  // Load expense categories because budgets apply to spending categories.
  const categories = useQuery({
    queryKey: ["categories", "expense"],
    queryFn: () => categoryApi.getAll("expense"),
  });

  // Fetch budget progress for the selected month.
  const budgets = useQuery({
    queryKey: ["budgets", periodStart, "INR"],
    queryFn: () => budgetApi.getAll(periodStart, "INR"),
  });

  // Refresh budget data after creating or updating a budget.
  const refreshBudgets = async () => {
    await queryClient.invalidateQueries({ queryKey: ["budgets"] });
  };

  const createBudget = useMutation({
    mutationFn: budgetApi.create,
    onSuccess: async () => {
      setCategoryId("");
      setAmount("");
      setThreshold("80");
      setError("");
      await refreshBudgets();
    },
    onError: () => setError("Unable to create budget. Check the selected category."),
  });

  const deleteBudget = useMutation({
    mutationFn: budgetApi.delete,
    onSuccess: refreshBudgets,
    onError: () => setError("Unable to delete budget."),
  });

  // Submit a new budget using the exact backend request schema.
  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    setError("");

    if (!categoryId) {
      setError("Please select an expense category.");
      return;
    }

    createBudget.mutate({
      category_id: categoryId,
      amount: Number(amount),
      currency: "INR",
      period_start: periodStart,
      alert_threshold: Number(threshold),
    });
  };

  // Choose a visual indicator based on the backend-calculated budget status.
  const getStatusColor = (status: string) => {
    switch (status) {
      case "exceeded":
        return "text-red-400";
      case "warning":
        return "text-yellow-400";
      default:
        return "text-green-400";
    }
  };

  return (
    <main className="min-h-screen bg-[#080b16] p-6 text-white md:p-10">
      <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Monthly Budgets</h1>
          <p className="mt-2 text-gray-400">
            Set spending limits and monitor your expenses.
          </p>
        </div>

        <input
          type="month"
          value={periodStart.slice(0, 7)}
          onChange={(event) =>
            setPeriodStart(`${event.target.value}-01`)
          }
          className="rounded-lg border border-gray-700 bg-[#111827] p-3"
        />
      </div>

      <form
        onSubmit={handleSubmit}
        className="mb-10 grid gap-4 rounded-xl border border-gray-800 bg-[#111827] p-6 md:grid-cols-4"
      >
        <select
          required
          value={categoryId}
          onChange={(event) => setCategoryId(event.target.value)}
          className="rounded-lg border border-gray-700 bg-[#080b16] p-3"
        >
          <option value="">Select expense category</option>
          {categories.data?.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </select>

        <input
          type="number"
          required
          min="0.0001"
          step="0.0001"
          placeholder="Budget amount (INR)"
          value={amount}
          onChange={(event) => setAmount(event.target.value)}
          className="rounded-lg border border-gray-700 bg-[#080b16] p-3"
        />

        <input
          type="number"
          required
          min="1"
          max="100"
          placeholder="Alert threshold (%)"
          value={threshold}
          onChange={(event) => setThreshold(event.target.value)}
          className="rounded-lg border border-gray-700 bg-[#080b16] p-3"
        />

        <button
          type="submit"
          disabled={createBudget.isPending}
          className="rounded-lg bg-cyan-500 p-3 font-semibold text-black disabled:opacity-50"
        >
          {createBudget.isPending ? "Creating..." : "Create Budget"}
        </button>

        {error && (
          <p role="alert" className="text-red-400 md:col-span-4">
            {error}
          </p>
        )}
      </form>

      <section>
        <h2 className="mb-5 text-xl font-semibold">Budget Overview</h2>

        {budgets.isLoading ? (
          <p>Loading budgets...</p>
        ) : budgets.isError ? (
          <p className="text-red-400">Unable to load budgets.</p>
        ) : budgets.data?.items.length === 0 ? (
          <p className="text-gray-400">
            No budgets found for this month. Create your first budget.
          </p>
        ) : (
          <div className="grid gap-5 md:grid-cols-2">
            {budgets.data?.items.map((item) => {
              const percentage = Math.min(
                100,
                Math.max(0, Number(item.utilization_percent))
              );

              return (
                <article
                  key={item.budget.id}
                  className="rounded-xl border border-gray-800 bg-[#111827] p-6"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-xl font-semibold">
                        {item.category_name}
                      </h3>
                      <p className="mt-1 text-sm text-gray-400">
                        {item.budget.period_start} to {item.period_end}
                      </p>
                    </div>

                    <span className={`text-sm font-semibold capitalize ${getStatusColor(item.status)}`}>
                      {item.status.replace("_", " ")}
                    </span>
                  </div>

                  <div className="mt-6 flex justify-between text-sm">
                    <span className="text-gray-400">Spent</span>
                    <span>{formatMoney(item.spent, item.budget.currency)}</span>
                  </div>

                  <div className="mt-2 h-3 overflow-hidden rounded-full bg-gray-700">
                    <div
                      className={`h-full rounded-full ${
                        item.status === "exceeded"
                          ? "bg-red-500"
                          : item.status === "warning"
                            ? "bg-yellow-400"
                            : "bg-cyan-400"
                      }`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>

                  <div className="mt-3 flex justify-between text-sm">
                    <span className="text-gray-400">
                      {percentage.toFixed(1)}% used
                    </span>
                    <span>
                      Limit: {formatMoney(item.budget.amount, item.budget.currency)}
                    </span>
                  </div>

                  <p className="mt-3 text-sm text-gray-400">
                    Remaining: {formatMoney(item.remaining, item.budget.currency)}
                  </p>

                  <div className="mt-5 flex justify-end">
                    <button
                      type="button"
                      onClick={() => {
                        if (window.confirm("Delete this budget?")) {
                          deleteBudget.mutate(item.budget.id);
                        }
                      }}
                      disabled={deleteBudget.isPending}
                      className="text-sm text-red-400 hover:text-red-300"
                    >
                      Delete budget
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </main>
  );
}