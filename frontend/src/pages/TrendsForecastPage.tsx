import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Area, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { TrendingDown, TrendingUp } from "lucide-react";
import { endpoints } from "@/lib/endpoints";
import { useDimensions } from "@/hooks/useDimensions";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Spinner, ErrorState } from "@/components/ui/States";
import { formatCompactCurrency, formatCurrency, formatMonth } from "@/lib/format";

export function TrendsForecastPage() {
  const dims = useDimensions();
  const [categoryId, setCategoryId] = useState<string>("");
  const [monthsAhead, setMonthsAhead] = useState(3);

  const catId = categoryId ? Number(categoryId) : undefined;
  const forecast = useQuery({
    queryKey: ["forecast", catId, monthsAhead],
    queryFn: () => endpoints.analytics.forecast(catId, monthsAhead),
  });

  const chartData = useMemo(() => {
    if (!forecast.data) return [];
    const history = forecast.data.history.map((h) => ({
      month: formatMonth(h.period_month),
      actual: h.actual,
      lower: undefined as number | undefined,
      band: undefined as number | undefined,
      forecast: undefined as number | undefined,
    }));
    const future = forecast.data.forecast.map((f) => ({
      month: formatMonth(f.period_month),
      actual: undefined as number | undefined,
      lower: f.lower_bound,
      band: f.upper_bound - f.lower_bound,
      forecast: f.forecast,
    }));
    return [...history, ...future];
  }, [forecast.data]);

  const slope = forecast.data?.trend_slope_per_month ?? null;

  return (
    <div>
      <PageHeader title="Trends & Forecast" description="Month-over-month trend with classical statistical projection (linear regression, not machine learning)" />

      <div className="mb-4 flex gap-3">
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
        <select
          value={monthsAhead}
          onChange={(e) => setMonthsAhead(Number(e.target.value))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500"
        >
          <option value={3}>Forecast 3 months</option>
          <option value={6}>Forecast 6 months</option>
          <option value={12}>Forecast 12 months</option>
        </select>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Spend Trend &amp; Projection</CardTitle>
          {slope != null && (
            <div className={`flex items-center gap-1 text-xs font-medium ${slope >= 0 ? "text-negative-600" : "text-positive-600"}`}>
              {slope >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {formatCurrency(Math.abs(slope))} / month trend
            </div>
          )}
        </CardHeader>
        <CardBody>
          {forecast.isLoading ? (
            <Spinner />
          ) : forecast.isError ? (
            <ErrorState message="Could not load forecast" />
          ) : (
            <>
              <ResponsiveContainer width="100%" height={320}>
                <ComposedChart data={chartData} margin={{ left: -12 }}>
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
                  <Area dataKey="lower" stackId="band" stroke="none" fill="transparent" isAnimationActive={false} />
                  <Area dataKey="band" stackId="band" stroke="none" fill="#4f46e5" fillOpacity={0.12} name="Confidence band" isAnimationActive={false} />
                  <Line type="monotone" dataKey="actual" stroke="#4f46e5" strokeWidth={2.5} dot={false} name="Actual spend" isAnimationActive={false} />
                  <Line type="monotone" dataKey="forecast" stroke="#f59e0b" strokeWidth={2.5} strokeDasharray="6 4" dot={false} name="Forecast" isAnimationActive={false} />
                </ComposedChart>
              </ResponsiveContainer>
              {forecast.data?.note && <p className="mt-3 text-xs text-slate-500">{forecast.data.note}</p>}
            </>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
