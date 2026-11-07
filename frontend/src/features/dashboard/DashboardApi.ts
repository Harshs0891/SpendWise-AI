import { api } from "../../lib/api";

import type {
  AnalyticsSummary,
  CashFlowResponse,
  CategoryBreakdown,
  RecentTransactionsResponse,
  AccountBalancesResponse,
} from "./DashboardTypes";

// Group dashboard HTTP calls here so pages and hooks do not manage raw URLs.
export const dashboardApi = {
  getSummary: async () => {
    const response = await api.get<AnalyticsSummary>(
      "/analytics/summary"
    );
    return response.data;
  },

  getCashFlow: async (currency: string) => {
    const response = await api.get<CashFlowResponse>(
      "/analytics/cash-flow",
      { params: { currency } }
    );
    return response.data;
  },

  getCategoryBreakdown: async (currency: string) => {
    const response = await api.get<CategoryBreakdown>(
      "/analytics/category-breakdown",
      { params: { currency } }
    );
    return response.data;
  },

  getRecentTransactions: async () => {
    const response = await api.get<RecentTransactionsResponse>(
      "/analytics/recent-transactions",
      { params: { limit: 5 } }
    );
    return response.data;
  },

  getAccountBalances: async () => {
    const response = await api.get<AccountBalancesResponse>(
      "/analytics/account-balances"
    );
    return response.data;
  },
};