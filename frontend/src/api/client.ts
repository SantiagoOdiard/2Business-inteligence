import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000/api/v1";

export const api = axios.create({ baseURL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export async function login(username: string, password: string) {
  const { data } = await api.post("/auth/login", { username, password, device: navigator.userAgent });
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  return data;
}

export function logout() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}
