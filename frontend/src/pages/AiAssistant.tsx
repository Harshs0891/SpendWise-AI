import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, MessageSquarePlus, Send, Trash2, Sparkles, UserRound, LoaderCircle } from "lucide-react";
import { aiApi, type AIMessage } from "../features/ai/AiApi";

const suggestions = [
  "Where did most of my money go this month?",
  "How can I improve my savings?",
  "Summarize my recent spending patterns",
  "Am I on track with my budgets?",
];

function MessageBubble({ message }: { message: AIMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${isUser ? "bg-violet-500/15 text-violet-300" : "bg-cyan-500/15 text-cyan-300"}`}>
        {isUser ? <UserRound size={17} /> : <Bot size={18} />}
      </div>
      <div className={`max-w-[min(82%,760px)] rounded-2xl px-4 py-3 ${isUser ? "rounded-tr-sm bg-cyan-500 text-slate-950" : "rounded-tl-sm border border-slate-800 bg-slate-900 text-slate-200"}`}>
        <p className="whitespace-pre-wrap text-sm leading-7">{message.content}</p>
        <time className={`mt-2 block text-[10px] ${isUser ? "text-slate-800/70" : "text-slate-500"}`}>
          {new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </time>
      </div>
    </div>
  );
}

export default function AiAssistant() {
  const client = useQueryClient();
  const [activeId, setActiveId] = useState<string>();
  const [draft, setDraft] = useState("");
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const conversations = useQuery({ queryKey: ["ai", "conversations"], queryFn: aiApi.listConversations });
  const detail = useQuery({
    queryKey: ["ai", "conversation", activeId],
    queryFn: () => aiApi.getConversation(activeId!),
    enabled: Boolean(activeId),
  });
  const send = useMutation({
    mutationFn: ({ text, id }: { text: string; id?: string }) => aiApi.sendMessage(text, id),
    onSuccess: async (result) => {
      setDraft("");
      setError("");
      setActiveId(result.conversation_id);
      await Promise.all([
        client.invalidateQueries({ queryKey: ["ai", "conversations"] }),
        client.invalidateQueries({ queryKey: ["ai", "conversation", result.conversation_id] }),
      ]);
    },
    onError: (cause) => {
      const response = cause as { response?: { data?: { detail?: string } } };
      setError(response.response?.data?.detail ?? "I couldn't process that message. Please try again.");
    },
  });
  const remove = useMutation({
    mutationFn: aiApi.deleteConversation,
    onSuccess: async (_, id) => {
      if (activeId === id) setActiveId(undefined);
      await client.invalidateQueries({ queryKey: ["ai", "conversations"] });
    },
  });
  const messages = detail.data?.messages ?? [];
  const optimisticMessages = useMemo(() => messages, [messages]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [optimisticMessages.length, send.isPending]);
  useEffect(() => {
    if (!activeId && conversations.data?.length) setActiveId(conversations.data[0].id);
  }, [activeId, conversations.data]);

  function submit(event: FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || send.isPending) return;
    setError("");
    send.mutate({ text, id: activeId });
  }

  function startNew() {
    setActiveId(undefined);
    setDraft("");
    setError("");
  }

  return (
    <main className="mx-auto flex h-[calc(100vh-7.5rem)] max-w-[1600px] flex-col gap-5 px-4 py-6 md:px-8">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div><p className="text-xs font-semibold uppercase tracking-[.2em] text-cyan-400">SpendWise intelligence</p><h1 className="mt-1 text-2xl font-bold text-white md:text-3xl">AI Assistant</h1><p className="mt-1 text-sm text-slate-400">Ask questions about your finances. Answers use your actual SpendWise data.</p></div>
        <div className="flex items-center gap-2 rounded-full border border-cyan-500/20 bg-cyan-500/10 px-3 py-2 text-xs text-cyan-300"><span className="h-2 w-2 rounded-full bg-emerald-400" /> Finance tools enabled</div>
      </header>
      <section className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[270px_minmax(0,1fr)]">
        <aside className="flex min-h-0 flex-col rounded-2xl border border-slate-800 bg-slate-900/70 p-3">
          <button onClick={startNew} className="flex items-center justify-center gap-2 rounded-xl bg-cyan-400 px-3 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"><MessageSquarePlus size={17} /> New conversation</button>
          <p className="px-2 pb-2 pt-5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">Recent conversations</p>
          <div className="min-h-0 flex-1 space-y-1 overflow-y-auto">
            {conversations.isLoading && <p className="px-2 py-4 text-xs text-slate-500">Loading history…</p>}
            {conversations.data?.map((item) => (
              <div key={item.id} className={`group flex items-center gap-1 rounded-xl ${activeId === item.id ? "bg-slate-800" : "hover:bg-slate-800/60"}`}>
                <button onClick={() => setActiveId(item.id)} className="min-w-0 flex-1 px-3 py-3 text-left"><span className="block truncate text-sm text-slate-200">{item.title || "New conversation"}</span><span className="mt-1 block text-[10px] text-slate-500">{new Date(item.updated_at).toLocaleDateString()}</span></button>
                <button aria-label="Delete conversation" title="Delete conversation" onClick={() => remove.mutate(item.id)} className="mr-2 rounded-lg p-2 text-slate-500 opacity-0 transition hover:bg-rose-500/10 hover:text-rose-300 group-hover:opacity-100"><Trash2 size={14} /></button>
              </div>
            ))}
            {!conversations.isLoading && !conversations.data?.length && <p className="px-2 py-4 text-xs leading-5 text-slate-500">Your saved conversations will appear here.</p>}
          </div>
        </aside>
        <div className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-3 border-b border-slate-800 px-5 py-4"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-300"><Sparkles size={18} /></div><div><p className="text-sm font-semibold text-white">SpendWise AI</p><p className="text-xs text-slate-500">Personal finance copilot</p></div></div>
          <div className="min-h-0 flex-1 space-y-5 overflow-y-auto p-4 md:p-6">
            {!activeId && !messages.length && <div className="mx-auto flex min-h-full max-w-xl flex-col items-center justify-center text-center"><div className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl border border-cyan-500/20 bg-cyan-500/10 text-cyan-300"><Bot size={30} /></div><h2 className="text-xl font-semibold text-white">Your money, made clearer.</h2><p className="mt-2 text-sm leading-6 text-slate-400">Ask about spending, budgets, transactions, or ways to save. SpendWise AI can look up your financial data to give grounded answers.</p><div className="mt-6 grid w-full gap-2 sm:grid-cols-2">{suggestions.map((item) => <button key={item} onClick={() => setDraft(item)} className="rounded-xl border border-slate-800 bg-slate-900 px-3 py-3 text-left text-xs text-slate-300 transition hover:border-cyan-500/40 hover:text-cyan-200">{item}</button>)}</div></div>}
            {detail.isLoading && <p className="text-sm text-slate-500">Loading conversation…</p>}
            {detail.isError && <p role="alert" className="text-sm text-rose-300">Couldn't load this conversation. Try selecting it again.</p>}
            {messages.map((message) => <MessageBubble key={message.id} message={message} />)}
            {send.isPending && <div className="flex items-center gap-2 text-xs text-cyan-300"><LoaderCircle className="animate-spin" size={16} /> Checking your finances…</div>}
            <div ref={bottomRef} />
          </div>
          {error && <p role="alert" className="px-5 pb-2 text-xs text-rose-300">{error}</p>}
          <form onSubmit={submit} className="border-t border-slate-800 p-3 md:p-4"><div className="flex items-end gap-2 rounded-2xl border border-slate-700 bg-slate-900 p-2 focus-within:border-cyan-500/60"><textarea aria-label="Message SpendWise AI" rows={1} maxLength={10000} value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submit(event); } }} placeholder="Ask anything about your finances…" className="max-h-32 min-h-10 flex-1 resize-y bg-transparent px-2 py-2 text-sm text-white outline-none placeholder:text-slate-500" /><button type="submit" disabled={!draft.trim() || send.isPending} className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-cyan-400 text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-40" aria-label="Send message"><Send size={17} /></button></div><p className="mt-2 px-1 text-[10px] text-slate-600">AI can make mistakes. Verify important financial decisions against your records.</p></form>
        </div>
      </section>
    </main>
  );
}
