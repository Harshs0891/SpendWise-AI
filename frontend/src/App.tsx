import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import AppLayout from "./components/AppLayout";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Accounts from "./pages/Accounts";
import Transactions from "./pages/Transactions";
import Budgets from "./pages/Budgets";
import Transfers from "./pages/Transfers";
import CsvManagement from "./pages/CsvManagement";
import AiAssistant from "./pages/AiAssistant";
import SpendingInsights from "./pages/SpendingInsights";
import BudgetAdvisor from "./pages/BudgetAdvisor";
import MonthlyReport from "./pages/MonthlyReport";

export default function App() {
  return <Routes>
    <Route path="/login" element={<Login />} />
    <Route path="/register" element={<Register />} />
    <Route element={<ProtectedRoute />}>
      <Route element={<AppLayout />}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/accounts" element={<Accounts />} />
        <Route path="/transactions" element={<Transactions />} />
        <Route path="/budgets" element={<Budgets />} />
        <Route path="/transfers" element={<Transfers />} />
        <Route path="/csv" element={<CsvManagement />} />
        <Route path="/ai-assistant" element={<AiAssistant />} />
        <Route path="/insights" element={<SpendingInsights />} />
        <Route path="/budget-advisor" element={<BudgetAdvisor />} />
        <Route path="/monthly-report" element={<MonthlyReport />} />
      </Route>
    </Route>
    <Route path="/" element={<Navigate to="/dashboard" replace />} />
    <Route path="*" element={<Navigate to="/dashboard" replace />} />
  </Routes>;
}
