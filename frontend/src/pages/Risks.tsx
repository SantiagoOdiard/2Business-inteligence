import { useQuery } from "@tanstack/react-query";
import { ShieldAlert } from "lucide-react";
import { fetchDashboard } from "../api/queries";
import { DataPanel } from "../components/DataPanel";
import { ErrorState, LoadingState } from "../components/State";

export function Risks() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["dashboard"], queryFn: fetchDashboard });
  if (isLoading) return <LoadingState rows={6} />;
  if (isError || !data) return <ErrorState />;
  return (
    <DataPanel title="Risk engine">
      <div className="grid gap-3 md:grid-cols-2">
        {data.risks.map((risk, index) => (
          <article key={index} className="rounded-md border border-line p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-medium"><ShieldAlert className="h-4 w-4 text-orange-600" />{risk.category}</div>
              <strong>{risk.score}/100</strong>
            </div>
            <div className="mt-3 h-2 rounded bg-slate-100">
              <div className="h-2 rounded bg-orange-500" style={{ width: `${Math.min(100, risk.score)}%` }} />
            </div>
            <p className="mt-3 text-sm text-slate-600">{risk.reason}</p>
          </article>
        ))}
      </div>
    </DataPanel>
  );
}
