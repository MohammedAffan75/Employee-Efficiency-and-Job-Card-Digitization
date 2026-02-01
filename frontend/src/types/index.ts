// Employee Efficiency Tracking - TypeScript Types

export enum RoleEnum {
  OPERATOR = 'OPERATOR',
  SUPERVISOR = 'SUPERVISOR',
  ADMIN = 'ADMIN',
}

export enum EfficiencyTypeEnum {
  TIME_BASED = 'TIME_BASED',
  QUANTITY_BASED = 'QUANTITY_BASED',
  TASK_BASED = 'TASK_BASED',
}

export enum JobCardStatusEnum {
  C = 'C',  // Complete
  IC = 'IC', // Incomplete
}

export enum FlagTypeEnum {
  MSD_WINDOW = 'MSD_WINDOW',
  DUPLICATION = 'DUPLICATION',
  AWC = 'AWC',
  SPLIT_CANDIDATE = 'SPLIT_CANDIDATE',
  QTY_MISMATCH = 'QTY_MISMATCH',
}

export interface Employee {
  id: number;
  ec_number: string;
  name: string;
  role: RoleEnum;
  join_date: string;
  is_active: boolean;
  supervisor_efficiency_module?: string | null;
}

export interface Machine {
  id: number;
  machine_code: string;
  description: string;
  work_center: string;
}

export interface WorkOrder {
  id: number;
  wo_number: string;
  machine_id: number;
  planned_qty: number;
  msd_month: string;
  machine_code?: string;
  machine_description?: string;
}

export interface ActivityCode {
  id: number;
  code: string;
  description: string;
  efficiency_type: EfficiencyTypeEnum;
  std_hours_per_unit?: number | null;
  std_qty_per_hour?: number | null;
  last_updated: string;
}

export interface JobCard {
  id: number;
  employee_id: number;
  supervisor_id?: number | null;
  machine_id: number;
  work_order_id: number;
  activity_code_id?: number | null;
  activity_desc: string;
  qty: number;
  actual_hours: number;
  status: string;
  entry_date: string;
  source: string;
  efficiency_module?: string;
  has_flags?: boolean;
  approval_status?: string;
  supervisor_remarks?: string | null;
  approved_at?: string | null;
  approved_by?: number | null;
  shift?: number;
  manual_machine_text?: string | null;
  manual_work_order_text?: string | null;
  machine_code?: string | null;
  wo_number?: string | null;
  activity_code?: string | null;
  std_hours_per_unit?: number | null;
  std_qty_per_hour?: number | null;
}

export interface ValidationFlag {
  flag_id: number;
  job_card_id: number;
  flag_type: string;
  details: string;
  resolved: boolean;
  resolved_by?: number | null;
  employee_id?: number | null;
  employee_name?: string | null;
  machine_code?: string | null;
  wo_number?: string | null;
  activity_code?: string | null;
  entry_date?: string | null;
  actual_hours?: number | null;
  qty?: number | null;
}

export interface EfficiencyMetrics {
  employee_id: number;
  period_start: string;
  period_end: string;
  time_efficiency: number | null;
  task_efficiency: number | null;
  quantity_efficiency: number | null;
  awc_pct: number;
  standard_hours_allowed: number;
  actual_hours: number;
  standard_quantity_allowed?: number;
  actual_quantity?: number;
  tasks_completed?: number;
  total_tasks?: number;
}

export interface DashboardSummary {
  team_id?: string | null;
  period_start: string;
  period_end: string;
  employee_count: number;
  avg_time_efficiency: number | null;
  avg_qty_efficiency: number | null;
  avg_task_efficiency: number | null;
  avg_awc_pct: number;
  total_std_hours: number;
  total_actual_hours: number;
  standard_quantity_allowed?: number;
  actual_quantity?: number;
  total_tasks?: number;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  employee: Employee;
}

export interface CreateJobCardRequest {
  employee_id: number;
  machine_id?: number;
  work_order_id?: number;
  activity_code_id?: number | null;
  activity_desc: string;
  qty: number;
  actual_hours: number;
  status: JobCardStatusEnum;
  entry_date: string;
  source: string;
  shift?: number;
  is_awc?: boolean;
  manual_machine_text?: string | null;
  manual_work_order_text?: string | null;
}

export interface ImportReport {
  total_rows: number;
  accepted_count: number;
  rejected_count: number;
  flagged_count: number;
  rejected: RejectedRow[];
  flagged: FlaggedJobCard[];
}

export interface RejectedRow {
  row_number: number;
  reason: string;
}

export interface FlaggedJobCard {
  jobcard_id: number;
  flags: string[];
}
