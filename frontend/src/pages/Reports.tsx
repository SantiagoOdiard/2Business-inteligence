import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, FilePlus2 } from "lucide-react";
import { api } from "../api/client";
import { fetchReports } from "../api/queries";
import { DataPanel } from "../components/DataPanel";
import { EmptyState, ErrorState, LoadingState, SavingState } from "../components/State";

export function Reports() {
  const client = useQueryClient();
  const { data, isLoading, isError } = useQuery({ queryKey: ["reports"], queryFn: fetchReports });
  const create = useMutation({
    mutationFn: () => api.post("/reports", { period: "Weekly", title: "Weekly Executive Operations Report" }),
    onSuccess: () => client.invalidateQueries({ queryKey: ["reports"] }),
  });
  const exportReport = useMutation({ mutationFn: (format: string) => api.get(`/reports/export/${format}`) });
  if (isLoading) return <LoadingState rows={5} />;
  if (isError) return <ErrorState />;
  return (
    <DataPanel
      title="Executive reports"
      action={<button className="inline-flex items-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-white" onClick={() => create.mutate()}>{create.isPending ? <SavingState /> : <FilePlus2 className="h-4 w-4" />}Generate</button>}
    >
      <div className="mb-4 flex flex-wrap gap-2">
        {["pdf", "excel", "csv"].map((format) => (
          <button key={format} className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm" onClick={() => exportReport.mutate(format)}>
            <Download className="h-4 w-4" /> Export {format.toUpperCase()}
          </button>
        ))}
      </div>
      {!data.length ? <EmptyState label="No executive reports have been generated yet." /> : (
        <div className="space-y-3">
          {data.map((report: any) => (
            <article key={report.id} className="rounded-md border border-line p-4">
              <div className="font-semibold">{report.title}</div>
              <p className="mt-1 text-sm text-slate-600">{report.summary}</p>
              <div className="mt-2 text-xs text-slate-500">{report.period} · {new Date(report.created_at).toLocaleString()}</div>
            </article>
          ))}
        </div>
      )}
    </DataPanel>
  );
}
