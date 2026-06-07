import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, BrainCircuit, History, Lightbulb, MessageSquarePlus, SendHorizontal, Sparkles, User } from "lucide-react";
import { api } from "../api/client";
import { fetchConversation, fetchConversations, fetchInsights } from "../api/queries";
import { DataPanel } from "../components/DataPanel";
import { ErrorState, LoadingState, SavingState } from "../components/State";
import type { AIChatResponse, AIMessage } from "../types/api";

const prompts = [
  "Hola",
  "Como estas?",
  "Cual es el mayor riesgo actual?",
  "Analiza productividad por departamento.",
];

export function Advisor() {
  const [message, setMessage] = useState("");
  const [activeConversationId, setActiveConversationId] = useState<number | null>(null);
  const [localMessages, setLocalMessages] = useState<AIMessage[]>([]);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const client = useQueryClient();
  const insights = useQuery({ queryKey: ["insights"], queryFn: fetchInsights });
  const conversations = useQuery({ queryKey: ["ai-conversations"], queryFn: fetchConversations });
  const conversation = useQuery({
    queryKey: ["ai-conversation", activeConversationId],
    queryFn: () => fetchConversation(activeConversationId as number),
    enabled: Boolean(activeConversationId),
  });
  const chat = useMutation({
    mutationFn: async (content: string) => {
      const { data } = await api.post<AIChatResponse>("/ai-chat", { message: content, conversation_id: activeConversationId });
      return data;
    },
    onSuccess: (data) => {
      setActiveConversationId(data.conversation_id);
      setLocalMessages((items) => [...items, data.answer]);
      client.invalidateQueries({ queryKey: ["ai-conversations"] });
      client.invalidateQueries({ queryKey: ["ai-conversation", data.conversation_id] });
    },
  });

  const messages = useMemo(() => {
    const persisted = conversation.data?.messages ?? [];
    if (!activeConversationId) return localMessages;
    return persisted.length ? persisted : localMessages;
  }, [activeConversationId, conversation.data?.messages, localMessages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, chat.isPending]);

  function submit(event?: FormEvent, prompt?: string) {
    event?.preventDefault();
    const content = (prompt ?? message).trim();
    if (!content || chat.isPending) return;
    const optimistic: AIMessage = { id: Date.now(), role: "user", content, created_at: new Date().toISOString() };
    setLocalMessages((items) => [...items, optimistic]);
    setMessage("");
    chat.mutate(content);
  }

  function newChat() {
    setActiveConversationId(null);
    setLocalMessages([]);
    setMessage("");
  }

  if (insights.isLoading || conversations.isLoading) return <LoadingState rows={6} />;
  if (insights.isError || conversations.isError) return <ErrorState />;

  return (
    <div className="grid min-h-[calc(100vh-7rem)] gap-4 xl:grid-cols-[280px_1fr_340px]">
      <DataPanel
        title="Historial IA"
        action={<button className="grid h-8 w-8 place-items-center rounded-md border border-line hover:bg-slate-50" onClick={newChat} title="Nuevo chat"><MessageSquarePlus className="h-4 w-4" /></button>}
      >
        <div className="space-y-2">
          {conversations.data?.length ? conversations.data.map((item) => (
            <button
              key={item.id}
              className={`w-full rounded-md border px-3 py-2 text-left text-sm ${activeConversationId === item.id ? "border-teal-200 bg-teal-50 text-teal-900" : "border-line hover:bg-slate-50"}`}
              onClick={() => {
                setActiveConversationId(item.id);
                setLocalMessages([]);
              }}
            >
              <div className="flex items-center gap-2">
                <History className="h-4 w-4 shrink-0" />
                <span className="truncate">{item.title}</span>
              </div>
              <div className="mt-1 text-xs text-slate-500">{new Date(item.updated_at).toLocaleString()}</div>
            </button>
          )) : <p className="text-sm text-slate-500">Aun no hay historial.</p>}
        </div>
      </DataPanel>

      <section className="flex min-h-[680px] flex-col rounded-md border border-line bg-white shadow-panel">
        <div className="flex items-center gap-3 border-b border-line px-4 py-3">
          <div className="grid h-9 w-9 place-items-center rounded-md bg-teal-50 text-primary">
            <BrainCircuit className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-semibold">Asistente IA</h1>
              <span className="inline-flex items-center gap-1 rounded bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                <Sparkles className="h-3 w-3" />
                Conversacional
              </span>
            </div>
            <p className="text-sm text-slate-500">Conversa de forma natural y usa datos solo cuando pides analisis de negocio.</p>
          </div>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {!messages.length && (
            <div className="rounded-md border border-dashed border-teal-200 bg-teal-50/60 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-teal-900">
                <Bot className="h-4 w-4" />
                Hola, soy tu asistente IA.
              </div>
              <p className="mt-2 text-sm leading-6 text-teal-900/80">
                Puedes escribirme como si hablaras con una persona. Si saludas, respondo sin metricas; si preguntas por negocio, analizo datos con evidencia, razonamiento y confianza.
              </p>
            </div>
          )}
          {!messages.length && (
            <div className="grid gap-3 md:grid-cols-2">
              {prompts.map((prompt) => (
                <button key={prompt} className="rounded-md border border-line p-4 text-left text-sm hover:bg-slate-50" onClick={() => submit(undefined, prompt)}>
                  <Lightbulb className="mb-3 h-4 w-4 text-primary" />
                  {prompt}
                </button>
              ))}
            </div>
          )}
          {messages.map((item) => (
            <article key={`${item.role}-${item.id}`} className={`flex max-w-3xl gap-3 ${item.role === "user" ? "ml-auto flex-row-reverse" : ""}`}>
              <div className={`grid h-8 w-8 shrink-0 place-items-center rounded-md ${item.role === "user" ? "bg-teal-600 text-white" : "bg-slate-100 text-primary"}`}>
                {item.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
              </div>
              <div className={`rounded-md border p-4 ${item.role === "user" ? "border-teal-200 bg-teal-50" : "border-line bg-white"}`}>
                <div className="mb-2 text-xs font-semibold uppercase text-slate-500">{item.role === "user" ? "Tu" : "Asistente IA"}</div>
                <p className="whitespace-pre-line text-sm leading-6">{item.content}</p>
                {item.role === "assistant" && (
                  <div className="mt-3 rounded-md bg-slate-50 p-3 text-xs text-slate-600">
                    {item.reasoning && <div>{item.reasoning}</div>}
                    {item.confidence && <div className="mt-1 font-medium text-teal-700">Confianza {item.confidence}%</div>}
                  </div>
                )}
              </div>
            </article>
          ))}
          {chat.isPending && <div className="flex items-center gap-2 text-sm text-slate-500"><SavingState /> Pensando...</div>}
          <div ref={messagesEndRef} />
        </div>

        <form className="border-t border-line p-3" onSubmit={(event) => submit(event)}>
          <div className="flex gap-2">
            <input
              className="min-w-0 flex-1 rounded-md border border-line px-3 py-2 text-sm"
              placeholder="Escribe como quieras: Hola, como estas, analiza riesgos, compara departamentos..."
              value={message}
              onChange={(event) => setMessage(event.target.value)}
            />
            <button className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-white" disabled={chat.isPending || !message.trim()}>
              {chat.isPending ? <SavingState /> : <SendHorizontal className="h-4 w-4" />}
              Enviar
            </button>
          </div>
          {chat.isError && <div className="mt-2 text-sm text-red-700">La IA no pudo responder. Revisa backend o autenticacion.</div>}
        </form>
      </section>

      <DataPanel title="Recomendaciones activas">
        <div className="space-y-3">
          {insights.data?.slice(0, 4).map((item, index) => (
            <article key={index} className="rounded-md border border-line p-3">
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-sm font-semibold">{item.title}</h3>
                <span className="rounded bg-teal-50 px-2 py-1 text-xs text-teal-800">{item.priority}</span>
              </div>
              <p className="mt-2 text-xs leading-5 text-slate-600">{item.reason}</p>
              <div className="mt-2 text-xs font-medium text-teal-700">Confianza {item.confidence}%</div>
            </article>
          ))}
        </div>
      </DataPanel>
    </div>
  );
}
