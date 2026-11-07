import { api } from "../../lib/api";
import type {
  Transfer,
  TransferCreate,
  TransferListResponse,
} from "./TransferTypes";

export const transferApi = {
  // Fetch paginated transfer history.
  getAll: async (limit = 20, offset = 0) => {
    const response = await api.get<TransferListResponse>("/transfers", {
      params: { limit, offset },
    });

    return response.data;
  },

  // Create a unique key so retries cannot accidentally create duplicate transfers.
  create: async (data: TransferCreate) => {
    const idempotencyKey = crypto.randomUUID();

    const response = await api.post<Transfer>("/transfers", data, {
      headers: {
        "Idempotency-Key": idempotencyKey,
      },
    });

    return response.data;
  },

  // Fetch one transfer by its ID.
  getById: async (id: string) => {
    const response = await api.get<Transfer>(`/transfers/${id}`);
    return response.data;
  },
};