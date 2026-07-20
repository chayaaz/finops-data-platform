import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { endpoints } from "@/lib/endpoints";
import { useDimensions } from "@/hooks/useDimensions";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Spinner, ErrorState, EmptyState } from "@/components/ui/States";
import { formatCurrency, formatPercent } from "@/lib/format";

const YEARS = [2023, 2024, 2025];

export function AllocationPage() {
  const dims = useDimensions();
  const [year, setYear] = useState(2025);
  const [categoryId, setCategoryId] = useState<number | null>(null);

  useEffect(() => {
    if (categoryId === null && dims.categories.data && dims.categories.data.length > 0) {
      setCategoryId(dims.categories.data[0].id);
    }
  }, [dims.categories.data, categoryId]);

  const allocation = useQuery({
    queryKey: ["allocation", categoryId, year],
    queryFn: () => endpoints.analytics.allocation(categoryId!, `${year}-01-01`, `${year}-12-31`),
    enabled: categoryId !== null,
  });

  const total = (allocation.data ?? []).reduce((sum, r) => sum + r.allocated_amount, 0);

  return (
    <div>
      <PageHeader title="Cost Allocation / Showback" description="Proportional chargeback of shared costs across departments" />

      <div className="mb-4 flex gap-3">
        <select
          value={categoryId ?? ""}
          onChange={(e) => setCategoryId(Number(e.target.value))}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500"
        >
          {(dims.categories.data ?? []).map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
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

      <Card className="mb-5">
        <CardHeader>
          <CardTitle>Allocated Spend by Department</CardTitle>
        </CardHeader>
        <CardBody>
          {allocation.isLoading ? (
            <Spinner />
          ) : allocation.isError ? (
            <ErrorState message="Could not load allocation data" />
          ) : !allocation.data || allocation.data.length === 0 ? (
            <EmptyState message="No spend to allocate for this category and period" />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={allocation.data} layout="vertical" margin={{ left: 24 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
                <XAxis type="number" tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} tickFormatter={(v) => formatCurrency(v)} />
                <YAxis
                  type="category"
                  dataKey="department_name"
                  tick={{ fontSize: 11, fill: "#334155" }}
                  axisLine={false}
                  tickLine={false}
                  width={130}
                />
                <Tooltip formatter={(v: number) => formatCurrency(v)} contentStyle={{ borderRadius: 10, border: "1px solid #e2e8f0", fontSize: 12 }} />
                <Bar dataKey="allocated_amount" fill="#4f46e5" radius={[0, 4, 4, 0]} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardBody>
      </Card>

      {allocation.data && allocation.data.length > 0 && (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-6 py-3">Department</th>
                <th className="px-2 py-3 text-right">Weight</th>
                <th className="px-2 py-3 text-right">Allocated Amount</th>
              </tr>
            </thead>
            <tbody>
              {allocation.data.map((row) => (
                <tr key={row.department_id} className="border-b border-slate-50 hover:bg-slate-50">
                  <td className="px-6 py-2.5 font-medium text-slate-800">{row.department_name}</td>
                  <td className="px-2 py-2.5 text-right tabular text-slate-600">{formatPercent(row.weight_pct)}</td>
                  <td className="px-2 py-2.5 text-right tabular font-medium text-slate-900">{formatCurrency(row.allocated_amount)}</td>
                </tr>
              ))}
              <tr className="bg-slate-50 font-semibold">
                <td className="px-6 py-2.5 text-slate-800">Total</td>
                <td className="px-2 py-2.5 text-right text-slate-600">100%</td>
                <td className="px-2 py-2.5 text-right tabular text-slate-900">{formatCurrency(total)}</td>
              </tr>
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
