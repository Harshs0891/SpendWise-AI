import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useAuth } from "../features/auth/AuthContext";
import { useDashboard } from "../features/dashboard/useDashboard";

// Colors used to distinguish expense categories in the pie chart.
const CATEGORY_COLORS = [
  "#8b5cf6",
  "#06b6d4",
  "#22c55e",
  "#f59e0b",
  "#ef4444",
  "#ec4899",
  "#3b82f6",
  "#14b8a6",
  "#f97316",
  "#a3e635",
];

// Format monetary values consistently using the currency returned by the API.
const formatMoney = (amount: number, currency: string) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(Number(amount));

// Custom tooltip for the expense pie chart.
function ExpenseTooltip({
  active,
  payload,
  currency,
}: {
  active?: boolean;
  payload?: Array<{
    name?: string;
    value?: number;
    payload?: { percentage?: number };
  }>;
  currency: string;
}) {
  if (!active || !payload?.length) return null;

  const item = payload[0];

  return (
    <div className="rounded-lg border border-gray-700 bg-[#080b16] p-3 shadow-xl">
      <p className="font-medium text-white">{item.name}</p>
      <p className="mt-1 text-sm text-cyan-400">
        {formatMoney(Number(item.value ?? 0), currency)}
      </p>
      <p className="text-xs text-gray-400">
        {Number(item.payload?.percentage ?? 0).toFixed(1)}% of expenses
      </p>
    </div>
  );
}

export default function Dashboard() {
  const { user, logout } = useAuth();

  const {
    summary,
    cashFlow,
    categoryBreakdown,
    recentTransactions,
    accountBalances,
  } = useDashboard();

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

  // Prefer INR so the KPI cards and charts use a consistent currency.
  const summaries = summary.data?.items ?? [];

  const selected =
    summaries.find((item) => item.currency === "INR") ?? summaries[0];

  const currency = selected?.currency ?? "INR";

  // Normalize decimal values from the API into JavaScript numbers.
  // Recharts requires numeric values to calculate pie slices correctly.
  const expenseItems = (categoryBreakdown.data?.items ?? [])
    .map((item) => ({
      ...item,
      total: Number(item.total),
      percentage: Number(item.percentage),
    }))
    .filter(
      (item) => Number.isFinite(item.total) && item.total > 0,
    );

  const totalCategoryExpenses = expenseItems.reduce(
    (sum, item) => sum + item.total,
    0,
  );

  return (
    <main className="min-h-screen bg-[#080b16] p-6 text-white md:p-10">
      {/* Dashboard header */}
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

      {/* Financial summary cards */}
      <section className="mb-8 grid gap-5 md:grid-cols-3">
        {[
          {
            title: "Total Income",
            value: Number(selected?.total_income ?? 0),
          },
          {
            title: "Total Expenses",
            value: Number(selected?.total_expenses ?? 0),
          },
          {
            title: "Net Savings",
            value: Number(selected?.net_savings ?? 0),
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

      {/* Financial charts */}
      <section className="mb-8 grid gap-5 lg:grid-cols-2">

        {/* Monthly cash flow */}
        <div className="rounded-2xl border border-gray-800 bg-[#111827] p-6">
          <h2 className="mb-6 text-lg font-semibold">
            Monthly Cash Flow
          </h2>

          {cashFlow.isLoading ? (
            <p className="text-gray-400">Loading chart...</p>
          ) : cashFlow.isError ? (
            <p className="text-red-400">
              Unable to load cash flow.
            </p>
          ) : (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={cashFlow.data?.items ?? []}>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#374151"
                  />
                  <XAxis dataKey="month" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#080b16",
                      border: "1px solid #374151",
                      borderRadius: "8px",
                      color: "#fff",
                    }}
                  />
                  <Legend />
                  <Bar
                    dataKey="income"
                    name="Income"
                    fill="#22c55e"
                    radius={[4, 4, 0, 0]}
                  />
                  <Bar
                    dataKey="expenses"
                    name="Expenses"
                    fill="#ef4444"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Expense breakdown */}
        <div className="rounded-2xl border border-gray-800 bg-[#111827] p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">
              Expense Breakdown
            </h2>

            {totalCategoryExpenses > 0 && (
              <span className="text-sm text-gray-400">
                {formatMoney(totalCategoryExpenses, currency)}
              </span>
            )}
          </div>

          {categoryBreakdown.isLoading ? (
            <div className="flex h-72 items-center justify-center">
              <p className="text-gray-400">Loading expense breakdown...</p>
            </div>
          ) : categoryBreakdown.isError ? (
            <div className="flex h-72 items-center justify-center">
              <p className="text-red-400">
                Unable to load expense categories.
              </p>
            </div>
          ) : expenseItems.length === 0 ? (
            <div className="flex h-72 flex-col items-center justify-center text-center">
              <p className="font-medium text-gray-300">
                No expense data available
              </p>
              <p className="mt-2 text-sm text-gray-500">
                Add categorized expense transactions to see your breakdown.
              </p>
            </div>
          ) : (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={expenseItems}
                    dataKey="total"
                    nameKey="category_name"
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={95}
                    paddingAngle={3}
                    stroke="#111827"
                    strokeWidth={2}
                  >
                    {expenseItems.map((item, index) => (
                      <Cell
                        key={item.category_id ?? item.category_name}
                        fill={
                          CATEGORY_COLORS[index % CATEGORY_COLORS.length]
                        }
                      />
                    ))}
                  </Pie>

                  <Tooltip
                    content={
                      <ExpenseTooltip currency={currency} />
                    }
                  />

                  <Legend
                    verticalAlign="bottom"
                    height={36}
                    formatter={(value) => (
                      <span className="text-xs text-gray-300">
                        {value}
                      </span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </section>

      {/* Recent transactions */}
      <section className="mb-8 rounded-2xl border border-gray-800 bg-[#111827] p-6">
        <h2 className="mb-5 text-lg font-semibold">
          Recent Transactions
        </h2>

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
                  <tr
                    key={transaction.id}
                    className="border-t border-gray-800"
                  >
                    <td className="p-3">
                      {transaction.description}
                    </td>

                    <td className="p-3">
                      {transaction.category_name ?? "Uncategorized"}
                    </td>

                    <td className="p-3">
                      {transaction.transaction_date}
                    </td>

                    <td
                      className={`p-3 font-semibold ${
                        transaction.type === "income"
                          ? "text-green-400"
                          : "text-red-400"
                      }`}
                    >
                      {transaction.type === "income" ? "+" : "-"}
                      {formatMoney(
                        Number(transaction.amount),
                        transaction.currency,
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Account balances */}
      <section className="rounded-2xl border border-gray-800 bg-[#111827] p-6">
        <h2 className="mb-5 text-lg font-semibold">
          Account Balances
        </h2>

        {accountBalances.data?.items.length === 0 ? (
          <p className="text-gray-400">
            No accounts created yet.
          </p>
        ) : (
          <div className="grid gap-4 md:grid-cols-3">
            {accountBalances.data?.items.map((account) => (
              <div
                key={account.account_id}
                className="rounded-xl border border-gray-700 p-4"
              >
                <p className="text-gray-400">
                  {account.account_name}
                </p>

                <p className="mt-2 text-xl font-semibold">
                  {formatMoney(
                    Number(account.balance),
                    account.currency,
                  )}
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