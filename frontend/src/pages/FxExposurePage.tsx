import { useQuery } from "@tanstack/react-query";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { endpoints } from "@/lib/endpoints";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Spinner, ErrorState, EmptyState } from "@/components/ui/States";
import { formatCurrency, formatNumber, formatPercent } from "@/lib/format";

const COLORS = ["#4f46e5", "#6366f1", "#818cf8", "#a5b4fc", "#f59e0b", "#34d399", "#94a3b8"];

export function FxExposurePage() {
  const fx = useQuery({ queryKey: ["fx-exposure"], queryFn: endpoints.analytics.fxExposure });

  return (
    <div>
      <PageHeader title="FX Exposure" description="Multi-currency spend, normalized to base currency using point-in-time exchange rates" />

      {fx.isLoading ? (
        <Spinner />
      ) : fx.isError ? (
        <ErrorState message="Could not load FX exposure" />
      ) : !fx.data || fx.data.length === 0 ? (
        <EmptyState message="No FX exposure data available" />
      ) : (
        <div className="grid grid-cols-1 gap-5 xl:grid-cols-3">
          <Card className="xl:col-span-1">
            <CardHeader>
              <CardTitle>Exposure by Currency</CardTitle>
            </CardHeader>
            <CardBody>
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={fx.data} dataKey="total_base_currency" nameKey="currency" innerRadius={55} outerRadius={90} paddingAngle={2} isAnimationActive={false}>
                    {fx.data.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={{ borderRadius: 10, fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            </CardBody>
          </Card>

          <Card className="xl:col-span-2">
            <CardHeader>
              <CardTitle>Currency Breakdown</CardTitle>
            </CardHeader>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-6 py-3">Currency</th>
                  <th className="px-2 py-3 text-right">Base Amount</th>
                  <th className="px-2 py-3 text-right">Share</th>
                  <th className="px-2 py-3 text-right">Transactions</th>
                </tr>
              </thead>
              <tbody>
                {fx.data.map((row, i) => (
                  <tr key={row.currency} className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="px-6 py-2.5">
                      <div className="flex items-center gap-2 font-semibold text-slate-800">
                        <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                        {row.currency}
                      </div>
                    </td>
                    <td className="px-2 py-2.5 text-right tabular font-medium text-slate-900">{formatCurrency(row.total_base_currency)}</td>
                    <td className="px-2 py-2.5 text-right tabular text-slate-600">{formatPercent(row.share_pct)}</td>
                    <td className="px-2 py-2.5 text-right tabular text-slate-600">{formatNumber(row.transaction_count)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      )}
    </div>
  );
}
