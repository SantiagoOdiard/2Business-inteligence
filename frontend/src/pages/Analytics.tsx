import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchDepartments, fetchForecasts } from "../api/queries";
import { DataPanel } from "../components/DataPanel";
import { ErrorState, LoadingState } from "../components/State";

export function Analytics() {
  const departments = useQuery({ queryKey: ["departments"], queryFn: fetchDepartments });
  const forecasts = useQuery({ queryKey: ["forecasts"], queryFn: fetchForecasts });
  if (departments.isLoading || forecasts.isLoading) return <LoadingState rows={7} />;
  if (departments.isError || forecasts.isError) return <ErrorState />;
  return (
    <div className="space-y-5">
      <DataPanel title="Department comparison">
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={departments.data}>
              <CartesianGrid stroke="#E5E7EB" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="productivity" fill="#14B8A6" />
              <Bar dataKey="risk" fill="#F97316" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </DataPanel>
      <DataPanel title="Forecasting">
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {forecasts.data.slice(0, 18).map((item: any, index: number) => (
            <article key={index} className="rounded-md border border-line p-4">
              <div className="text-sm font-semibold">{item.metric}</div>
              <div className="mt-2 text-2xl font-semibold">{Number(item.prediction).toLocaleString()}</div>
              <p className="mt-2 text-sm text-slate-500">{item.explanation}</p>
              <div className="mt-3 text-xs text-teal-700">Confidence {item.confidence}%</div>
            </article>
          ))}
        </div>
      </DataPanel>
    </div>
  );
}
