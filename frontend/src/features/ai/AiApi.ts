import { api } from "../../lib/api";

export interface AIConversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}
export interface AIMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}
export interface AIConversationDetail extends AIConversation { messages: AIMessage[] }
export interface AIChatResult {
  conversation_id: string;
  message_id: string;
  response: string;
  tools_used: string[];
}
export interface SpendingInsight {
  currency: string;
  period: { start_date: string; end_date: string };
  financial_summary: { total_income: string; total_expenses: string; net_savings: string; savings_rate: string | null };
  comparison: { previous_month_income: string; previous_month_expenses: string; expense_change_percentage: string | null };
  top_category: { name: string; amount: string; percentage: string } | null;
  categories: Array<{ category: string; amount: string; percentage_of_spending: string; previous_month_amount: string; percentage_change: string | null }>;
  observations: string[];
}
export interface SpendingInsightsResponse { generated_at: string; insights: SpendingInsight[] }
export interface BudgetRecommendation {
  budget_id: string; category: string; currency: string; budget_amount: string; spent: string;
  remaining: string; utilization_percent: string; status: "on_track" | "warning" | "exceeded";
  priority: "low" | "medium" | "high"; recommendation: string;
}
export interface BudgetAdvisorResponse {
  period: string;
  summary: { total_budgets: number; exceeded: number; warning: number; on_track: number };
  recommendations: BudgetRecommendation[];
}
export interface MonthlyReportCurrency {
  currency: string;
  financial_summary: SpendingInsight["financial_summary"];
  month_comparison: SpendingInsight["comparison"];
  top_category: SpendingInsight["top_category"];
  category_breakdown: SpendingInsight["categories"];
  budget_summary: BudgetAdvisorResponse["summary"];
  budget_recommendations: BudgetRecommendation[];
  observations: string[];
}
export interface MonthlyReportResponse {
  report_type: string;
  period: { start_date: string; end_date: string; month: string; year: number };
  generated_at: string;
  currency_reports: MonthlyReportCurrency[];
}

export const aiApi = {
  listConversations: async () => (await api.get<AIConversation[]>("/ai/conversations")).data,
  getConversation: async (id: string) => (await api.get<AIConversationDetail>(`/ai/conversations/${id}`)).data,
  sendMessage: async (message: string, conversationId?: string) =>
    (await api.post<AIChatResult>("/ai/chat", { message, conversation_id: conversationId ?? null })).data,
  deleteConversation: async (id: string) => api.delete(`/ai/conversations/${id}`),
  getSpendingInsights: async (referenceDate: string, currency?: string) =>
    (await api.get<SpendingInsightsResponse>("/ai/insights/spending", { params: { reference_date: referenceDate, ...(currency ? { currency } : {}) } })).data,
  getBudgetAdvice: async (referenceDate: string, currency?: string) =>
    (await api.get<BudgetAdvisorResponse>("/ai/advisor/budget", { params: { reference_date: referenceDate, ...(currency ? { currency } : {}) } })).data,
  getMonthlyReport: async (referenceDate: string, currency?: string) =>
    (await api.get<MonthlyReportResponse>("/ai/reports/monthly", { params: { reference_date: referenceDate, ...(currency ? { currency } : {}) } })).data,
};
