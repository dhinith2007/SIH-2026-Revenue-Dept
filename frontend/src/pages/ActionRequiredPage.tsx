import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  Search,
  RefreshCw,
  ExternalLink,
  MapPin,
  FileQuestion,
  RotateCcw,
  CheckCircle2,
} from 'lucide-react';
import { apiService } from '../services/api';
import { ApplicationSummary } from '../types/application';
import { PriorityBadge } from '../components/common/PriorityBadge';

export const ActionRequiredPage: React.FC = () => {
  const navigate = useNavigate();
  const [applications, setApplications] = useState<ApplicationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [reprocessingId, setReprocessingId] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchActionRequired = async () => {
    try {
      setLoading(true);
      const res = await apiService.getActionRequiredApplications({
        page,
        page_size: 15,
        search: searchTerm || undefined,
      });
      setApplications(res.items);
      setTotalPages(res.pagination.total_pages);
      setTotalCount(res.pagination.total);
    } catch (err) {
      console.warn('Failed to load action-required applications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActionRequired();
  }, [page, searchTerm]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchActionRequired();
  };

  const handleQuickReprocess = async (e: React.MouseEvent, appId: string) => {
    e.stopPropagation();
    try {
      setReprocessingId(appId);
      await apiService.reprocessApplication(appId);
      setActionSuccess(`Application ${appId} successfully ingested citizen response and moved to PROCESSING.`);
      setTimeout(() => setActionSuccess(null), 4000);
      fetchActionRequired();
    } catch (err: any) {
      alert(`Reprocessing failed: ${err.message}`);
    } finally {
      setReprocessingId(null);
    }
  };

  const parseQueryCategory = (actionStr?: string) => {
    if (!actionStr) return 'CLARIFICATION';
    if (actionStr.includes('NEW_DOCUMENT')) return 'NEW_DOCUMENT';
    if (actionStr.includes('CORRECT_ADDRESS')) return 'CORRECT_ADDRESS';
    if (actionStr.includes('MISSING_INFO') || actionStr.includes('MISSING_INFORMATION')) return 'MISSING_INFO';
    return 'CLARIFICATION';
  };

  const getCategoryBadge = (cat: string) => {
    switch (cat) {
      case 'NEW_DOCUMENT':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'CORRECT_ADDRESS':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'MISSING_INFO':
        return 'bg-rose-100 text-rose-800 border-rose-200';
      case 'CLARIFICATION':
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Success Notification */}
      {actionSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-emerald-800 text-sm animate-in fade-in duration-200">
          <div className="flex items-center space-x-2 font-medium">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            <span>{actionSuccess}</span>
          </div>
          <button onClick={() => setActionSuccess(null)} className="text-xs text-emerald-600 hover:underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center space-x-2 text-amber-700 font-semibold text-xs uppercase tracking-wider mb-1">
            <AlertTriangle className="w-4 h-4" />
            <span>Citizen Action & Clarification Desk</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Action Required Queue
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Applications awaiting citizen proof upload, address correction, or missing information before scrutiny resumes.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="bg-amber-50 border border-amber-200 px-4 py-2 rounded-lg text-right">
            <span className="text-xs text-amber-700 font-medium block">Pending Clarification</span>
            <span className="text-xl font-bold text-amber-900">{totalCount} Applications</span>
          </div>
          <button
            onClick={fetchActionRequired}
            disabled={loading}
            className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors"
            title="Refresh Queue"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-96">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-600" />
          <input
            type="text"
            placeholder="Search by ID, Citizen Name, or Taluka..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:bg-white transition-all"
          />
        </form>
        <div className="text-xs text-slate-600 font-mono">
          Showing {applications.length} of {totalCount} action-required cases
        </div>
      </div>

      {/* Action Required Applications Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading && applications.length === 0 ? (
          <div className="p-12 text-center text-slate-600">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-amber-600" />
            <p className="text-sm">Loading action-required queue...</p>
          </div>
        ) : applications.length === 0 ? (
          <div className="p-12 text-center text-slate-600">
            <FileQuestion className="w-10 h-10 mx-auto mb-2 text-slate-600" />
            <h3 className="text-base font-semibold text-slate-700">No action-required applications</h3>
            <p className="text-xs text-slate-600 mt-1">
              Applications requiring citizen documents or address corrections will appear here.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3.5">Application & Citizen</th>
                  <th className="px-6 py-3.5">Location</th>
                  <th className="px-6 py-3.5">Priority</th>
                  <th className="px-6 py-3.5">Query Category</th>
                  <th className="px-6 py-3.5">Officer Request / Message</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {applications.map((app) => {
                  const category = parseQueryCategory(app.required_action);
                  return (
                    <tr
                      key={app.application_id}
                      onClick={() => navigate(`/applications/${app.application_id}`)}
                      className="hover:bg-slate-50/80 transition-colors cursor-pointer"
                    >
                      <td className="px-6 py-4">
                        <div className="font-semibold text-slate-900">{app.citizen_name}</div>
                        <div className="text-xs font-mono text-primary-700 flex items-center gap-1 mt-0.5">
                          <span>{app.application_id}</span>
                          <span className="text-slate-600">•</span>
                          <span className="text-slate-600">{app.citizen_reference_id}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-xs text-slate-700 flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-slate-600" />
                          <span>
                            {app.taluka}, {app.district}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <PriorityBadge priority={app.priority} />
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-block px-2.5 py-1 rounded-md text-xs font-semibold border ${getCategoryBadge(
                            category
                          )}`}
                        >
                          {category}
                        </span>
                      </td>
                      <td className="px-6 py-4 max-w-xs">
                        <p className="text-xs text-slate-700 line-clamp-2 leading-relaxed bg-amber-50/60 p-2 rounded border border-amber-200/50">
                          {app.required_action?.replace(/^Citizen Information Required \[[^\]]+\]:\s*/i, '') ||
                            'Additional supporting proof requested by officer.'}
                        </p>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={(e) => handleQuickReprocess(e, app.application_id)}
                            disabled={reprocessingId === app.application_id}
                            className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:text-emerald-900 bg-emerald-50 hover:bg-emerald-100 px-2.5 py-1.5 rounded-md transition-colors border border-emerald-200"
                            title="Ingest Citizen Response & Reprocess"
                          >
                            <RotateCcw
                              className={`w-3.5 h-3.5 ${
                                reprocessingId === app.application_id ? 'animate-spin' : ''
                              }`}
                            />
                            <span>Reprocess</span>
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/applications/${app.application_id}`);
                            }}
                            className="inline-flex items-center gap-1 text-xs font-semibold text-primary-700 hover:text-primary-900 bg-primary-50 hover:bg-primary-100 px-2.5 py-1.5 rounded-md transition-colors"
                          >
                            <span>Inspect</span>
                            <ExternalLink className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
            <span className="text-xs text-slate-600">
              Page {page} of {totalPages}
            </span>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="px-3 py-1 bg-white border border-slate-200 rounded text-xs font-medium text-slate-700 disabled:opacity-50 hover:bg-slate-50"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="px-3 py-1 bg-white border border-slate-200 rounded text-xs font-medium text-slate-700 disabled:opacity-50 hover:bg-slate-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
