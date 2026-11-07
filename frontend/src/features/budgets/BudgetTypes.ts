export type BudgetStatus = "on_track" | "warning" | "exceeded";

export interface Budget {
  id: string;
  user_id: string;
  category_id: string;
  amount: number | string;
  currency: string;
  period_start: string;
  alert_threshold: number;
  created_at: string;
  updated_at: string;
}

export interface BudgetProgress {
  budget: Budget;
  category_name: string;
  period_end: string;
  spent: number | string;
  remaining: number | string;
  utilization_percent: number | string;
  status: BudgetStatus;
}

export interface BudgetListResponse {
  items: BudgetProgress[];
  total: number;
}

export interface BudgetCreate {
  category_id: string;
  amount: number;
  currency: string;
  period_start: string;
  alert_threshold: number;
}

export interface BudgetUpdate {
  amount?: number;
  alert_threshold?: number;
}