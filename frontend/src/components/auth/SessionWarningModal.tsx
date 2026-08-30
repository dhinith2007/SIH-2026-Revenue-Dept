import React from 'react';
import { AlertTriangle, Clock, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const SessionWarningModal: React.FC = () => {
  const { sessionWarning, dismissWarning, logout } = useAuth();

  if (!sessionWarning) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 animate-fade-in">
      <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-2xl border-2 border-amber-400">
        <div className="flex items-center gap-3 text-amber-700 pb-3 border-b border-slate-100">
          <div className="p-2.5 bg-amber-100 rounded-full">
            <AlertTriangle className="w-6 h-6 text-amber-600" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Session Inactivity Warning</h3>
            <span className="text-xs text-amber-800 font-medium">Departmental Security Policy</span>
          </div>
        </div>

        <p className="text-xs text-slate-600 mt-4 leading-relaxed">
          You have been inactive for over 25 minutes. To protect sensitive revenue records, your session will automatically terminate in <strong>5 minutes</strong> unless you confirm your presence.
        </p>

        <div className="mt-6 flex flex-col sm:flex-row gap-2.5">
          <button
            onClick={dismissWarning}
            className="flex-1 py-2.5 bg-gov-navy hover:bg-gov-navy-light text-white text-xs font-bold rounded shadow-sm flex items-center justify-center gap-2 transition-colors"
          >
            <Clock className="w-4 h-4 text-gov-gold" />
            <span>Stay Signed In (Extend Session)</span>
          </button>
          <button
            onClick={logout}
            className="py-2.5 px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded border border-slate-300 flex items-center justify-center gap-1.5 transition-colors"
          >
            <LogOut className="w-4 h-4 text-slate-500" />
            <span>Log Out</span>
          </button>
        </div>
      </div>
    </div>
  );
};
