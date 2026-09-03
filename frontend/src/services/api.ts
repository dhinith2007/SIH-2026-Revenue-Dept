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

export interface BaseResponse<T = any> {
  success: boolean;
  data: T;
  message?: string;
  error?: {
    code?: string;
    message?: string;
    correlationId?: string;
    details?: any;
  };
}

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

function cleanBaseUrl(url: string | undefined): string {
  if (!url) return '';
  let cleaned = url.trim().replace(/\/+$/, ''); // Remove trailing slashes
  if (cleaned.endsWith('/api/v1')) {
    cleaned = cleaned.substring(0, cleaned.length - 7);
  } else if (cleaned.endsWith('/api')) {
    cleaned = cleaned.substring(0, cleaned.length - 4);
  }
  return cleaned;
}

const PRODUCTION_BACKEND_URL = 'https://sih-2026-revenue-dept.onrender.com';
const RAW_API_URL = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? PRODUCTION_BACKEND_URL : '');
const API_BASE_URL = cleanBaseUrl(RAW_API_URL);
const TOKEN_STORAGE_KEY = 'revenue_dept_access_token';

let currentToken: string | null = localStorage.getItem(TOKEN_STORAGE_KEY);

/**
 * Safely parses API responses to prevent "Unexpected end of JSON input" on network/HTML errors
 */
async function parseJsonResponse<T = any>(response: Response, defaultErrorMsg = 'Request failed'): Promise<T> {
  const contentType = response.headers.get('content-type') || '';
  let data: any = null;

  if (contentType.includes('application/json')) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  } else {
    const text = await response.text().catch(() => '');
    if (!response.ok) {
      if (response.status === 405) {
        const error = new Error(`HTTP 405 Method Not Allowed at '${response.url}'. This occurs when POST requests hit your static Vercel frontend host instead of your deployed FastAPI backend service. In Vercel Project Settings -> Environment Variables, set 'VITE_API_URL' to your deployed FastAPI backend URL (e.g. https://your-backend.onrender.com).`);
        (error as any).code = 'HTTP_405_METHOD_NOT_ALLOWED';
        throw error;
      }
      const error = new Error(`Backend error (HTTP ${response.status}): ${response.statusText || 'Non-JSON response'}. Verify VITE_API_URL and backend health.`);
      (error as any).code = `HTTP_${response.status}`;
      throw error;
    }
    if (text.includes('<!DOCTYPE html>') || text.includes('<html')) {
      const error = new Error(`Received HTML instead of JSON from '${response.url}'. The Revenue backend service may be offline or VITE_API_URL is misconfigured.`);
      (error as any).code = 'INVALID_HTML_RESPONSE';
      throw error;
    }
  }

  if (!response.ok) {
    const errorMsg = data?.error?.message || data?.message || defaultErrorMsg;
    const errorCode = data?.error?.code || data?.code || `HTTP_${response.status}`;
    const error = new Error(errorMsg);
    (error as any).code = errorCode;
    throw error;
  }

  if (!data && response.status !== 204) {
    const error = new Error(`Empty response received from '${response.url}'. Verify backend service status.`);
    (error as any).code = 'EMPTY_RESPONSE';
    throw error;
  }

  return data;
}

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
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier, password }),
      });

      const data = await parseJsonResponse<LoginResult>(response, 'Login failed. Please verify credentials.');
      this.setToken(data.access_token);
      return data;
    } catch (err: any) {
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        throw new Error(`Unable to reach Revenue backend at '${API_BASE_URL || window.location.origin}'. Ensure backend is running and CORS is configured.`);
      }
      throw err;
    }
  },

  async getCurrentUser(): Promise<User> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
        headers: this.getAuthHeaders(),
      });

      const data = await parseJsonResponse<BaseResponse<User>>(response, 'Failed to fetch user session.');
      return (data as any).data || (data as any);
    } catch (err: any) {
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        throw new Error('Unable to connect to Revenue authentication service.');
      }
      throw err;
    }
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

    const data = await parseJsonResponse<any>(response, 'Re-authentication failed.');
    return data.success === true;
  },

  async getDepartmentUsers(): Promise<User[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/admin/users`, {
      headers: this.getAuthHeaders(),
    });

    const data = await parseJsonResponse<BaseResponse<User[]>>(response, 'Access restricted. Administrator role required.');
    return data.data;
  },

  /**
   * Phase 03: Dashboard & Application Management APIs
   */
  async getDashboardSummary(): Promise<DashboardSummaryData> {
    try {
      const url = API_BASE_URL ? `${API_BASE_URL}/api/v1/revenue/dashboard/summary` : '/api/v1/revenue/dashboard/summary';
      const response = await fetch(url, {
        headers: this.getAuthHeaders(),
      }).catch(() => null);

      if (response && response.ok) {
        const payload = await response.json().catch(() => null);
        if (payload && payload.success && payload.data) {
          return payload.data;
        }
      }
    } catch (error) {
      // Fallback below
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
      today_applications: 3,
      govmesh_connection: 'DEMO ONLINE',
      api_status: 'ONLINE',
      pending_events: 1,
    };
  },

  /**
   * Phase 11: Backend-Authoritative Analytics & Dashboard API
   */
  async getFullDashboardAnalytics(
    days: number = 7,
    status?: string,
    recommendationBand?: string,
    riskFlag?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    params.set('days', days.toString());
    if (status) params.set('status', status);
    if (recommendationBand) params.set('recommendation_band', recommendationBand);
    if (riskFlag) params.set('risk_flag', riskFlag);

    try {
      const url = API_BASE_URL ? `${API_BASE_URL}/api/v1/analytics/dashboard?${params.toString()}` : `/api/v1/analytics/dashboard?${params.toString()}`;
      const response = await fetch(url, {
        headers: this.getAuthHeaders(),
      }).catch(() => null);

      if (response && response.ok) {
        const payload = await response.json().catch(() => null);
        if (payload && payload.success && payload.data) {
          return payload.data;
        }
      }
    } catch (error) {
      // Fallback below
    }

    return null;
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
    const data = await parseJsonResponse<BaseResponse<WorkflowActionResponse>>(response, 'Failed to start review.');
    return data.data;
  },

  async validateConsent(applicationId: string): Promise<ConsentValidationResult> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/validate-consent`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    const data = await parseJsonResponse<BaseResponse<ConsentValidationResult>>(response, 'Consent validation request failed.');
    return data.data;
  },

  async validateData(applicationId: string): Promise<DataValidationResult> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/validate-data`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    const data = await parseJsonResponse<BaseResponse<DataValidationResult>>(response, 'Data validation request failed.');
    return data.data;
  },

  async verifyDocument(applicationId: string): Promise<DocumentVerificationResult> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/verify-document`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    const data = await parseJsonResponse<BaseResponse<DocumentVerificationResult>>(response, 'Document verification request failed.');
    return data.data;
  },

  async approveApplication(applicationId: string, reason?: string, reauthPassword?: string): Promise<WorkflowActionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/approve`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ reason, reauth_password: reauthPassword }),
    });
    const data = await parseJsonResponse<BaseResponse<WorkflowActionResponse>>(response, 'Approval failed.');
    return data.data;
  },

  async rejectApplication(applicationId: string, reason: string): Promise<WorkflowActionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/reject`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify({ reason }),
    });
    const data = await parseJsonResponse<BaseResponse<WorkflowActionResponse>>(response, 'Rejection failed.');
    return data.data;
  },

  async requestInformation(applicationId: string, payload: InformationRequestPayload): Promise<WorkflowActionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/request-info`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    const data = await parseJsonResponse<BaseResponse<WorkflowActionResponse>>(response, 'Failed to request additional information.');
    return data.data;
  },

  async reprocessApplication(applicationId: string): Promise<WorkflowActionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/revenue/application/${applicationId}/reprocess`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
    });
    const data = await parseJsonResponse<BaseResponse<WorkflowActionResponse>>(response, 'Reprocessing request failed.');
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
    const data = await parseJsonResponse<BaseResponse<WorkflowActionResponse>>(response, 'Operational retry request failed.');
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

    const payload = await parseJsonResponse<BaseResponse<DocumentUploadResponse>>(response, 'Document upload failed');
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

    const payload = await parseJsonResponse<BaseResponse<DocumentVerificationResult>>(response, 'Document verification failed');
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

    const payload = await parseJsonResponse<BaseResponse<DocumentVerificationResult>>(response, 'Manual override failed');
    return payload.data;
  },

  getDocumentPreviewUrl(documentId: string): string {
    return `${API_BASE_URL}/api/v1/revenue/document/${documentId}/preview`;
  },
};

