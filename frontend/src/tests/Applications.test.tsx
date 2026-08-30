import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import { apiService } from '../services/api';

describe('Phase 03: Dashboard and Application Management UI', () => {
  it('renders dashboard with operational metrics after officer login', async () => {
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
      expect(screen.getByText(/Manage All Applications/i)).toBeInTheDocument();
      expect(screen.getByText(/GovMesh Channel:/i)).toBeInTheDocument();
    });
  });

  it('navigates to applications scrutiny queue and displays search and filters', async () => {
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
      expect(screen.getByText(/Manage All Applications/i)).toBeInTheDocument();
    });

    const manageBtn = screen.getByText(/Manage All Applications/i);
    fireEvent.click(manageBtn);

    await waitFor(() => {
      expect(screen.getByText(/Incoming Applications Scrutiny/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Search by Application ID/i)).toBeInTheDocument();
      expect(screen.getByText(/All Statuses/i)).toBeInTheDocument();
    });
  });
});
