import { useQuery } from "@tanstack/react-query";
import { DataPanel } from "../components/DataPanel";
import { EmptyState, ErrorState, LoadingState } from "../components/State";
import { fetchOperationsCenter } from "../api/queries";

export function Operations() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["operations-center"], queryFn: fetchOperationsCenter });
  if (isLoading) return <LoadingState rows={7} />;
  if (isError || !data) return <ErrorState />;
  return (
    <div className="space-y-5">
      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-md border border-line bg-white p-4">Active operations <strong className="block text-3xl">{data.active_operations}</strong></div>
        <div className="rounded-md border border-line bg-white p-4">SLA attainment <strong className="block text-3xl">{data.sla.attainment}%</strong></div>
        <div className="rounded-md border border-line bg-white p-4">SLA breaches <strong className="block text-3xl">{data.sla.breached}</strong></div>
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <DataPanel title="Projects">
          <Rows rows={data.projects} columns={["name", "status", "spent", "due_date"]} />
        </DataPanel>
        <DataPanel title="Incidents">
          <Rows rows={data.incidents} columns={["title", "severity", "status", "sla_due_at"]} />
        </DataPanel>
        <DataPanel title="Capacity and workload">
          <Rows rows={data.capacity} columns={["department", "workload", "productivity"]} />
        </DataPanel>
        <DataPanel title="Blockers and delays">
          <Rows rows={data.blockers} columns={["title", "status", "due_date", "variance_hours"]} />
        </DataPanel>
      </div>
    </div>
  );
}

function Rows({ rows, columns }: { rows: any[]; columns: string[] }) {
  if (!rows.length) return <EmptyState label="No records match this operational view." />;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase text-slate-500">
          <tr>{columns.map((column) => <th key={column} className="px-2 py-2">{column.replace(/_/g, " ")}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index} className="border-t border-line">
              {columns.map((column) => <td key={column} className="max-w-64 truncate px-2 py-2">{String(row[column])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
