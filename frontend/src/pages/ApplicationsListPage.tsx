import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Search,
  Filter,
  RefreshCw,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  X,
  FileQuestion,
} from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { apiService } from '../services/api';
import { ApplicationSummary, PaginationMetadata } from '../types/application';

export const ApplicationsListPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [applications, setApplications] = useState<ApplicationSummary[]>([]);
  const [pagination, setPagination] = useState<PaginationMetadata>({
    page: 1,
    page_size: 20,
    total: 0,
    total_pages: 1,
  });
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Filter & Search states initialized from URL search params if present
  const [searchTerm, setSearchTerm] = useState(searchParams.get('search') || '');
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || 'ALL');
  const [priorityFilter, setPriorityFilter] = useState(searchParams.get('priority') || 'ALL');
  const [sortBy, setSortBy] = useState('received_at');
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');
  const [currentPage, setCurrentPage] = useState(1);

  const fetchApplications = async (page = currentPage, isBackground = false) => {
    if (!isBackground) {
      setLoading(true);
    } else {
      setIsRefreshing(true);
    }
    try {
      const data = await apiService.getApplications({
        page,
        page_size: 10,
        status: statusFilter !== 'ALL' ? statusFilter : undefined,
        priority: priorityFilter !== 'ALL' ? priorityFilter : undefined,
        search: searchTerm.trim() || undefined,
        sort_by: sortBy,
        sort_order: sortOrder,
      });
      if (data && data.items) {
        setApplications(data.items);
        setPagination(data.pagination);
        setCurrentPage(data.pagination.page);
      }
    } catch (error) {
      console.warn('Failed to fetch applications:', error);
    } finally {
      if (!isBackground) setLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchApplications(1, false);
    const interval = setInterval(() => {
      fetchApplications(currentPage, true);
    }, 5000);
    return () => clearInterval(interval);
  }, [statusFilter, priorityFilter, sortBy, sortOrder, currentPage]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchApplications(1);
  };

  const handleClearFilters = () => {
    setSearchTerm('');
    setStatusFilter('ALL');
    setPriorityFilter('ALL');
    setSearchParams({});
  };

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= pagination.total_pages) {
      fetchApplications(newPage);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-200">
        <div>
          <div className="text-xs font-semibold text-gov-gold-dark uppercase tracking-wider">
            Departmental Queue • Land Records & Address Change Ingestion
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-gov-navy mt-0.5">
            Incoming Applications Scrutiny
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchApplications(currentPage, true)}
            disabled={loading || isRefreshing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded shadow-sm transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading || isRefreshing ? 'animate-spin' : ''}`} />
            <span>Refresh Queue</span>
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col md:flex-row items-center gap-3">
          {/* Search input */}
          <div className="relative flex-1 w-full">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Search className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by Application ID (GM-...), Citizen Name, Correlation ID, or Taluka..."
              className="w-full pl-9 pr-8 py-2 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-gov-navy focus:border-gov-navy outline-none"
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => {
                  setSearchTerm('');
                  fetchApplications(1);
                }}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <button
            type="submit"
            className="w-full md:w-auto px-4 py-2 bg-gov-navy hover:bg-gov-navy-light text-white text-xs font-bold rounded transition-colors shadow-sm"
          >
            Search
          </button>
        </form>

        {/* Operational Queue Quick Tabs */}
        <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-100">
          {[
            { label: 'All Cases', value: 'ALL' },
            { label: 'Pending', value: 'PENDING' },
            { label: 'Processing', value: 'PROCESSING' },
            { label: 'Action Required', value: 'ACTION_REQUIRED' },
            { label: 'Verified', value: 'VERIFIED' },
            { label: 'Rejected', value: 'REJECTED' },
            { label: 'Queued / Stalled', value: 'QUEUED' },
          ].map((tab) => {
            const isActive = statusFilter === tab.value;
            return (
              <button
                key={tab.value}
                type="button"
                onClick={() => {
                  setStatusFilter(tab.value);
                  setSearchParams(tab.value !== 'ALL' ? { status: tab.value } : {});
                }}
                className={`px-3 py-1 rounded-full text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-gov-navy text-gov-gold-light shadow-sm'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Dropdown Filters Row */}
        <div className="flex flex-wrap items-center gap-2.5 pt-2 border-t border-slate-100 text-xs">
          <div className="flex items-center gap-1.5">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <span className="font-semibold text-slate-700">Filters:</span>
          </div>

          {/* Status filter */}
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setSearchParams(e.target.value !== 'ALL' ? { status: e.target.value } : {});
            }}
            className="py-1.5 px-2.5 border border-slate-300 rounded text-xs bg-white text-slate-700 focus:ring-2 focus:ring-gov-navy outline-none font-medium"
          >
            <option value="ALL">All Statuses</option>
            <option value="PENDING">PENDING REVIEW</option>
            <option value="PROCESSING">IN PROCESSING</option>
            <option value="ACTION_REQUIRED">ACTION REQUIRED</option>
            <option value="VERIFIED">VERIFIED / APPROVED</option>
            <option value="REJECTED">REJECTED</option>
            <option value="QUEUED">QUEUED IN BUFFER</option>
          </select>

          {/* Priority filter */}
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="py-1.5 px-2.5 border border-slate-300 rounded text-xs bg-white text-slate-700 focus:ring-2 focus:ring-gov-navy outline-none font-medium"
          >
            <option value="ALL">All Priorities</option>
            <option value="URGENT">URGENT</option>
            <option value="HIGH">HIGH</option>
            <option value="NORMAL">NORMAL</option>
            <option value="LOW">LOW</option>
          </select>

          {/* Sort field */}
          <div className="flex items-center gap-1 ml-auto">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [sb, so] = e.target.value.split('-');
                setSortBy(sb);
                setSortOrder(so as 'asc' | 'desc');
              }}
              className="py-1.5 px-2.5 border border-slate-300 rounded text-xs bg-white text-slate-700 focus:ring-2 focus:ring-gov-navy outline-none font-medium"
            >
              <option value="received_at-desc">Received: Newest First</option>
              <option value="received_at-asc">Received: Oldest First</option>
              <option value="priority-desc">Priority: High to Low</option>
              <option value="application_id-asc">Application ID: Ascending</option>
            </select>
          </div>

          {(statusFilter !== 'ALL' || priorityFilter !== 'ALL' || searchTerm) && (
            <button
              onClick={handleClearFilters}
              className="text-xs text-rose-600 font-semibold hover:underline px-2 py-1"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Applications Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">
            <div className="w-6 h-6 border-2 border-gov-navy border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
            <span>Loading departmental application records from database...</span>
          </div>
        ) : applications.length === 0 ? (
          <div className="p-12 text-center text-slate-500 text-xs space-y-2">
            <FileQuestion className="w-8 h-8 text-slate-400 mx-auto mb-1" />
            <h4 className="font-bold text-slate-700">No Applications Found</h4>
            <p className="text-slate-400 max-w-sm mx-auto">
              No applications match your specified filter or search criteria in the Revenue database.
            </p>
            <button
              onClick={handleClearFilters}
              className="px-3 py-1.5 bg-gov-navy text-white rounded text-xs font-bold mt-2"
            >
              Clear Filters
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-700 font-bold uppercase tracking-wider border-b border-slate-200 text-[11px]">
                  <th className="py-3.5 px-4">Application ID</th>
                  <th className="py-3.5 px-4">Citizen Name</th>
                  <th className="py-3.5 px-4">Service</th>
                  <th className="py-3.5 px-4">Jurisdiction</th>
                  <th className="py-3.5 px-4">Received Time</th>
                  <th className="py-3.5 px-4">Priority</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {applications.map((app) => {
                  const isDemo124 = app.application_id === 'GM-2026-000124';
                  return (
                    <tr
                      key={app.application_id}
                      className={`transition-colors ${
                        isDemo124
                          ? 'bg-amber-50/70 hover:bg-amber-100/60 border-l-4 border-l-amber-500'
                          : 'hover:bg-slate-50/80'
                      }`}
                    >
                      <td className="py-3.5 px-4">
                        <div className="font-mono font-bold text-gov-navy flex items-center gap-1.5">
                          <span>{app.application_id}</span>
                        </div>
                        {isDemo124 && (
                          <span className="inline-block mt-1 px-1.5 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300 font-extrabold text-[9px] uppercase tracking-wide">
                            GovMesh Demo — Recently Received
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 font-semibold text-slate-900">
                        {app.citizen_name}
                      </td>
                      <td className="py-3.5 px-4 text-slate-700">
                        {app.service_type.replace(/_/g, ' ')}
                      </td>
                      <td className="py-3.5 px-4 text-slate-600">
                        <div>
                          {app.taluka}, {app.district}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-slate-500 font-mono text-[11px]">
                        {new Date(app.received_at).toLocaleString('en-IN', {
                          dateStyle: 'medium',
                          timeStyle: 'short',
                        })}
                      </td>
                      <td className="py-3.5 px-4">
                        <PriorityBadge priority={app.priority} size="sm" />
                      </td>
                      <td className="py-3.5 px-4">
                        <StatusBadge status={app.status} size="sm" />
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => navigate(`/applications/${app.application_id}`)}
                          className="inline-flex items-center gap-1 px-3 py-1.5 bg-gov-navy hover:bg-gov-navy-light text-white text-xs font-semibold rounded transition-colors shadow-2xs"
                        >
                          <span>Inspect</span>
                          <ExternalLink className="w-3 h-3 text-gov-gold" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Table Footer & Pagination */}
        <div className="p-3.5 bg-slate-50 border-t border-slate-200 text-xs text-slate-600 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div>
            Showing{' '}
            <strong>
              {pagination.total > 0 ? (pagination.page - 1) * pagination.page_size + 1 : 0}
            </strong>{' '}
            to{' '}
            <strong>
              {Math.min(pagination.page * pagination.page_size, pagination.total)}
            </strong>{' '}
            of <strong>{pagination.total}</strong> applications
          </div>

          {pagination.total_pages > 1 && (
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => handlePageChange(pagination.page - 1)}
                disabled={pagination.page <= 1}
                className="p-1.5 border border-slate-300 rounded bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
                title="Previous Page"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              <span className="px-2.5 font-bold text-slate-800">
                Page {pagination.page} of {pagination.total_pages}
              </span>

              <button
                onClick={() => handlePageChange(pagination.page + 1)}
                disabled={pagination.page >= pagination.total_pages}
                className="p-1.5 border border-slate-300 rounded bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed"
                title="Next Page"
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
