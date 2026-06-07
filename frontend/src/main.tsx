import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createBrowserRouter, Navigate, RouterProvider } from "react-router-dom";
import "./styles/index.css";
import { Layout } from "./components/Layout";
import { Login } from "./pages/Login";
import { Dashboard } from "./pages/Dashboard";
import { Operations } from "./pages/Operations";
import { Workflows } from "./pages/Workflows";
import { Analytics } from "./pages/Analytics";
import { Risks } from "./pages/Risks";
import { Advisor } from "./pages/Advisor";
import { Reports } from "./pages/Reports";
import { HowItWorks } from "./pages/HowItWorks";

function Protected({ children }: { children: React.ReactNode }) {
  return localStorage.getItem("access_token") ? <>{children}</> : <Navigate to="/login" replace />;
}

const router = createBrowserRouter([
  { path: "/login", element: <Login /> },
  {
    path: "/",
    element: <Protected><Layout /></Protected>,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "operations", element: <Operations /> },
      { path: "workflows", element: <Workflows /> },
      { path: "analytics", element: <Analytics /> },
      { path: "risks", element: <Risks /> },
      { path: "advisor", element: <Advisor /> },
      { path: "reports", element: <Reports /> },
      { path: "how-it-works", element: <HowItWorks /> },
    ],
  },
]);

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>
);
