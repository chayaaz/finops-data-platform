import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { endpoints } from "@/lib/endpoints";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Spinner, ErrorState, EmptyState } from "@/components/ui/States";
import { formatDateTime } from "@/lib/format";
import type { IssueSeverity, IssueStatus } from "@/types/api";

const severityTone: Record<IssueSeverity, "negative" | "warn" | "brand" | "slate"> = {
  critical: "negative",
  high: "warn",
  medium: "brand",
  low: "slate",
};

const statusTone: Record<IssueStatus, "negative" | "warn" | "positive"> = {
  open: "negative",
  acknowledged: "warn",
  resolved: "positive",
};

export function DataQualityPage() {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const queryClient = useQueryClient();

  const summary = useQuery({ queryKey: ["issue-summary"], queryFn: endpoints.issues.summary });
  const issues = useQuery({
    queryKey: ["issues", statusFilter, severityFilter],
    queryFn: () => endpoints.issues.list({ status: statusFilter || undefined, severity: severityFilter || undefined, limit: 200 }),
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: IssueStatus }) => endpoints.issues.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["issues"] });
      queryClient.invalidateQueries({ queryKey: ["issue-summary"] });
    },
  });

  const ruleData = summary.data
    ? Object.entries(summary.data.by_rule_code).map(([rule, count]) => ({ rule, count }))
    : [];

  return (
    <div>
      <PageHeader title="Data Quality & Issues" description="Configurable rule engine findings from the cleaning pipeline" />

      <Card className="mb-5">
        <CardHeader>
          <CardTitle>Issues by Rule</CardTitle>
        </CardHeader>
        <CardBody>
          {summary.isLoading ? (
            <Spinner />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={ruleData} margin={{ left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="rule" tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} interval={0} angle={-20} textAnchor="end" height={60} />
                <YAxis tick={{ fontSize: 11, fill: "#64748b" }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip contentStyle={{ borderRadius: 10, border: "1px solid #e2e8f0", fontSize: 12 }} />
                <Bar dataKey="count" fill="#4f46e5" radius={[4, 4, 0, 0]} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </CardBody>
      </Card>

      <div className="mb-4 flex gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500"
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
        </select>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500"
        >
          <option value="">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {issues.isLoading ? (
        <Spinner />
      ) : issues.isError ? (
        <ErrorState message="Could not load issues" />
      ) : !issues.data || issues.data.length === 0 ? (
        <EmptyState message="No issues match these filters" />
      ) : (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3">Rule</th>
                <th className="px-2 py-3">Description</th>
                <th className="px-2 py-3">Severity</th>
                <th className="px-2 py-3">Status</th>
                <th className="px-2 py-3">Detected</th>
                <th className="px-2 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {issues.data.map((issue) => (
                <tr key={issue.id} className="border-b border-slate-50 hover:bg-slate-50">
                  <td className="px-4 py-2.5 font-mono text-xs text-slate-600">{issue.rule_code}</td>
                  <td className="px-2 py-2.5 text-slate-700">{issue.description}</td>
                  <td className="px-2 py-2.5">
                    <Badge tone={severityTone[issue.severity]}>{issue.severity}</Badge>
                  </td>
                  <td className="px-2 py-2.5">
                    <Badge tone={statusTone[issue.status]}>{issue.status}</Badge>
                  </td>
                  <td className="px-2 py-2.5 text-xs text-slate-500">{formatDateTime(issue.detected_at)}</td>
                  <td className="px-2 py-2.5 text-right">
                    {issue.status !== "resolved" && (
                      <div className="flex justify-end gap-2">
                        {issue.status === "open" && (
                          <button
                            onClick={() => updateStatus.mutate({ id: issue.id, status: "acknowledged" })}
                            className="text-xs font-medium text-brand-600 hover:underline"
                          >
                            Acknowledge
                          </button>
                        )}
                        <button
                          onClick={() => updateStatus.mutate({ id: issue.id, status: "resolved" })}
                          className="text-xs font-medium text-positive-600 hover:underline"
                        >
                          Resolve
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
