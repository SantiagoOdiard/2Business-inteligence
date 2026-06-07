import { BarChart3, BrainCircuit, ClipboardList, FileText, Gauge, LogOut, Menu, Network, ShieldAlert, Workflow, X } from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { logout } from "../api/client";

const links = [
  { to: "/", label: "Dashboard", icon: Gauge },
  { to: "/operations", label: "Operations", icon: Network },
  { to: "/workflows", label: "Workflows", icon: Workflow },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/risks", label: "Risks", icon: ShieldAlert },
  { to: "/advisor", label: "AI Advisor", icon: BrainCircuit },
  { to: "/reports", label: "Reports", icon: FileText },
  { to: "/how-it-works", label: "How it works", icon: ClipboardList },
];

export function Layout() {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const sidebar = (
    <>
      <div className="flex items-center justify-between border-b border-line px-5 py-5">
        <div>
          <div className="text-sm font-semibold text-primary">Enterprise Ops</div>
          <div className="mt-1 text-lg font-semibold leading-tight">Intelligence Suite</div>
        </div>
        <button
          className="grid h-9 w-9 place-items-center rounded-md border border-line text-slate-600 hover:bg-slate-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          title="Close navigation"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <nav className="space-y-1 p-3">
        {links.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={() => setSidebarOpen(false)}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-md px-3 py-2 text-sm ${isActive ? "bg-teal-50 text-teal-800" : "text-slate-600 hover:bg-slate-50"}`
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </>
  );

  return (
    <div className="min-h-screen bg-canvas text-ink">
      {sidebarOpen && <button className="fixed inset-0 z-30 bg-slate-900/30 lg:hidden" onClick={() => setSidebarOpen(false)} title="Close navigation overlay" />}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 border-r border-line bg-white lg:block">
        {sidebar}
      </aside>
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-72 max-w-[85vw] border-r border-line bg-white shadow-xl transition-transform duration-200 lg:hidden ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        {sidebar}
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-line bg-white px-4 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <button
              className="grid h-9 w-9 shrink-0 place-items-center rounded-md border border-line text-slate-600 hover:bg-slate-50 lg:hidden"
              onClick={() => setSidebarOpen(true)}
              title="Open navigation"
            >
              <Menu className="h-4 w-4" />
            </button>
            <div className="min-w-0">
              <div className="truncate text-sm text-slate-500">Enterprise command workspace</div>
              <div className="truncate font-semibold">Live operational intelligence</div>
            </div>
          </div>
          <button
            className="inline-flex items-center gap-2 rounded-md border border-line bg-white px-3 py-2 text-sm hover:bg-slate-50"
            onClick={() => {
              logout();
              navigate("/login");
            }}
            title="Log out"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
        </header>
        <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
