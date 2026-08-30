export type RoleType =
  | 'REVENUE_OFFICER'
  | 'SENIOR_REVENUE_OFFICER'
  | 'DEPARTMENT_ADMINISTRATOR'
  | 'READ_ONLY_AUDITOR';

export type PermissionType =
  | 'APPLICATION_VIEW_ASSIGNED'
  | 'APPLICATION_VIEW_ALL'
  | 'DOCUMENT_VERIFY'
  | 'APPLICATION_APPROVE'
  | 'APPLICATION_REJECT'
  | 'REQUEST_INFORMATION'
  | 'ESCALATED_CASE_REVIEW'
  | 'EXCEPTION_OVERRIDE'
  | 'USER_MANAGE'
  | 'SERVICE_METADATA_CONFIGURE'
  | 'SYSTEM_HEALTH_VIEW'
  | 'AUDIT_VIEW';

export interface User {
  id: string;
  username: string;
  email: string;
  mobile: string;
  full_name: string;
  role: RoleType;
  department: string;
  division: string;
  is_active: boolean;
  created_at: string;
  last_login_at?: string | null;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  role: RoleType | null;
  permissions: PermissionType[];
  isAuthenticated: boolean;
  isLoading: boolean;
  sessionWarning: boolean;
}
