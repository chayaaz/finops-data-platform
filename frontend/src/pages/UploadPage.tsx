import { useRef, useState, type DragEvent } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, FileSpreadsheet, ShieldOff, UploadCloud, XCircle } from "lucide-react";
import { clsx } from "clsx";
import { endpoints } from "@/lib/endpoints";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardBody } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/States";
import { useAuth } from "@/context/AuthContext";
import { ApiError } from "@/lib/apiClient";
import { formatNumber } from "@/lib/format";
import type { IngestionBatch } from "@/types/api";

export function UploadPage() {
  const { user } = useAuth();
  const [dragActive, setDragActive] = useState(false);
  const [result, setResult] = useState<IngestionBatch | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (file: File) => endpoints.upload.submit(file),
    onSuccess: (batch) => {
      setResult(batch);
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: ["ingestion-batches"] });
    },
    onError: (err) => {
      setResult(null);
      setErrorMsg(err instanceof ApiError ? err.message : "Upload failed");
    },
  });

  function handleFile(file: File | undefined) {
    if (!file) return;
    setResult(null);
    setErrorMsg(null);
    mutation.mutate(file);
  }

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragActive(false);
    handleFile(e.dataTransfer.files?.[0]);
  }

  if (user?.role === "auditor") {
    return (
      <div>
        <PageHeader title="Upload Data" description="Ingest raw transaction files" />
        <Card>
          <EmptyState message="Auditors have read-only access and cannot upload files" icon={ShieldOff} />
        </Card>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Upload Data"
        description="Ingest raw transaction files — validated, cleaned, and staged automatically"
      />

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={clsx(
          "flex cursor-pointer flex-col items-center justify-center rounded-xl2 border-2 border-dashed px-6 py-16 text-center transition-colors",
          dragActive ? "border-brand-500 bg-brand-50" : "border-slate-300 bg-white hover:border-brand-300"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-50 text-brand-600">
          <UploadCloud size={26} />
        </div>
        <p className="mt-4 text-sm font-semibold text-slate-800">
          {mutation.isPending ? "Processing upload…" : "Drop a CSV or Excel file here, or click to browse"}
        </p>
        <p className="mt-1 text-xs text-slate-500">Supported formats: .csv, .xlsx, .xls</p>
      </div>

      {mutation.isPending && (
        <Card className="mt-5">
          <CardBody className="pt-6 text-sm text-slate-500">Uploading, staging, and running the cleaning pipeline…</CardBody>
        </Card>
      )}

      {errorMsg && (
        <Card className="mt-5 border-negative-50">
          <CardBody className="flex items-center gap-2 pt-6 text-sm text-negative-600">
            <XCircle size={18} /> {errorMsg}
          </CardBody>
        </Card>
      )}

      {result && (
        <Card className="mt-5">
          <CardBody className="pt-6">
            <div className="flex items-center gap-2 text-positive-600">
              <CheckCircle2 size={20} />
              <span className="text-sm font-semibold">Batch processed successfully</span>
            </div>
            <div className="mt-4 flex items-center gap-2 text-sm text-slate-700">
              <FileSpreadsheet size={16} className="text-slate-400" />
              {result.file_name}
            </div>
            <div className="mt-4 grid grid-cols-3 gap-4">
              <ResultStat label="Rows Received" value={result.row_count} />
              <ResultStat label="Accepted" value={result.accepted_count} tone="text-positive-600" />
              <ResultStat label="Rejected" value={result.rejected_count} tone="text-negative-600" />
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}

function ResultStat({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <div className="rounded-lg bg-slate-50 p-3 text-center">
      <p className={clsx("text-lg font-bold tabular", tone ?? "text-slate-900")}>{formatNumber(value)}</p>
      <p className="mt-0.5 text-xs text-slate-500">{label}</p>
    </div>
  );
}
