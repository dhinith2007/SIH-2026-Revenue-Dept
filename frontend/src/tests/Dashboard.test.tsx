import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import { apiService } from '../services/api';

describe('Phase 11: Revenue Department Dashboard & Analytics UI', () => {
  it('renders full dashboard analytics with statutory disclaimer and KPI cards after login', async () => {
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
      // Statutory AI/OCR Disclaimer
      expect(screen.getByText(/Statutory AI\/OCR Analytics Disclaimer/i)).toBeInTheDocument();
      expect(screen.getByText(/AI\/OCR metrics are assistive evidence analytics/i)).toBeInTheDocument();

      // Dashboard Header & Operational Cards
      expect(screen.getByText(/Departmental Officer Dashboard/i)).toBeInTheDocument();
      expect(screen.getByText(/Server-Side Analytics Filters/i)).toBeInTheDocument();
      expect(screen.getByText(/Document Verification & Local OCR Performance Analytics/i)).toBeInTheDocument();
      expect(screen.getByText(/AI Confidence & Recommendation Bands/i)).toBeInTheDocument();
      expect(screen.getByText(/Operational Officer Workload Distribution/i)).toBeInTheDocument();
    });
  });
});
