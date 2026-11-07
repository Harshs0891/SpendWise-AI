import { api } from "../../lib/api";
import type {
  Transaction,
  TransactionCreate,
  TransactionFilters,
  TransactionListResponse,
} from "./TransactionTypes";

// Centralize transaction endpoints, query parameters, and response typing.
export const transactionApi = {
  getAll: async (filters: TransactionFilters = {}) => {
    const response = await api.get<TransactionListResponse>(
      "/transactions",
      {
        params: {
          type: filters.type,
          account_id: filters.account_id,
          category_id: filters.category_id,
          start_date: filters.start_date,
          end_date: filters.end_date,
          // Use default pagination values when the caller does not provide them.
          limit: filters.limit ?? 20,
          offset: filters.offset ?? 0,
        },
      }
    );

    return response.data;
  },

  create: async (data: TransactionCreate) => {
    const response = await api.post<Transaction>(
      "/transactions",
      data
    );

    return response.data;
  },
};