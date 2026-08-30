import {
  ApplicationDetail,
  ApplicationFilterParams,
  ApplicationListResult,
  DashboardSummaryData,
  ConsentValidationResult,
  DataValidationResult,
  DocumentVerificationResult,
  WorkflowActionResponse,
  InformationRequestPayload,
  AuditLogListResult,
  NotificationListResult,
  FailureSimulationMode,
  ProofDocumentMetadata,
  DocumentUploadResponse,
  DocumentOverridePayload,
} from '../types/application';
import { User, PermissionType } from '../types/auth';

export interface ServiceHealthData {
  status: string;
  service: string;
  environment: string;
  version: string;
  timestamp: string;
}

export interface DatabaseHealthData {
  status: string;
  database: string;
  latency_ms: number;
  error?: string | null;
}

export interface SystemInfoData {
  department: string;
  sub_department: string;
  state: string;
  project_code: string;
  architecture_role: string;
  current_phase: string;
  simulated: boolean;
  status: string;
}

export interface LoginResult {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
  permissions: PermissionType[];
}

const API_BASE_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '';
const TOKEN_STORAGE_KEY = 'revenue_dept_access_token';

let currentToken: string | null = localStorage.getItem(TOKEN_STORAGE_KEY);

export const apiService = {
  /**
   * Token management
   */
  setToken(token: string | null) {
    currentToken = token;
    if (token) {
      localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  },

  getToken(): string | null {
    if (!currentToken) {
      currentToken = localStorage.getItem(TOKEN_STORAGE_KEY);
    }
    return currentToken;
  },

  getAuthHeaders(): Record<string, string> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  },

  /**
   * Authentication endpoints
   */
  async login(identifier: string, password: string): Promise<LoginResult> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier, password }),
    });

    const data = await response.json();
    if (!response.ok) {
      const errorMsg = data?.error?.message || 'Login failed. Please verify credentials.';
      const errorCode = data?.error?.code || 'AUTH_ERROR';
      const error = new Error(errorMsg);
      (error as any).code = errorCode;
      throw error;
    }

    this.setToken(data.access_token);
    return data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
      headers: this.getAuthHeaders(),
    });

    const data = await response.json();
    if (!response.ok) {
      const errorMsg = data?.error?.message || 'Failed to fetch user session.';
      const errorCode = data?.error?.code || 'AUTH_ERROR';
      const error = new Error(errorMsg);
      (error as any).code = errorCode;
      throw error;
    }

    return data.data;
  },

  async logout(): Promise<void> {
    try {
      await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });
    } catch {
      // Best effort
    } finally {
      this.setToken(null);
    }
  },

  async reauthenticate(password: string): Promise<boolean> {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/reauthenticate`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ password }),
    });

    const data = await response.json();
    if (!response.ok) {
      const errorMsg = data?.error?.message || 'Re-authentication failed.';
      const errorCode = data?.error?.code || 'REAUTH_FAILED';
      const error = new Error(errorMsg);
      (error as any).code = errorCode;
      throw error;
    }

    return data.success === true;
  },

  async getDepartmentUsers(): Promise<User[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/admin/users`, {
      headers: this.getAuthHeaders(),
    });

    const data = await response.json();
    if (!response.ok) {
      const errorMsg = data?.error?.message || 'Access restricted. Administrator role required.';
      const errorCode = data?.error?.code || 'FORBIDDEN';
      const error = new Error(errorMsg);
      (error as any).code = errorCode;
      throw error;
    }

    return data.data;
  },

  /**
   * Phase 03: Dashboard & Application Management APIs
   */
  async getDashboardSummary(): Promise<DashboardSummaryData> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/revenue/dashboard/summary`, {
        headers: this.getAuthHeaders(),
      });
      if (response.ok) {
        const payload = await response.json();
        if (payload.success && payload.data) {
          return payload.data;
        }
      }
    } catch (error) {
      console.warn('Using client fallback for dashboard summary:', error);
    }

    return {
      total_incoming: 12,
      pending: 4,
      processing: 4,
      completed: 2,
      rejected: 0,
      action_required: 1,
      failed_or_queued: 1,
      average_processing_time: '2h 15m',
      today_applications: 5,
      govmesh_connection: 'DEMO ONLINE',
      api_status: 'ONLINE',
      pending_events: 1,
    };
  },

  async getApplications(params: ApplicationFilterParams = {}): Promise<ApplicationListResult> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page.toString());
    if (params.page_size) query.set('page_size', params.page_size.toString());
    if (params.status && params.status !== 'ALL') query.set('status', params.status);
    if (params.priority && params.priority !== 'ALL') query.set('priority', params.priority);
    if (params.service_type && params.service_type !== 'ALL') query.set('service_type', params.service_type);
    if (params.search) query.set('search', params.search);
    if (params.sort_by) query.set('sort_by', params.sort_by);
    if (params.sort_order) query.set('sort_order', params.sort_order);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/revenue/applications?${query.toString()}`, {
        headers: this.getAuthHeaders(),
      });
      if (response.ok) {
        const payload = await response.json();
        if (payload.success && payload.data) {
          return payload.data;
        }
      }
    } catch (error) {
      console.warn('Failed to load applications from API, using fallback:', error);
    }

    return {
      items: [
        {
          id: 'APP-REV-001',
          application_id: 'GM-2026-000124',
          correlation_id: 'CORR-2026-000124',
          citizen_reference_id: 'CIT-MH-1001',
          citizen_name: 'Rajesh Shantaram Patil',
          service_type: 'ADDRESS_CHANGE',
          requested_operation: 'UPDATE_REVENUE_ADDRESS',
          priority: 'HIGH',
          status: 'PENDING',
          required_action: 'Verify new residential address against Taluka land registry & electricity proof',
          received_at: new Date().toISOString(),
          taluka: 'Haveli',
          district: 'Pune',
        },
      ],
      pagination: {
        page: 1,
        page_size: 20,
        total: 1,
        total_pages: 1,
      },
    };
  },

  async getApplicationById(id: string): Promise<ApplicationDetail | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/revenue/applications/${id}`, {
        headers: this.getAuthHeaders(),
      });
      if (response.ok) {
        const payload = await response.json();
        if (payload.success && payload.data) {
          return payload.data;
        }
      }
    } catch (error) {
      console.warn(`Failed to fetch application ${id} from API:`, error);
    }

    return null;
  },

  /**
   * Phase 04: Workflow Actions & Authoritative Validation APIs
   */
  async startReview(applicationId: string): Promise<WorkflowActionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/start-review`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      const msg = data?.error?.message || 'Failed to start review.';
      throw new Error(msg);
    }
    return data.data;
  },

  async validateConsent(applicationId: string): Promise<ConsentValidationResult> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/validate-consent`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      const msg = data?.error?.message || 'Consent validation request failed.';
      throw new Error(msg);
    }
    return data.data;
  },

  async validateData(applicationId: string): Promise<DataValidationResult> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/validate-data`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      const msg = data?.error?.message || 'Data validation request failed.';
      throw new Error(msg);
    }
    return data.data;
  },

  async verifyDocument(applicationId: string): Promise<DocumentVerificationResult> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/verify-document`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      const msg = data?.error?.message || 'Document verification request failed.';
      throw new Error(msg);
    }
    return data.data;
  },

  async approveApplication(applicationId: string, reason?: string, reauthPassword?: string): Promise<WorkflowActionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/approve`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ reason, reauth_password: reauthPassword }),
    });
    const data = await response.json();
    if (!response.ok) {
      const msg = data?.error?.message || 'Approval failed.';
      const err = new Error(msg);
      (err as any).code = data?.error?.code || 'APPROVAL_ERROR';
      throw err;
    }
    return data.data;
  },

  async rejectApplication(applicationId: string, reason: string): Promise<WorkflowActionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/reject`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ reason }),
    });
    const data = await response.json();
    if (!response.ok) {
      const msg = data?.error?.message || 'Rejection failed.';
      const err = new Error(msg);
      (err as any).code = data?.error?.code || 'REJECTION_ERROR';
      throw err;
    }
    return data.data;
  },

  async requestInformation(applicationId: string, payload: InformationRequestPayload): Promise<WorkflowActionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/request-info`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      const msg = data?.error?.message || 'Failed to request additional information.';
      const err = new Error(msg);
      (err as any).code = data?.error?.code || 'REQUEST_INFO_ERROR';
      throw err;
    }
    return data.data;
  },

  async reprocessApplication(applicationId: string): Promise<WorkflowActionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/reprocess`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      const msg = data?.error?.message || 'Reprocessing request failed.';
      throw new Error(msg);
    }
    return data.data;
  },

  async getAuditLogs(params: { page?: number; page_size?: number; application_id?: string; officer_id?: string } = {}): Promise<AuditLogListResult> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page.toString());
    if (params.page_size) query.set('page_size', params.page_size.toString());
    if (params.application_id) query.set('application_id', params.application_id);
    if (params.officer_id) query.set('officer_id', params.officer_id);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/revenue/audit-logs?${query.toString()}`, {
        headers: this.getAuthHeaders(),
      });
      if (response.ok) {
        const payload = await response.json();
        if (payload.success && payload.data) {
          return payload.data;
        }
      }
    } catch (error) {
      console.warn('Failed to load audit logs from API:', error);
    }

    return {
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 1,
    };
  },

  /**
   * Health and System metadata endpoints
   */
  async getServiceHealth(): Promise<ServiceHealthData> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return await response.json();
    } catch {
      return {
        status: 'unreachable',
        service: 'revenue-department',
        environment: 'local-fallback',
        version: '0.4.0',
        timestamp: new Date().toISOString(),
      };
    }
  },

  async getDatabaseHealth(): Promise<DatabaseHealthData> {
    try {
      const response = await fetch(`${API_BASE_URL}/health/db`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      return await response.json();
    } catch {
      return {
        status: 'disconnected',
        database: 'PostgreSQL',
        latency_ms: 0,
        error: 'Backend API offline or database unavailable',
      };
    }
  },

  async getSystemInfo(): Promise<SystemInfoData> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/revenue/system-info`);
      if (!response.ok) throw new Error(`HTTP error ${response.status}`);
      const payload = await response.json();
      return payload.data;
    } catch {
      return {
        department: 'Revenue & Forest Department',
        sub_department: 'Land Records & Citizen Revenue Services',
        state: 'Maharashtra',
        project_code: 'SIH26129',
        architecture_role: 'Independent Department System (Department 1)',
        current_phase: 'Phase 05 - Workflow Completion, Failure Handling & Operations',
        simulated: true,
        status: 'STANDALONE_READY',
      };
    }
  },

  /**
   * Phase 05: Operational Queues, Failure Recovery, Notifications & Simulation
   */
  async retryApplication(applicationId: string): Promise<WorkflowActionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/retry`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    const data = await response.json();
    if (!response.ok) {
      const msg = data?.error?.message || 'Operational retry request failed.';
      const err = new Error(msg);
      (err as any).code = data?.error?.code || 'RETRY_ERROR';
      (err as any).correlationId = data?.error?.correlationId;
      throw err;
    }
    return data.data;
  },

  async getCompletedApplications(params: ApplicationFilterParams = {}): Promise<ApplicationListResult> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page.toString());
    if (params.page_size) query.set('page_size', params.page_size.toString());
    if (params.search) query.set('search', params.search);
    if (params.sort_by) query.set('sort_by', params.sort_by);
    if (params.sort_order) query.set('sort_order', params.sort_order);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/revenue/applications/completed?${query.toString()}`, {
        headers: this.getAuthHeaders(),
      });
      if (response.ok) {
        const payload = await response.json();
        if (payload.success && payload.data) {
          return payload.data;
        }
      }
    } catch (error) {
      console.warn('Failed to load completed applications:', error);
    }

    return {
      items: [],
      pagination: { page: 1, page_size: 20, total: 0, total_pages: 1 },
    };
  },

  async getRejectedApplications(params: ApplicationFilterParams = {}): Promise<ApplicationListResult> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page.toString());
    if (params.page_size) query.set('page_size', params.page_size.toString());
    if (params.search) query.set('search', params.search);
    if (params.sort_by) query.set('sort_by', params.sort_by);
    if (params.sort_order) query.set('sort_order', params.sort_order);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/revenue/applications/rejected?${query.toString()}`, {
        headers: this.getAuthHeaders(),
      });
      if (response.ok) {
        const payload = await response.json();
        if (payload.success && payload.data) {
          return payload.data;
        }
      }
    } catch (error) {
      console.warn('Failed to load rejected applications:', error);
    }

    return {
      items: [],
      pagination: { page: 1, page_size: 20, total: 0, total_pages: 1 },
    };
  },

  async getActionRequiredApplications(params: ApplicationFilterParams = {}): Promise<ApplicationListResult> {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page.toString());
    if (params.page_size) query.set('page_size', params.page_size.toString());
    if (params.search) query.set('search', params.search);
    if (params.sort_by) query.set('sort_by', params.sort_by);
    if (params.sort_order) query.set('sort_order', params.sort_order);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/revenue/applications/action-required?${query.toString()}`, {
        headers: this.getAuthHeaders(),
      });
      if (response.ok) {
        const payload = await response.json();
        if (payload.success && payload.data) {
          return payload.data;
        }
      }
    } catch (error) {
      console.warn('Failed to load action-required applications:', error);
    }

    return {
      items: [],
      pagination: { page: 1, page_size: 20, total: 0, total_pages: 1 },
    };
  },

  async getNotifications(unreadOnly = false, limit = 50): Promise<NotificationListResult> {
    try {
      const query = new URLSearchParams({
        unread_only: unreadOnly ? 'true' : 'false',
        limit: limit.toString(),
      });
      const response = await fetch(`${API_BASE_URL}/api/v1/revenue/notifications?${query.toString()}`, {
        headers: this.getAuthHeaders(),
      });
      if (response.ok) {
        const payload = await response.json();
        if (payload.success && payload.data) {
          return payload.data;
        }
      }
    } catch (error) {
      console.warn('Failed to load notifications from API:', error);
    }

    return {
      items: [],
      total: 0,
      unread_count: 0,
    };
  },

  async getUnreadNotificationCount(): Promise<number> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/revenue/notifications/unread-count`, {
        headers: this.getAuthHeaders(),
      });
      if (response.ok) {
        const payload = await response.json();
        if (payload.success && payload.data) {
          return payload.data.unread_count || 0;
        }
      }
    } catch {
      // Fallback
    }
    return 0;
  },

  async markNotificationRead(id: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/revenue/notifications/${id}/read`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });
      return response.ok;
    } catch {
      return false;
    }
  },

  async markAllNotificationsRead(): Promise<number> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/revenue/notifications/mark-all-read`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });
      if (response.ok) {
        const payload = await response.json();
        return payload?.data?.marked_read_count || 0;
      }
    } catch {
      // Fallback
    }
    return 0;
  },

  async getFailureMode(): Promise<FailureSimulationMode> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/revenue/simulation/failure-mode`, {
        headers: this.getAuthHeaders(),
      });
      if (response.ok) {
        const payload = await response.json();
        return payload?.data?.failure_mode || 'NONE';
      }
    } catch {
      // Fallback
    }
    return 'NONE';
  },

  async setFailureMode(mode: FailureSimulationMode): Promise<FailureSimulationMode> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/simulation/failure-mode`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ mode }),
    });
    const payload = await response.json();
    return payload?.data?.failure_mode || mode;
  },

  // ==========================================================================
  // Phase 06: Document Verification, Ingestion & Manual Override
  // ==========================================================================
  async uploadDocument(
    applicationId: string,
    file: File,
    documentType: string = 'ELECTRICITY_BILL'
  ): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    const token = this.getToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(
      `${API_BASE_URL}/api/v1/revenue/application/${applicationId}/documents`,
      {
        method: 'POST',
        headers,
        body: formData,
      }
    );

    if (!response.ok) {
      const err = await response.json().catch(() => ({ error: { message: 'Document upload failed' } }));
      throw new Error(err.error?.message || 'Document upload failed');
    }

    const payload = await response.json();
    return payload.data;
  },

  async getApplicationDocuments(applicationId: string): Promise<ProofDocumentMetadata[]> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/revenue/application/${applicationId}/documents`,
        {
          headers: this.getAuthHeaders(),
        }
      );
      if (response.ok) {
        const payload = await response.json();
        return payload.data || [];
      }
    } catch {
      // Fallback
    }
    return [];
  },

  async getDocumentById(documentId: string): Promise<ProofDocumentMetadata | null> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/revenue/document/${documentId}`, {
        headers: this.getAuthHeaders(),
      });
      if (response.ok) {
        const payload = await response.json();
        return payload.data;
      }
    } catch {
      // Fallback
    }
    return null;
  },

  async verifyDocumentById(documentId: string): Promise<DocumentVerificationResult> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/document/${documentId}/verify`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ error: { message: 'Document verification failed' } }));
      throw new Error(err.error?.message || 'Document verification failed');
    }

    const payload = await response.json();
    return payload.data;
  },

  async overrideDocumentVerification(
    documentId: string,
    payloadData: DocumentOverridePayload
  ): Promise<DocumentVerificationResult> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/document/${documentId}/override`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(payloadData),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ error: { message: 'Manual override failed' } }));
      throw new Error(err.error?.message || 'Manual override failed');
    }

    const payload = await response.json();
    return payload.data;
  },

  getDocumentPreviewUrl(documentId: string): string {
    return `${API_BASE_URL}/api/v1/revenue/document/${documentId}/preview`;
  },
};

