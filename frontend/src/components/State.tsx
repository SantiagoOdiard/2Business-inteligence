import { AlertTriangle, Loader2 } from "lucide-react";

export function LoadingState({ rows = 4 }: { rows?: number }) {
  return (
    <div className="space-y-3" aria-busy="true">
      {Array.from({ length: rows }).map((_, index) => (
        <div key={index} className="h-14 rounded-md skeleton" />
      ))}
    </div>
  );
}

export function ErrorState({ message = "Unable to load enterprise data." }: { message?: string }) {
  return (
    <div className="flex items-center gap-3 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      <AlertTriangle className="h-5 w-5" />
      <span>{message}</span>
    </div>
  );
}

export function EmptyState({ label }: { label: string }) {
  return <div className="rounded-md border border-line bg-white p-6 text-sm text-slate-500">{label}</div>;
}

export function SavingState() {
  return <Loader2 className="h-4 w-4 animate-spin" aria-label="Loading" />;
}
