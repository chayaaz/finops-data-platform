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
const QUARTERS = [1, 2, 3, 4];

// Share of budget used above which a line or period turns orange, then red.
const WARN_PCT = 80;
const DANGER_PCT = 95;

type BudgetStatus = "on_track" | "near_limit" | "at_risk" | "over_budget";
type StatusFilter = "all" | "flagged" | "red";

const statusStyles = {
  on_track: { label: "On track", tone: "positive", bar: "bg-positive-500", icon: CheckCircle2, iconClass: "text-positive-600" },
  near_limit: { label: "Near limit", tone: "warn", bar: "bg-warn-500", icon: AlertTriangle, iconClass: "text-warn-600" },
  at_risk: { label: "At risk", tone: "negative", bar: "bg-negative-500", icon: AlertTriangle, iconClass: "text-negative-600" },
  over_budget: { label: "Over budget", tone: "negative", bar: "bg-negative-500", icon: XCircle, iconClass: "text-negative-600" },
} as const;

/** Percent of budget used; null when there is spend but no budget at all. */
function usedPct(budget: number, actual: number): number | null {
  if (budget > 0) return (actual / budget) * 100;
  return actual > 0 ? null : 0;
}

function budgetStatus(pct: number | null): BudgetStatus {
  if (pct === null || pct > 100) return "over_budget";
  if (pct > DANGER_PCT) return "at_risk";
  if (pct > WARN_PCT) return "near_limit";
  return "on_track";
}

const isRed = (s: BudgetStatus) => s === "at_risk" || s === "over_budget";

export function BudgetsPage() {
  const [year, setYear] = useState(2025);
  const [quarter, setQuarter] = useState<number | null>(null);
  const [categoryId, setCategoryId] = useState<string>("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const dims = useDimensions();

  const catId = categoryId ? Number(categoryId) : undefined;
  const [periodStart, periodEnd] = quarterBounds(year, quarter);
  const periodLabel = quarter ? `Q${quarter} ${year}` : String(year);

  const burnDown = useQuery({
    queryKey: ["burn-down", year, quarter, categoryId],
    queryFn: () => endpoints.budgets.burnDown(year, { category_id: catId, quarter: quarter ?? undefined }),
  });

  const variance = useQuery({
    queryKey: ["variance", periodStart, periodEnd, categoryId],
    queryFn: () => endpoints.budgets.variance(periodStart, periodEnd, { category_id: catId }),
  });

  const categoryName = (id: number | null) => dims.categories.data?.find((c) => c.id === id)?.name ?? "—";
  const costCenterCode = (id: number | null) => dims.costCenters.data?.find((c) => c.id === id)?.code ?? "—";

  const chartData = (burnDown.data ?? []).map((p) => ({
    month: formatMonth(p.period_month),
    Budget: p.cumulative_budget,
    Actual: p.cumulative_actual,
  }));

  // Worst lines first, so overspending is visible without scrolling.
  const tableRows = (variance.data ?? [])
    .map((row) => {
      const pct = usedPct(row.budget_amount, row.actual_amount);
      return { ...row, pct, status: budgetStatus(pct) };
    })
    .filter((row) => statusFilter === "all" || (statusFilter === "red" ? isRed(row.status) : row.status !== "on_track"))
    .sort((a, b) => (b.pct ?? Infinity) - (a.pct ?? Infinity));

  const selectClass = "rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500";

  return (
    <div>
      <PageHeader title="Budget vs Actual" description="Cumulative burn-down and per-period variance analysis" />

      <div className="mb-4 flex flex-wrap gap-3">
        <select value={year} onChange={(e) => setYear(Number(e.target.value))} className={selectClass} aria-label="Year">
          {YEARS.map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
        <select
          value={quarter ?? ""}
          onChange={(e) => setQuarter(e.target.value ? Number(e.target.value) : null)}
          className={selectClass}
          aria-label="Quarter"
        >
          <option value="">Full year</option>
          {QUARTERS.map((q) => (
            <option key={q} value={q}>
              Q{q}
            </option>
          ))}
        </select>
        <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)} className={selectClass} aria-label="Category">
          <option value="">All categories</option>
          {(dims.categories.data ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      {variance.data && variance.data.length > 0 && <BudgetHealthSummary rows={variance.data} periodLabel={periodLabel} />}

      <Card className="mb-5">
        <CardHeader>
          <CardTitle>Cumulative Burn-Down — {periodLabel}</CardTitle>
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
        <CardHeader className="flex-wrap gap-3">
          <CardTitle>
            Variance by Line — {periodLabel}
            {catId ? ` · ${categoryName(catId)}` : ""}
          </CardTitle>
          <div className="flex items-center gap-3">
            <ThresholdLegend />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as StatusFilter)}
              className="rounded-lg border border-slate-300 px-2 py-1 text-xs outline-none focus:border-brand-500"
              aria-label="Filter lines by status"
            >
              <option value="all">All lines</option>
              <option value="flagged">Above {WARN_PCT}% only</option>
              <option value="red">Above {DANGER_PCT}% only</option>
            </select>
          </div>
        </CardHeader>
        {variance.isLoading ? (
          <Spinner />
        ) : variance.isError ? (
          <ErrorState message="Could not load variance data" />
        ) : tableRows.length === 0 ? (
          <EmptyState message="No budget lines match this view" />
        ) : (
          <div className="max-h-[32rem] overflow-y-auto">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-white">
                <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-6 py-3">Period</th>
                  <th className="px-2 py-3">Cost center</th>
                  <th className="px-2 py-3">Category</th>
                  <th className="px-2 py-3 text-right">Budget</th>
                  <th className="px-2 py-3 text-right">Actual</th>
                  <th className="px-2 py-3 text-right">Variance</th>
                  <th className="px-2 py-3 text-right">Used</th>
                  <th className="px-2 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {tableRows.map((row) => (
                  <tr
                    key={`${row.cost_center_id}-${row.category_id}-${row.period_month}`}
                    className="border-b border-slate-50 hover:bg-slate-50"
                  >
                    <td className="px-6 py-2.5 text-slate-700">{formatMonth(row.period_month)}</td>
                    <td className="px-2 py-2.5 font-mono text-xs text-slate-600">{costCenterCode(row.cost_center_id)}</td>
                    <td className="px-2 py-2.5 text-slate-600">{categoryName(row.category_id)}</td>
                    <td className="px-2 py-2.5 text-right tabular text-slate-700">{formatCurrency(row.budget_amount)}</td>
                    <td className="px-2 py-2.5 text-right tabular font-medium text-slate-900">{formatCurrency(row.actual_amount)}</td>
                    <td className={`px-2 py-2.5 text-right tabular ${row.variance > 0 ? "text-negative-600" : "text-positive-600"}`}>
                      {row.variance > 0 ? "+" : ""}
                      {formatCurrency(row.variance)}
                    </td>
                    <td className="px-2 py-2.5 text-right tabular text-slate-600">
                      {row.pct != null ? formatPercent(row.pct, 0) : "No budget"}
                    </td>
                    <td className="px-2 py-2.5">
                      <Badge tone={statusStyles[row.status].tone}>{statusStyles[row.status].label}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

function quarterBounds(year: number, quarter: number | null): [string, string] {
  if (!quarter) return [`${year}-01-01`, `${year}-12-31`];
  const firstMonth = 3 * (quarter - 1) + 1;
  const lastMonth = firstMonth + 2;
  const lastDay = new Date(Date.UTC(year, lastMonth, 0)).getUTCDate();
  const pad = (n: number) => String(n).padStart(2, "0");
  return [`${year}-${pad(firstMonth)}-01`, `${year}-${pad(lastMonth)}-${pad(lastDay)}`];
}

function ThresholdLegend() {
  return (
    <div className="hidden items-center gap-3 text-xs text-slate-500 md:flex">
      <span className="flex items-center gap-1">
        <span className="h-2 w-2 rounded-full bg-positive-500" />≤ {WARN_PCT}%
      </span>
      <span className="flex items-center gap-1">
        <span className="h-2 w-2 rounded-full bg-warn-500" />
        {WARN_PCT}–{DANGER_PCT}%
      </span>
      <span className="flex items-center gap-1">
        <span className="h-2 w-2 rounded-full bg-negative-500" />&gt; {DANGER_PCT}%
      </span>
    </div>
  );
}

function BudgetHealthSummary({ rows, periodLabel }: { rows: BudgetVarianceRow[]; periodLabel: string }) {
  const totalBudget = rows.reduce((sum, r) => sum + r.budget_amount, 0);
  const totalActual = rows.reduce((sum, r) => sum + r.actual_amount, 0);
  const remaining = totalBudget - totalActual;
  const pct = usedPct(totalBudget, totalActual);
  const status = budgetStatus(pct);
  const style = statusStyles[status];
  const Icon = style.icon;

  const lineStatuses = rows.map((r) => budgetStatus(usedPct(r.budget_amount, r.actual_amount)));
  const orangeLines = lineStatuses.filter((s) => s === "near_limit").length;
  const redLines = lineStatuses.filter(isRed).length;

  const headline =
    remaining < 0
      ? `Spending is ${formatCurrency(Math.abs(remaining))} over the ${periodLabel} budget`
      : `${formatCurrency(remaining)} of the ${periodLabel} budget remains`;

  const explanation = {
    on_track: `Less than ${WARN_PCT}% of the budget has been used.`,
    near_limit: `More than ${WARN_PCT}% of the budget has been used — watch spending closely.`,
    at_risk: `More than ${DANGER_PCT}% of the budget has been used — very little headroom is left.`,
    over_budget: "Actual spending has exceeded the budget.",
  }[status];

  return (
    <Card className="mb-5">
      <CardBody className="pt-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <Icon size={28} className={style.iconClass} />
            <div>
              <div className="flex items-center gap-2">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Overall status — {periodLabel}</p>
                <Badge tone={style.tone}>{style.label}</Badge>
              </div>
              <p className="mt-1 text-lg font-bold text-slate-900">{headline}</p>
              <p className="mt-0.5 text-sm text-slate-500">{explanation}</p>
            </div>
          </div>
          {pct !== null && (
            <div className="text-right">
              <p className="text-2xl font-bold tabular text-slate-900">{formatPercent(pct, 1)}</p>
              <p className="text-xs text-slate-500">of budget used</p>
            </div>
          )}
        </div>

        {pct !== null && (
          <div className="relative mt-4 h-2.5 overflow-hidden rounded-full bg-slate-100">
            <div className={`h-full ${style.bar}`} style={{ width: `${Math.min(pct, 100)}%` }} />
            <span className="absolute top-0 h-full w-px bg-slate-400" style={{ left: `${WARN_PCT}%` }} title={`${WARN_PCT}%`} />
            <span className="absolute top-0 h-full w-px bg-slate-400" style={{ left: `${DANGER_PCT}%` }} title={`${DANGER_PCT}%`} />
          </div>
        )}

        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-5">
          <SummaryFigure label="Total budget" value={formatCurrency(totalBudget)} />
          <SummaryFigure label="Actual spend" value={formatCurrency(totalActual)} />
          <SummaryFigure
            label={remaining >= 0 ? "Remaining" : "Overspend"}
            value={formatCurrency(Math.abs(remaining))}
            tone={remaining >= 0 ? "text-positive-600" : "text-negative-600"}
          />
          <SummaryFigure label={`Lines ${WARN_PCT}–${DANGER_PCT}%`} value={formatNumber(orangeLines)} tone="text-warn-600" />
          <SummaryFigure label={`Lines above ${DANGER_PCT}%`} value={formatNumber(redLines)} tone="text-negative-600" />
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
