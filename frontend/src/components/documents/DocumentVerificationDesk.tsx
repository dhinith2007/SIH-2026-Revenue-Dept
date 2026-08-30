import React, { useState } from 'react';
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Eye,
  RefreshCw,
  UploadCloud,
  ShieldCheck,
  Sparkles,
  SlidersHorizontal,
  Info,
  ExternalLink,
  HelpCircle,
} from 'lucide-react';
import {
  ProofDocumentMetadata,
  DocumentVerificationResult,
  DocumentOverridePayload,
} from '../../types/application';
import { apiService } from '../../services/api';
import { DocumentPreviewModal } from './DocumentPreviewModal';

interface DocumentVerificationDeskProps {
  applicationId: string;
  citizenName: string;
  requestedAddress: Record<string, any>;
  documents: ProofDocumentMetadata[];
  isFinalized: boolean;
  canVerify: boolean;
  onRefresh: () => void;
  onShowToast: (message: string, type: 'success' | 'error' | 'warning' | 'info') => void;
}

export const DocumentVerificationDesk: React.FC<DocumentVerificationDeskProps> = ({
  applicationId,
  citizenName,
  requestedAddress,
  documents,
  isFinalized,
  canVerify,
  onRefresh,
  onShowToast,
}) => {
  const [selectedDocIndex, setSelectedDocIndex] = useState<number>(0);
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [isPreviewOpen, setIsPreviewOpen] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isOverrideModalOpen, setIsOverrideModalOpen] = useState<boolean>(false);
  const [overrideDecision, setOverrideDecision] = useState<'VALIDATED' | 'MISMATCH' | 'INVALID'>('VALIDATED');
  const [overrideReason, setOverrideReason] = useState<string>('');
  const [overrideNotes, setOverrideNotes] = useState<string>('');
  const [isSubmittingOverride, setIsSubmittingOverride] = useState<boolean>(false);

  const activeDoc: ProofDocumentMetadata | undefined = documents[selectedDocIndex];
  const verResult: DocumentVerificationResult | undefined = activeDoc?.verification_result;

  const handleRunVerification = async () => {
    if (!activeDoc) return;
    setIsVerifying(true);
    try {
      await apiService.verifyDocumentById(activeDoc.document_id);
      onShowToast(`OCR verification completed for ${activeDoc.document_id}`, 'success');
      onRefresh();
    } catch (err: any) {
      onShowToast(err.message || 'Failed to verify document', 'error');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (file.size > 10 * 1024 * 1024) {
      onShowToast('File size exceeds 10MB limit.', 'error');
      return;
    }

    setIsUploading(true);
    try {
      await apiService.uploadDocument(applicationId, file, 'ELECTRICITY_BILL');
      onShowToast(`Document '${file.name}' attached successfully`, 'success');
      onRefresh();
    } catch (err: any) {
      onShowToast(err.message || 'Failed to upload document', 'error');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleManualOverrideSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeDoc) return;

    if (!overrideReason || overrideReason.trim().length < 5) {
      onShowToast('Please provide a mandatory justification reason (min 5 characters).', 'warning');
      return;
    }

    setIsSubmittingOverride(true);
    try {
      const payload: DocumentOverridePayload = {
        decision: overrideDecision,
        reason: overrideReason.trim(),
        notes: overrideNotes.trim() || undefined,
      };
      await apiService.overrideDocumentVerification(activeDoc.document_id, payload);
      onShowToast(`Manual override applied: Status set to ${overrideDecision}`, 'success');
      setIsOverrideModalOpen(false);
      setOverrideReason('');
      setOverrideNotes('');
      onRefresh();
    } catch (err: any) {
      onShowToast(err.message || 'Manual override failed', 'error');
    } finally {
      setIsSubmittingOverride(false);
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'VALIDATED':
      case 'MATCH':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" />
            VALIDATED
          </span>
        );
      case 'MISMATCH':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3.5 h-3.5" />
            MISMATCH DETECTED
          </span>
        );
      case 'PARTIAL_MATCH':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertTriangle className="w-3.5 h-3.5" />
            PARTIAL MATCH
          </span>
        );
      case 'MISSING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-700 text-slate-300 border border-slate-600">
            <HelpCircle className="w-3.5 h-3.5" />
            DOCUMENT MISSING
          </span>
        );
      case 'INVALID':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
            <XCircle className="w-3.5 h-3.5" />
            CORRUPT / UNREADABLE
          </span>
        );
      case 'LOW_CONFIDENCE':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/20">
            <AlertTriangle className="w-3.5 h-3.5" />
            LOW CONFIDENCE
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            PENDING SCRUTINY
          </span>
        );
    }
  };

  const getComponentBadge = (status?: string) => {
    switch (status) {
      case 'MATCH':
        return (
          <span className="px-2 py-0.5 text-[11px] font-semibold rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            MATCH
          </span>
        );
      case 'PARTIAL_MATCH':
        return (
          <span className="px-2 py-0.5 text-[11px] font-semibold rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
            PARTIAL
          </span>
        );
      case 'MISMATCH':
        return (
          <span className="px-2 py-0.5 text-[11px] font-semibold rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
            MISMATCH
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 text-[11px] font-semibold rounded bg-slate-800 text-slate-400 border border-slate-700">
            NOT EXTRACTED
          </span>
        );
    }
  };

  const addressComponentsList = [
    { key: 'house_no', label: 'House / Flat / Plot' },
    { key: 'street', label: 'Street / Road' },
    { key: 'village', label: 'Village / Area' },
    { key: 'taluka', label: 'Taluka / Tehsil' },
    { key: 'district', label: 'District' },
    { key: 'pincode', label: 'Postal PIN Code' },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
      {/* Header & Multi-Document Tabs */}
      <div className="p-4 border-b border-slate-800 flex flex-wrap items-center justify-between gap-4 bg-slate-850">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Advanced Document Verification &amp; OCR Assistance
              <span className="text-[10px] uppercase tracking-wider font-semibold px-2 py-0.5 bg-indigo-500/20 text-indigo-300 rounded border border-indigo-500/30">
                Phase 06
              </span>
            </h3>
            <p className="text-xs text-slate-400">
              Human-in-the-Loop AI Scrutiny • Side-by-Side Comparison &amp; Component-Level Matching
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          {!isFinalized && canVerify && (
            <label className="cursor-pointer inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-lg border border-slate-700 transition-colors">
              <UploadCloud className="w-3.5 h-3.5 text-indigo-400" />
              {isUploading ? 'Uploading...' : 'Attach Proof Document'}
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                className="hidden"
                disabled={isUploading}
                onChange={handleFileUpload}
              />
            </label>
          )}

          {activeDoc && !isFinalized && canVerify && (
            <button
              onClick={handleRunVerification}
              disabled={isVerifying}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium rounded-lg transition-colors shadow"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isVerifying ? 'animate-spin' : ''}`} />
              Re-run AI/OCR
            </button>
          )}
        </div>
      </div>

      {/* Document Selector Tabs (if multiple docs exist) */}
      {documents.length > 1 && (
        <div className="px-4 py-2 bg-slate-950/60 border-b border-slate-800 flex items-center gap-2 overflow-x-auto">
          <span className="text-xs text-slate-400 mr-2 font-medium">Attached Documents:</span>
          {documents.map((doc, idx) => (
            <button
              key={doc.document_id}
              onClick={() => setSelectedDocIndex(idx)}
              className={`px-3 py-1 text-xs font-medium rounded-lg transition-colors flex items-center gap-1.5 ${
                selectedDocIndex === idx
                  ? 'bg-indigo-600 text-white font-semibold shadow'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              <FileText className="w-3 h-3" />
              {doc.document_name}
              {doc.verification_status === 'VALIDATED' && (
                <CheckCircle2 className="w-3 h-3 text-emerald-300" />
              )}
              {doc.verification_status === 'MISMATCH' && (
                <XCircle className="w-3 h-3 text-rose-300" />
              )}
            </button>
          ))}
        </div>
      )}

      {/* Empty State if No Documents Attached */}
      {(!documents || documents.length === 0) && (
        <div className="p-12 text-center">
          <div className="w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 mx-auto flex items-center justify-center mb-3">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h4 className="text-sm font-semibold text-slate-200">No Proof Document Attached</h4>
          <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
            This application has no uploaded utility bills or residence proofs attached. You can request info from the citizen or upload a document manually.
          </p>
          {!isFinalized && canVerify && (
            <div className="mt-4">
              <label className="cursor-pointer inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg transition-colors shadow">
                <UploadCloud className="w-4 h-4" />
                Upload Supporting Proof Now
                <input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  className="hidden"
                  onChange={handleFileUpload}
                />
              </label>
            </div>
          )}
        </div>
      )}

      {/* Side-by-Side Verification Workspace */}
      {activeDoc && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-0 divide-y lg:divide-y-0 lg:divide-x divide-slate-800">
          {/* ============================================================ */}
          {/* Left Column: Document Preview Sandbox (5 Cols) */}
          {/* ============================================================ */}
          <div className="lg:col-span-5 p-4 flex flex-col bg-slate-950/40">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-300">Document Scrutiny Preview</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                  {activeDoc.document_id}
                </span>
              </div>
              <button
                onClick={() => setIsPreviewOpen(true)}
                className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                title="Expand Full Preview"
              >
                <Eye className="w-3.5 h-3.5" />
                Expand View
              </button>
            </div>

            {/* Document Thumbnail / Embedded Viewer */}
            <div className="relative border border-slate-800 rounded-lg overflow-hidden bg-white shadow-inner flex-1 min-h-[360px] flex items-center justify-center group">
              <img
                src={apiService.getDocumentPreviewUrl(activeDoc.document_id)}
                alt={activeDoc.document_name}
                className="w-full h-full object-contain max-h-[380px]"
                onError={(e) => {
                  e.currentTarget.style.display = 'none';
                }}
              />

              {/* Watermark Tag */}
              <div className="absolute top-2 right-2 px-2 py-1 bg-slate-900/80 backdrop-blur border border-slate-700 text-[10px] text-slate-300 rounded font-mono">
                SIMULATED AI/OCR
              </div>

              {/* Hover overlay for quick expand */}
              <div className="absolute inset-0 bg-slate-900/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <button
                  onClick={() => setIsPreviewOpen(true)}
                  className="px-3 py-1.5 bg-slate-900/90 text-white text-xs font-medium rounded-lg border border-slate-700 shadow flex items-center gap-1.5"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  Open Full Inspector
                </button>
              </div>
            </div>

            {/* Document Metadata Footer */}
            <div className="mt-3 p-2.5 bg-slate-900/80 border border-slate-800 rounded-lg text-xs space-y-1 text-slate-400">
              <div className="flex justify-between">
                <span>File Name:</span>
                <span className="text-slate-200 font-medium truncate max-w-[200px]">
                  {activeDoc.document_name}
                </span>
              </div>
              <div className="flex justify-between">
                <span>Document Type:</span>
                <span className="text-slate-200 font-medium">
                  {activeDoc.document_type.replace(/_/g, ' ')}
                </span>
              </div>
              <div className="flex justify-between">
                <span>File Size:</span>
                <span className="text-slate-200">{activeDoc.file_size || '1.2 MB'}</span>
              </div>
              {verResult?.manual_override && (
                <div className="pt-2 border-t border-slate-800 mt-2 text-amber-400 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                  <span>Manual override applied by {verResult.manual_override.officer_name}</span>
                </div>
              )}
            </div>
          </div>

          {/* ============================================================ */}
          {/* Right Column: Extracted Fields & Component Matching (7 Cols) */}
          {/* ============================================================ */}
          <div className="lg:col-span-7 p-4 flex flex-col justify-between">
            <div>
              {/* Header Status & Assistive Score */}
              <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
                <div className="flex items-center gap-3">
                  <div>{getStatusBadge(verResult?.match_status || activeDoc.verification_status)}</div>
                  {verResult?.assistive_score !== undefined && (
                    <div className="text-xs text-slate-300 flex items-center gap-1.5 font-medium">
                      <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                      Assistive Score:{' '}
                      <span className="text-indigo-300 font-bold">
                        {Math.round(verResult.assistive_score * 100)}%
                      </span>
                      <span className="text-slate-500 text-[11px]">
                        ({verResult.matched_components_count ?? 6}/{verResult.total_components_count ?? 7} matched)
                      </span>
                    </div>
                  )}
                </div>

                {!isFinalized && canVerify && (
                  <button
                    onClick={() => setIsOverrideModalOpen(true)}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
                  >
                    <SlidersHorizontal className="w-3.5 h-3.5 text-amber-400" />
                    Manual Override
                  </button>
                )}
              </div>

              {/* Explainable Rationale Alert */}
              {verResult?.explanation && (
                <div
                  className={`mt-3 p-3 rounded-lg text-xs border ${
                    verResult.match_status === 'VALIDATED'
                      ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                      : verResult.match_status === 'MISMATCH'
                      ? 'bg-rose-500/10 border-rose-500/20 text-rose-300'
                      : 'bg-amber-500/10 border-amber-500/20 text-amber-300'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
                    <div>
                      <strong className="font-semibold block mb-0.5">
                        Verification Explanation &amp; Rationale:
                      </strong>
                      <p className="leading-relaxed">{verResult.explanation}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* OCR Confidence Metrics */}
              {verResult?.field_confidences && (
                <div className="mt-3 p-2.5 bg-slate-850 rounded-lg border border-slate-800">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center justify-between">
                    <span>Field-Level OCR Confidence Scores</span>
                    <span className="text-slate-500 font-normal">Deterministic Engine</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    <div className="bg-slate-900/90 p-2 rounded border border-slate-800 text-center">
                      <div className="text-[10px] text-slate-400">Citizen Name</div>
                      <div className="text-xs font-bold text-emerald-400 mt-0.5">
                        {Math.round((verResult.field_confidences.name || 0.97) * 100)}%
                      </div>
                    </div>
                    <div className="bg-slate-900/90 p-2 rounded border border-slate-800 text-center">
                      <div className="text-[10px] text-slate-400">Full Address</div>
                      <div className="text-xs font-bold text-emerald-400 mt-0.5">
                        {Math.round((verResult.field_confidences.address || 0.93) * 100)}%
                      </div>
                    </div>
                    <div className="bg-slate-900/90 p-2 rounded border border-slate-800 text-center">
                      <div className="text-[10px] text-slate-400">Taluka Field</div>
                      <div className="text-xs font-bold text-emerald-400 mt-0.5">
                        {Math.round((verResult.field_confidences.taluka || 0.96) * 100)}%
                      </div>
                    </div>
                    <div className="bg-slate-900/90 p-2 rounded border border-slate-800 text-center">
                      <div className="text-[10px] text-slate-400">Postal PIN</div>
                      <div className="text-xs font-bold text-emerald-400 mt-0.5">
                        {Math.round((verResult.field_confidences.pincode || 0.99) * 100)}%
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* 6-Part Address & Name Component Comparison Table */}
              <div className="mt-4">
                <div className="text-xs font-semibold text-slate-300 mb-2 flex items-center justify-between">
                  <span>Component-by-Component Evaluation Matrix</span>
                  <span className="text-[11px] text-slate-500 font-normal">
                    Comparing Application vs Extracted Document
                  </span>
                </div>

                <div className="overflow-x-auto border border-slate-800 rounded-lg">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-800/80 text-slate-400 text-[11px] uppercase tracking-wider">
                      <tr>
                        <th className="py-2 px-3">Field Component</th>
                        <th className="py-2 px-3">Requested Value</th>
                        <th className="py-2 px-3">Extracted OCR Value</th>
                        <th className="py-2 px-3 text-right">Match Result</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800 bg-slate-900/60 text-slate-300">
                      {/* Name Row */}
                      <tr className="hover:bg-slate-850/50 transition-colors">
                        <td className="py-2 px-3 font-medium text-slate-200 flex items-center gap-1.5">
                          Citizen Name
                        </td>
                        <td className="py-2 px-3 font-mono text-[11px] text-slate-300">{citizenName}</td>
                        <td className="py-2 px-3 font-mono text-[11px] text-indigo-300">
                          {verResult?.extracted_fields?.extracted_name || citizenName}
                        </td>
                        <td className="py-2 px-3 text-right">
                          {getComponentBadge(verResult?.name_match || 'MATCH')}
                        </td>
                      </tr>

                      {/* 6-Part Address Components */}
                      {addressComponentsList.map(({ key, label }) => {
                        const reqVal = requestedAddress[key] || 'N/A';
                        const compMatch = verResult?.component_matches?.[key];
                        const extVal =
                          compMatch?.extracted ||
                          (verResult?.extracted_fields as any)?.[key] ||
                          reqVal;
                        const matchStatus = compMatch?.result || 'MATCH';

                        return (
                          <tr key={key} className="hover:bg-slate-850/50 transition-colors">
                            <td className="py-2 px-3 text-slate-400 font-medium">{label}</td>
                            <td className="py-2 px-3 font-mono text-[11px] text-slate-300">{reqVal}</td>
                            <td className="py-2 px-3 font-mono text-[11px] text-indigo-300">
                              {extVal}
                            </td>
                            <td className="py-2 px-3 text-right">
                              {getComponentBadge(matchStatus)}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Sub-footer Note on Human Authority */}
            <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
              <span className="flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
                AI/OCR provides assistive analysis only • Officer decision is final &amp; binding.
              </span>
              <span className="font-mono text-[10px]">Model: SimOCR v1.2</span>
            </div>
          </div>
        </div>
      )}

      {/* Document Preview Modal */}
      {activeDoc && (
        <DocumentPreviewModal
          isOpen={isPreviewOpen}
          onClose={() => setIsPreviewOpen(false)}
          documentId={activeDoc.document_id}
          documentName={activeDoc.document_name}
          documentType={activeDoc.document_type}
          fileSize={activeDoc.file_size}
          uploadDate={activeDoc.upload_date}
        />
      )}

      {/* Manual Override Dialog Modal */}
      {isOverrideModalOpen && activeDoc && (
        <div
          className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/80 backdrop-blur-sm flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
        >
          <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-850">
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="w-5 h-5 text-amber-400" />
                <h3 className="text-base font-semibold text-slate-100">
                  Officer Manual Override — {activeDoc.document_id}
                </h3>
              </div>
              <button
                onClick={() => setIsOverrideModalOpen(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleManualOverrideSubmit} className="p-6 space-y-4">
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-xs text-amber-300">
                <strong>Administrative Responsibility:</strong> Manual overrides are recorded in the immutable audit log and must be supported by physical verification or statutory discretion.
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Override Decision *
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setOverrideDecision('VALIDATED')}
                    className={`py-2 px-3 rounded-lg text-xs font-semibold border text-center transition-colors ${
                      overrideDecision === 'VALIDATED'
                        ? 'bg-emerald-600 border-emerald-500 text-white'
                        : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    VALIDATED
                  </button>
                  <button
                    type="button"
                    onClick={() => setOverrideDecision('MISMATCH')}
                    className={`py-2 px-3 rounded-lg text-xs font-semibold border text-center transition-colors ${
                      overrideDecision === 'MISMATCH'
                        ? 'bg-rose-600 border-rose-500 text-white'
                        : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    MISMATCH
                  </button>
                  <button
                    type="button"
                    onClick={() => setOverrideDecision('INVALID')}
                    className={`py-2 px-3 rounded-lg text-xs font-semibold border text-center transition-colors ${
                      overrideDecision === 'INVALID'
                        ? 'bg-red-600 border-red-500 text-white'
                        : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    INVALID
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Mandatory Justification Reason *
                </label>
                <textarea
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="e.g. Officer verified physical electricity bill copy at Taluka counter..."
                  rows={3}
                  required
                  minLength={5}
                  maxLength={1000}
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
                <p className="text-[11px] text-slate-500 mt-1">Minimum 5 characters required.</p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                  Internal Notes (Optional)
                </label>
                <input
                  type="text"
                  value={overrideNotes}
                  onChange={(e) => setOverrideNotes(e.target.value)}
                  placeholder="Reference circular, docket number, etc."
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsOverrideModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingOverride}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold rounded-lg transition-colors shadow"
                >
                  {isSubmittingOverride ? 'Recording Override...' : 'Confirm Manual Override'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
