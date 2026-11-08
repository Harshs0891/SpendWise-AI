import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useState } from "react";
import { Activity, ArrowLeftRight, Bot, FileSpreadsheet, FileText, LayoutDashboard, LogOut, Menu, PiggyBank, Sparkles, Wallet, X } from "lucide-react";
import { useAuth } from "../features/auth/AuthContext";

const navigation = [
  { label: "Overview", items: [
    { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
    { label: "Transactions", path: "/transactions", icon: Activity },
    { label: "Accounts", path: "/accounts", icon: Wallet },
    { label: "Budgets", path: "/budgets", icon: PiggyBank },
    { label: "Transfers", path: "/transfers", icon: ArrowLeftRight },
    { label: "CSV import / export", path: "/csv", icon: FileSpreadsheet },
  ]},
  { label: "AI intelligence", items: [
    { label: "AI Assistant", path: "/ai-assistant", icon: Bot },
    { label: "Spending insights", path: "/insights", icon: Sparkles },
    { label: "Budget advisor", path: "/budget-advisor", icon: PiggyBank },
    { label: "Monthly report", path: "/monthly-report", icon: FileText },
  ]},
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  function signOut() { logout(); navigate("/login", { replace: true }); }
  const sidebar = <><div className="flex items-center gap-3 px-5 py-6"><img src="/favicon.svg" alt="SpendWise AI" className="h-10 w-10 rounded-xl"/><div><p className="font-bold tracking-tight text-white">SpendWise <span className="text-cyan-400">AI</span></p><p className="text-[10px] tracking-wide text-slate-500">PERSONAL FINANCE</p></div></div><div className="mx-4 h-px bg-slate-800"/><nav aria-label="Main navigation" className="flex-1 space-y-6 overflow-y-auto px-3 py-5">{navigation.map(group=><div key={group.label}><p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[.18em] text-slate-600">{group.label}</p><div className="space-y-1">{group.items.map(item=>{const Icon=item.icon;return <NavLink key={item.path} to={item.path} onClick={()=>setMobileOpen(false)} className={({isActive})=>`flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium transition ${isActive?"bg-cyan-500/10 text-cyan-300":"text-slate-400 hover:bg-slate-800/70 hover:text-slate-100"}`}><Icon size={17}/>{item.label}</NavLink>})}</div></div>)}</nav><div className="border-t border-slate-800 p-4"><div className="mb-3 flex min-w-0 items-center gap-3 rounded-xl bg-slate-900 p-3"><div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-violet-500/15 text-xs font-semibold text-violet-300">{(user?.email?.[0]??"U").toUpperCase()}</div><div className="min-w-0 flex-1"><p className="truncate text-xs font-medium text-slate-200">{user?.email??"Your account"}</p><p className="text-[10px] text-slate-500">Personal workspace</p></div></div><button onClick={signOut} className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm text-slate-400 transition hover:bg-rose-500/10 hover:text-rose-300"><LogOut size={16}/> Sign out</button></div></>;

  return <div className="min-h-screen bg-[#080b16] text-slate-100">
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-[250px] flex-col border-r border-slate-800 bg-[#0b1020] lg:flex">{sidebar}</aside>
    <div className="lg:pl-[250px]"><header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-800 bg-[#080b16]/90 px-4 backdrop-blur-xl md:px-8"><div className="flex items-center gap-3"><button aria-label="Open navigation" onClick={()=>setMobileOpen(true)} className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 lg:hidden"><Menu size={20}/></button><span className="text-sm font-semibold text-white lg:hidden">SpendWise <span className="text-cyan-400">AI</span></span><div className="hidden items-center gap-2 text-xs text-slate-500 lg:flex"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400"/> Your workspace</div></div><div className="flex items-center gap-3"><span className="hidden text-xs text-slate-500 sm:block">{new Date().toLocaleDateString("en-IN",{weekday:"short",day:"numeric",month:"short",year:"numeric"})}</span><button onClick={()=>navigate("/ai-assistant")} className="flex items-center gap-2 rounded-xl border border-cyan-500/20 bg-cyan-500/10 px-3 py-2 text-xs font-medium text-cyan-300 transition hover:bg-cyan-500/15"><Sparkles size={14}/> Ask AI</button></div></header><div className="min-h-[calc(100vh-4rem)]"><Outlet/></div></div>
    {mobileOpen&&<div className="fixed inset-0 z-50 lg:hidden"><button aria-label="Close navigation overlay" className="absolute inset-0 bg-black/70" onClick={()=>setMobileOpen(false)}/><aside className="absolute inset-y-0 left-0 flex w-[280px] flex-col border-r border-slate-800 bg-[#0b1020]">{sidebar}<button onClick={()=>setMobileOpen(false)} aria-label="Close navigation" className="absolute right-3 top-5 rounded-lg p-2 text-slate-400"><X size={18}/></button></aside></div>}
  </div>;
}
