import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, ArrowLeft, LogIn, Lock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const UnauthorizedPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, role, logout } = useAuth();

  const handleSwitchAccount = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="max-w-xl mx-auto py-12 px-4">
      <div className="bg-white rounded-xl border-2 border-rose-200 shadow-md p-8 text-center">
        <div className="w-16 h-16 rounded-full bg-rose-50 border-2 border-rose-200 text-rose-600 mx-auto flex items-center justify-center mb-4 shadow-sm">
          <ShieldAlert className="w-8 h-8 text-rose-600" />
        </div>

        <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-rose-50 text-rose-800 rounded-full text-xs font-bold uppercase tracking-wider mb-2 border border-rose-200">
          <Lock className="w-3.5 h-3.5" />
          <span>HTTP 403 • Access Restricted</span>
        </div>

        <h2 className="text-2xl font-extrabold text-slate-900 mt-2">
          Insufficient Department Permissions
        </h2>

        <p className="text-xs sm:text-sm text-slate-600 max-w-md mx-auto mt-3 leading-relaxed">
          Your active departmental officer credentials do not possess the role permissions required to inspect or modify this resource.
        </p>

        {user && (
          <div className="mt-6 bg-slate-50 border border-slate-200 rounded-lg p-4 text-xs text-left max-w-sm mx-auto space-y-1.5">
            <div className="flex justify-between">
              <span className="text-slate-500">Active Officer:</span>
              <strong className="text-slate-900">{user.full_name}</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Current Role:</span>
              <span className="font-bold text-gov-navy bg-gov-gold-pale/50 px-2 py-0.5 rounded border border-amber-200">
                {role?.replace(/_/g, ' ')}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Jurisdiction:</span>
              <span className="text-slate-700">{user.division}</span>
            </div>
          </div>
        )}

        <div className="mt-8 flex flex-col sm:flex-row justify-center gap-3">
          <button
            onClick={() => navigate('/dashboard')}
            className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 bg-gov-navy hover:bg-gov-navy-light text-white text-xs font-bold rounded shadow-sm transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Dashboard</span>
          </button>

          <button
            onClick={handleSwitchAccount}
            className="inline-flex items-center justify-center gap-1.5 px-4 py-2.5 border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold rounded shadow-sm transition-colors"
          >
            <LogIn className="w-3.5 h-3.5 text-gov-gold" />
            <span>Switch Officer Role</span>
          </button>
        </div>
      </div>
    </div>
  );
};
