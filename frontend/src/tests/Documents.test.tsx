import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DocumentPreviewModal } from '../components/documents/DocumentPreviewModal';
import { DocumentVerificationDesk } from '../components/documents/DocumentVerificationDesk';
import { ProofDocumentMetadata } from '../types/application';

// Mock API service
vi.mock('../services/api', () => ({
  apiService: {
    getDocumentPreviewUrl: (docId: string) => `http://localhost:8000/api/v1/revenue/document/${docId}/preview`,
    verifyDocumentById: vi.fn(),
    uploadDocument: vi.fn(),
    overrideDocumentVerification: vi.fn(),
  },
}));

describe('Phase 06 — Document Verification UI Components', () => {
  const mockDocument: ProofDocumentMetadata = {
    document_id: 'DOC-REV-9081',
    application_id: 'GM-2026-000124',
    document_name: 'Pune_Electricity_Bill_2026.pdf',
    document_type: 'ELECTRICITY_BILL',
    mime_type: 'application/pdf',
    file_size: '1.2 MB',
    upload_date: '2026-08-30',
    verification_status: 'VALIDATED',
    extracted_name: 'Rajesh Shantaram Patil',
    extracted_address: 'Flat 402, Shivshankar Heights, Karve Road, Kothrud, Taluka: Haveli, Dist: Pune - 411038',
    verification_result: {
      document_id: 'DOC-REV-9081',
      document_name: 'Pune_Electricity_Bill_2026.pdf',
      document_type: 'ELECTRICITY_BILL',
      valid: true,
      match_status: 'VALIDATED',
      name_match: 'MATCH',
      address_match: 'MATCH',
      assistive_score: 1.0,
      matched_components_count: 7,
      total_components_count: 7,
      field_confidences: {
        overall: 0.95,
        name: 0.97,
        address: 0.93,
        taluka: 0.96,
        pincode: 0.99,
      },
      component_matches: {
        house_no: { result: 'MATCH', score: 1.0, requested: 'Flat 402', extracted: 'Flat 402' },
        street: { result: 'MATCH', score: 1.0, requested: 'Karve Road', extracted: 'Karve Road' },
        village: { result: 'MATCH', score: 1.0, requested: 'Kothrud', extracted: 'Kothrud' },
        taluka: { result: 'MATCH', score: 1.0, requested: 'Haveli', extracted: 'Haveli' },
        district: { result: 'MATCH', score: 1.0, requested: 'Pune', extracted: 'Pune' },
        pincode: { result: 'MATCH', score: 1.0, requested: '411038', extracted: '411038' },
      },
      explanation: 'Simulated AI/OCR verification passed: Citizen name, Taluka jurisdiction, and address components match municipal proof document.',
      extracted_fields: {
        extracted_name: 'Rajesh Shantaram Patil',
        extracted_address: 'Flat 402, Shivshankar Heights, Karve Road, Kothrud, Taluka: Haveli, Dist: Pune - 411038',
        document_type: 'ELECTRICITY_BILL',
        document_reference: 'DOC-REV-9081',
      },
      is_simulated_ocr: true,
    },
  };

  it('renders DocumentPreviewModal with zoom and rotation controls', () => {
    const handleClose = vi.fn();
    render(
      <DocumentPreviewModal
        isOpen={true}
        onClose={handleClose}
        documentId="DOC-REV-9081"
        documentName="Pune_Electricity_Bill_2026.pdf"
        documentType="ELECTRICITY_BILL"
        fileSize="1.2 MB"
      />
    );

    expect(screen.getByText('Pune_Electricity_Bill_2026.pdf')).toBeDefined();
    expect(screen.getByText('DOC-REV-9081')).toBeDefined();
    expect(screen.getByText('100%')).toBeDefined();

    // Zoom In
    const zoomInBtn = screen.getByLabelText('Zoom In');
    fireEvent.click(zoomInBtn);
    expect(screen.getByText('125%')).toBeDefined();

    // Close button
    const closeBtn = screen.getByLabelText('Close modal');
    fireEvent.click(closeBtn);
    expect(handleClose).toHaveBeenCalled();
  });

  it('renders DocumentVerificationDesk side-by-side comparison with confidence scores', () => {
    render(
      <DocumentVerificationDesk
        applicationId="GM-2026-000124"
        citizenName="Rajesh Shantaram Patil"
        requestedAddress={{
          house_no: 'Flat 402',
          street: 'Karve Road',
          village: 'Kothrud',
          taluka: 'Haveli',
          district: 'Pune',
          pincode: '411038',
        }}
        documents={[mockDocument]}
        isFinalized={false}
        canVerify={true}
        onRefresh={vi.fn()}
        onShowToast={vi.fn()}
      />
    );

    // Verify Title & Badges
    expect(screen.getByText(/Advanced Document Verification/i)).toBeDefined();
    expect(screen.getByText('VALIDATED')).toBeDefined();
    expect(screen.getByText(/Assistive Score:/i)).toBeDefined();
    expect(screen.getByText('100%')).toBeDefined();

    // Field-level confidence scores
    expect(screen.getByText('97%')).toBeDefined();
    expect(screen.getByText('93%')).toBeDefined();
    expect(screen.getByText('96%')).toBeDefined();
    expect(screen.getByText('99%')).toBeDefined();

    // 6-part address table elements
    expect(screen.getAllByText('Citizen Name').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Taluka / Tehsil')).toBeDefined();
    expect(screen.getByText('Postal PIN Code')).toBeDefined();
  });

  it('renders empty state when no documents are attached', () => {
    render(
      <DocumentVerificationDesk
        applicationId="GM-2026-000128"
        citizenName="Sunita Vilas Jadhav"
        requestedAddress={{}}
        documents={[]}
        isFinalized={false}
        canVerify={true}
        onRefresh={vi.fn()}
        onShowToast={vi.fn()}
      />
    );

    expect(screen.getByText('No Proof Document Attached')).toBeDefined();
    expect(screen.getByText(/Upload Supporting Proof Now/i)).toBeDefined();
  });

  it('opens manual override modal and handles officer justification', () => {
    render(
      <DocumentVerificationDesk
        applicationId="GM-2026-000124"
        citizenName="Rajesh Shantaram Patil"
        requestedAddress={{}}
        documents={[mockDocument]}
        isFinalized={false}
        canVerify={true}
        onRefresh={vi.fn()}
        onShowToast={vi.fn()}
      />
    );

    // Open Manual Override Dialog
    const overrideBtn = screen.getByText('Manual Override');
    fireEvent.click(overrideBtn);

    expect(screen.getByText(/Officer Manual Override/i)).toBeDefined();
    expect(screen.getByPlaceholderText(/Officer verified physical electricity bill copy/i)).toBeDefined();
  });
});
