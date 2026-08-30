import React, { useState } from 'react';
import { X, ZoomIn, ZoomOut, RotateCw, FileText, ShieldCheck } from 'lucide-react';
import { apiService } from '../../services/api';

interface DocumentPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: string;
  documentName: string;
  documentType: string;
  fileSize?: string;
  uploadDate?: string;
}

export const DocumentPreviewModal: React.FC<DocumentPreviewModalProps> = ({
  isOpen,
  onClose,
  documentId,
  documentName,
  documentType,
  fileSize,
  uploadDate,
}) => {
  const [zoom, setZoom] = useState<number>(100);
  const [rotation, setRotation] = useState<number>(0);

  if (!isOpen) return null;

  const previewUrl = apiService.getDocumentPreviewUrl(documentId);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 25, 200));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 25, 50));
  const handleRotate = () => setRotation((prev) => (prev + 90) % 360);

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/80 backdrop-blur-sm flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="preview-modal-title"
    >
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-5xl h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-850">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 id="preview-modal-title" className="text-base font-semibold text-slate-100 flex items-center gap-2">
                {documentName}
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono font-normal">
                  {documentId}
                </span>
              </h3>
              <p className="text-xs text-slate-400">
                {documentType.replace(/_/g, ' ')} • {fileSize || '1.2 MB'} • Uploaded: {uploadDate || 'Today'}
              </p>
            </div>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-2">
            <div className="flex items-center bg-slate-800 rounded-lg border border-slate-700 p-1 mr-2">
              <button
                onClick={handleZoomOut}
                className="p-1.5 hover:bg-slate-700 text-slate-300 rounded transition-colors"
                title="Zoom Out"
                aria-label="Zoom Out"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="text-xs font-mono px-2 text-slate-300 min-w-[3rem] text-center">
                {zoom}%
              </span>
              <button
                onClick={handleZoomIn}
                className="p-1.5 hover:bg-slate-700 text-slate-300 rounded transition-colors"
                title="Zoom In"
                aria-label="Zoom In"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
              <div className="w-px h-4 bg-slate-700 mx-1" />
              <button
                onClick={handleRotate}
                className="p-1.5 hover:bg-slate-700 text-slate-300 rounded transition-colors"
                title="Rotate Clockwise"
                aria-label="Rotate"
              >
                <RotateCw className="w-4 h-4" />
              </button>
            </div>

            <button
              onClick={onClose}
              className="p-2 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-lg transition-colors"
              aria-label="Close modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Security Banner */}
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2 flex items-center justify-between text-xs text-amber-300">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-amber-400" />
            <span>
              <strong>Secure Scrutiny Viewer:</strong> Simulated residence proof document rendered in a sandboxed read-only container.
            </span>
          </div>
          <span className="font-mono text-[10px] uppercase tracking-wider bg-amber-500/20 px-2 py-0.5 rounded text-amber-300">
            INTERNAL USE ONLY
          </span>
        </div>

        {/* Document Viewer Body */}
        <div className="flex-1 bg-slate-950 p-6 overflow-auto flex items-center justify-center relative">
          <div
            className="transition-transform duration-200 origin-center bg-white shadow-2xl rounded border border-slate-300 max-w-full"
            style={{
              transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
              width: '600px',
              minHeight: '800px',
            }}
          >
            <img
              src={previewUrl}
              alt={`Document Preview - ${documentName}`}
              className="w-full h-auto block select-none pointer-events-none"
              onError={(e) => {
                // Fallback SVG if network issue
                e.currentTarget.style.display = 'none';
              }}
            />
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-800 bg-slate-900 flex items-center justify-between text-xs text-slate-400">
          <span>Human-in-the-Loop Verification Desk • Department of Revenue & Forest</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium rounded-lg transition-colors"
          >
            Close Preview
          </button>
        </div>
      </div>
    </div>
  );
};
