export type TransactionType = "income" | "expense";

export interface Transaction {
  id: string;
  user_id: string;
  account_id: string;
  category_id: string | null;
  type: TransactionType;
  amount: number;
  currency: string;
  description: string;
  merchant: string | null;
  transaction_date: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface TransactionCreate {
  account_id: string;
  category_id: string | null;
  type: TransactionType;
  amount: number;
  currency: string;
  description: string;
  merchant: string | null;
  transaction_date: string;
  notes: string | null;
}

export type TransactionUpdate = Partial<TransactionCreate>;

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  limit: number;
  offset: number;
}

export interface TransactionFilters {
  type?: TransactionType;
  account_id?: string;
  category_id?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}