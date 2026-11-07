export type AccountType =
  | "cash"
  | "bank"
  | "savings"
  | "wallet"
  | "credit_card";

export interface Account {
  id: string;
  user_id: string;
  name: string;
  account_type: AccountType;
  currency: string;
  opening_balance: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AccountCreate {
  name: string;
  account_type: AccountType;
  currency: string;
  opening_balance: number;
}