import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, Download } from "lucide-react";
import { endpoints } from "@/lib/endpoints";
import { useDimensions } from "@/hooks/useDimensions";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Spinner, ErrorState, EmptyState } from "@/components/ui/States";
import { formatCurrency, formatDate, formatNumber } from "@/lib/format";
import type { ApprovalStatus } from "@/types/api";

const LIMIT = 25;

const approvalTone: Record<ApprovalStatus, "positive" | "warn" | "negative" | "brand"> = {
  paid: "positive",
  approved: "brand",
  pending: "warn",
  rejected: "negative",
};

interface Filters {
  date_from: string;
  date_to: string;
  vendor_id: string;
  department_id: string;
  category_id: string;
  currency: string;
}

const emptyFilters: Filters = { date_from: "", date_to: "", vendor_id: "", department_id: "", category_id: "", currency: "" };

export function TransactionsPage() {
  const [filters, setFilters] = useState<Filters>(emptyFilters);
  const [skip, setSkip] = useState(0);
  const dims = useDimensions();

  const params = useMemo(
    () => ({
      date_from: filters.date_from || undefined,
      date_to: filters.date_to || undefined,
      vendor_id: filters.vendor_id || undefined,
      department_id: filters.department_id || undefined,
      category_id: filters.category_id || undefined,
      currency: filters.currency || undefined,
      skip,
      limit: LIMIT,
    }),
    [filters, skip]
  );

  const page = useQuery({ queryKey: ["transactions", params], queryFn: () => endpoints.transactions.list(params) });

  function updateFilter(key: keyof Filters, value: string) {
    setSkip(0);
    setFilters((f) => ({ ...f, [key]: value }));
  }

  function exportCsv() {
    if (!page.data) return;
    const headers = ["record_id", "date", "vendor_id", "category_id", "currency", "total_amount", "base_amount", "status"];
    const rows = page.data.items.map((t) => [
      t.record_id,
      t.transaction_date,
      t.vendor_id ?? "",
      t.category_id ?? "",
      t.currency,
      t.total_amount,
      t.total_amount_base_currency ?? "",
      t.approval_status,
    ]);
    const csv = [headers, ...rows].map((r) => r.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "transactions_export.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  const vendorName = (id: number | null) => dims.vendors.data?.find((v) => v.id === id)?.name ?? "—";
  const categoryName = (id: number | null) => dims.categories.data?.find((c) => c.id === id)?.name ?? "—";

  return (
    <div>
      <PageHeader
        title="Transactions Explorer"
        description="Search and filter cleaned transactions across every dimension"
        actions={
          <Button variant="secondary" onClick={exportCsv} disabled={!page.data?.items.length}>
            <Download size={15} /> Export CSV
          </Button>
        }
      />

      <Card className="mb-4">
        <div className="grid grid-cols-2 gap-3 p-4 md:grid-cols-3 xl:grid-cols-6">
          <FilterInput label="From" type="date" value={filters.date_from} onChange={(v) => updateFilter("date_from", v)} />
          <FilterInput label="To" type="date" value={filters.date_to} onChange={(v) => updateFilter("date_to", v)} />
          <FilterSelect
            label="Vendor"
            value={filters.vendor_id}
            onChange={(v) => updateFilter("vendor_id", v)}
            options={(dims.vendors.data ?? []).map((v) => ({ value: String(v.id), label: v.name }))}
          />
          <FilterSelect
            label="Department"
            value={filters.department_id}
            onChange={(v) => updateFilter("department_id", v)}
            options={(dims.departments.data ?? []).map((d) => ({ value: String(d.id), label: d.name }))}
          />
          <FilterSelect
            label="Category"
            value={filters.category_id}
            onChange={(v) => updateFilter("category_id", v)}
            options={(dims.categories.data ?? []).map((c) => ({ value: String(c.id), label: c.name }))}
          />
          <FilterSelect
            label="Currency"
            value={filters.currency}
            onChange={(v) => updateFilter("currency", v)}
            options={["USD", "EUR", "GBP", "ILS", "JPY", "CAD", "AUD"].map((c) => ({ value: c, label: c }))}
          />
        </div>
      </Card>

      {page.isLoading ? (
        <Spinner />
      ) : page.isError ? (
        <ErrorState message="Could not load transactions" />
      ) : !page.data || page.data.items.length === 0 ? (
        <EmptyState message="No transactions match these filters" />
      ) : (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="px-4 py-3">Record</th>
                <th className="px-2 py-3">Date</th>
                <th className="px-2 py-3">Vendor</th>
                <th className="px-2 py-3">Category</th>
                <th className="px-2 py-3">Status</th>
                <th className="px-2 py-3 text-right">Amount</th>
                <th className="px-2 py-3 text-right">Base Amount</th>
              </tr>
            </thead>
            <tbody>
              {page.data.items.map((t) => (
                <tr key={t.id} className="border-b border-slate-50 hover:bg-slate-50">
                  <td className="px-4 py-2.5 font-mono text-xs text-slate-500">{t.record_id}</td>
                  <td className="px-2 py-2.5 text-slate-700">{formatDate(t.transaction_date)}</td>
                  <td className="px-2 py-2.5 text-slate-700">{vendorName(t.vendor_id)}</td>
                  <td className="px-2 py-2.5 text-slate-700">{categoryName(t.category_id)}</td>
                  <td className="px-2 py-2.5">
                    <Badge tone={approvalTone[t.approval_status]}>{t.approval_status}</Badge>
                  </td>
                  <td className="px-2 py-2.5 text-right tabular text-slate-800">{formatCurrency(t.total_amount, t.currency)}</td>
                  <td className="px-2 py-2.5 text-right tabular font-medium text-slate-900">
                    {t.total_amount_base_currency != null ? formatCurrency(t.total_amount_base_currency) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-sm text-slate-500">
            <span>
              Showing {skip + 1}–{Math.min(skip + LIMIT, page.data.total)} of {formatNumber(page.data.total)}
            </span>
            <div className="flex gap-2">
              <button
                disabled={skip === 0}
                onClick={() => setSkip(Math.max(0, skip - LIMIT))}
                className="flex items-center gap-1 rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs disabled:opacity-40"
              >
                <ChevronLeft size={14} /> Prev
              </button>
              <button
                disabled={skip + LIMIT >= page.data.total}
                onClick={() => setSkip(skip + LIMIT)}
                className="flex items-center gap-1 rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs disabled:opacity-40"
              >
                Next <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

function FilterInput({
  label,
  type,
  value,
  onChange,
}: {
  label: string;
  type: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-[11px] font-medium text-slate-500">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs outline-none focus:border-brand-500"
      />
    </label>
  );
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-[11px] font-medium text-slate-500">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-lg border border-slate-300 px-2.5 py-1.5 text-xs outline-none focus:border-brand-500"
      >
        <option value="">All</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </label>
  );
}
