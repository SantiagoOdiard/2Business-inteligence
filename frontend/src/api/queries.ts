import { api } from "./client";
import type { AIConversation, Dashboard, Insight, OperationsCenter } from "../types/api";

export const fetchDashboard = async () => (await api.get<Dashboard>("/dashboard")).data;
export const fetchOperationsCenter = async () => (await api.get<OperationsCenter>("/operations-center")).data;
export const fetchWorkflows = async () => (await api.get("/workflows")).data;
export const fetchForecasts = async () => (await api.get("/forecasts")).data;
export const fetchDepartments = async () => (await api.get("/analytics/departments")).data;
export const fetchInsights = async () => (await api.get<Insight[]>("/ai-insights")).data;
export const fetchReports = async () => (await api.get("/reports")).data;
export const fetchMe = async () => (await api.get("/auth/me")).data;
export const fetchConversations = async () => (await api.get<AIConversation[]>("/ai-chat/conversations")).data;
export const fetchConversation = async (id: number) => (await api.get<AIConversation>(`/ai-chat/conversations/${id}`)).data;
