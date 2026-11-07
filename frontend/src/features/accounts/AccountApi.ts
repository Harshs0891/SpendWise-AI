import { api } from "../../lib/api";
import type { Account, AccountCreate } from "./AccountTypes";

export const accountApi = {
  getAll: async () => {
    const response = await api.get<Account[]>("/accounts");
    return response.data;
  },

  create: async (data: AccountCreate) => {
    const response = await api.post<Account>("/accounts", data);
    return response.data;
  },
};