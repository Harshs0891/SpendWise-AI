export interface TransferCreate {
  source_account_id: string;
  destination_account_id: string;
  amount: number;
  currency: string;
  description: string;
  transaction_date: string;
}

export interface Transfer {
  id: string;
  user_id: string;
  source_account_id: string;
  destination_account_id: string;
  amount: number;
  currency: string;
  description: string;
  transaction_date: string;
  idempotency_key: string;
  created_at: string;
  debit_transaction_id: string;
  credit_transaction_id: string;
}

export interface TransferListResponse {
  items: Transfer[];
  total: number;
  limit: number;
  offset: number;
}