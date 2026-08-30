import React, { useState } from 'react';
import { Lock, ShieldCheck, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface ReauthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  actionTitle: string;
  actionDescription?: string;
}

export const ReauthModal: React.FC<ReauthModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
  actionTitle,
  actionDescription,
}) => {
  const { reauthenticate, user } = useAuth();
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) {
      setError('Please enter your password.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const ok = await reauthenticate(password);
      if (ok) {
        setPassword('');
        onSuccess();
        onClose();
      }
    } catch (err: any) {
      setError(err?.message || 'Password confirmation failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 animate-fade-in">
      <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
        <div className="flex items-start justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2.5 text-gov-navy">
            <div className="p-2 bg-gov-navy/10 rounded-lg">
              <ShieldCheck className="w-5 h-5 text-gov-navy" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Security Verification Required</h3>
              <p className="text-[11px] text-slate-500 font-medium">Re-authentication for Sensitive Action</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 font-bold text-sm p-1"
          >
            ✕
          </button>
        </div>

        <div className="my-4 p-3 bg-amber-50 border border-amber-200 rounded text-xs text-amber-900">
          <strong className="block font-bold mb-0.5">{actionTitle}</strong>
          <span className="text-[11px] text-amber-800">
            {actionDescription ||
              'Departmental security policy requires password verification before completing this operation.'}
          </span>
        </div>

        {error && (
          <div className="mb-4 p-2.5 bg-rose-50 border border-rose-200 rounded text-rose-800 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-600" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
              Officer Account: <strong>{user?.full_name}</strong>
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                <Lock className="w-4 h-4" />
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter current password to confirm"
                className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-gov-navy focus:border-gov-navy outline-none"
                autoFocus
              />
            </div>
          </div>

          <div className="flex gap-2 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-2.5 bg-gov-navy hover:bg-gov-navy-light text-white text-xs font-bold rounded shadow-sm transition-colors"
            >
              {loading ? 'Verifying...' : 'Confirm & Proceed'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded border border-slate-300"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
