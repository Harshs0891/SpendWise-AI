import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "./DashboardApi";

// React Query caches each dashboard section independently and refreshes invalidated data.
export function useDashboard() {
  const summary = useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: dashboardApi.getSummary,
  });

  const recentTransactions = useQuery({
    queryKey: ["dashboard", "recent-transactions"],
    queryFn: dashboardApi.getRecentTransactions,
  });

  const accountBalances = useQuery({
    queryKey: ["dashboard", "account-balances"],
    queryFn: dashboardApi.getAccountBalances,
  });

  // Prefer INR; otherwise use the first currency returned by the summary endpoint.
  const currency =
    summary.data?.items.find((item) => item.currency === "INR")
      ?.currency ?? summary.data?.items[0]?.currency;

  const cashFlow = useQuery({
    queryKey: ["dashboard", "cash-flow", currency],
    queryFn: () => dashboardApi.getCashFlow(currency!),
    enabled: Boolean(currency),
  });

  const categoryBreakdown = useQuery({
    queryKey: ["dashboard", "category-breakdown", currency],
    queryFn: () => dashboardApi.getCategoryBreakdown(currency!),
    enabled: Boolean(currency),
  });

  return {
    summary,
    cashFlow,
    categoryBreakdown,
    recentTransactions,
    accountBalances,
  };
}