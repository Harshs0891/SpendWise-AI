import type { TransactionType } from "../transactions/TransactionTypes";

export interface CsvExportFilters {
  type?: TransactionType;
  account_id?: string;
  category_id?: string;
  start_date?: string;
  end_date?: string;
}

export interface CsvImportResult {
  imported_count: number;
  transaction_ids: string[];
}

export interface CsvImportRowError {
  row: number;
  errors: string[];
}

export interface CsvImportErrorResponse {
  message: string;
  row_errors: CsvImportRowError[];
}