import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, DollarSign, Radar, ShieldCheck } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { endpoints } from "@/lib/endpoints";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatCard } from "@/components/ui/StatCard";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Spinner, ErrorState } from "@/components/ui/States";
import { formatCompactCurrency, formatCurrency, formatMonth, formatNumber } from "@/lib/format";

export function DashboardPage() {
  const kpis = useQuery({ queryKey: ["kpis"], queryFn: endpoints.analytics.kpis });
  const trends = useQuery({ queryKey: ["trends"], queryFn: () => endpoints.analytics.trends() });
  const issueSummary = useQuery({ queryKey: ["issue-summary"], queryFn: () => endpoints.issues.summary() });

  if (kpis.isLoading) return <Spinner label="Loading dashboard" />;
  if (kpis.isError || !kpis.data) return <ErrorState message="Could not load dashboard KPIs" />;

  const k = kpis.data;
  const chartData = (trends.data ?? []).map((p) => ({ month: formatMonth(p.period_month), spend: p.total_spend }));

  return (
    <div>
      <PageHeader title="Executive Dashboard" description="Portfolio-wide financial health at a glance" />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Total Spend"
          value={formatCompactCurrency(k.total_spend)}
          icon={DollarSign}
          accent="brand"
          trend={k.mom_growth_pct != null ? { value: k.mom_growth_pct, label: "vs last month" } : null}
        />
        <StatCard label="Transactions Processed" value={formatNumber(k.total_transactions)} icon={ShieldCheck} accent="brand" />
        <StatCard
          label="Data Quality Score"
          value={`${k.data_quality_score_pct.toFixed(1)}%`}
          icon={ShieldCheck}
          accent={k.data_quality_score_pct >= 95 ? "positive" : k.data_quality_score_pct >= 85 ? "warn" : "negative"}
          footer={`${k.open_issues} open issue${k.open_issues === 1 ? "" : "s"}`}
        />
        <StatCard
          label="Open Anomalies"
          value={formatNumber(k.open_anomalies)}
          icon={Radar}
          accent={k.open_anomalies > 0 ? "warn" : "positive"}
          footer="Statistical outliers awaiting review"
        />
      </div>

      <div className="mt-5 grid grid-cols-1 gap-5 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Monthly Spend Trend</CardTitle>
          </CardHeader>
          <CardBody>
            {trends.isLoading ? (
              <Spinner />
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={chartData} margin={{ left: -12 }}>
                  <defs>
                    <linearGradient id="spendGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#4f46e5" stopOpacity={0.28} />
                      <stop offset="100%" stopColor="#4f46e5" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
                  <YAxis
                    tick={{ fontSize: 11, fill: "#64748b" }}
                    axisLine={false}
                    tickLine={false}
                    tickFormatter={(v) => formatCompactCurrency(v)}
                    width={64}
                  />
                  <Tooltip
                    formatter={(value: number) => formatCurrency(value)}
                    contentStyle={{ borderRadius: 10, border: "1px solid #e2e8f0", fontSize: 12 }}
                  />
                  <Area type="monotone" dataKey="spend" stroke="#4f46e5" strokeWidth={2} fill="url(#spendGradient)" isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </CardBody>
        </Card>

        <div className="flex flex-col gap-5">
          <Card>
            <CardHeader>
              <CardTitle>Top Spending Category</CardTitle>
            </CardHeader>
            <CardBody>
              {k.top_category_name ? (
                <div>
                  <p className="text-lg font-bold text-slate-900">{k.top_category_name}</p>
                  <p className="mt-1 text-sm text-slate-500">{formatCurrency(k.top_category_spend ?? 0)} total spend</p>
                </div>
              ) : (
                <p className="text-sm text-slate-400">No category data yet</p>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Issues by Severity</CardTitle>
            </CardHeader>
            <CardBody>
              {issueSummary.isLoading ? (
                <Spinner />
              ) : issueSummary.data ? (
                <div className="space-y-2.5">
                  {Object.entries(issueSummary.data.by_severity).map(([severity, count]) => (
                    <SeverityBar key={severity} severity={severity} count={count} />
                  ))}
                </div>
              ) : (
                <div className="flex items-center gap-2 text-sm text-slate-400">
                  <AlertTriangle size={16} /> No issue data
                </div>
              )}
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}

const severityColor: Record<string, string> = {
  critical: "bg-negative-500",
  high: "bg-warn-500",
  medium: "bg-brand-400",
  low: "bg-slate-400",
};

function SeverityBar({ severity, count }: { severity: string; count: number }) {
  return (
    <div className="flex items-center gap-3">
      <span className="w-16 shrink-0 text-xs font-medium capitalize text-slate-600">{severity}</span>
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full ${severityColor[severity] ?? "bg-slate-400"}`} style={{ width: `${Math.min(count * 4, 100)}%` }} />
      </div>
      <span className="w-6 text-right text-xs font-semibold tabular text-slate-700">{count}</span>
    </div>
  );
}
