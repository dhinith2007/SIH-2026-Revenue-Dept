import React from 'react';
import { AlertCircle } from 'lucide-react';

export const PrototypeBanner: React.FC = () => {
  return (
    <div className="bg-amber-600 text-white text-xs py-1.5 px-4 font-medium tracking-wide flex items-center justify-between border-b border-amber-700">
      <div className="flex items-center gap-2 max-w-7xl mx-auto w-full">
        <AlertCircle className="w-4 h-4 flex-shrink-0 text-amber-200" />
        <span>
          <strong className="font-semibold uppercase tracking-wider">GovMesh SIH26129 Demonstration Prototype</strong> — Simulated Revenue & Forest Department System (Department 1). Non-production environment.
        </span>
      </div>
      <span className="hidden md:inline-block text-[11px] bg-amber-800/80 px-2 py-0.5 rounded font-mono">
        Phase 01: Foundation
      </span>
    </div>
  );
};
