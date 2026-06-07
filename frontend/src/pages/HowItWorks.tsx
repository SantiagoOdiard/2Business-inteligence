import { Activity, DatabaseZap, LineChart, ShieldCheck, SlidersHorizontal } from "lucide-react";

const steps = [
  { icon: DatabaseZap, title: "Connect data", body: "Operational records, users, departments, incidents, projects and workflow events feed a shared enterprise model." },
  { icon: Activity, title: "Monitor operations", body: "Command views track live workload, capacity, SLA status, blockers and delivery health across departments." },
  { icon: ShieldCheck, title: "Detect risks", body: "Risk scores are calculated from historical incidents, workload, budget pressure and workflow delays." },
  { icon: LineChart, title: "Analyze performance", body: "Executives compare revenue, cost, productivity, satisfaction and department trends from the same underlying data." },
  { icon: SlidersHorizontal, title: "Optimize decisions", body: "Advisor recommendations explain priority, impact, confidence and the next operational action." },
];

export function HowItWorks() {
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold">How it works</h1>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
        {steps.map((step) => (
          <article key={step.title} className="rounded-md border border-line bg-white p-4 shadow-panel">
            <step.icon className="h-5 w-5 text-primary" />
            <h2 className="mt-4 font-semibold">{step.title}</h2>
            <p className="mt-2 text-sm text-slate-600">{step.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
