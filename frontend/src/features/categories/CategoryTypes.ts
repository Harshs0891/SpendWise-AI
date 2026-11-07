export type CategoryKind = "income" | "expense";

export interface Category {
  id: string;
  user_id: string | null;
  name: string;
  kind: CategoryKind;
  icon: string | null;
  color: string | null;
  is_system: boolean;
  created_at: string;
  updated_at: string;
}