import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  XCircle,
  Search,
  RefreshCw,
  ExternalLink,
  MapPin,
  AlertOctagon,
  FileX2,
  ShieldAlert,
} from 'lucide-react';
import { apiService } from '../services/api';
import { ApplicationSummary } from '../types/application';
import { PriorityBadge } from '../components/common/PriorityBadge';

export const RejectedApplicationsPage: React.FC = () => {
  const navigate = useNavigate();
  const [applications, setApplications] = useState<ApplicationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);

  const fetchRejected = async () => {
    try {
      setLoading(true);
      const res = await apiService.getRejectedApplications({
        page,
        page_size: 15,
        search: searchTerm || undefined,
      });
      setApplications(res.items);
      setTotalPages(res.pagination.total_pages);
      setTotalCount(res.pagination.total);
    } catch (err) {
      console.warn('Failed to load rejected applications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRejected();
  }, [page, searchTerm]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchRejected();
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center space-x-2 text-rose-700 font-semibold text-xs uppercase tracking-wider mb-1">
            <ShieldAlert className="w-4 h-4" />
            <span>Statutory Rejection Register</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Rejected Applications
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Auditable log of applications denied with formal statutory justifications (e.g. proof document mismatch or jurisdiction issues).
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="bg-rose-50 border border-rose-200 px-4 py-2 rounded-lg text-right">
            <span className="text-xs text-rose-700 font-medium block">Total Rejected</span>
            <span className="text-xl font-bold text-rose-900">{totalCount} Applications</span>
          </div>
          <button
            onClick={fetchRejected}
            disabled={loading}
            className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition-colors"
            title="Refresh Rejection Register"
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
          Showing {applications.length} of {totalCount} rejected records
        </div>
      </div>

      {/* Rejected Applications Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading && applications.length === 0 ? (
          <div className="p-12 text-center text-slate-600">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-rose-600" />
            <p className="text-sm">Loading statutory rejection registry...</p>
          </div>
        ) : applications.length === 0 ? (
          <div className="p-12 text-center text-slate-600">
            <FileX2 className="w-10 h-10 mx-auto mb-2 text-slate-600" />
            <h3 className="text-base font-semibold text-slate-700">No rejected applications found</h3>
            <p className="text-xs text-slate-600 mt-1">
              Applications formally rejected by officers with statutory reasons will appear here.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3.5">Application & Citizen</th>
                  <th className="px-6 py-3.5">Taluka / District</th>
                  <th className="px-6 py-3.5">Priority</th>
                  <th className="px-6 py-3.5">Statutory Rejection Reason</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {applications.map((app) => (
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
                    <td className="px-6 py-4 max-w-xs">
                      <div className="flex items-start gap-1.5 text-xs text-rose-800 bg-rose-50/80 p-2 rounded border border-rose-200/60">
                        <AlertOctagon className="w-3.5 h-3.5 text-rose-600 mt-0.5 flex-shrink-0" />
                        <span className="line-clamp-2 leading-relaxed">
                          {app.required_action?.replace(/^Application rejected\. Reason:\s*/i, '') ||
                            'Statutory documentation criteria not fulfilled.'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-100 text-rose-800 border border-rose-200">
                        <XCircle className="w-3.5 h-3.5 text-rose-600" />
                        <span>REJECTED (FINAL)</span>
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/applications/${app.application_id}`);
                        }}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-primary-700 hover:text-primary-900 bg-primary-50 hover:bg-primary-100 px-3 py-1.5 rounded-md transition-colors"
                      >
                        <span>Inspect</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
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
