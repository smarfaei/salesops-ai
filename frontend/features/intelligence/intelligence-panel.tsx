"use client";
import { useCallback, useState } from "react";
import {
  BrainCircuit,
  Check,
  Clipboard,
  RefreshCw,
  Sparkles,
  TriangleAlert,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { formatDate, priorityTone } from "@/lib/utils";
import { useApi } from "@/hooks/use-api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ErrorState, LoadingState } from "@/components/ui/state";
export function IntelligencePanel({
  leadId,
  onGenerated,
}: {
  leadId: number;
  onGenerated?: () => void;
}) {
  const loader = useCallback(async () => {
    try {
      return await api.intelligence(leadId);
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) return null;
      throw e;
    }
  }, [leadId]);
  const { data, loading, error, reload } = useApi(loader);
  const [generating, setGenerating] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const generate = async () => {
    setGenerating(true);
    setActionError(null);
    try {
      await api.generateIntelligence(leadId);
      await reload();
      onGenerated?.();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  };
  if (loading)
    return (
      <Card>
        <LoadingState label="Loading intelligence" />
      </Card>
    );
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!data)
    return (
      <Card className="border-blue-200 bg-blue-50/30">
        <CardContent className="flex min-h-64 flex-col items-center justify-center text-center">
          <div className="rounded-2xl bg-blue-100 p-4 text-blue-700">
            <BrainCircuit className="size-7" />
          </div>
          <h2 className="mt-4 text-lg font-bold">
            Turn lead data into a sales brief
          </h2>
          <p className="mt-2 max-w-lg text-sm leading-6 text-slate-600">
            Generate an AI-assisted recommendation from the lead profile,
            timeline, and open tasks. The deterministic local provider works
            without paid services.
          </p>
          <Button className="mt-5" onClick={generate} disabled={generating}>
            <Sparkles className="size-4" />
            {generating ? "Generating…" : "Generate intelligence"}
          </Button>
          {actionError && (
            <p className="mt-3 text-sm text-rose-700">{actionError}</p>
          )}
        </CardContent>
      </Card>
    );
  return (
    <Card>
      <CardHeader>
        <div>
          <div className="flex items-center gap-2">
            <BrainCircuit className="size-5 text-blue-700" />
            <h2 className="font-bold text-slate-950">Sales Intelligence</h2>
            <Badge className="bg-blue-50 text-blue-700 ring-blue-200">
              AI-assisted recommendation
            </Badge>
          </div>
          <p className="mt-2 text-xs text-slate-500">
            {data.provider} provider · Generated {formatDate(data.generated_at)}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={generate}
          disabled={generating}
        >
          <RefreshCw
            className={generating ? "size-4 animate-spin" : "size-4"}
          />
          {generating ? "Regenerating…" : "Regenerate"}
        </Button>
      </CardHeader>
      <CardContent className="space-y-6">
        <section>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Qualification summary
          </h3>
          <p className="mt-2 text-sm leading-6 text-slate-700">
            {data.qualification_summary}
          </p>
        </section>
        <div className="grid gap-5 lg:grid-cols-2">
          <SignalList
            title="Buying signals"
            icon={<Check className="size-4 text-emerald-600" />}
            items={data.buying_signals}
          />
          <SignalList
            title="Risks to validate"
            icon={<TriangleAlert className="size-4 text-amber-600" />}
            items={data.risks}
          />
        </div>
        <section className="rounded-xl border border-blue-100 bg-blue-50/50 p-4">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-sm font-bold text-slate-900">
              Next best action
            </h3>
            <span
              className={`text-xs font-bold uppercase ${priorityTone[data.next_best_action.priority]}`}
            >
              {data.next_best_action.priority} priority
            </span>
          </div>
          <p className="mt-2 font-semibold text-blue-800">
            {data.next_best_action.action}
          </p>
          <p className="mt-1 text-sm leading-6 text-slate-600">
            {data.next_best_action.reason}
          </p>
        </section>
        <section className="rounded-xl border border-slate-200">
          <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
            <div>
              <h3 className="text-sm font-bold">Suggested follow-up</h3>
              <p className="text-xs text-slate-500">
                Ready to copy into a future Gmail or CRM integration
              </p>
            </div>
            <CopyButton
              text={`${data.follow_up.subject}\n\n${data.follow_up.message}`}
            />
          </div>
          <div className="p-4">
            <p className="text-sm font-semibold text-slate-900">
              {data.follow_up.subject}
            </p>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-600">
              {data.follow_up.message}
            </p>
          </div>
        </section>
        {actionError && <p className="text-sm text-rose-700">{actionError}</p>}
      </CardContent>
    </Card>
  );
}
function SignalList({
  title,
  icon,
  items,
}: {
  title: string;
  icon: React.ReactNode;
  items: { signal: string; evidence: string }[];
}) {
  return (
    <section>
      <h3 className="flex items-center gap-2 text-sm font-bold text-slate-900">
        {icon}
        {title}
      </h3>
      <div className="mt-3 space-y-3">
        {items.length ? (
          items.map((x, i) => (
            <div
              key={`${x.signal}-${i}`}
              className="rounded-lg bg-slate-50 p-3"
            >
              <p className="text-sm font-semibold text-slate-800">{x.signal}</p>
              <p className="mt-1 text-xs leading-5 text-slate-500">
                Evidence: {x.evidence}
              </p>
            </div>
          ))
        ) : (
          <p className="text-sm text-slate-500">No items identified.</p>
        )}
      </div>
    </section>
  );
}
function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <Button variant="ghost" size="sm" onClick={copy}>
      {copied ? <Check className="size-4" /> : <Clipboard className="size-4" />}
      {copied ? "Copied" : "Copy"}
    </Button>
  );
}
