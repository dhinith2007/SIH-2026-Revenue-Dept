import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { NotificationCenter } from '../components/notifications/NotificationCenter';
import { CompletedApplicationsPage } from '../pages/CompletedApplicationsPage';
import { RejectedApplicationsPage } from '../pages/RejectedApplicationsPage';
import { ActionRequiredPage } from '../pages/ActionRequiredPage';
import { apiService } from '../services/api';

describe('Phase 05: Revenue Operations, Queues & Notification Center UI', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders NotificationCenter with unread badge and dropdown menu', async () => {
    vi.spyOn(apiService, 'getUnreadNotificationCount').mockResolvedValue(2);
    vi.spyOn(apiService, 'getNotifications').mockResolvedValue({
      items: [
        {
          id: 'NOTIF-001',
          type: 'NEW_APPLICATION',
          application_id: 'GM-2026-000124',
          title: 'New Revenue Application',
          message: 'New application for Rajesh Patil awaiting review.',
          timestamp: new Date().toISOString(),
          read: false,
          severity: 'INFO',
          target_role: 'REVENUE_OFFICER',
        },
        {
          id: 'NOTIF-002',
          type: 'ACTION_REQUIRED',
          application_id: 'GM-2026-000128',
          title: 'Missing Document Query',
          message: 'Citizen response needed for missing document.',
          timestamp: new Date().toISOString(),
          read: false,
          severity: 'WARNING',
          target_role: 'REVENUE_OFFICER',
        },
      ],
      total: 2,
      unread_count: 2,
    });

    render(
      <BrowserRouter>
        <NotificationCenter />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument();
    });

    const bellBtn = screen.getByRole('button', { name: /department notifications/i });
    fireEvent.click(bellBtn);

    await waitFor(() => {
      expect(screen.getByText('Department Alerts')).toBeInTheDocument();
      expect(screen.getByText('New Revenue Application')).toBeInTheDocument();
      expect(screen.getByText('Missing Document Query')).toBeInTheDocument();
    });
  });

  it('renders CompletedApplicationsPage with verified application records', async () => {
    vi.spyOn(apiService, 'getCompletedApplications').mockResolvedValue({
      items: [
        {
          id: 'APP-131',
          application_id: 'GM-2026-000131',
          correlation_id: 'CORR-2026-000131',
          citizen_reference_id: 'CIT-MH-1008',
          citizen_name: 'Deepak Raghunath Jagtap',
          service_type: 'ADDRESS_CHANGE',
          requested_operation: 'UPDATE_REVENUE_ADDRESS',
          priority: 'NORMAL',
          status: 'VERIFIED',
          required_action: 'Application verified & approved by Revenue Officer.',
          received_at: new Date().toISOString(),
          taluka: 'Bhor',
          district: 'Pune',
        },
      ],
      pagination: {
        page: 1,
        page_size: 15,
        total: 1,
        total_pages: 1,
      },
    });

    render(
      <BrowserRouter>
        <CompletedApplicationsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Completed Applications/i)).toBeInTheDocument();
      expect(screen.getByText('Deepak Raghunath Jagtap')).toBeInTheDocument();
      expect(screen.getByText('GM-2026-000131')).toBeInTheDocument();
      expect(screen.getByText(/VERIFIED \(FINAL\)/i)).toBeInTheDocument();
    });
  });

  it('renders RejectedApplicationsPage displaying statutory rejection reason', async () => {
    vi.spyOn(apiService, 'getRejectedApplications').mockResolvedValue({
      items: [
        {
          id: 'APP-129',
          application_id: 'GM-2026-000129',
          correlation_id: 'CORR-2026-000129',
          citizen_reference_id: 'CIT-MH-1006',
          citizen_name: 'Suresh Babanrao Kadam',
          service_type: 'ADDRESS_CHANGE',
          requested_operation: 'UPDATE_REVENUE_ADDRESS',
          priority: 'NORMAL',
          status: 'REJECTED',
          required_action: 'Application rejected. Reason: Mismatched Taluka documentation on utility bill.',
          received_at: new Date().toISOString(),
          taluka: 'Baramati',
          district: 'Pune',
        },
      ],
      pagination: {
        page: 1,
        page_size: 15,
        total: 1,
        total_pages: 1,
      },
    });

    render(
      <BrowserRouter>
        <RejectedApplicationsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Rejected Applications/i)).toBeInTheDocument();
      expect(screen.getByText('Suresh Babanrao Kadam')).toBeInTheDocument();
      expect(screen.getByText(/Mismatched Taluka documentation/i)).toBeInTheDocument();
      expect(screen.getByText(/REJECTED \(FINAL\)/i)).toBeInTheDocument();
    });
  });

  it('renders ActionRequiredPage and triggers quick reprocess', async () => {
    vi.spyOn(apiService, 'getActionRequiredApplications').mockResolvedValue({
      items: [
        {
          id: 'APP-128',
          application_id: 'GM-2026-000128',
          correlation_id: 'CORR-2026-000128',
          citizen_reference_id: 'CIT-MH-1005',
          citizen_name: 'Pooja Nitin Deshmukh',
          service_type: 'ADDRESS_CHANGE',
          requested_operation: 'UPDATE_REVENUE_ADDRESS',
          priority: 'NORMAL',
          status: 'ACTION_REQUIRED',
          required_action: 'Citizen Information Required [NEW_DOCUMENT]: Please upload proof document.',
          received_at: new Date().toISOString(),
          taluka: 'Daund',
          district: 'Pune',
        },
      ],
      pagination: {
        page: 1,
        page_size: 15,
        total: 1,
        total_pages: 1,
      },
    });

    vi.spyOn(apiService, 'reprocessApplication').mockResolvedValue({
      applicationId: 'GM-2026-000128',
      status: 'PROCESSING',
      department: 'REVENUE',
      action: 'REPROCESSED',
      changedBy: 'revenue.officer',
      timestamp: new Date().toISOString(),
    });

    render(
      <BrowserRouter>
        <ActionRequiredPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Action Required Queue/i)).toBeInTheDocument();
      expect(screen.getByText('Pooja Nitin Deshmukh')).toBeInTheDocument();
      expect(screen.getByText('NEW_DOCUMENT')).toBeInTheDocument();
    });

    const reprocessBtn = screen.getByRole('button', { name: /reprocess/i });
    fireEvent.click(reprocessBtn);

    await waitFor(() => {
      expect(apiService.reprocessApplication).toHaveBeenCalledWith('GM-2026-000128');
    });
  });
});
