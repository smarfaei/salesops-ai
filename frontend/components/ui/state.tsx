import { AlertCircle, Inbox, LoaderCircle } from "lucide-react";
import { Button } from "./button";
export function LoadingState({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex min-h-52 items-center justify-center gap-2 text-sm text-slate-500">
      <LoaderCircle className="size-5 animate-spin" />
      {label}…
    </div>
  );
}
export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex min-h-52 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-rose-200 bg-rose-50/40 p-8 text-center">
      <AlertCircle className="size-6 text-rose-600" />
      <div>
        <p className="font-semibold text-slate-900">Unable to load this view</p>
        <p className="mt-1 text-sm text-slate-600">{message}</p>
      </div>
      {onRetry && (
        <Button variant="outline" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex min-h-52 flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 p-8 text-center">
      <Inbox className="size-7 text-slate-400" />
      <p className="mt-3 font-semibold text-slate-900">{title}</p>
      <p className="mt-1 max-w-md text-sm text-slate-500">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
