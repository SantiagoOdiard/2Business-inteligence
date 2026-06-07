import { useQuery } from "@tanstack/react-query";
import { fetchWorkflows } from "../api/queries";
import { DataPanel } from "../components/DataPanel";
import { ErrorState, LoadingState } from "../components/State";

export function Workflows() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["workflows"], queryFn: fetchWorkflows });
  if (isLoading) return <LoadingState rows={8} />;
  if (isError) return <ErrorState />;
  return (
    <DataPanel title="Workflow engine">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {data.map((item: any) => (
          <article key={item.id} className="rounded-md border border-line p-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="truncate font-medium">{item.name}</h3>
              <span className="rounded bg-slate-100 px-2 py-1 text-xs">{item.status}</span>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <span>Duration <strong className="block">{item.duration_hours}h</strong></span>
              <span>Average <strong className="block">{item.average_time_hours}h</strong></span>
              <span>Delay <strong className="block">{item.delay_hours}h</strong></span>
              <span>Risk <strong className="block">{item.risk_score}/100</strong></span>
            </div>
          </article>
        ))}
      </div>
    </DataPanel>
  );
}
