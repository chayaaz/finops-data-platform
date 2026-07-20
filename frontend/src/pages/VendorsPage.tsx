import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { endpoints } from "@/lib/endpoints";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Spinner, ErrorState, EmptyState } from "@/components/ui/States";
import { formatCurrency, formatMonth, formatPercent } from "@/lib/format";

const YEARS = [2023, 2024, 2025];
const PIE_COLORS = ["#4f46e5", "#6366f1", "#818cf8", "#a5b4fc", "#c7d2fe", "#f59e0b", "#94a3b8"];

const riskTone: Record<string, "positive" | "warn" | "negative"> = {
  low: "positive",
  moderate: "warn",
  high: "negative",
};

export function VendorsPage() {
  const [year, setYear] = useState(2025);

  const concentration = useQuery({
    queryKey: ["vendor-concentration", year],
    queryFn: () => endpoints.vendors.concentration(`${year}-01-01`, `${year}-12-31`),
  });

  const commitments = useQuery({
    queryKey: ["commitments", year],
    queryFn: () => endpoints.vendors.commitments({ period_start: `${year}-01-01`, period_end: `${year}-12-31` }),
  });

  const topShares = (concentration.data?.vendor_shares ?? []).slice(0, 7);

  return (
    <div>
      <PageHeader title="Vendor Analytics" description="Concentration risk (HHI) and cloud/vendor commitment utilization" />

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
      </div>

      <div className="mb-5 grid grid-cols-1 gap-5 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle>Vendor Spend Concentration</CardTitle>
          </CardHeader>
          <CardBody>
            {concentration.isLoading ? (
              <Spinner />
            ) : concentration.isError || !concentration.data ? (
              <ErrorState message="Could not load vendor concentration" />
            ) : (
              <div className="flex flex-col items-center gap-4 sm:flex-row">
                <ResponsiveContainer width="100%" height={220} className="sm:w-1/2">
                  <PieChart>
                    <Pie data={topShares} dataKey="spend" nameKey="vendor_name" innerRadius={55} outerRadius={85} paddingAngle={2} isAnimationActive={false}>
                      {topShares.map((_, i) => (
                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={{ borderRadius: 10, fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="w-full space-y-1.5 sm:w-1/2">
                  {topShares.map((v, i) => (
                    <div key={v.vendor_id} className="flex items-center gap-2 text-xs">
                      <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: PIE_COLORS[i % PIE_COLORS.length] }} />
                      <span className="flex-1 truncate text-slate-700">{v.vendor_name}</span>
                      <span className="tabular font-medium text-slate-600">{formatPercent(v.share_pct)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Concentration Risk</CardTitle>
          </CardHeader>
          <CardBody>
            {concentration.data && (
              <div className="text-center">
                <p className="text-4xl font-bold tabular text-slate-900">{concentration.data.hhi.toFixed(0)}</p>
                <p className="mt-1 text-xs text-slate-500">Herfindahl-Hirschman Index</p>
                <div className="mt-3 flex justify-center">
                  <Badge tone={riskTone[concentration.data.risk_level] ?? "slate"}>{concentration.data.risk_level} risk</Badge>
                </div>
                <p className="mt-4 text-xs leading-relaxed text-slate-500">
                  HHI below 1,500 indicates a competitive, diversified vendor base. Above 2,500 signals high dependency on
                  a small number of suppliers.
                </p>
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Commitment Utilization</CardTitle>
        </CardHeader>
        {commitments.isLoading ? (
          <Spinner />
        ) : !commitments.data || commitments.data.length === 0 ? (
          <EmptyState message="No vendor commitments for this period" />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-6 py-3">Vendor</th>
                <th className="px-2 py-3">Entity</th>
                <th className="px-2 py-3">Period</th>
                <th className="px-2 py-3 text-right">Committed</th>
                <th className="px-2 py-3 text-right">Utilized</th>
                <th className="px-2 py-3 w-40">Utilization</th>
              </tr>
            </thead>
            <tbody>
              {commitments.data.map((c, idx) => (
                <tr key={idx} className="border-b border-slate-50 hover:bg-slate-50">
                  <td className="px-6 py-2.5 font-medium text-slate-800">{c.vendor_name}</td>
                  <td className="px-2 py-2.5 text-slate-600">{c.business_entity_name}</td>
                  <td className="px-2 py-2.5 text-slate-600">{formatMonth(c.period_month)}</td>
                  <td className="px-2 py-2.5 text-right tabular text-slate-700">{formatCurrency(c.committed_amount, c.currency)}</td>
                  <td className="px-2 py-2.5 text-right tabular text-slate-700">{formatCurrency(c.utilized_amount, c.currency)}</td>
                  <td className="px-2 py-2.5">
                    <div className="flex items-center gap-2">
                      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className={`h-full ${c.utilization_pct > 100 ? "bg-negative-500" : c.utilization_pct > 85 ? "bg-warn-500" : "bg-positive-500"}`}
                          style={{ width: `${Math.min(c.utilization_pct, 100)}%` }}
                        />
                      </div>
                      <span className="w-10 text-right text-xs tabular text-slate-600">{c.utilization_pct.toFixed(0)}%</span>
                    </div>
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
