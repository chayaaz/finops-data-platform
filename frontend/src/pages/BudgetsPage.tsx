import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { endpoints } from "@/lib/endpoints";
import { useDimensions } from "@/hooks/useDimensions";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Spinner, ErrorState, EmptyState } from "@/components/ui/States";
import { formatCompactCurrency, formatCurrency, formatMonth, formatPercent } from "@/lib/format";

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
