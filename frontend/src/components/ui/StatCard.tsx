import type { ReactNode } from "react";
import { clsx } from "clsx";
import { ArrowDownRight, ArrowUpRight, type LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string;
  icon: LucideIcon;
  trend?: { value: number; label?: string } | null;
  accent?: "brand" | "positive" | "negative" | "warn";
  footer?: ReactNode;
}

const accentClasses = {
  brand: "bg-brand-50 text-brand-600",
  positive: "bg-positive-50 text-positive-600",
  negative: "bg-negative-50 text-negative-600",
  warn: "bg-warn-50 text-warn-600",
};

export function StatCard({ label, value, icon: Icon, trend, accent = "brand", footer }: StatCardProps) {
  return (
    <div className="rounded-xl2 border border-slate-200 bg-white p-5 shadow-card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
          <p className="mt-2 text-2xl font-bold tabular text-slate-900">{value}</p>
        </div>
        <div className={clsx("flex h-10 w-10 items-center justify-center rounded-lg", accentClasses[accent])}>
          <Icon size={20} />
        </div>
      </div>
      {trend && (
        <div className="mt-3 flex items-center gap-1 text-sm">
          <span
            className={clsx(
              "flex items-center gap-0.5 font-medium",
              trend.value >= 0 ? "text-positive-600" : "text-negative-600"
            )}
          >
            {trend.value >= 0 ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
            {Math.abs(trend.value).toFixed(1)}%
          </span>
          {trend.label && <span className="text-slate-400">{trend.label}</span>}
        </div>
      )}
      {footer && <div className="mt-3 text-sm text-slate-500">{footer}</div>}
    </div>
  );
}
