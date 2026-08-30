import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import { apiService } from '../services/api';

describe('Frontend Authentication & RBAC Suite', () => {
  it('renders login form with identifier and password inputs', () => {
    render(<App />);
    expect(screen.getByPlaceholderText(/e\.g\. revenue\.officer/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Enter password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In to Department Portal/i })).toBeInTheDocument();
  });

  it('renders quick demo login buttons for all four roles', () => {
    render(<App />);
    expect(screen.getByText('Revenue Officer')).toBeInTheDocument();
    expect(screen.getByText('Senior Officer')).toBeInTheDocument();
    expect(screen.getByText('Administrator')).toBeInTheDocument();
    expect(screen.getByText('Read-only Auditor')).toBeInTheDocument();
  });

  it('handles successful demo login flow', async () => {
    // Mock login in apiService
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
    });
  });
});
