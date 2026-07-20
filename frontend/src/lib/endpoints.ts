import { api } from "./apiClient";
import type {
  AllocationRow,
  Anomaly,
  AnomalyStatus,
  AuditLogEntry,
  BenfordGroupResult,
  Budget,
  BudgetVarianceRow,
  BurnDownPoint,
  BusinessEntity,
  Category,
  CommitmentUtilization,
  CostCenter,
  DashboardKpis,
  DataQualityIssue,
  DataQualityRule,
  Department,
  ForecastResult,
  FxExposureRow,
  IngestionBatch,
  IssueStatus,
  IssueSummary,
  RawTransaction,
  Region,
  TransactionPage,
  User,
  Vendor,
  VendorConcentration,
} from "@/types/api";

export const endpoints = {
  dimensions: {
    businessEntities: () => api.get<BusinessEntity[]>("/dimensions/business-entities"),
    departments: () => api.get<Department[]>("/dimensions/departments"),
    costCenters: () => api.get<CostCenter[]>("/dimensions/cost-centers"),
    regions: () => api.get<Region[]>("/dimensions/regions"),
    categories: () => api.get<Category[]>("/dimensions/categories"),
  },
  ingestion: {
    batches: (skip = 0, limit = 100) => api.get<IngestionBatch[]>("/ingestion/batches", { skip, limit }),
    batch: (id: number) => api.get<IngestionBatch>(`/ingestion/batches/${id}`),
  },
  upload: {
    submit: (file: File) => api.upload<IngestionBatch>("/upload", file),
  },
  transactions: {
    list: (params: Record<string, string | number | undefined | null>) =>
      api.get<TransactionPage>("/transactions", params),
    raw: (batchId: number, skip = 0, limit = 200) =>
      api.get<RawTransaction[]>("/transactions/raw", { batch_id: batchId, skip, limit }),
  },
  issues: {
    list: (params: Record<string, string | number | undefined | null> = {}) =>
      api.get<DataQualityIssue[]>("/issues", params),
    summary: () => api.get<IssueSummary>("/issues/summary"),
    updateStatus: (id: number, status: IssueStatus) => api.patch<DataQualityIssue>(`/issues/${id}`, { status }),
  },
  anomalies: {
    list: (params: Record<string, string | number | undefined | null> = {}) =>
      api.get<Anomaly[]>("/anomalies", params),
    benford: (groupBy: "category" | "vendor" = "category") =>
      api.get<BenfordGroupResult[]>("/anomalies/benford", { group_by: groupBy }),
    detect: () => api.post<{ created: number }>("/anomalies/detect"),
    updateStatus: (id: number, status: AnomalyStatus) => api.patch<Anomaly>(`/anomalies/${id}`, { status }),
  },
  budgets: {
    list: (params: Record<string, string | number | undefined | null> = {}) =>
      api.get<Budget[]>("/budgets", params),
    variance: (periodStart: string, periodEnd: string, params: Record<string, number | undefined> = {}) =>
      api.get<BudgetVarianceRow[]>("/budgets/variance", { period_start: periodStart, period_end: periodEnd, ...params }),
    burnDown: (year: number, params: Record<string, number | undefined> = {}) =>
      api.get<BurnDownPoint[]>("/budgets/burn-down", { year, ...params }),
    create: (payload: {
      cost_center_id: number;
      category_id?: number | null;
      period_month: string;
      currency: string;
      budget_amount: number;
    }) => api.post<Budget>("/budgets", payload),
    update: (id: number, budgetAmount: number) => api.patch<Budget>(`/budgets/${id}`, { budget_amount: budgetAmount }),
  },
  vendors: {
    list: () => api.get<Vendor[]>("/vendors"),
    concentration: (periodStart: string, periodEnd: string, params: Record<string, number | undefined> = {}) =>
      api.get<VendorConcentration>("/vendors/concentration", { period_start: periodStart, period_end: periodEnd, ...params }),
    commitments: (params: Record<string, string | number | undefined> = {}) =>
      api.get<CommitmentUtilization[]>("/vendors/commitments", params),
  },
  analytics: {
    kpis: () => api.get<DashboardKpis>("/analytics/kpis"),
    trends: (categoryId?: number) => api.get<{ period_month: string; total_spend: number }[]>("/analytics/trends", { category_id: categoryId }),
    forecast: (categoryId?: number, monthsAhead = 3) =>
      api.get<ForecastResult>("/analytics/forecast", { category_id: categoryId, months_ahead: monthsAhead }),
    allocation: (categoryId: number, periodStart: string, periodEnd: string) =>
      api.get<AllocationRow[]>("/analytics/allocation", { category_id: categoryId, period_start: periodStart, period_end: periodEnd }),
    fxExposure: () => api.get<FxExposureRow[]>("/analytics/fx-exposure"),
  },
  admin: {
    users: () => api.get<User[]>("/admin/users"),
    createUser: (payload: { email: string; full_name: string; role: string; password: string }) =>
      api.post<User>("/admin/users", payload),
    updateUser: (id: number, payload: Partial<{ full_name: string; role: string; is_active: boolean }>) =>
      api.patch<User>(`/admin/users/${id}`, payload),
    rules: () => api.get<DataQualityRule[]>("/admin/rules"),
    updateRule: (id: number, payload: Partial<{ severity: string; threshold: number; is_active: boolean }>) =>
      api.patch<DataQualityRule>(`/admin/rules/${id}`, payload),
    auditLog: (skip = 0, limit = 200) => api.get<AuditLogEntry[]>("/admin/audit-log", { skip, limit }),
  },
};
