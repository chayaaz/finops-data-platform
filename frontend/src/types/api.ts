export type UserRole = "admin" | "finance_manager" | "analyst" | "auditor";
export type IngestionStatus = "processing" | "completed" | "failed";
export type ApprovalStatus = "pending" | "approved" | "paid" | "rejected";
export type IssueSeverity = "low" | "medium" | "high" | "critical";
export type IssueStatus = "open" | "acknowledged" | "resolved";
export type AnomalyStatus = "open" | "reviewed" | "dismissed";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user: User;
}

export interface BusinessEntity {
  id: number;
  name: string;
  country: string;
  base_currency: string;
}

export interface Department {
  id: number;
  name: string;
  business_entity_id: number;
}

export interface CostCenter {
  id: number;
  code: string;
  name: string;
  department_id: number;
}

export interface Region {
  id: number;
  code: string;
  name: string;
}

export interface Category {
  id: number;
  name: string;
  parent_category_id: number | null;
}

export interface IngestionBatch {
  id: number;
  file_name: string;
  uploaded_at: string;
  status: IngestionStatus;
  row_count: number;
  accepted_count: number;
  rejected_count: number;
}

export interface CleanTransaction {
  id: number;
  record_id: string;
  transaction_date: string;
  posting_date: string | null;
  invoice_number: string | null;
  vendor_id: number | null;
  department_id: number | null;
  cost_center_id: number | null;
  category_id: number | null;
  business_entity_id: number | null;
  region_id: number | null;
  currency: string;
  net_amount: number;
  tax_amount: number;
  total_amount: number;
  total_amount_base_currency: number | null;
  payment_method: string | null;
  approval_status: ApprovalStatus;
  description: string | null;
}

export interface TransactionPage {
  items: CleanTransaction[];
  total: number;
  skip: number;
  limit: number;
}

export interface RawTransaction {
  id: number;
  batch_id: number;
  record_id: string;
  vendor_name: string | null;
  department: string | null;
  cost_center: string | null;
  category: string | null;
  transaction_date: string | null;
  currency: string | null;
  total_amount: string | null;
}

export interface DataQualityIssue {
  id: number;
  batch_id: number;
  raw_transaction_id: number | null;
  clean_transaction_id: number | null;
  rule_code: string;
  severity: IssueSeverity;
  description: string;
  status: IssueStatus;
  detected_at: string;
  resolved_by_id: number | null;
  resolved_at: string | null;
}

export interface IssueRawRow {
  id: number;
  batch_id: number;
  record_id: string;
  transaction_date: string | null;
  vendor_name: string | null;
  department: string | null;
  cost_center: string | null;
  category: string | null;
  currency: string | null;
  net_amount: string | null;
  tax_amount: string | null;
  total_amount: string | null;
  business_entity: string | null;
  is_accepted: boolean;
}

export type IssueRowCorrections = Partial<Omit<IssueRawRow, "id" | "batch_id" | "is_accepted">>;

export interface IssueRowFixResult {
  clean_transaction_id: number;
  was_added: boolean;
  remaining_problems: string[];
}

export interface IssueSummary {
  by_status: Record<string, number>;
  by_severity: Record<string, number>;
  by_rule_code: Record<string, number>;
}

export interface Anomaly {
  id: number;
  clean_transaction_id: number;
  anomaly_type: string;
  z_score: number | null;
  detail: string | null;
  status: AnomalyStatus;
  detected_at: string;
  reviewed_by_id: number | null;
  reviewed_at: string | null;
}

export interface BenfordGroupResult {
  group_id: number;
  sample_size: number;
  chi_square: number;
  observed_distribution: Record<string, number>;
  expected_distribution: Record<string, number>;
  flagged: boolean;
}

export interface Budget {
  id: number;
  cost_center_id: number;
  category_id: number | null;
  period_month: string;
  currency: string;
  budget_amount: number;
}

export interface BudgetVarianceRow {
  cost_center_id: number | null;
  category_id: number | null;
  period_month: string;
  budget_amount: number;
  actual_amount: number;
  variance: number;
  variance_pct: number | null;
  is_over_budget: boolean;
}

export interface BurnDownPoint {
  period_month: string;
  cumulative_budget: number;
  cumulative_actual: number;
}

export interface Vendor {
  id: number;
  name: string;
  default_category_id: number | null;
  contract_type: string | null;
  is_active: boolean;
}

export interface VendorShare {
  vendor_id: number;
  vendor_name: string;
  spend: number;
  share_pct: number;
}

export interface VendorConcentration {
  hhi: number;
  risk_level: string;
  total_spend: number | null;
  vendor_shares: VendorShare[];
}

export interface CommitmentUtilization {
  vendor_id: number;
  vendor_name: string;
  business_entity_id: number;
  business_entity_name: string;
  period_month: string;
  currency: string;
  committed_amount: number;
  utilized_amount: number;
  utilization_pct: number;
}

export interface DashboardKpis {
  total_spend: number;
  total_transactions: number;
  open_issues: number;
  open_anomalies: number;
  data_quality_score_pct: number;
  mom_growth_pct: number | null;
  top_category_name: string | null;
  top_category_spend: number | null;
}

export interface TrendPoint {
  period_month: string;
  total_spend: number;
}

export interface ForecastPoint {
  period_month: string;
  forecast: number;
  lower_bound: number;
  upper_bound: number;
}

export interface ForecastResult {
  history: { period_month: string; actual: number }[];
  forecast: ForecastPoint[];
  trend_slope_per_month: number | null;
  note: string | null;
}

export interface AllocationRow {
  department_id: number;
  department_name: string;
  weight_pct: number;
  allocated_amount: number;
}

export interface FxExposureRow {
  currency: string;
  total_base_currency: number;
  share_pct: number;
  transaction_count: number;
}

export interface DataQualityRule {
  id: number;
  code: string;
  name: string;
  description: string | null;
  rule_type: string;
  severity: IssueSeverity;
  threshold: number | null;
  is_active: boolean;
}

export interface AuditLogEntry {
  id: number;
  user_id: number | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  details: string | null;
  created_at: string;
}
