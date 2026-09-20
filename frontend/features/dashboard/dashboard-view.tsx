"use client";
import {
  BriefcaseBusiness,
  CheckCircle2,
  CircleDollarSign,
  Flame,
  ListChecks,
  Users,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useCallback } from "react";
import { api } from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useApi } from "@/hooks/use-api";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { ErrorState, LoadingState } from "@/components/ui/state";
const colors = [
  "#2563eb",
  "#0f766e",
  "#d97706",
  "#7c3aed",
  "#16a34a",
  "#64748b",
];
export function DashboardView({ analytics = false }: { analytics?: boolean }) {
  const loader = useCallback(() => api.dashboard(), []);
  const { data, loading, error, reload } = useApi(loader);
  if (loading) return <LoadingState label="Loading live sales data" />;
  if (error || !data)
    return (
      <ErrorState
        message={error ?? "Dashboard data is unavailable"}
        onRetry={reload}
      />
    );
  const cards = [
    { label: "Total Leads", value: data.kpis.total_leads, icon: Users },
    { label: "Hot Leads", value: data.kpis.hot_leads, icon: Flame },
    {
      label: "Qualified Leads",
      value: data.kpis.qualified_leads,
      icon: CheckCircle2,
    },
    {
      label: "Open Pipeline",
      value: formatCurrency(data.kpis.open_pipeline_value),
      icon: CircleDollarSign,
    },
    { label: "Won Leads", value: data.kpis.won_leads, icon: BriefcaseBusiness },
    {
      label: "Pending Tasks",
      value: data.kpis.pending_tasks,
      icon: ListChecks,
    },
  ];
  return (
    <div className="space-y-6">
      {!analytics && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-6">
          {cards.map(({ label, value, icon: Icon }) => (
            <Card key={label}>
              <CardContent className="pt-5">
                <div className="flex items-center justify-between">
                  <div className="rounded-lg bg-slate-100 p-2 text-slate-600">
                    <Icon className="size-4" />
                  </div>
                  <span className="text-xs text-slate-400">Live</span>
                </div>
                <p className="mt-4 text-2xl font-bold tracking-tight text-slate-950">
                  {value}
                </p>
                <p className="mt-1 text-xs font-medium text-slate-500">
                  {label}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
      <div className="grid gap-6 xl:grid-cols-2">
        <ChartCard
          title="Lead qualification"
          subtitle="Hot, warm and cold distribution"
        >
          <ResponsiveContainer width="100%" height={270}>
            <PieChart>
              <Pie
                data={data.lead_status_distribution}
                dataKey="value"
                nameKey="name"
                innerRadius={65}
                outerRadius={95}
                paddingAngle={4}
                isAnimationActive={false}
              >
                {data.lead_status_distribution.map((x, i) => (
                  <Cell key={x.name} fill={colors[i]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <Legend data={data.lead_status_distribution} />
        </ChartCard>
        <ChartCard
          title="Pipeline distribution"
          subtitle="Leads at every sales stage"
        >
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.pipeline_distribution}>
              <CartesianGrid vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar
                dataKey="value"
                radius={[6, 6, 0, 0]}
                fill="#2563eb"
                isAnimationActive={false}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard
          title="Score distribution"
          subtitle="Authoritative backend score bands"
        >
          <ResponsiveContainer width="100%" height={270}>
            <BarChart data={data.score_distribution} layout="vertical">
              <CartesianGrid horizontal={false} stroke="#e2e8f0" />
              <XAxis type="number" allowDecimals={false} />
              <YAxis type="category" dataKey="name" width={65} />
              <Tooltip />
              <Bar
                dataKey="value"
                fill="#0f766e"
                radius={[0, 6, 6, 0]}
                isAnimationActive={false}
              />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Tasks overview" subtitle="Workload by task status">
          <ResponsiveContainer width="100%" height={270}>
            <PieChart>
              <Pie
                data={data.task_status_distribution}
                dataKey="value"
                nameKey="name"
                innerRadius={55}
                outerRadius={90}
                isAnimationActive={false}
              >
                {data.task_status_distribution.map((x, i) => (
                  <Cell key={x.name} fill={colors[i + 1]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <Legend data={data.task_status_distribution} />
        </ChartCard>
      </div>
    </div>
  );
}
function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <div>
          <h2 className="font-semibold text-slate-900">{title}</h2>
          <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
        </div>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
function Legend({ data }: { data: { name: string; value: number }[] }) {
  return (
    <div className="flex flex-wrap justify-center gap-4">
      {data.map((x, i) => (
        <span
          key={x.name}
          className="flex items-center gap-2 text-xs text-slate-600"
        >
          <span
            className="size-2 rounded-full"
            style={{ backgroundColor: colors[i] }}
          />
          {x.name} · {x.value}
        </span>
      ))}
    </div>
  );
}
