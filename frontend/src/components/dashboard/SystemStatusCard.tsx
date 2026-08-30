import React, { useEffect, useState } from 'react';
import { Activity, Database, Server, Radio, RefreshCw } from 'lucide-react';
import { apiService, ServiceHealthData, DatabaseHealthData } from '../../services/api';

export const SystemStatusCard: React.FC = () => {
  const [serviceHealth, setServiceHealth] = useState<ServiceHealthData | null>(null);
  const [dbHealth, setDbHealth] = useState<DatabaseHealthData | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchHealth = async () => {
    setLoading(true);
    try {
      const [svc, db] = await Promise.all([
        apiService.getServiceHealth(),
        apiService.getDatabaseHealth(),
      ]);
      setServiceHealth(svc);
      setDbHealth(db);
    } catch (err) {
      console.error('Health fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const isBackendOk = serviceHealth?.status === 'ok';
  const isDbOk = dbHealth?.status === 'connected';

  return (
    <div className="bg-white rounded-lg p-5 shadow-sm border border-slate-200">
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-gov-navy" />
          <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
            Subsystem Status & Connectivity
          </h3>
        </div>
        <button
          onClick={fetchHealth}
          disabled={loading}
          className="text-xs text-slate-500 hover:text-gov-navy flex items-center gap-1 p-1 rounded hover:bg-slate-50 transition-colors"
          title="Refresh Connectivity"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Backend API Status */}
        <div className="p-3 bg-slate-50 rounded-md border border-slate-100 flex items-start gap-3">
          <div className={`p-2 rounded ${isBackendOk ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'}`}>
            <Server className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-500 uppercase">FastAPI Backend</div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`w-2 h-2 rounded-full ${isBackendOk ? 'bg-emerald-500' : 'bg-rose-500'}`} />
              <span className="text-xs font-bold text-slate-800">
                {isBackendOk ? 'Online (v0.1.0)' : 'Offline / Standalone'}
              </span>
            </div>
            <div className="text-[10px] text-slate-400 mt-1">Port 8000 (REST)</div>
          </div>
        </div>

        {/* PostgreSQL Database Status */}
        <div className="p-3 bg-slate-50 rounded-md border border-slate-100 flex items-start gap-3">
          <div className={`p-2 rounded ${isDbOk ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}>
            <Database className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-500 uppercase">PostgreSQL DB</div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={`w-2 h-2 rounded-full ${isDbOk ? 'bg-emerald-500' : 'bg-amber-500'}`} />
              <span className="text-xs font-bold text-slate-800">
                {isDbOk ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <div className="text-[10px] text-slate-400 mt-1">
              Latency: {dbHealth?.latency_ms ? `${dbHealth.latency_ms} ms` : 'N/A'}
            </div>
          </div>
        </div>

        {/* GovMesh Interop Connector */}
        <div className="p-3 bg-slate-50 rounded-md border border-slate-100 flex items-start gap-3">
          <div className="p-2 rounded bg-blue-100 text-blue-700">
            <Radio className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-500 uppercase">GovMesh Connector</div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              <span className="text-xs font-bold text-slate-800">Simulated / Ready</span>
            </div>
            <div className="text-[10px] text-slate-400 mt-1">REST Contract (Phase 06)</div>
          </div>
        </div>

        {/* Event Queue & Processing */}
        <div className="p-3 bg-slate-50 rounded-md border border-slate-100 flex items-start gap-3">
          <div className="p-2 rounded bg-purple-100 text-purple-700">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-500 uppercase">Department Queue</div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="w-2 h-2 rounded-full bg-purple-500" />
              <span className="text-xs font-bold text-slate-800">5 Mock Ingested</span>
            </div>
            <div className="text-[10px] text-slate-400 mt-1">Phase 01 Shell Buffer</div>
          </div>
        </div>
      </div>
    </div>
  );
};
