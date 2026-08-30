import React, { useState } from 'react';
import {
  User,
  Shield,
  Building,
  Mail,
  Phone,
  KeyRound,
  CheckCircle2,
  LogOut,
  Lock,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { ReauthModal } from '../components/auth/ReauthModal';

export const ProfilePage: React.FC = () => {
  const { user, role, permissions, logout } = useAuth();
  const [isReauthOpen, setIsReauthOpen] = useState(false);
  const [testSuccess, setTestSuccess] = useState(false);

  const handleTestReauthSuccess = () => {
    setTestSuccess(true);
    setTimeout(() => setTestSuccess(false), 5000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-200">
        <div>
          <div className="text-xs font-semibold text-gov-gold-dark uppercase tracking-wider">
            Officer Profile & Credentials Management
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-gov-navy mt-0.5">
            Departmental Identity & Session
          </h2>
        </div>

        <button
          onClick={logout}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded shadow-sm transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out of Session</span>
        </button>
      </div>

      {testSuccess && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-900 text-xs flex items-center gap-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>
            <strong>Re-authentication Verified!</strong> Sensitive action authorization token confirmed for current session.
          </span>
        </div>
      )}

      {/* Main Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Officer Card */}
        <div className="md:col-span-1 bg-white rounded-lg border border-slate-200 shadow-sm p-6 text-center">
          <div className="w-20 h-20 rounded-full bg-gov-navy text-white mx-auto flex items-center justify-center border-4 border-gov-gold shadow-md">
            <User className="w-10 h-10 text-gov-gold-pale" />
          </div>

          <h3 className="text-base font-bold text-slate-900 mt-3">{user?.full_name}</h3>
          <p className="text-xs text-slate-500 font-mono">@{user?.username}</p>

          <div className="mt-4 pt-3 border-t border-slate-100">
            <span className="inline-block px-3 py-1 bg-gov-navy text-gov-gold-light text-xs font-bold uppercase tracking-wider rounded-full border border-gov-navy-light">
              {role?.replace(/_/g, ' ')}
            </span>
          </div>

          <div className="mt-4 text-left text-xs text-slate-600 space-y-2 bg-slate-50 p-3 rounded border border-slate-100">
            <div className="flex items-center gap-2">
              <Building className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
              <span className="truncate">{user?.division}</span>
            </div>
            <div className="flex items-center gap-2">
              <Mail className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
              <span className="truncate">{user?.email}</span>
            </div>
            <div className="flex items-center gap-2">
              <Phone className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
              <span>{user?.mobile}</span>
            </div>
          </div>
        </div>

        {/* Right 2 Columns: Permissions & Re-Auth Test */}
        <div className="md:col-span-2 space-y-6">
          {/* Active RBAC Permissions */}
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5">
            <div className="flex items-center gap-2 text-gov-navy font-bold text-sm pb-3 mb-3 border-b border-slate-100">
              <Shield className="w-4 h-4 text-gov-gold" />
              <span>Active Departmental Permissions ({permissions.length})</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {permissions.map((perm) => (
                <div
                  key={perm}
                  className="p-2.5 bg-slate-50 border border-slate-200 rounded text-xs text-slate-700 flex items-center gap-2"
                >
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                  <span className="font-mono text-[11px] font-semibold">{perm}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Sensitive Action Re-Authentication Sandbox */}
          <div className="bg-white rounded-lg border-2 border-slate-200 shadow-sm p-5">
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-100">
              <div className="flex items-center gap-2 text-gov-navy font-bold text-sm">
                <Lock className="w-4 h-4 text-gov-navy" />
                <span>Sensitive Action Re-Authentication Test</span>
              </div>
              <span className="text-[10px] font-bold bg-amber-100 text-amber-800 px-2 py-0.5 rounded">
                Phase 02 Security Sandbox
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed mb-4">
              The Revenue specification requires interactive password verification before performing sensitive operations such as exception overrides, user role modifications, and certificate revocations.
            </p>

            <button
              onClick={() => setIsReauthOpen(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-gov-navy hover:bg-gov-navy-light text-white text-xs font-bold rounded shadow-sm transition-colors"
            >
              <KeyRound className="w-4 h-4 text-gov-gold" />
              <span>Trigger Sensitive Action Re-authentication Modal</span>
            </button>
          </div>
        </div>
      </div>

      <ReauthModal
        isOpen={isReauthOpen}
        onClose={() => setIsReauthOpen(false)}
        onSuccess={handleTestReauthSuccess}
        actionTitle="Test Sensitive Departmental Operation"
        actionDescription="Demonstration of security step-up verification for GovMesh SIH26129."
      />
    </div>
  );
};
