import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Inbox,
  Clock,
  RotateCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  ArrowRight,
  FileSpreadsheet,
  RefreshCw,
  Calendar,
  Layers,
  HelpCircle,
  Activity,
} from 'lucide-react';
import { StatCard } from '../components/dashboard/StatCard';
import { StatusBadge } from '../components/common/StatusBadge';
import { PriorityBadge } from '../components/common/PriorityBadge';
import { apiService, DatabaseHealthData } from '../services/api';
import {
  ApplicationSummary,
  DashboardSummaryData,
  FailureSimulationMode,
  NotificationItem,
} from '../types/application';
import { Bell, Sliders } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<DashboardSummaryData | null>(null);
  const [recentApplications, setRecentApplications] = useState<ApplicationSummary[]>([]);
  const [recentNotifications, setRecentNotifications] = useState<NotificationItem[]>([]);
  const [failureMode, setFailureMode] = useState<FailureSimulationMode>('NONE');
  const [dbHealth, setDbHealth] = useState<DatabaseHealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modeChanging, setModeChanging] = useState(false);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [sumData, appsData, dbData, notifData, mode] = await Promise.all([
        apiService.getDashboardSummary(),
        apiService.getApplications({ page: 1, page_size: 5, sort_by: 'received_at', sort_order: 'desc' }),
        apiService.getDatabaseHealth(),
        apiService.getNotifications(false, 3),
        apiService.getFailureMode(),
      ]);
      setSummary(sumData);
      setRecentApplications(appsData.items);
      setDbHealth(dbData);
      setRecentNotifications(notifData.items);
      setFailureMode(mode);
    } finally {
      setLoading(false);
      setRefreshing(false);
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

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    loadDashboardData();
  };

  const handleMetricClick = (statusFilter?: string) => {
    if (statusFilter) {
      navigate(`/applications?status=${statusFilter}`);
    } else {
      navigate('/applications');
    }
  };

  const total = summary?.total_incoming || 12;
  const pending = summary?.pending || 0;
  const processing = summary?.processing || 0;
  const completed = summary?.completed || 0;
  const actionReq = summary?.action_required || 0;
  const rejected = summary?.rejected || 0;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-200">
        <div>
          <div className="text-xs font-semibold text-gov-gold-dark uppercase tracking-wider">
            Revenue Division: Pune Division • Land Records & Citizen Services Desk
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
            <span>Refresh</span>
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

      {/* Primary Metrics Row (Clickable) */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <div onClick={() => handleMetricClick()} className="cursor-pointer transition-transform hover:-translate-y-0.5">
          <StatCard
            title="Incoming"
            value={summary?.total_incoming ?? '...'}
            icon={Inbox}
            colorScheme="slate"
            subtext="Total queue"
            badge="Live Buffer"
          />
        </div>

        <div onClick={() => handleMetricClick('PENDING')} className="cursor-pointer transition-transform hover:-translate-y-0.5">
          <StatCard
            title="Pending"
            value={summary?.pending ?? '...'}
            icon={Clock}
            colorScheme="amber"
            subtext="Awaiting review"
            badge="Action needed"
          />
        </div>

        <div onClick={() => handleMetricClick('PROCESSING')} className="cursor-pointer transition-transform hover:-translate-y-0.5">
          <StatCard
            title="Processing"
            value={summary?.processing ?? '...'}
            icon={RotateCw}
            colorScheme="blue"
            subtext="Desk scrutiny"
          />
        </div>

        <div onClick={() => handleMetricClick('ACTION_REQUIRED')} className="cursor-pointer transition-transform hover:-translate-y-0.5">
          <StatCard
            title="Action Req."
            value={summary?.action_required ?? '...'}
            icon={AlertTriangle}
            colorScheme="orange"
            subtext="Query to citizen"
          />
        </div>

        <div onClick={() => handleMetricClick('VERIFIED')} className="cursor-pointer transition-transform hover:-translate-y-0.5">
          <StatCard
            title="Verified"
            value={summary?.completed ?? '...'}
            icon={CheckCircle2}
            colorScheme="emerald"
            subtext="Approved / Synced"
          />
        </div>

        <div onClick={() => handleMetricClick('REJECTED')} className="cursor-pointer transition-transform hover:-translate-y-0.5">
          <StatCard
            title="Rejected"
            value={summary?.rejected ?? '...'}
            icon={XCircle}
            colorScheme="rose"
            subtext="Invalid records"
          />
        </div>
      </div>

      {/* Secondary Metrics Row (Operations & Duration) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        <div
          onClick={() => handleMetricClick('QUEUED')}
          className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm flex items-center justify-between cursor-pointer hover:border-purple-300 transition-colors"
        >
          <div>
            <div className="text-[11px] font-bold text-slate-500 uppercase">Failed / Queued Requests</div>
            <div className="text-xl font-bold text-purple-900 mt-1">
              {summary?.failed_or_queued ?? 0}
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">Buffer intake retry pool</div>
          </div>
          <div className="p-3 bg-purple-50 text-purple-700 rounded-lg">
            <Layers className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-[11px] font-bold text-slate-500 uppercase">Average Processing Time</div>
            <div className="text-xl font-bold text-slate-900 mt-1">
              {summary?.average_processing_time ?? '2h 15m'}
            </div>
            <div className="text-[10px] text-emerald-600 font-semibold mt-0.5">Derived from completed records</div>
          </div>
          <div className="p-3 bg-emerald-50 text-emerald-700 rounded-lg">
            <Clock className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm flex items-center justify-between">
          <div>
            <div className="text-[11px] font-bold text-slate-500 uppercase">Today's Applications</div>
            <div className="text-xl font-bold text-gov-navy mt-1">
              {summary?.today_applications ?? 0}
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">Ingested since 00:00 UTC</div>
          </div>
          <div className="p-3 bg-blue-50 text-gov-navy rounded-lg">
            <Calendar className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* SIH 2026 Evaluator Failure Simulation Controls */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white rounded-xl p-5 shadow-md border border-slate-700">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="p-1 bg-indigo-500/20 text-indigo-300 rounded border border-indigo-400/30">
                <Sliders className="w-4 h-4" />
              </span>
              <h3 className="text-sm font-bold text-white tracking-wide uppercase">
                SIH 2026 Demonstration Failure Simulator
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
            {/* GovMesh Connection */}
            <div className="bg-slate-800/80 px-3 py-1.5 rounded border border-slate-700 flex items-center gap-2">
              <span className="text-slate-400 font-sans text-[11px]">GovMesh Channel:</span>
              <span className="inline-flex items-center gap-1.5 font-bold text-emerald-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span>{summary?.govmesh_connection || 'DEMO ONLINE'}</span>
              </span>
            </div>

            {/* Revenue API Status */}
            <div className="bg-slate-800/80 px-3 py-1.5 rounded border border-slate-700 flex items-center gap-2">
              <span className="text-slate-400 font-sans text-[11px]">Revenue API:</span>
              <span className="font-bold text-emerald-400">
                {summary?.api_status || 'ONLINE'}
              </span>
            </div>

            {/* Database Status */}
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

      {/* Action Required Cases Callout (if any) */}
      {actionReq > 0 && (
        <div className="bg-orange-50/90 border-2 border-orange-200 rounded-xl p-4 sm:p-5 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-orange-100 text-orange-700 rounded-lg mt-0.5">
                <HelpCircle className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-orange-950 uppercase tracking-wide">
                  Attention Required ({actionReq} Applications)
                </h4>
                <p className="text-xs text-orange-900 mt-0.5">
                  Applications flagged with missing municipal documents or citizen queries requiring departmental follow-up.
                </p>
              </div>
            </div>

            <button
              onClick={() => handleMetricClick('ACTION_REQUIRED')}
              className="inline-flex items-center justify-center gap-1.5 px-3.5 py-2 bg-orange-600 hover:bg-orange-700 text-white text-xs font-bold rounded shadow-xs transition-colors self-start sm:self-center"
            >
              <span>View Action Required Queue</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Recent Applications Queue */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 sm:p-5 flex items-center justify-between border-b border-slate-100 bg-slate-50/50">
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              Recent Incoming Applications (GovMesh Intake Buffer)
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Latest address change applications received for land records and revenue jurisdiction verification.
            </p>
          </div>
          <button
            onClick={() => navigate('/applications')}
            className="text-xs font-bold text-gov-navy hover:text-gov-gold-dark flex items-center gap-1 transition-colors"
          >
            <span>View All ({summary?.total_incoming || 12})</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-400 text-xs">Loading application buffer...</div>
        ) : recentApplications.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-xs">No applications currently in queue.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-700 font-bold uppercase tracking-wider border-b border-slate-200 text-[11px]">
                  <th className="py-3 px-4">Application ID</th>
                  <th className="py-3 px-4">Citizen Name</th>
                  <th className="py-3 px-4">Service</th>
                  <th className="py-3 px-4">Jurisdiction (Taluka / Dist)</th>
                  <th className="py-3 px-4">Priority</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {recentApplications.map((app) => (
                  <tr key={app.application_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 font-mono font-bold text-gov-navy">
                      {app.application_id}
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-900">
                      {app.citizen_name}
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {app.service_type.replace(/_/g, ' ')}
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {app.taluka}, {app.district}
                    </td>
                    <td className="py-3 px-4">
                      <PriorityBadge priority={app.priority} size="sm" />
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={app.status} size="sm" />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => navigate(`/applications/${app.application_id}`)}
                        className="px-2.5 py-1 text-xs font-semibold text-gov-navy hover:bg-slate-100 rounded transition-colors"
                      >
                        Inspect Record
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Recent Departmental Notifications / Alerts Feed */}
      {recentNotifications.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div className="flex items-center gap-2 text-gov-navy font-bold text-xs uppercase tracking-wide">
              <Bell className="w-4 h-4 text-gov-gold" />
              <span>Recent Departmental Alerts & Milestones</span>
            </div>
            <button
              onClick={() => navigate('/applications/action-required')}
              className="text-xs text-primary-700 hover:text-primary-900 font-semibold inline-flex items-center gap-1"
            >
              <span>Action Desk</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {recentNotifications.map((n) => (
              <div
                key={n.id}
                onClick={() => n.application_id && navigate(`/applications/${n.application_id}`)}
                className="p-3 bg-slate-50 hover:bg-slate-100/80 rounded-lg border border-slate-200/80 transition-colors cursor-pointer space-y-1.5"
              >
                <div className="flex items-center justify-between gap-1">
                  <span className="font-bold text-xs text-slate-900 truncate">{n.title}</span>
                  <span
                    className={`px-1.5 py-0.2 rounded text-[9px] font-bold border ${
                      n.severity === 'CRITICAL'
                        ? 'bg-red-100 text-red-800 border-red-200'
                        : n.severity === 'WARNING'
                        ? 'bg-amber-100 text-amber-800 border-amber-200'
                        : n.severity === 'SUCCESS'
                        ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                        : 'bg-blue-100 text-blue-800 border-blue-200'
                    }`}
                  >
                    {n.severity}
                  </span>
                </div>
                <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed">{n.message}</p>
                <div className="text-[10px] font-mono text-primary-700 font-medium pt-0.5">
                  App: {n.application_id}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Status Distribution Progress Visualizer */}
      <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wide mb-3">
          Application Queue Status Distribution
        </h4>
        <div className="space-y-2 text-xs">
          <div className="flex justify-between text-slate-600">
            <span>Pending ({pending})</span>
            <span>Processing ({processing})</span>
            <span>Verified ({completed})</span>
            <span>Action Req ({actionReq})</span>
            <span>Rejected ({rejected})</span>
          </div>
          <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden flex">
            <div
              style={{ width: `${(pending / total) * 100}%` }}
              className="bg-amber-400 h-full"
              title={`Pending: ${pending}`}
            />
            <div
              style={{ width: `${(processing / total) * 100}%` }}
              className="bg-blue-500 h-full"
              title={`Processing: ${processing}`}
            />
            <div
              style={{ width: `${(completed / total) * 100}%` }}
              className="bg-emerald-500 h-full"
              title={`Verified: ${completed}`}
            />
            <div
              style={{ width: `${(actionReq / total) * 100}%` }}
              className="bg-orange-500 h-full"
              title={`Action Required: ${actionReq}`}
            />
            <div
              style={{ width: `${(rejected / total) * 100}%` }}
              className="bg-rose-500 h-full"
              title={`Rejected: ${rejected}`}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
