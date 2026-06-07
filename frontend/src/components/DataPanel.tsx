import type { ReactNode } from "react";

export function DataPanel({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  return (
    <section className="rounded-md border border-line bg-white shadow-panel">
      <div className="flex items-center justify-between border-b border-line px-4 py-3">
        <h2 className="text-sm font-semibold">{title}</h2>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </section>
  );
}

export function MetricTile({ label, value, unit, delta }: { label: string; value: number; unit: string; delta: number }) {
  const formatted = unit === "USD" ? new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value) : value.toLocaleString();
  return (
    <div className="rounded-md border border-line bg-white p-4 shadow-panel">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-2 flex items-end justify-between gap-2">
        <div className="min-w-0 text-2xl font-semibold tabular-nums">{formatted}</div>
        <div className={`text-xs tabular-nums ${delta >= 0 ? "text-teal-700" : "text-red-700"}`}>{delta ? `${delta > 0 ? "+" : ""}${delta}%` : unit}</div>
      </div>
    </div>
  );
}
