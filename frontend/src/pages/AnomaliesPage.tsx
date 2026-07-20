import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Radar, RefreshCw } from "lucide-react";
import { endpoints } from "@/lib/endpoints";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Spinner, ErrorState, EmptyState } from "@/components/ui/States";
import { formatDateTime } from "@/lib/format";
import { useAuth } from "@/context/AuthContext";
import type { AnomalyStatus } from "@/types/api";

const statusTone: Record<AnomalyStatus, "negative" | "positive" | "slate"> = {
  open: "negative",
  reviewed: "positive",
  dismissed: "slate",
};

export function AnomaliesPage() {
  const { user } = useAuth();
  const [groupBy, setGroupBy] = useState<"category" | "vendor">("category");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const queryClient = useQueryClient();

  const anomalies = useQuery({
    queryKey: ["anomalies", statusFilter],
    queryFn: () => endpoints.anomalies.list({ status: statusFilter || undefined, limit: 200 }),
  });
  const benford = useQuery({ queryKey: ["benford", groupBy], queryFn: () => endpoints.anomalies.benford(groupBy) });

  const detect = useMutation({
    mutationFn: endpoints.anomalies.detect,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["anomalies"] }),
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: AnomalyStatus }) => endpoints.anomalies.updateStatus(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["anomalies"] }),
  });

  const canDetect = user && (user.role === "admin" || user.role === "finance_manager");
  const flaggedGroups = (benford.data ?? []).filter((g) => g.flagged).slice(0, 6);

  return (
    <div>
      <PageHeader
        title="Anomaly Detection"
        description="Rolling z-score outliers and Benford's Law leading-digit screening"
        actions={
          canDetect ? (
            <Button onClick={() => detect.mutate()} disabled={detect.isPending}>
              <RefreshCw size={15} className={detect.isPending ? "animate-spin" : ""} />
              {detect.isPending ? "Scanning…" : "Run Detection"}
            </Button>
          ) : undefined
        }
      />

      <Card className="mb-5">
        <CardHeader>
          <CardTitle>Benford's Law Screening — Leading Digit Distribution</CardTitle>
          <select
            value={groupBy}
            onChange={(e) => setGroupBy(e.target.value as "category" | "vendor")}
            className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs outline-none focus:border-brand-500"
          >
            <option value="category">By Category</option>
            <option value="vendor">By Vendor</option>
          </select>
        </CardHeader>
        <CardBody>
          {benford.isLoading ? (
            <Spinner />
          ) : flaggedGroups.length === 0 ? (
            <p className="py-6 text-center text-sm text-slate-400">
              No groups currently deviate significantly from Benford's Law distribution
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
              {flaggedGroups.map((group) => {
                const data = Array.from({ length: 9 }, (_, i) => {
                  const digit = String(i + 1);
                  return {
                    digit,
                    observed: group.observed_distribution[digit] ?? 0,
                    expected: group.expected_distribution[digit] ?? 0,
                  };
                });
                return (
                  <div key={group.group_id} className="rounded-lg border border-warn-50 bg-warn-50/40 p-3">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-700">Group #{group.group_id}</span>
                      <Badge tone="warn">chi&sup2; {group.chi_square.toFixed(1)}</Badge>
                    </div>
                    <ResponsiveContainer width="100%" height={120}>
                      <BarChart data={data}>
                        <XAxis dataKey="digit" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                        <YAxis hide />
                        <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                        <Bar dataKey="expected" fill="#cbd5e1" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                        <Bar dataKey="observed" fill="#f59e0b" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                      </BarChart>
                    </ResponsiveContainer>
                    <p className="mt-1 text-center text-[11px] text-slate-500">n = {group.sample_size}</p>
                  </div>
                );
              })}
            </div>
          )}
        </CardBody>
      </Card>

      <div className="mb-4 flex items-center justify-between">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500"
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="reviewed">Reviewed</option>
          <option value="dismissed">Dismissed</option>
        </select>
      </div>

      {anomalies.isLoading ? (
        <Spinner />
      ) : anomalies.isError ? (
        <ErrorState message="Could not load anomalies" />
      ) : !anomalies.data || anomalies.data.length === 0 ? (
        <EmptyState message="No anomalies detected" icon={Radar} />
      ) : (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3">Type</th>
                <th className="px-2 py-3">Detail</th>
                <th className="px-2 py-3 text-right">Z-Score</th>
                <th className="px-2 py-3">Status</th>
                <th className="px-2 py-3">Detected</th>
                <th className="px-2 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {anomalies.data.map((a) => (
                <tr key={a.id} className="border-b border-slate-50 hover:bg-slate-50">
                  <td className="px-4 py-2.5 font-mono text-xs text-slate-600">{a.anomaly_type}</td>
                  <td className="px-2 py-2.5 text-slate-700">{a.detail ?? "—"}</td>
                  <td className="px-2 py-2.5 text-right tabular font-medium text-slate-800">
                    {a.z_score != null ? a.z_score.toFixed(2) : "—"}
                  </td>
                  <td className="px-2 py-2.5">
                    <Badge tone={statusTone[a.status]}>{a.status}</Badge>
                  </td>
                  <td className="px-2 py-2.5 text-xs text-slate-500">{formatDateTime(a.detected_at)}</td>
                  <td className="px-2 py-2.5 text-right">
                    {a.status === "open" && (
                      <div className="flex justify-end gap-2">
                        <button
                          onClick={() => updateStatus.mutate({ id: a.id, status: "reviewed" })}
                          className="text-xs font-medium text-positive-600 hover:underline"
                        >
                          Mark Reviewed
                        </button>
                        <button
                          onClick={() => updateStatus.mutate({ id: a.id, status: "dismissed" })}
                          className="text-xs font-medium text-slate-500 hover:underline"
                        >
                          Dismiss
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
