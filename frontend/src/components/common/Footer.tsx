import React from 'react';
import { Shield, Info } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-400 text-xs border-t-4 border-gov-gold mt-auto">
      {/* Top Banner */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-6 border-b border-slate-800">
          {/* Col 1: Portal & Project Info */}
          <div>
            <div className="flex items-center gap-2 text-white font-bold text-sm mb-2">
              <Shield className="w-4 h-4 text-gov-gold" />
              <span>Revenue & Forest Department Portal</span>
            </div>
            <p className="text-slate-400 leading-relaxed text-xs">
              Simulated departmental subsystem for the <strong>GovMesh SIH26129</strong> Interoperability Framework. Built to demonstrate decentralized cross-departmental data exchange, address verification, and citizen-centric governance.
            </p>
          </div>

          {/* Col 2: Simulated Architecture Role */}
          <div>
            <h4 className="text-white font-semibold text-xs uppercase tracking-wider mb-2">
              Architecture Boundaries (Phase 01)
            </h4>
            <ul className="space-y-1.5 text-slate-400 text-xs">
              <li className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-gov-gold"></span>
                <span>Independent Department Database & Backend</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-gov-gold"></span>
                <span>REST / JSON Integration Contract</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-gov-gold"></span>
                <span>Internal Revenue Data Schema Model</span>
              </li>
            </ul>
          </div>

          {/* Col 3: Legal & Prototype Disclaimer */}
          <div>
            <div className="flex items-center gap-1.5 text-amber-400 font-semibold mb-2">
              <Info className="w-4 h-4" />
              <span>Demonstration Prototype Notice</span>
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">
              This system is a simulated software prototype created solely for the Smart India Hackathon 2026 (SIH26129). It does not represent a live integration with the Government of Maharashtra and does not process real citizen identity data.
            </p>
          </div>
        </div>

        {/* Bottom copyright and metadata */}
        <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-slate-500">
          <div>
            &copy; {new Date().getFullYear()} GovMesh SIH26129 — Revenue & Forest Department Module (Simulated).
          </div>
          <div className="flex items-center gap-4">
            <span className="text-slate-400">Environment: Development / Sandbox</span>
            <span>•</span>
            <span className="text-slate-400">Version: 0.1.0 (Phase 01 Shell)</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
