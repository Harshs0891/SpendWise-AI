import { api } from "../../lib/api";
import type { Category, CategoryKind } from "./CategoryTypes";

// The optional kind filter returns only income or expense categories when requested.
export const categoryApi = {
  getAll: async (kind?: CategoryKind) => {
    const response = await api.get<Category[]>("/categories", {
      params: kind ? { kind } : {},
    });

    return response.data;
  },
};