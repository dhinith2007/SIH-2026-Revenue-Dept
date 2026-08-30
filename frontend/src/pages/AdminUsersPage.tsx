import React, { useState, useEffect } from 'react';
import {
  Users,
  RefreshCw,
  Plus,
  Building,
  CheckCircle2,
} from 'lucide-react';
import { apiService } from '../services/api';
import { User } from '../types/auth';
import { ReauthModal } from '../components/auth/ReauthModal';

export const AdminUsersPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Sensitive action state
  const [isReauthOpen, setIsReauthOpen] = useState(false);
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getDepartmentUsers();
      setUsers(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load department users.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreateUserClick = () => {
    setIsReauthOpen(true);
  };

  const handleReauthSuccess = () => {
    setActionSuccessMsg(
      'Security credentials re-verified successfully! Administrator action validated.'
    );
    setTimeout(() => setActionSuccessMsg(null), 5000);
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-200">
        <div>
          <div className="text-xs font-semibold text-gov-gold-dark uppercase tracking-wider">
            State Revenue Administration • Role-Based Access Control
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-gov-navy mt-0.5">
            Department Personnel & Role Management
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchUsers}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded shadow-sm transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>

          <button
            onClick={handleCreateUserClick}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-gov-navy hover:bg-gov-navy-light text-white text-xs font-bold rounded shadow-sm transition-colors"
          >
            <Plus className="w-3.5 h-3.5 text-gov-gold" />
            <span>Provision Officer (Sensitive Action)</span>
          </button>
        </div>
      </div>

      {actionSuccessMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-md text-emerald-900 text-xs flex items-center gap-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{actionSuccessMsg}</span>
        </div>
      )}

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-xs">
          <strong>Access Error:</strong> {error}
        </div>
      )}

      {/* Users Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 sm:p-5 flex items-center justify-between border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-gov-navy" />
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              Registered Department Officers ({users.length})
            </h3>
          </div>
          <span className="text-[11px] font-mono bg-blue-50 text-blue-800 px-2 py-0.5 rounded border border-blue-200">
            Permission: USER_MANAGE Active
          </span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            Loading department users from database...
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-700 font-bold uppercase tracking-wider border-b border-slate-200 text-[11px]">
                  <th className="py-3.5 px-4">User ID</th>
                  <th className="py-3.5 px-4">Officer Name</th>
                  <th className="py-3.5 px-4">Role Classification</th>
                  <th className="py-3.5 px-4">Assigned Division</th>
                  <th className="py-3.5 px-4">Contact (Email / Mobile)</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-gov-navy">
                      {u.id}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-900">{u.full_name}</div>
                      <div className="text-[11px] text-slate-500 font-mono">@{u.username}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="inline-block px-2.5 py-1 rounded text-[10px] font-bold tracking-wide uppercase bg-slate-100 text-slate-800 border border-slate-200">
                        {u.role.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">
                      <div className="flex items-center gap-1.5">
                        <Building className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
                        <span>{u.division}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">
                      <div>{u.email}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{u.mobile}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          u.is_active
                            ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                            : 'bg-rose-50 text-rose-800 border border-rose-200'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            u.is_active ? 'bg-emerald-500' : 'bg-rose-500'
                          }`}
                        />
                        <span>{u.is_active ? 'ACTIVE' : 'DEACTIVATED'}</span>
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={handleCreateUserClick}
                        className="px-2.5 py-1 text-xs font-semibold text-gov-navy hover:bg-slate-100 rounded transition-colors"
                      >
                        Edit Role
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Sensitive Action Re-authentication Modal */}
      <ReauthModal
        isOpen={isReauthOpen}
        onClose={() => setIsReauthOpen(false)}
        onSuccess={handleReauthSuccess}
        actionTitle="Officer Provisioning & Role Modification"
        actionDescription="This sensitive administrative operation alters departmental RBAC access rights. Please enter your administrator password to proceed."
      />
    </div>
  );
};
