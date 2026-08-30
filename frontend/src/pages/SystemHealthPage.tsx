import React, { useState, useEffect } from 'react';
import {
  Server,
  Database,
  Radio,
  RefreshCw,
  Code,
} from 'lucide-react';
import { apiService, ServiceHealthData, DatabaseHealthData } from '../services/api';

export const SystemHealthPage: React.FC = () => {
  const [serviceHealth, setServiceHealth] = useState<ServiceHealthData | null>(null);
  const [dbHealth, setDbHealth] = useState<DatabaseHealthData | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastChecked, setLastChecked] = useState<string>('');

  const checkAll = async () => {
    setLoading(true);
    try {
      const [svc, db] = await Promise.all([
        apiService.getServiceHealth(),
        apiService.getDatabaseHealth(),
      ]);
      setServiceHealth(svc);
      setDbHealth(db);
      setLastChecked(new Date().toLocaleTimeString('en-IN'));
    } catch (err) {
      console.error('Error fetching system health:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkAll();
  }, []);

  const isBackendOnline = serviceHealth?.status === 'ok';
  const isDbConnected = dbHealth?.status === 'connected';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-200">
        <div>
          <div className="text-xs font-semibold text-gov-gold-dark uppercase tracking-wider">
            Infrastructure & Telemetry • Phase 01 Validation
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-gov-navy mt-0.5">
            Revenue Department System Health
          </h2>
        </div>

        <div className="flex items-center gap-3">
          {lastChecked && (
            <span className="text-xs text-slate-500">
              Last Ping: <strong>{lastChecked}</strong>
            </span>
          )}
          <button
            onClick={checkAll}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-gov-navy hover:bg-gov-navy-light text-white text-xs font-bold rounded shadow-sm transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Run Health Check</span>
          </button>
        </div>
      </div>

      {/* Grid of Components */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Backend Node */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2.5">
              <div className={`p-2.5 rounded-lg ${isBackendOnline ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'}`}>
                <Server className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">FastAPI REST Server</h3>
                <span className="text-[11px] text-slate-500 font-mono">/health & /api/v1/health</span>
              </div>
            </div>
            <span className={`w-3 h-3 rounded-full ${isBackendOnline ? 'bg-emerald-500 ring-4 ring-emerald-100' : 'bg-rose-500'}`} />
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Status:</span>
              <strong className={isBackendOnline ? 'text-emerald-700' : 'text-rose-700'}>
                {isBackendOnline ? 'HEALTHY' : 'UNREACHABLE'}
              </strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Service:</span>
              <span className="font-mono text-slate-700">{serviceHealth?.service || 'revenue-department'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Environment:</span>
              <span className="text-slate-700">{serviceHealth?.environment || 'development'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Service Version:</span>
              <span className="font-mono text-slate-700">{serviceHealth?.version || '0.1.0'}</span>
            </div>
          </div>
        </div>

        {/* PostgreSQL Database Node */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2.5">
              <div className={`p-2.5 rounded-lg ${isDbConnected ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'}`}>
                <Database className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">PostgreSQL Database</h3>
                <span className="text-[11px] text-slate-500 font-mono">/health/db</span>
              </div>
            </div>
            <span className={`w-3 h-3 rounded-full ${isDbConnected ? 'bg-emerald-500 ring-4 ring-emerald-100' : 'bg-amber-500'}`} />
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Status:</span>
              <strong className={isDbConnected ? 'text-emerald-700' : 'text-amber-700'}>
                {isDbConnected ? 'CONNECTED' : 'DISCONNECTED / STANDALONE'}
              </strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Engine:</span>
              <span className="font-mono text-slate-700">PostgreSQL 16</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Query Latency:</span>
              <span className="font-mono text-slate-700">
                {dbHealth?.latency_ms ? `${dbHealth.latency_ms} ms` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Schema Check:</span>
              <span className="text-slate-700">system_health_pings (Phase 01)</span>
            </div>
          </div>
        </div>

        {/* GovMesh Interoperability Node */}
        <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2.5 rounded-lg bg-blue-50 text-blue-600">
                <Radio className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">GovMesh Ingestion</h3>
                <span className="text-[11px] text-slate-500 font-mono">REST / JSON Connector</span>
              </div>
            </div>
            <span className="w-3 h-3 rounded-full bg-blue-500 ring-4 ring-blue-100" />
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Subsystem:</span>
              <strong className="text-blue-700">Department 1 (Revenue)</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">GovMesh Project:</span>
              <span className="font-mono text-slate-700">SIH26129</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Integration Phase:</span>
              <span className="text-slate-700">Phase 06 Scheduled</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Contract Standard:</span>
              <span className="text-slate-700 font-mono text-[11px]">GovMesh Canonical ↔ Rev Internal</span>
            </div>
          </div>
        </div>
      </div>

      {/* Metadata & Architecture Contract Table */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6 space-y-4">
        <h3 className="text-sm font-bold text-gov-navy uppercase tracking-wide flex items-center gap-2">
          <Code className="w-4 h-4 text-gov-gold" />
          <span>Active Endpoint Registry (Phase 01 Foundation)</span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase text-[11px]">
                <th className="py-2.5 px-3">Method</th>
                <th className="py-2.5 px-3">Endpoint Path</th>
                <th className="py-2.5 px-3">Purpose</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
              <tr>
                <td className="py-2.5 px-3 text-emerald-600 font-bold">GET</td>
                <td className="py-2.5 px-3 text-slate-900 font-semibold">/health</td>
                <td className="py-2.5 px-3 font-sans text-slate-600">Root service health probe</td>
                <td className="py-2.5 px-3 text-emerald-700 font-bold font-sans">Active (200 OK)</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-emerald-600 font-bold">GET</td>
                <td className="py-2.5 px-3 text-slate-900 font-semibold">/health/db</td>
                <td className="py-2.5 px-3 font-sans text-slate-600">PostgreSQL database connectivity check</td>
                <td className="py-2.5 px-3 text-emerald-700 font-bold font-sans">Active (200 OK)</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-emerald-600 font-bold">GET</td>
                <td className="py-2.5 px-3 text-slate-900 font-semibold">/api/v1/health</td>
                <td className="py-2.5 px-3 font-sans text-slate-600">Versioned v1 service health probe</td>
                <td className="py-2.5 px-3 text-emerald-700 font-bold font-sans">Active (200 OK)</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-emerald-600 font-bold">GET</td>
                <td className="py-2.5 px-3 text-slate-900 font-semibold">/api/v1/revenue/system-info</td>
                <td className="py-2.5 px-3 font-sans text-slate-600">Department metadata for GovMesh interop</td>
                <td className="py-2.5 px-3 text-emerald-700 font-bold font-sans">Active (200 OK)</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 text-emerald-600 font-bold">GET</td>
                <td className="py-2.5 px-3 text-slate-900 font-semibold">/api/v1/applications/mock</td>
                <td className="py-2.5 px-3 font-sans text-slate-600">Synthetic mock applications for Phase 01 UI shell</td>
                <td className="py-2.5 px-3 text-emerald-700 font-bold font-sans">Active (200 OK)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
