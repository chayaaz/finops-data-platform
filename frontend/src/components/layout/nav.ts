import {
  ArrowLeftRight,
  Banknote,
  Boxes,
  Gauge,
  LayoutGrid,
  ListChecks,
  Radar,
  Scale,
  ShieldCheck,
  ShieldQuestion,
  TrendingUp,
  UploadCloud,
  Wallet,
  type LucideIcon,
} from "lucide-react";
import type { UserRole } from "@/types/api";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  roles?: UserRole[];
}

export interface NavGroup {
  title: string;
  items: NavItem[];
}

export const navGroups: NavGroup[] = [
  {
    title: "Overview",
    items: [{ to: "/", label: "Executive Dashboard", icon: LayoutGrid }],
  },
  {
    title: "Data Pipeline",
    items: [
      { to: "/upload", label: "Upload Data", icon: UploadCloud, roles: ["admin", "finance_manager", "analyst"] },
      { to: "/ingestion", label: "Ingestion Monitor", icon: Gauge },
      { to: "/quality", label: "Data Quality & Issues", icon: ShieldQuestion },
      { to: "/anomalies", label: "Anomaly Detection", icon: Radar },
    ],
  },
  {
    title: "Explore",
    items: [{ to: "/transactions", label: "Transactions", icon: ListChecks }],
  },
  {
    title: "Financial Planning",
    items: [
      { to: "/budgets", label: "Budget vs Actual", icon: Wallet },
      { to: "/fx-exposure", label: "FX Exposure", icon: ArrowLeftRight },
    ],
  },
  {
    title: "Vendors & Costs",
    items: [
      { to: "/vendors", label: "Vendor Analytics", icon: Boxes },
      { to: "/allocation", label: "Cost Allocation", icon: Scale },
    ],
  },
  {
    title: "Insights",
    items: [{ to: "/trends", label: "Trends & Forecast", icon: TrendingUp }],
  },
  {
    title: "System",
    items: [{ to: "/admin", label: "Admin", icon: ShieldCheck, roles: ["admin"] }],
  },
];

export const brandIcon = Banknote;
