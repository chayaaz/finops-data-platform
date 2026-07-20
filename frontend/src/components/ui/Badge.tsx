import type { ReactNode } from "react";
import { clsx } from "clsx";

type Tone = "slate" | "positive" | "negative" | "warn" | "brand";

const toneClasses: Record<Tone, string> = {
  slate: "bg-slate-100 text-slate-700",
  positive: "bg-positive-50 text-positive-600",
  negative: "bg-negative-50 text-negative-600",
  warn: "bg-warn-50 text-warn-600",
  brand: "bg-brand-50 text-brand-700",
};

export function Badge({ tone = "slate", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        toneClasses[tone]
      )}
    >
      {children}
    </span>
  );
}
