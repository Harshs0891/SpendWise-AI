import { api } from "../../lib/api";

import type {
  CsvExportFilters,
  CsvImportResult,
} from "./CsvTypes";

export const csvApi = {
  // Download filtered transactions as a CSV blob.
  exportTransactions: async (filters: CsvExportFilters = {}) => {
    const response = await api.get<Blob>(
      "/transactions/csv/export",
      {
        params: filters,
        responseType: "blob",
      },
    );

    return response.data;
  },

  // Upload CSV using multipart/form-data.
  importTransactions: async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post<CsvImportResult>(
      "/transactions/csv/import",
      formData,
      {
        // Remove the shared JSON header.
        // Axios/browser will generate multipart/form-data with its boundary.
        headers: {
          "Content-Type": undefined,
        },
      },
    );

    return response.data;
  },
};