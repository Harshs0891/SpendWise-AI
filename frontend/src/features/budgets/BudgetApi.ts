import { api } from "../../lib/api";
import type {
  BudgetCreate,
  BudgetListResponse,
  BudgetProgress,
  BudgetUpdate,
} from "./BudgetTypes";

// Keep all budget-related HTTP requests in one feature module.
export const budgetApi = {
  // Fetch budgets for a particular month and currency.
  getAll: async (periodStart: string, currency = "INR") => {
    const response = await api.get<BudgetListResponse>("/budgets", {
      params: {
        period_start: periodStart,
        currency,
      },
    });

    return response.data;
  },

  // Create a new monthly spending limit for a category.
  create: async (data: BudgetCreate) => {
    const response = await api.post<BudgetProgress>("/budgets", data);
    return response.data;
  },

  // Update the spending limit or warning threshold.
  update: async (id: string, data: BudgetUpdate) => {
    const response = await api.patch<BudgetProgress>(`/budgets/${id}`, data);
    return response.data;
  },

  // Delete a budget.
  delete: async (id: string) => {
    await api.delete(`/budgets/${id}`);
  },
};