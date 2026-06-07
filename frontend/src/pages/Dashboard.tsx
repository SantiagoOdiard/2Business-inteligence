import { useQuery } from "@tanstack/react-query";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { DataPanel, MetricTile } from "../components/DataPanel";
import { EmptyState, ErrorState, LoadingState } from "../components/State";
import { fetchDashboard } from "../api/queries";

export function Dashboard() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["dashboard"], queryFn: fetchDashboard });
  if (isLoading) return <LoadingState rows={8} />;
  if (isError || !data) return <ErrorState />;
  return (
    <div className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {data.kpis.map((kpi) => <MetricTile key={kpi.key} label={kpi.label} value={kpi.value} unit={kpi.unit} delta={kpi.delta} />)}
      </div>
      <div className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
        <DataPanel title="Revenue, cost and productivity trend">
          {data.trend.length ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.trend}>
                  <CartesianGrid stroke="#E5E7EB" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Area dataKey="revenue" stroke="#14B8A6" fill="#CCFBF1" />
                  <Area dataKey="cost" stroke="#64748B" fill="#E2E8F0" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          ) : <EmptyState label="No historical trend is available." />}
        </DataPanel>
        <DataPanel title="Department performance">
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.departments.slice(0, 8)}>
                <CartesianGrid stroke="#E5E7EB" />
                <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="productivity" fill="#14B8A6" />
                <Bar dataKey="satisfaction" fill="#475569" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </DataPanel>
      </div>
    </div>
  );
}
