import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, ShieldAlert, Sparkles } from "lucide-react";
import { aiApi } from "../features/ai/AiApi";

const today = () => new Date().toISOString().slice(0,10);
const money = (value:string,currency:string) => new Intl.NumberFormat("en-IN",{style:"currency",currency,maximumFractionDigits:0}).format(Number(value||0));
const statusStyles = {
  exceeded: { icon: ShieldAlert, iconClass: "bg-rose-500/10 text-rose-300", barClass: "bg-rose-400", label: "Exceeded" },
  warning: { icon: AlertTriangle, iconClass: "bg-amber-500/10 text-amber-300", barClass: "bg-amber-400", label: "Needs attention" },
  on_track: { icon: CheckCircle2, iconClass: "bg-emerald-500/10 text-emerald-300", barClass: "bg-emerald-400", label: "On track" },
};
export default function BudgetAdvisor() {
  const [referenceDate,setReferenceDate]=useState(today);
  const [currency,setCurrency]=useState("");
  const query=useQuery({queryKey:["ai","budget-advisor",referenceDate,currency],queryFn:()=>aiApi.getBudgetAdvice(referenceDate,currency||undefined)});
  const data=query.data;
  return <main className="mx-auto max-w-[1450px] space-y-6 px-4 py-7 md:px-8">
    <header className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">Personalized guidance</p><h1 className="mt-1 text-3xl font-bold text-white">Smart Budget Advisor</h1><p className="mt-2 text-sm text-slate-400">A read-only review of your budgets, prioritized by risk.</p></div><div className="flex gap-2"><input aria-label="Month" type="date" value={referenceDate} onChange={e=>setReferenceDate(e.target.value)} className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white"/><input aria-label="Currency" value={currency} onChange={e=>setCurrency(e.target.value.toUpperCase().slice(0,3))} maxLength={3} placeholder="Currency" className="w-28 rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-white placeholder:text-slate-500"/></div></header>
    {query.isLoading&&<p className="rounded-2xl border border-slate-800 bg-slate-900 p-8 text-sm text-slate-400">Reviewing your budgets…</p>}
    {query.isError&&<p role="alert" className="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-5 text-sm text-rose-300">Unable to load budget advice. Please try again.</p>}
    {data&&<><section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{[["Total budgets",data.summary.total_budgets,"text-white"],["On track",data.summary.on_track,"text-emerald-300"],["Needs attention",data.summary.warning,"text-amber-300"],["Exceeded",data.summary.exceeded,"text-rose-300"]].map(([label,value,color])=><div key={String(label)} className="rounded-2xl border border-slate-800 bg-slate-900 p-5"><p className="text-xs text-slate-500">{label}</p><p className={`mt-2 text-3xl font-bold ${color}`}>{value}</p></div>)}</section>
    {!data.recommendations.length?<div className="rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center"><Sparkles className="mx-auto text-cyan-300" size={30}/><h2 className="mt-3 font-semibold text-white">No budgets to review yet</h2><p className="mt-1 text-sm text-slate-500">Create monthly budgets in the Budgets section to receive personalized guidance.</p></div>:<section className="space-y-3">{data.recommendations.map(item=>{const style=statusStyles[item.status];const Icon=style.icon;const used=Math.min(100,Math.max(0,Number(item.utilization_percent)));return <article key={item.budget_id} className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div className="flex items-center gap-3"><div className={`rounded-xl p-3 ${style.iconClass}`}><Icon size={20}/></div><div><h2 className="font-semibold text-white">{item.category}</h2><p className="mt-1 text-xs text-slate-500">{item.priority.toUpperCase()} PRIORITY · {style.label}</p></div></div><div className="text-right"><p className="font-semibold text-white">{money(item.spent,item.currency)} <span className="text-xs font-normal text-slate-500">of {money(item.budget_amount,item.currency)}</span></p><p className="mt-1 text-xs text-slate-400">{Number(item.utilization_percent).toFixed(1)}% used</p></div></div><div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-800"><div className={`h-full rounded-full ${style.barClass}`} style={{width:`${used}%`}}/></div><p className="mt-3 text-sm leading-6 text-slate-300">{item.recommendation}</p><p className="mt-2 text-xs text-slate-500">{money(item.remaining,item.currency)} remaining</p></article>})}</section>}</>}
    <p className="text-xs text-slate-600">Recommendations are informational and do not change your budgets or move money.</p>
  </main>;
}
