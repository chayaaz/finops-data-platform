import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronRight } from "lucide-react";
import { endpoints } from "@/lib/endpoints";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Spinner, ErrorState, EmptyState } from "@/components/ui/States";
import { formatDateTime, formatNumber } from "@/lib/format";
import type { IngestionStatus } from "@/types/api";

const statusTone: Record<IngestionStatus, "positive" | "warn" | "negative"> = {
  completed: "positive",
  processing: "warn",
  failed: "negative",
};

export function IngestionMonitorPage() {
  const [expanded, setExpanded] = useState<number | null>(null);
  const batches = useQuery({ queryKey: ["ingestion-batches"], queryFn: () => endpoints.ingestion.batches(0, 100) });

  return (
    <div>
      <PageHeader title="Ingestion Monitor" description="Track every upload batch through the cleaning pipeline" />

      {batches.isLoading ? (
        <Spinner />
      ) : batches.isError ? (
        <ErrorState message="Could not load ingestion batches" />
      ) : !batches.data || batches.data.length === 0 ? (
        <EmptyState message="No batches uploaded yet" />
      ) : (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="w-8 px-4 py-3" />
                <th className="px-2 py-3">File</th>
                <th className="px-2 py-3">Uploaded</th>
                <th className="px-2 py-3">Status</th>
                <th className="px-2 py-3 text-right">Rows</th>
                <th className="px-2 py-3 text-right">Accepted</th>
                <th className="px-2 py-3 text-right">Rejected</th>
              </tr>
            </thead>
            <tbody>
              {batches.data.map((batch) => (
                <BatchRow
                  key={batch.id}
                  batch={batch}
                  expanded={expanded === batch.id}
                  onToggle={() => setExpanded(expanded === batch.id ? null : batch.id)}
                />
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

function BatchRow({
  batch,
  expanded,
  onToggle,
}: {
  batch: import("@/types/api").IngestionBatch;
  expanded: boolean;
  onToggle: () => void;
}) {
  const raw = useQuery({
    queryKey: ["raw-transactions", batch.id],
    queryFn: () => endpoints.transactions.raw(batch.id, 0, 25),
    enabled: expanded,
  });

  return (
    <>
      <tr className="cursor-pointer border-b border-slate-50 hover:bg-slate-50" onClick={onToggle}>
        <td className="px-4 py-3 text-slate-400">{expanded ? <ChevronDown size={15} /> : <ChevronRight size={15} />}</td>
        <td className="px-2 py-3 font-medium text-slate-800">{batch.file_name}</td>
        <td className="px-2 py-3 text-slate-500">{formatDateTime(batch.uploaded_at)}</td>
        <td className="px-2 py-3">
          <Badge tone={statusTone[batch.status]}>{batch.status}</Badge>
        </td>
        <td className="px-2 py-3 text-right tabular text-slate-700">{formatNumber(batch.row_count)}</td>
        <td className="px-2 py-3 text-right tabular text-positive-600">{formatNumber(batch.accepted_count)}</td>
        <td className="px-2 py-3 text-right tabular text-negative-600">{formatNumber(batch.rejected_count)}</td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={7} className="bg-slate-50 px-4 py-4">
            {raw.isLoading ? (
              <Spinner label="Loading raw rows" />
            ) : !raw.data || raw.data.length === 0 ? (
              <p className="py-2 text-center text-xs text-slate-400">No raw rows found for this batch</p>
            ) : (
              <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-100 text-left uppercase tracking-wide text-slate-400">
                      <th className="px-3 py-2">Record</th>
                      <th className="px-3 py-2">Vendor</th>
                      <th className="px-3 py-2">Department</th>
                      <th className="px-3 py-2">Category</th>
                      <th className="px-3 py-2">Date</th>
                      <th className="px-3 py-2">Currency</th>
                      <th className="px-3 py-2 text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {raw.data.map((row) => (
                      <tr key={row.id} className="border-b border-slate-50 last:border-0">
                        <td className="px-3 py-1.5 text-slate-500">{row.record_id}</td>
                        <td className="px-3 py-1.5">{row.vendor_name ?? <span className="text-negative-500">missing</span>}</td>
                        <td className="px-3 py-1.5">{row.department ?? "—"}</td>
                        <td className="px-3 py-1.5">{row.category ?? "—"}</td>
                        <td className="px-3 py-1.5">{row.transaction_date ?? <span className="text-negative-500">missing</span>}</td>
                        <td className="px-3 py-1.5">{row.currency ?? "—"}</td>
                        <td className="px-3 py-1.5 text-right tabular">{row.total_amount ?? "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  );
}
