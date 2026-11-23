import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import { endpoints } from "@/lib/endpoints";
import { useDimensions } from "@/hooks/useDimensions";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Spinner, ErrorState, EmptyState } from "@/components/ui/States";
import { formatCompactCurrency, formatCurrency, formatMonth, formatNumber, formatPercent } from "@/lib/format";
import type { BudgetVarianceRow } from "@/types/api";

const YEARS = [2023, 2024, 2025];

export function BudgetsPage() {
  const [year, setYear] = useState(2025);
  const [categoryId, setCategoryId] = useState<string>("");
  const dims = useDimensions();

  const burnDown = useQuery({
    queryKey: ["burn-down", year, categoryId],
    queryFn: () => endpoints.budgets.burnDown(year, { category_id: categoryId ? Number(categoryId) : undefined }),
  });

  const variance = useQuery({
    queryKey: ["variance", year, categoryId],
    queryFn: () =>
      endpoints.budgets.variance(`${year}-01-01`, `${year}-12-31`, {
        category_id: categoryId ? Number(categoryId) : undefined,
      }),
  });

  const categoryName = (id: number | null) => dims.categories.data?.find((c) => c.id === id)?.name ?? "All categories";

  const chartData = (burnDown.data ?? []).map((p) => ({
    month: formatMonth(p.period_month),
    Budget: p.cumulative_budget,
    Actual: p.cumulative_actual,
  }));

  return (
    <div>
      <PageHeader title="Budget vs Actual" description="Cumulative burn-down and per-period variance analysis" />

      <div className="mb-4 flex gap-3">
        <select
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500"
        >
          {YEARS.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
        <select
          value={categoryId}
          onChange={(e) => setCategoryId(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500"
        >
          <option value="">All categories</option>
          {(dims.categories.data ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {variance.data && variance.data.length > 0 && <BudgetHealthSummary rows={variance.data} year={year} />}

      <Card className="mb-5">
        <CardHeader>
          <CardTitle>Cumulative Burn-Down — {year}</CardTitle>
        </CardHeader>
        <CardBody>
          {burnDown.isLoading ? (
            <Spinner />
          ) : !chartData.length ? (
            <EmptyState message="No budget data for this period" />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData} margin={{ left: -12 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} />
                <YAxis
                  tick={{ fontSize: 11, fill: "#64748b" }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={(v) => formatCompactCurrency(v)}
                  width={64}
                />
                <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={{ borderRadius: 10, border: "1px solid #e2e8f0", fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="Budget" stroke="#94a3b8" strokeWidth={2} strokeDasharray="5 4" dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="Actual" stroke="#4f46e5" strokeWidth={2.5} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Variance by Period — {categoryName(categoryId ? Number(categoryId) : null)}</CardTitle>
        </CardHeader>
        {variance.isLoading ? (
          <Spinner />
        ) : variance.isError ? (
          <ErrorState message="Could not load variance data" />
        ) : !variance.data || variance.data.length === 0 ? (
          <EmptyState message="No variance data for this period" />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-6 py-3">Period</th>
                <th className="px-2 py-3 text-right">Budget</th>
                <th className="px-2 py-3 text-right">Actual</th>
                <th className="px-2 py-3 text-right">Variance</th>
                <th className="px-2 py-3 text-right">Variance %</th>
                <th className="px-2 py-3">Status</th>
              </tr>
            </thead>
            <tbody>
              {variance.data.map((row, idx) => (
                <tr key={idx} className="border-b border-slate-50 hover:bg-slate-50">
                  <td className="px-6 py-2.5 text-slate-700">{formatMonth(row.period_month)}</td>
                  <td className="px-2 py-2.5 text-right tabular text-slate-700">{formatCurrency(row.budget_amount)}</td>
                  <td className="px-2 py-2.5 text-right tabular font-medium text-slate-900">{formatCurrency(row.actual_amount)}</td>
                  <td className={`px-2 py-2.5 text-right tabular ${row.variance >= 0 ? "text-negative-600" : "text-positive-600"}`}>
                    {row.variance >= 0 ? "+" : ""}
                    {formatCurrency(row.variance)}
                  </td>
                  <td className="px-2 py-2.5 text-right tabular text-slate-600">
                    {row.variance_pct != null ? formatPercent(row.variance_pct) : "—"}
                  </td>
                  <td className="px-2 py-2.5">
                    <Badge tone={row.is_over_budget ? "negative" : "positive"}>
                      {row.is_over_budget ? "Over budget" : "Within budget"}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}

// Share of budget used at which the overall status turns from "on track" to "near limit".
const NEAR_LIMIT_PCT = 90;

const healthStyles = {
  on_track: { label: "On track", tone: "positive", bar: "bg-positive-500", icon: CheckCircle2, iconClass: "text-positive-600" },
  near_limit: { label: "Near limit", tone: "warn", bar: "bg-warn-500", icon: AlertTriangle, iconClass: "text-warn-600" },
  over_budget: { label: "Over budget", tone: "negative", bar: "bg-negative-500", icon: XCircle, iconClass: "text-negative-600" },
} as const;

function BudgetHealthSummary({ rows, year }: { rows: BudgetVarianceRow[]; year: number }) {
  const totalBudget = rows.reduce((sum, r) => sum + r.budget_amount, 0);
  const totalActual = rows.reduce((sum, r) => sum + r.actual_amount, 0);
  const remaining = totalBudget - totalActual;
  const usedPct = totalBudget > 0 ? (totalActual / totalBudget) * 100 : null;
  const overLines = rows.filter((r) => r.is_over_budget).length;

  const health =
    usedPct === null || usedPct > 100 ? "over_budget" : usedPct >= NEAR_LIMIT_PCT ? "near_limit" : "on_track";
  const style = healthStyles[health];
  const Icon = style.icon;

  const headline =
    health === "over_budget"
      ? `Spending is ${formatCurrency(Math.abs(remaining))} over the ${year} budget`
      : `Spending is within the ${year} budget, with ${formatCurrency(remaining)} remaining`;

  return (
    <Card className="mb-5">
      <CardBody className="pt-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <Icon size={28} className={style.iconClass} />
            <div>
              <div className="flex items-center gap-2">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Overall status</p>
                <Badge tone={style.tone}>{style.label}</Badge>
              </div>
              <p className="mt-1 text-lg font-bold text-slate-900">{headline}</p>
              <p className="mt-0.5 text-sm text-slate-500">
                {formatNumber(overLines)} of {formatNumber(rows.length)} budget lines are over budget
              </p>
            </div>
          </div>
          {usedPct !== null && (
            <div className="text-right">
              <p className="text-2xl font-bold tabular text-slate-900">{formatPercent(usedPct, 1)}</p>
              <p className="text-xs text-slate-500">of budget used</p>
            </div>
          )}
        </div>

        {usedPct !== null && (
          <div className="mt-4 h-2.5 overflow-hidden rounded-full bg-slate-100">
            <div className={`h-full ${style.bar}`} style={{ width: `${Math.min(usedPct, 100)}%` }} />
          </div>
        )}

        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <SummaryFigure label="Total budget" value={formatCurrency(totalBudget)} />
          <SummaryFigure label="Actual spend" value={formatCurrency(totalActual)} />
          <SummaryFigure
            label={remaining >= 0 ? "Remaining" : "Overspend"}
            value={formatCurrency(Math.abs(remaining))}
            tone={remaining >= 0 ? "text-positive-600" : "text-negative-600"}
          />
          <SummaryFigure
            label="Lines over budget"
            value={`${formatNumber(overLines)} / ${formatNumber(rows.length)}`}
            tone={overLines > 0 ? "text-warn-600" : "text-positive-600"}
          />
        </div>
      </CardBody>
    </Card>
  );
}

function SummaryFigure({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`mt-0.5 text-base font-semibold tabular ${tone ?? "text-slate-900"}`}>{value}</p>
    </div>
  );
}
