import React, { useState, useEffect } from 'react';
import {
  Shield,
  RefreshCw,
  Search,
  Filter,
  FileText,
  User,
  ChevronLeft,
  ChevronRight,
  Fingerprint,
} from 'lucide-react';
import { apiService } from '../services/api';
import { AuditLogEntry, AuditLogListResult } from '../types/application';

export const AuditLogPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [actionFilter, setActionFilter] = useState('ALL');

  const fetchAuditLogs = async (targetPage = page) => {
    setLoading(true);
    try {
      const data: AuditLogListResult = await apiService.getAuditLogs({
        page: targetPage,
        page_size: 15,
        application_id: searchTerm.trim() || undefined,
      });
      setLogs(data.items);
      setTotal(data.total);
      setPage(data.page);
      setTotalPages(data.total_pages);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditLogs(1);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchAuditLogs(1);
  };

  const filteredLogs = logs.filter((item) => {
    if (actionFilter === 'ALL') return true;
    return item.action.toUpperCase() === actionFilter.toUpperCase();
  });

  const getActionBadgeColor = (action: string) => {
    switch (action.toUpperCase()) {
      case 'APPROVE':
      case 'APPROVED':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'REJECT':
      case 'REJECTED':
        return 'bg-rose-100 text-rose-800 border-rose-300';
      case 'REQUEST_INFORMATION':
      case 'INFORMATION_REQUESTED':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'START_REVIEW':
      case 'PROCESSING_STARTED':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'REPROCESS':
      case 'REPROCESSED':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-200">
        <div>
          <div className="text-xs font-semibold text-gov-gold-dark uppercase tracking-wider flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5" />
            <span>Statutory Compliance & Traceability</span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-gov-navy mt-0.5">
            Departmental Audit Log & Compliance Trail
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Immutable, append-only ledger recording all officer decisions, status changes, and GovMesh request handling.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchAuditLogs(page)}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded shadow-xs transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Audit Log</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs flex flex-col sm:flex-row items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by Application ID (GM-...)"
            className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-gov-navy outline-none"
          />
        </form>

        <div className="flex items-center gap-2 self-end sm:self-center text-xs">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="font-semibold text-slate-600">Action:</span>
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="py-1.5 px-2.5 border border-slate-300 rounded text-xs bg-white text-slate-700 font-medium outline-none focus:ring-2 focus:ring-gov-navy"
          >
            <option value="ALL">All Actions</option>
            <option value="APPROVE">APPROVE / VERIFIED</option>
            <option value="REJECT">REJECT</option>
            <option value="REQUEST_INFORMATION">REQUEST INFORMATION</option>
            <option value="START_REVIEW">START REVIEW</option>
            <option value="REPROCESS">REPROCESS</option>
          </select>
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <div className="w-6 h-6 border-2 border-gov-navy border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            <span>Loading immutable audit records...</span>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs">
            <FileText className="w-8 h-8 text-slate-400 mx-auto mb-2" />
            <h4 className="font-bold text-slate-700">No Audit Records Found</h4>
            <p className="text-slate-400 mt-1">No officer actions match the filter criteria.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-700 font-bold uppercase tracking-wider border-b border-slate-200 text-[11px]">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Officer</th>
                  <th className="py-3 px-4">Application</th>
                  <th className="py-3 px-4">Correlation Key</th>
                  <th className="py-3 px-4">Action Taken</th>
                  <th className="py-3 px-4">State Transition</th>
                  <th className="py-3 px-4">Reason / Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 text-slate-600 font-mono text-[11px]">
                      {new Date(log.timestamp).toLocaleString('en-IN', {
                        dateStyle: 'short',
                        timeStyle: 'medium',
                      })}
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-900">
                      <div className="flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5 text-slate-400" />
                        <span>{log.officer_name}</span>
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono block">
                        {log.officer_id}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-gov-navy">
                      <a
                        href={`/applications/${log.application_id}`}
                        className="hover:underline"
                      >
                        {log.application_id}
                      </a>
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-500 text-[11px]">
                      <div className="flex items-center gap-1">
                        <Fingerprint className="w-3 h-3 text-gov-gold" />
                        <span>{log.correlation_id}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${getActionBadgeColor(
                          log.action
                        )}`}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3 px-4 font-mono text-[11px] text-slate-700">
                      {log.previous_status || 'NONE'} →{' '}
                      <strong className="text-slate-900">{log.new_status}</strong>
                    </td>
                    <td className="py-3 px-4 text-slate-600 max-w-xs truncate" title={log.reason || '—'}>
                      {log.reason || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        <div className="p-3 bg-slate-50 border-t border-slate-200 text-xs text-slate-600 flex items-center justify-between">
          <div>
            Showing <strong>{filteredLogs.length}</strong> of <strong>{total}</strong> audit events
          </div>
          {totalPages > 1 && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => fetchAuditLogs(page - 1)}
                disabled={page <= 1}
                className="p-1 border border-slate-300 rounded bg-white hover:bg-slate-100 disabled:opacity-40"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="font-bold">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => fetchAuditLogs(page + 1)}
                disabled={page >= totalPages}
                className="p-1 border border-slate-300 rounded bg-white hover:bg-slate-100 disabled:opacity-40"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
