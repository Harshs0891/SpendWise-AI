export interface CurrencySummary {
  currency: string;
  total_income: number;
  total_expenses: number;
  net_savings: number;
}

export interface AnalyticsSummary {
  items: CurrencySummary[];
}

export interface MonthlyCashFlow {
  month: string;
  income: number;
  expenses: number;
}

export interface CashFlowResponse {
  currency: string;
  items: MonthlyCashFlow[];
}

export interface CategorySpending {
  category_id: string | null;
  category_name: string;
  total: number;
  percentage: number;
}

export interface CategoryBreakdown {
  currency: string;
  total_expenses: number;
  items: CategorySpending[];
}

export interface RecentTransaction {
  id: string;
  type: "income" | "expense";
  amount: number;
  currency: string;
  description: string;
  merchant: string | null;
  transaction_date: string;
  account_id: string;
  category_id: string | null;
  category_name: string | null;
}

export interface RecentTransactionsResponse {
  items: RecentTransaction[];
  limit: number;
}

export interface AccountBalance {
  account_id: string;
  account_name: string;
  account_type: string;
  currency: string;
  balance: number;
  balance_type: "asset" | "debt";
}

export interface AccountBalancesResponse {
  items: AccountBalance[];
}