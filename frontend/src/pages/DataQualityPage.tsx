import { useEffect, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CheckCircle2, Wrench, X } from "lucide-react";
import { endpoints } from "@/lib/endpoints";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Spinner, ErrorState, EmptyState } from "@/components/ui/States";
import { useAuth } from "@/context/AuthContext";
import { ApiError } from "@/lib/apiClient";
import { formatDateTime, formatNumber } from "@/lib/format";
import type { DataQualityIssue, IssueRawRow, IssueRowCorrections, IssueSeverity, IssueStatus } from "@/types/api";

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
  const { user } = useAuth();
  const canEdit = user?.role !== "auditor";
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [severityFilter, setSeverityFilter] = useState<string>("");
  const [batchFilter, setBatchFilter] = useState<string>("");
  const [fixingIssue, setFixingIssue] = useState<DataQualityIssue | null>(null);
  const [fixMessage, setFixMessage] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const batchId = batchFilter ? Number(batchFilter) : undefined;

  const batches = useQuery({ queryKey: ["ingestion-batches"], queryFn: () => endpoints.ingestion.batches(0, 100) });
  const summary = useQuery({ queryKey: ["issue-summary", batchId], queryFn: () => endpoints.issues.summary(batchId) });
  const issues = useQuery({
    queryKey: ["issues", statusFilter, severityFilter, batchId],
    queryFn: () =>
      endpoints.issues.list({
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
        batch_id: batchId,
        limit: 200,
      }),
  });

  const updateStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: IssueStatus }) => endpoints.issues.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["issues"] });
      queryClient.invalidateQueries({ queryKey: ["issue-summary"] });
    },
  });

  const fileName = (id: number) => batches.data?.find((b) => b.id === id)?.file_name ?? `Batch #${id}`;
  const selectedBatch = batches.data?.find((b) => b.id === batchId);

  const ruleData = summary.data
    ? Object.entries(summary.data.by_rule_code).map(([rule, count]) => ({ rule, count }))
    : [];

  function handleFixed(message: string) {
    setFixingIssue(null);
    setFixMessage(message);
    for (const key of ["issues", "issue-summary", "ingestion-batches", "kpis", "transactions", "trends"]) {
      queryClient.invalidateQueries({ queryKey: [key] });
    }
  }

  return (
    <div>
      <PageHeader title="Data Quality & Issues" description="Configurable rule engine findings from the cleaning pipeline" />

      <div className="mb-4 flex flex-wrap gap-3">
        <select
          value={batchFilter}
          onChange={(e) => {
            setBatchFilter(e.target.value);
            setFixMessage(null);
          }}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500"
          aria-label="Filter by file"
        >
          <option value="">All files</option>
          {(batches.data ?? []).map((b) => (
            <option key={b.id} value={b.id}>
              {b.file_name}
            </option>
          ))}
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500"
          aria-label="Filter by status"
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
          aria-label="Filter by severity"
        >
          <option value="">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {selectedBatch && (
        <div className="mb-4 grid grid-cols-3 gap-4">
          <BatchStat label="Rows in file" value={selectedBatch.row_count} />
          <BatchStat label="Accepted" value={selectedBatch.accepted_count} tone="text-positive-600" />
          <BatchStat label="Rejected" value={selectedBatch.rejected_count} tone="text-negative-600" />
        </div>
      )}

      {fixMessage && (
        <div className="mb-4 flex items-start gap-2 rounded-lg bg-positive-50 px-3 py-2 text-sm text-positive-600">
          <CheckCircle2 size={16} className="mt-0.5 shrink-0" />
          <span className="flex-1">{fixMessage}</span>
          <button onClick={() => setFixMessage(null)} aria-label="Dismiss">
            <X size={14} />
          </button>
        </div>
      )}

      <Card className="mb-5">
        <CardHeader>
          <CardTitle>Issues by Rule{selectedBatch ? ` — ${selectedBatch.file_name}` : ""}</CardTitle>
        </CardHeader>
        <CardBody>
          {summary.isLoading ? (
            <Spinner />
          ) : ruleData.length === 0 ? (
            <EmptyState message="No issues found" icon={CheckCircle2} />
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
                {!batchId && <th className="px-2 py-3">File</th>}
                <th className="px-2 py-3">Severity</th>
                <th className="px-2 py-3">Status</th>
                <th className="px-2 py-3">Detected</th>
                {canEdit && <th className="px-2 py-3 text-right">Actions</th>}
              </tr>
            </thead>
            <tbody>
              {issues.data.map((issue) => (
                <tr key={issue.id} className="border-b border-slate-50 hover:bg-slate-50">
                  <td className="px-4 py-2.5 font-mono text-xs text-slate-600">{issue.rule_code}</td>
                  <td className="px-2 py-2.5 text-slate-700">{issue.description}</td>
                  {!batchId && <td className="px-2 py-2.5 text-xs text-slate-500">{fileName(issue.batch_id)}</td>}
                  <td className="px-2 py-2.5">
                    <Badge tone={severityTone[issue.severity]}>{issue.severity}</Badge>
                  </td>
                  <td className="px-2 py-2.5">
                    <Badge tone={statusTone[issue.status]}>{issue.status}</Badge>
                  </td>
                  <td className="px-2 py-2.5 text-xs text-slate-500">{formatDateTime(issue.detected_at)}</td>
                  {canEdit && (
                    <td className="px-2 py-2.5 text-right">
                      {issue.status !== "resolved" && (
                        <div className="flex justify-end gap-2">
                          {issue.raw_transaction_id != null && (
                            <button
                              onClick={() => {
                                setFixMessage(null);
                                setFixingIssue(issue);
                              }}
                              className="text-xs font-medium text-brand-600 hover:underline"
                            >
                              Fix
                            </button>
                          )}
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
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {fixingIssue && (
        <FixRowDialog issue={fixingIssue} onClose={() => setFixingIssue(null)} onFixed={handleFixed} />
      )}
    </div>
  );
}

function BatchStat({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 text-center">
      <p className={`text-lg font-bold tabular ${tone ?? "text-slate-900"}`}>{formatNumber(value)}</p>
      <p className="mt-0.5 text-xs text-slate-500">{label}</p>
    </div>
  );
}

const FIX_FIELDS: { key: keyof IssueRowCorrections; label: string; hint?: string }[] = [
  { key: "record_id", label: "Record ID" },
  { key: "transaction_date", label: "Transaction date", hint: "YYYY-MM-DD" },
  { key: "vendor_name", label: "Vendor" },
  { key: "business_entity", label: "Business entity" },
  { key: "department", label: "Department" },
  { key: "cost_center", label: "Cost center" },
  { key: "category", label: "Category" },
  { key: "currency", label: "Currency" },
  { key: "net_amount", label: "Net amount" },
  { key: "tax_amount", label: "Tax amount" },
  { key: "total_amount", label: "Total amount" },
];

function FixRowDialog({
  issue,
  onClose,
  onFixed,
}: {
  issue: DataQualityIssue;
  onClose: () => void;
  onFixed: (message: string) => void;
}) {
  const row = useQuery({ queryKey: ["issue-raw-row", issue.id], queryFn: () => endpoints.issues.rawRow(issue.id) });
  const [form, setForm] = useState<Record<string, string>>({});

  useEffect(() => {
    if (row.data) {
      const initial: Record<string, string> = {};
      for (const { key } of FIX_FIELDS) initial[key] = (row.data[key as keyof IssueRawRow] as string | null) ?? "";
      setForm(initial);
    }
  }, [row.data]);

  const fix = useMutation({
    mutationFn: () => {
      const corrections: IssueRowCorrections = {};
      for (const { key } of FIX_FIELDS) {
        const original = (row.data?.[key as keyof IssueRawRow] as string | null) ?? "";
        if (form[key] !== original) corrections[key] = form[key];
      }
      return endpoints.issues.fixRow(issue.id, corrections);
    },
    onSuccess: (result) => {
      const action = result.was_added ? "Row added to clean transactions" : "Row updated";
      const remaining = result.remaining_problems.length
        ? ` — still flagged: ${result.remaining_problems.join("; ")}`
        : " — no remaining issues";
      onFixed(`${action}${remaining}`);
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    fix.mutate();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="fix-row-title"
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-xl2 bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between border-b border-slate-100 px-6 py-4">
          <div>
            <h2 id="fix-row-title" className="flex items-center gap-2 text-base font-semibold text-slate-900">
              <Wrench size={16} /> Fix source row
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              <span className="font-mono">{issue.rule_code}</span> — {issue.description}
            </p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700" aria-label="Close">
            <X size={18} />
          </button>
        </div>

        {row.isLoading ? (
          <Spinner label="Loading row" />
        ) : row.isError || !row.data ? (
          <div className="p-6">
            <ErrorState message="Could not load the source row" />
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="px-6 py-5">
            <p className="mb-4 text-xs text-slate-500">
              {row.data.is_accepted
                ? "This row is already in clean transactions. Saving re-runs the cleaning rules and updates it."
                : "This row was rejected. Saving re-runs the cleaning rules and, if it passes, adds it to clean transactions."}
            </p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {FIX_FIELDS.map(({ key, label, hint }) => (
                <label key={key} className="block">
                  <span className="mb-1 block text-xs font-medium text-slate-600">{label}</span>
                  <input
                    value={form[key] ?? ""}
                    placeholder={hint}
                    onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-brand-500"
                  />
                </label>
              ))}
            </div>

            {fix.isError && (
              <div className="mt-4 rounded-lg bg-negative-50 px-3 py-2 text-sm text-negative-600">
                {fix.error instanceof ApiError ? fix.error.message : "Could not save the fix"}
              </div>
            )}

            <div className="mt-5 flex justify-end gap-2">
              <Button type="button" variant="secondary" onClick={onClose}>
                Cancel
              </Button>
              <Button type="submit" disabled={fix.isPending}>
                {fix.isPending ? "Saving…" : row.data.is_accepted ? "Save & re-validate" : "Save & add row"}
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
