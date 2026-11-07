import { api } from "../../lib/api";
import type { Category, CategoryKind } from "./CategoryTypes";

export const categoryApi = {
  getAll: async (kind?: CategoryKind) => {
    const response = await api.get<Category[]>("/categories", {
      params: kind ? { kind } : {},
    });

    return response.data;
  },
};