import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import { apiService } from '../services/api';

describe('Phase 12: End-to-End & Failure Simulation UI Tests', () => {
  it('renders application verification desk with operational controls after officer login', async () => {
    vi.spyOn(apiService, 'login').mockResolvedValueOnce({
      access_token: 'mock-jwt-token-12345',
      token_type: 'bearer',
      expires_in: 1800,
      user: {
        id: 'USR-REV-001',
        username: 'revenue.officer',
        email: 'officer.pune@revenue.gov.in',
        mobile: '9820011223',
        full_name: 'Rajendra Mane (Revenue Officer)',
        role: 'REVENUE_OFFICER',
        department: 'Revenue & Forest Department',
        division: 'Pune Division',
        is_active: true,
        created_at: new Date().toISOString(),
      },
      permissions: ['APPLICATION_VIEW_ASSIGNED', 'DOCUMENT_VERIFY', 'APPLICATION_APPROVE'],
    });

    render(<App />);
    const officerBtn = screen.getByText('Revenue Officer');
    fireEvent.click(officerBtn);

    await waitFor(() => {
      expect(screen.getByText(/Departmental Officer Dashboard/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('handles API error states gracefully on dashboard without application crash', async () => {
    vi.spyOn(apiService, 'login').mockResolvedValueOnce({
      access_token: 'mock-jwt-token-12345',
      token_type: 'bearer',
      expires_in: 1800,
      user: {
        id: 'USR-REV-001',
        username: 'revenue.officer',
        email: 'officer.pune@revenue.gov.in',
        mobile: '9820011223',
        full_name: 'Rajendra Mane (Revenue Officer)',
        role: 'REVENUE_OFFICER',
        department: 'Revenue & Forest Department',
        division: 'Pune Division',
        is_active: true,
        created_at: new Date().toISOString(),
      },
      permissions: ['APPLICATION_VIEW_ASSIGNED', 'DOCUMENT_VERIFY', 'APPLICATION_APPROVE'],
    });
    vi.spyOn(apiService, 'getDashboardSummary').mockRejectedValueOnce(new Error('500 Internal Server Error'));
    vi.spyOn(apiService, 'getFullDashboardAnalytics').mockRejectedValueOnce(new Error('503 Service Unavailable'));

    render(<App />);
    const officerBtn = screen.getByText('Revenue Officer');
    fireEvent.click(officerBtn);

    await waitFor(() => {
      expect(screen.getByText(/Departmental Officer Dashboard/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('displays statutory AI/OCR disclaimer banner on officer dashboard', async () => {
    vi.spyOn(apiService, 'login').mockResolvedValueOnce({
      access_token: 'mock-jwt-token-12345',
      token_type: 'bearer',
      expires_in: 1800,
      user: {
        id: 'USR-REV-001',
        username: 'revenue.officer',
        email: 'officer.pune@revenue.gov.in',
        mobile: '9820011223',
        full_name: 'Rajendra Mane (Revenue Officer)',
        role: 'REVENUE_OFFICER',
        department: 'Revenue & Forest Department',
        division: 'Pune Division',
        is_active: true,
        created_at: new Date().toISOString(),
      },
      permissions: ['APPLICATION_VIEW_ASSIGNED', 'DOCUMENT_VERIFY', 'APPLICATION_APPROVE'],
    });

    render(<App />);
    const officerBtn = screen.getByText('Revenue Officer');
    fireEvent.click(officerBtn);

    await waitFor(() => {
      expect(screen.getByText(/AI\/OCR metrics are assistive evidence analytics/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});
