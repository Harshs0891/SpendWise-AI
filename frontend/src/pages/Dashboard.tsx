import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useAuth } from "../features/auth/AuthContext";
import { useDashboard } from "../features/dashboard/useDashboard";

// Format monetary values consistently using the currency returned by the API.
const formatMoney = (amount: number, currency: string) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(amount);

export default function Dashboard() {
  const { user, logout } = useAuth();

  const {
    summary,
    cashFlow,
    categoryBreakdown,
    recentTransactions,
    accountBalances,
  } = useDashboard();

  // Wait for the main dashboard requests before rendering the financial overview.
  const isLoading =
    summary.isLoading ||
    recentTransactions.isLoading ||
    accountBalances.isLoading;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#080b16] p-10 text-white">
        Loading your financial dashboard...
      </div>
    );
  }

  if (summary.isError) {
    return (
      <div className="min-h-screen bg-[#080b16] p-10 text-red-400">
        Unable to load dashboard data. Please refresh.
      </div>
    );
  }

  // Prefer INR so the KPI cards use the same currency as the main charts.
  const summaries = summary.data?.items ?? [];
  const selected = summaries.find((item) => item.currency === "INR")
    ?? summaries[0];

  const currency = selected?.currency ?? "INR";

  return (
    <main className="min-h-screen bg-[#080b16] p-6 text-white md:p-10">
      <header className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">SpendWise AI</h1>
          <p className="mt-1 text-gray-400">
            Welcome back, {user?.email}
          </p>
        </div>

        <button
          onClick={logout}
          className="rounded-lg border border-gray-700 px-4 py-2 hover:bg-gray-800"
        >
          Logout
        </button>
      </header>

      <section className="mb-8 grid gap-5 md:grid-cols-3">
        {[
          {
            title: "Total Income",
            value: selected?.total_income ?? 0,
          },
          {
            title: "Total Expenses",
            value: selected?.total_expenses ?? 0,
          },
          {
            title: "Net Savings",
            value: selected?.net_savings ?? 0,
          },
        ].map((item) => (
          <div
            key={item.title}
            className="rounded-2xl border border-gray-800 bg-[#111827] p-6"
          >
            <p className="text-sm text-gray-400">{item.title}</p>
            <h2 className="mt-4 text-3xl font-bold">
              {formatMoney(item.value, currency)}
            </h2>
          </div>
        ))}
      </section>

      <section className="mb-8 grid gap-5 lg:grid-cols-2">
        <div className="rounded-2xl border border-gray-800 bg-[#111827] p-6">
          <h2 className="mb-6 text-lg font-semibold">
            Monthly Cash Flow
          </h2>

          {cashFlow.isLoading ? (
            <p className="text-gray-400">Loading chart...</p>
          ) : cashFlow.isError ? (
            <p className="text-red-400">Unable to load cash flow.</p>
          ) : (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={cashFlow.data?.items ?? []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="month" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip />
                  <Bar dataKey="income" fill="#22c55e" />
                  <Bar dataKey="expenses" fill="#ef4444" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        <div className="rounded-2xl border border-gray-800 bg-[#111827] p-6">
          <h2 className="mb-6 text-lg font-semibold">
            Expense Breakdown
          </h2>

          {categoryBreakdown.isLoading ? (
            <p className="text-gray-400">Loading chart...</p>
          ) : categoryBreakdown.isError ? (
            <p className="text-red-400">Unable to load categories.</p>
          ) : (categoryBreakdown.data?.items.length ?? 0) === 0 ? (
            <p className="text-gray-400">No expense data yet.</p>
          ) : (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryBreakdown.data?.items ?? []}
                    dataKey="total"
                    nameKey="category_name"
                    outerRadius={100}
                    label
                  >
                    {(categoryBreakdown.data?.items ?? []).map((item) => (
                      <Cell key={item.category_id ?? item.category_name} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </section>

      <section className="mb-8 rounded-2xl border border-gray-800 bg-[#111827] p-6">
        <h2 className="mb-5 text-lg font-semibold">Recent Transactions</h2>

        {recentTransactions.data?.items.length === 0 ? (
          <p className="text-gray-400">No transactions yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-gray-400">
                <tr>
                  <th className="p-3">Description</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Date</th>
                  <th className="p-3">Amount</th>
                </tr>
              </thead>
              <tbody>
                {recentTransactions.data?.items.map((transaction) => (
                  <tr key={transaction.id} className="border-t border-gray-800">
                    <td className="p-3">{transaction.description}</td>
                    <td className="p-3">
                      {transaction.category_name ?? "Uncategorized"}
                    </td>
                    <td className="p-3">{transaction.transaction_date}</td>
                    <td className={`p-3 font-semibold ${
                      transaction.type === "income"
                        ? "text-green-400"
                        : "text-red-400"
                    }`}>
                      {transaction.type === "income" ? "+" : "-"}
                      {formatMoney(transaction.amount, transaction.currency)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="rounded-2xl border border-gray-800 bg-[#111827] p-6">
        <h2 className="mb-5 text-lg font-semibold">Account Balances</h2>

        {accountBalances.data?.items.length === 0 ? (
          <p className="text-gray-400">No accounts created yet.</p>
        ) : (
          <div className="grid gap-4 md:grid-cols-3">
            {accountBalances.data?.items.map((account) => (
              <div
                key={account.account_id}
                className="rounded-xl border border-gray-700 p-4"
              >
                <p className="text-gray-400">{account.account_name}</p>
                <p className="mt-2 text-xl font-semibold">
                  {formatMoney(account.balance, account.currency)}
                </p>
                <p className="mt-1 text-xs text-gray-500">
                  {account.account_type} · {account.balance_type}
                </p>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}