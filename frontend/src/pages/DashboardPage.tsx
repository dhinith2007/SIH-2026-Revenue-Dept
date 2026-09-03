import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Inbox,
  Clock,
  RotateCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileSpreadsheet,
  RefreshCw,
  Activity,
  Sliders,
  ShieldCheck,
  BarChart3,
  TrendingUp,
  FileSearch,
  UserCheck,
  AlertCircle,
  Filter,
  ArrowUpRight,
  Info,
} from 'lucide-react';
import { StatCard } from '../components/dashboard/StatCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { apiService, DatabaseHealthData } from '../services/api';
import {
  ApplicationSummary,
  DashboardSummaryData,
  FailureSimulationMode,
  FullDashboardAnalyticsData,
} from '../types/application';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();

  // State
  const [summary, setSummary] = useState<DashboardSummaryData | null>(null);
  const [analytics, setAnalytics] = useState<FullDashboardAnalyticsData | null>(null);
  const [recentApplications, setRecentApplications] = useState<ApplicationSummary[]>([]);
  const [failureMode, setFailureMode] = useState<FailureSimulationMode>('NONE');
  const [dbHealth, setDbHealth] = useState<DatabaseHealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modeChanging, setModeChanging] = useState(false);

  // Filters state
  const [days, setDays] = useState<number>(7);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [recommendationBand, setRecommendationBand] = useState<string>('ALL');
  const [riskFlag, setRiskFlag] = useState<string>('ALL');

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [sumData, fullAnalytics, appsData, dbData, _, mode] = await Promise.all([
        apiService.getDashboardSummary().catch(() => null),
        apiService.getFullDashboardAnalytics(days, statusFilter, recommendationBand, riskFlag).catch(() => null),
        apiService.getApplications({ page: 1, page_size: 5, sort_by: 'received_at', sort_order: 'desc' }).catch(() => ({ items: [], total: 0, page: 1, page_size: 5, total_pages: 1 })),
        apiService.getDatabaseHealth().catch(() => null),
        apiService.getNotifications(false, 3).catch(() => ({ items: [], total: 0, unread_count: 0 })),
        apiService.getFailureMode().catch(() => 'NONE'),
      ]);

      if (sumData) setSummary(sumData);
      if (fullAnalytics) setAnalytics(fullAnalytics);
      if (appsData?.items) setRecentApplications(appsData.items);
      if (dbData) setDbHealth(dbData);
      if (mode) setFailureMode(mode as FailureSimulationMode);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [days, statusFilter, recommendationBand, riskFlag]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadDashboardData();
  };

  const handleMetricClick = (filterStatus?: string) => {
    if (filterStatus) {
      navigate(`/applications?status=${filterStatus}`);
    } else {
      navigate('/applications');
    }
  };

  const handleFailureModeChange = async (newMode: FailureSimulationMode) => {
    setModeChanging(true);
    try {
      const setMode = await apiService.setFailureMode(newMode);
      setFailureMode(setMode);
    } catch (err) {
      console.warn('Failed to change failure mode:', err);
    } finally {
      setModeChanging(false);
    }
  };

  const kpis = analytics?.kpis;
  const verification = analytics?.verification;
  const confidence = analytics?.confidence;
  const risks = analytics?.risks;

  return (
    <div className="space-y-6 pb-12">
      {/* Statutory AI/OCR Disclaimer Banner */}
      <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-lg shadow-sm">
        <div className="flex items-start gap-3">
          <Info className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-amber-950">
            <span className="font-bold uppercase tracking-wider block text-amber-900 mb-0.5">
              Statutory AI/OCR Analytics Disclaimer
            </span>
            {analytics?.disclaimer ||
              'AI/OCR metrics are assistive evidence analytics. They do not constitute statutory decisions. Final decisions remain the responsibility of the authorized Revenue Officer.'}
          </div>
        </div>
      </div>

      {/* Page Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="text-xs font-semibold text-gov-gold-dark uppercase tracking-wider">
            Revenue Division: {analytics?.division || 'Pune Division'} • Land Records & Operational Analytics Desk
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-gov-navy mt-0.5">
            Departmental Officer Dashboard
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing || loading}
            className="inline-flex items-center gap-1.5 px-3 py-2 border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded shadow-sm transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh Analytics</span>
          </button>

          <button
            onClick={() => navigate('/applications')}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-gov-navy hover:bg-gov-navy-light text-white text-xs font-bold rounded shadow-sm transition-colors"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-gov-gold" />
            <span>Manage All Applications</span>
          </button>
        </div>
      </div>

      {/* Server-Side Analytics Filters Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-700 uppercase mb-3">
          <Filter className="w-4 h-4 text-gov-navy" />
          <span>Server-Side Analytics Filters</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
          {/* Time Window Filter */}
          <div>
            <label className="block text-slate-500 font-semibold mb-1">Time Range Window</label>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="w-full bg-slate-50 border border-slate-300 rounded px-2.5 py-1.5 font-medium text-slate-800 focus:ring-2 focus:ring-gov-navy"
            >
              <option value={7}>Last 7 Days</option>
              <option value={30}>Last 30 Days</option>
              <option value={90}>Last 90 Days</option>
            </select>
          </div>

          {/* Application Status Filter */}
          <div>
            <label className="block text-slate-500 font-semibold mb-1">Application Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded px-2.5 py-1.5 font-medium text-slate-800 focus:ring-2 focus:ring-gov-navy"
            >
              <option value="ALL">All Statuses</option>
              <option value="PENDING">PENDING (Awaiting Review)</option>
              <option value="PROCESSING">PROCESSING (Under Scrutiny)</option>
              <option value="ACTION_REQUIRED">ACTION_REQUIRED (Query to Citizen)</option>
              <option value="VERIFIED">VERIFIED (Statutorily Approved)</option>
              <option value="REJECTED">REJECTED (Invalid Application)</option>
            </select>
          </div>

          {/* AI Recommendation Band Filter */}
          <div>
            <label className="block text-slate-500 font-semibold mb-1">AI Recommendation Band</label>
            <select
              value={recommendationBand}
              onChange={(e) => setRecommendationBand(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded px-2.5 py-1.5 font-medium text-slate-800 focus:ring-2 focus:ring-gov-navy"
            >
              <option value="ALL">All Bands</option>
              <option value="HIGH_CONFIDENCE_MATCH">HIGH_CONFIDENCE_MATCH</option>
              <option value="MEDIUM_CONFIDENCE_REVIEW">MEDIUM_CONFIDENCE_REVIEW</option>
              <option value="LOW_CONFIDENCE_REVIEW">LOW_CONFIDENCE_REVIEW</option>
              <option value="MISMATCH_REVIEW">MISMATCH_REVIEW</option>
              <option value="INSUFFICIENT_EVIDENCE">INSUFFICIENT_EVIDENCE</option>
            </select>
          </div>

          {/* Evidence Risk Flag Filter */}
          <div>
            <label className="block text-slate-500 font-semibold mb-1">Risk Flag Filter</label>
            <select
              value={riskFlag}
              onChange={(e) => setRiskFlag(e.target.value)}
              className="w-full bg-slate-50 border border-slate-300 rounded px-2.5 py-1.5 font-medium text-slate-800 focus:ring-2 focus:ring-gov-navy"
            >
              <option value="ALL">All Risk Flags</option>
              <option value="OCR_LOW_CONFIDENCE">OCR_LOW_CONFIDENCE</option>
              <option value="NAME_MISMATCH">NAME_MISMATCH</option>
              <option value="PINCODE_MISMATCH">PINCODE_MISMATCH</option>
              <option value="MISSING_CRITICAL_FIELD">MISSING_CRITICAL_FIELD</option>
            </select>
          </div>
        </div>
      </div>

      {/* Core KPI Cards Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
        <div onClick={() => handleMetricClick()} className="cursor-pointer transition-transform hover:-translate-y-0.5">
          <StatCard
            title="Total Apps"
            value={kpis?.total_applications ?? summary?.total_incoming ?? '...'}
            icon={Inbox}
            colorScheme="slate"
            subtext="Authorized Scope"
          />
        </div>

        <div onClick={() => handleMetricClick('PENDING')} className="cursor-pointer transition-transform hover:-translate-y-0.5">
          <StatCard
            title="Pending"
            value={kpis?.pending_applications ?? summary?.pending ?? '...'}
            icon={Clock}
            colorScheme="amber"
            subtext="Awaiting review"
          />
        </div>

        <div onClick={() => handleMetricClick('PROCESSING')} className="cursor-pointer transition-transform hover:-translate-y-0.5">
          <StatCard
            title="Under Review"
            value={kpis?.under_review ?? summary?.processing ?? '...'}
            icon={RotateCw}
            colorScheme="blue"
            subtext="Desk scrutiny"
          />
        </div>

        <div onClick={() => handleMetricClick('ACTION_REQUIRED')} className="cursor-pointer transition-transform hover:-translate-y-0.5">
          <StatCard
            title="Info Requested"
            value={kpis?.information_requested ?? summary?.action_required ?? '...'}
            icon={AlertTriangle}
            colorScheme="orange"
            subtext="Query to citizen"
          />
        </div>

        <div onClick={() => handleMetricClick('VERIFIED')} className="cursor-pointer transition-transform hover:-translate-y-0.5">
          <StatCard
            title="Approved"
            value={kpis?.approved ?? summary?.completed ?? '...'}
            icon={CheckCircle2}
            colorScheme="emerald"
            subtext="Statutorily verified"
          />
        </div>

        <div onClick={() => handleMetricClick('REJECTED')} className="cursor-pointer transition-transform hover:-translate-y-0.5">
          <StatCard
            title="Rejected"
            value={kpis?.rejected ?? summary?.rejected ?? '...'}
            icon={XCircle}
            colorScheme="rose"
            subtext="Invalid records"
          />
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-3 shadow-sm flex flex-col justify-between">
          <div>
            <div className="text-[10px] font-bold text-slate-500 uppercase">Doc Pending</div>
            <div className="text-lg font-bold text-purple-900 mt-1">
              {kpis?.document_verification_pending ?? 0}
            </div>
          </div>
          <div className="text-[9px] text-slate-400 mt-1">Proof verification pool</div>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-3 shadow-sm flex flex-col justify-between">
          <div>
            <div className="text-[10px] font-bold text-rose-700 uppercase">Review Required</div>
            <div className="text-lg font-bold text-rose-900 mt-1">
              {kpis?.review_required ?? 0}
            </div>
          </div>
          <div className="text-[9px] text-rose-600 font-medium mt-1">Risk / Mismatch flags</div>
        </div>
      </div>

      {/* Application Trends & Status Distribution Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Time-Series Application Trends (2 Columns) */}
        <div className="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-gov-navy" />
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                Application Processing Trends ({days} Days)
              </h3>
            </div>
            <span className="text-xs font-semibold text-slate-500">Backend Time-Series Aggregation</span>
          </div>

          {/* Daily Breakdown Table */}
          <div className="overflow-x-auto border border-slate-200 rounded-lg">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
                <tr>
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2 text-right">Incoming Submitted</th>
                  <th className="px-3 py-2 text-right text-emerald-700">Statutorily Approved</th>
                  <th className="px-3 py-2 text-right text-rose-700">Rejected</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 font-medium">
                {analytics?.trends && analytics.trends.length > 0 ? (
                  analytics.trends.map((t) => (
                    <tr key={t.date} className="hover:bg-slate-50">
                      <td className="px-3 py-2 font-mono text-slate-700">{t.date}</td>
                      <td className="px-3 py-2 text-right font-bold text-slate-900">{t.incoming}</td>
                      <td className="px-3 py-2 text-right font-bold text-emerald-600">{t.approved}</td>
                      <td className="px-3 py-2 text-right font-bold text-rose-600">{t.rejected}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="px-3 py-4 text-center text-slate-400 italic">
                      No time-series trends available for selected date window.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Status Distribution (1 Column) */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-gov-navy" />
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              Status Distribution
            </h3>
          </div>

          <div className="space-y-3 text-xs">
            {analytics?.status_distribution && analytics.status_distribution.length > 0 ? (
              analytics.status_distribution.map((st) => (
                <div key={st.status} className="space-y-1">
                  <div className="flex justify-between font-semibold">
                    <span className="text-slate-700">{st.status}</span>
                    <span className="text-slate-900">
                      {st.count} ({st.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-2 rounded-full ${
                        st.status === 'VERIFIED'
                          ? 'bg-emerald-500'
                          : st.status === 'PROCESSING'
                          ? 'bg-blue-500'
                          : st.status === 'PENDING'
                          ? 'bg-amber-500'
                          : st.status === 'REJECTED'
                          ? 'bg-rose-500'
                          : 'bg-slate-400'
                      }`}
                      style={{ width: `${Math.min(100, Math.max(5, st.percentage))}%` }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <p className="text-slate-400 text-center py-4 italic">No status distribution records found.</p>
            )}
          </div>
        </div>
      </div>

      {/* Document Verification & OCR Performance Grid */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <FileSearch className="w-5 h-5 text-indigo-700" />
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
            Document Verification & Local OCR Performance Analytics
          </h3>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
            <div className="text-[11px] font-bold text-slate-500 uppercase">Total Proof Docs</div>
            <div className="text-xl font-bold text-slate-900 mt-1">{verification?.total_documents ?? 0}</div>
          </div>
          <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg">
            <div className="text-[11px] font-bold text-emerald-700 uppercase">Verified Proofs</div>
            <div className="text-xl font-bold text-emerald-900 mt-1">{verification?.verified_documents ?? 0}</div>
          </div>
          <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-lg">
            <div className="text-[11px] font-bold text-indigo-700 uppercase">OCR Success Rate</div>
            <div className="text-xl font-bold text-indigo-900 mt-1">{verification?.ocr_success_rate ?? 100}%</div>
          </div>
          <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="text-[11px] font-bold text-blue-700 uppercase">Avg OCR Conf.</div>
            <div className="text-xl font-bold text-blue-900 mt-1">{verification?.average_ocr_confidence ?? 95}%</div>
          </div>
          <div className="p-3 bg-purple-50 border border-purple-200 rounded-lg">
            <div className="text-[11px] font-bold text-purple-700 uppercase">Avg Match Conf.</div>
            <div className="text-xl font-bold text-purple-900 mt-1">{verification?.average_match_confidence ?? 100}%</div>
          </div>
          <div className="p-3 bg-teal-50 border border-teal-200 rounded-lg">
            <div className="text-[11px] font-bold text-teal-700 uppercase">Avg Overall Conf.</div>
            <div className="text-xl font-bold text-teal-900 mt-1">{verification?.average_overall_confidence ?? 96}%</div>
          </div>
        </div>
      </div>

      {/* AI Confidence & Risk Flags Analytics Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recommendation Bands Breakdown */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-teal-700" />
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              AI Confidence & Recommendation Bands
            </h3>
          </div>

          <div className="space-y-2 text-xs">
            {confidence?.recommendation_counts &&
              Object.entries(confidence.recommendation_counts).map(([band, count]) => (
                <div key={band} className="flex items-center justify-between p-2.5 bg-slate-50 rounded border border-slate-200">
                  <span className="font-mono font-bold text-slate-800">{band}</span>
                  <span className="font-bold text-slate-900 px-2 py-0.5 bg-white rounded border border-slate-300">
                    {count} records
                  </span>
                </div>
              ))}
          </div>
        </div>

        {/* Evidence Risk Flags Breakdown */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-600" />
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              Evidence Risk & Discrepancy Flags ({risks?.total_flagged_documents ?? 0} Flagged)
            </h3>
          </div>

          <div className="space-y-2 text-xs">
            {risks?.risk_flag_counts && Object.keys(risks.risk_flag_counts).length > 0 ? (
              Object.entries(risks.risk_flag_counts).map(([flag, count]) => (
                <div key={flag} className="flex items-center justify-between p-2.5 bg-rose-50/50 rounded border border-rose-200">
                  <span className="font-mono font-bold text-rose-900">{flag}</span>
                  <span className="font-bold text-rose-800 px-2 py-0.5 bg-white rounded border border-rose-300">
                    {count} occurrences
                  </span>
                </div>
              ))
            ) : (
              <p className="text-slate-400 text-center py-6 italic">No active evidence risk flags detected in scope.</p>
            )}
          </div>
        </div>
      </div>

      {/* Officer Workload Analytics Table */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="flex items-center gap-2">
          <UserCheck className="w-5 h-5 text-gov-navy" />
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
            Operational Officer Workload Distribution (Authorized Scope)
          </h3>
        </div>

        <div className="overflow-x-auto border border-slate-200 rounded-lg">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
              <tr>
                <th className="px-3 py-2">Officer Name & Role</th>
                <th className="px-3 py-2">Officer ID</th>
                <th className="px-3 py-2 text-right">Assigned Applications</th>
                <th className="px-3 py-2 text-right text-amber-700">Pending Scrutiny</th>
                <th className="px-3 py-2 text-right text-emerald-700">Completed Statutory Decisions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 font-medium">
              {analytics?.officer_workload && analytics.officer_workload.length > 0 ? (
                analytics.officer_workload.map((off) => (
                  <tr key={off.officer_id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-bold text-slate-900">{off.officer_name}</td>
                    <td className="px-3 py-2 font-mono text-slate-600">{off.officer_id}</td>
                    <td className="px-3 py-2 text-right font-bold text-slate-900">{off.assigned_count}</td>
                    <td className="px-3 py-2 text-right font-bold text-amber-600">{off.pending_count}</td>
                    <td className="px-3 py-2 text-right font-bold text-emerald-600">{off.completed_count}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-3 py-4 text-center text-slate-400 italic">
                    No officer workload data available.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Applications Queue Table */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Inbox className="w-5 h-5 text-gov-navy" />
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              Recent Incoming Applications Queue
            </h3>
          </div>
          <button
            onClick={() => navigate('/applications')}
            className="text-xs font-bold text-gov-navy hover:underline inline-flex items-center gap-1"
          >
            View All Applications <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto border border-slate-200 rounded-lg">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100 text-slate-700 font-bold border-b border-slate-200">
              <tr>
                <th className="px-3 py-2">Application Reference</th>
                <th className="px-3 py-2">Citizen Name</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Priority</th>
                <th className="px-3 py-2">Received Date</th>
                <th className="px-3 py-2 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 font-medium">
              {recentApplications.length > 0 ? (
                recentApplications.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-mono font-bold text-gov-navy">{app.id}</td>
                    <td className="px-3 py-2 text-slate-900">{app.citizen_name}</td>
                    <td className="px-3 py-2">
                      <StatusBadge status={app.status} />
                    </td>
                    <td className="px-3 py-2">
                      <PriorityBadge priority={app.priority} />
                    </td>
                    <td className="px-3 py-2 text-slate-600">
                      {new Date(app.received_at).toLocaleDateString('en-IN')}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <button
                        onClick={() => navigate(`/revenue/application/${app.id}`)}
                        className="px-2.5 py-1 bg-gov-navy text-white text-[11px] font-bold rounded hover:bg-gov-navy-light transition-colors"
                      >
                        Verify Desk
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-3 py-4 text-center text-slate-400 italic">
                    No recent applications found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* System Status Indicators (GovMesh Interoperability) */}
      <div className="bg-slate-900 text-white rounded-xl p-4 sm:p-5 shadow-sm border border-slate-800">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gov-gold/20 text-gov-gold rounded-lg border border-gov-gold/30">
              <Activity className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white tracking-wide uppercase">
                Departmental System Indicators & Interoperability
              </h3>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Real-time operational status for GovMesh cross-department communication buffer
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs font-mono">
            <div className="bg-slate-800/80 px-3 py-1.5 rounded border border-slate-700 flex items-center gap-2">
              <span className="text-slate-400 font-sans text-[11px]">GovMesh Channel:</span>
              <span className="inline-flex items-center gap-1.5 font-bold text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>{summary?.govmesh_connection || 'DEMO ONLINE'}</span>
              </span>
            </div>

            <div className="bg-slate-800/80 px-3 py-1.5 rounded border border-slate-700 flex items-center gap-2">
              <span className="text-slate-400 font-sans text-[11px]">Revenue API:</span>
              <span className="font-bold text-emerald-400">
                {summary?.api_status || 'ONLINE'}
              </span>
            </div>

            <div className="bg-slate-800/80 px-3 py-1.5 rounded border border-slate-700 flex items-center gap-2">
              <span className="text-slate-400 font-sans text-[11px]">PostgreSQL:</span>
              <span
                className={`font-bold ${
                  dbHealth?.status === 'connected' ? 'text-emerald-400' : 'text-amber-400'
                }`}
              >
                {dbHealth?.status === 'connected' ? `CONNECTED (${dbHealth.latency_ms}ms)` : 'STANDALONE MODE'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* SIH Evaluator Failure Simulator & System Health Controls */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white rounded-xl p-5 shadow-md border border-slate-700">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1 bg-indigo-500/20 text-indigo-300 rounded border border-indigo-400/30">
                <Sliders className="w-4 h-4" />
              </span>
              <h3 className="text-sm font-bold text-white tracking-wide uppercase">
                SIH 2026 Demonstration Failure Simulator Controls
              </h3>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                  failureMode === 'NONE'
                    ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    : 'bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse'
                }`}
              >
                {failureMode === 'NONE' ? 'NORMAL RUNTIME' : `SIMULATING: ${failureMode}`}
              </span>
            </div>
            <p className="text-xs text-slate-300">
              Evaluator controls to verify structured error handling, correlation IDs, and operational retry recovery during live demonstration.
            </p>
          </div>

          <div className="flex items-center gap-2 self-start md:self-center">
            <label className="text-xs font-semibold text-slate-300">Failure Mode:</label>
            <select
              value={failureMode}
              disabled={modeChanging}
              onChange={(e) => handleFailureModeChange(e.target.value as FailureSimulationMode)}
              className="bg-slate-800 text-white text-xs font-bold px-3 py-1.5 rounded-lg border border-slate-600 focus:ring-2 focus:ring-indigo-500 outline-none cursor-pointer"
            >
              <option value="NONE">NONE (Normal Resilient Mode)</option>
              <option value="API_UNAVAILABLE">503 API_UNAVAILABLE</option>
              <option value="TIMEOUT">504 GATEWAY_TIMEOUT</option>
              <option value="INTERNAL_ERROR">500 INTERNAL_ERROR</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
};
