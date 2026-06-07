export type KPI = { key: string; label: string; value: number; unit: string; delta: number };
export type Dashboard = {
  kpis: KPI[];
  trend: Array<{ date: string; revenue: number; cost: number; productivity: number }>;
  risks: Array<{ category: string; score: number; reason: string }>;
  departments: Array<{ name: string; revenue: number; cost: number; productivity: number; satisfaction: number }>;
};
export type OperationsCenter = {
  active_operations: number;
  projects: Array<{ name: string; status: string; budget: number; spent: number; due_date: string }>;
  incidents: Array<{ title: string; severity: string; status: string; sla_due_at: string }>;
  capacity: Array<{ department: string; workload: number; productivity: number }>;
  sla: { target: number; attainment: number; breached: number };
  blockers: Array<{ title: string; status: string; due_date: string; variance_hours: number }>;
};
export type Insight = {
  title: string;
  reason: string;
  impact: string;
  priority: string;
  suggested_action: string;
  confidence: number;
};

export type AIMessage = {
  id: number;
  role: "user" | "assistant";
  content: string;
  reasoning?: string | null;
  confidence?: number | null;
  created_at: string;
};

export type AIConversation = {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  messages: AIMessage[];
};

export type AIChatResponse = {
  conversation_id: number;
  answer: AIMessage;
  context: { kpis: number; risks: number; departments: number; forecasts: number };
};
