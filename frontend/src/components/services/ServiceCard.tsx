import React from 'react';
import { RevenueServiceItem } from '../../types/service';
import { Clock, Building2, Check, ArrowRight } from 'lucide-react';

interface ServiceCardProps {
  service: RevenueServiceItem;
  onApplyClick?: (service: RevenueServiceItem) => void;
}

export const ServiceCard: React.FC<ServiceCardProps> = ({ service, onApplyClick }) => {
  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm hover:shadow-md transition-shadow p-5 flex flex-col justify-between">
      <div>
        {/* Top Badges */}
        <div className="flex items-center justify-between gap-2 mb-2.5">
          <span className="text-[10px] font-mono font-bold px-2 py-0.5 bg-slate-100 text-slate-700 rounded border border-slate-200">
            {service.code}
          </span>
          {service.isPopular && (
            <span className="text-[10px] font-bold px-2 py-0.5 bg-amber-50 text-amber-800 rounded-full border border-amber-200 uppercase">
              Frequent Service
            </span>
          )}
        </div>

        {/* Title */}
        <h3 className="text-base font-bold text-gov-navy leading-snug">
          {service.name}
        </h3>
        <p className="text-xs text-gov-gold-dark font-medium mt-0.5">
          {service.marathiName}
        </p>

        {/* Description */}
        <p className="text-xs text-slate-600 mt-2.5 leading-relaxed">
          {service.description}
        </p>

        {/* Meta details */}
        <div className="mt-4 pt-3 border-t border-slate-100 space-y-1.5 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <Clock className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
            <span>Delivery Timeline: <strong>{service.deliveryDays} Working Days</strong></span>
          </div>
          <div className="flex items-center gap-2">
            <Building2 className="w-3.5 h-3.5 text-slate-400 flex-shrink-0" />
            <span className="truncate">Authority: <strong>{service.issuingAuthority}</strong></span>
          </div>
        </div>

        {/* Required Documents Preview */}
        <div className="mt-3 bg-slate-50 p-2.5 rounded text-[11px] text-slate-600 border border-slate-100">
          <div className="font-semibold text-slate-700 mb-1">Key Proof Documents:</div>
          <ul className="space-y-0.5">
            {service.requiredDocuments.slice(0, 2).map((doc, idx) => (
              <li key={idx} className="flex items-center gap-1">
                <Check className="w-3 h-3 text-emerald-600 flex-shrink-0" />
                <span className="truncate">{doc}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Action footer */}
      <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between">
        <span className="text-[11px] text-slate-400">GovMesh Interop: Enabled</span>
        <button
          onClick={() => onApplyClick && onApplyClick(service)}
          className="inline-flex items-center gap-1 text-xs font-semibold text-gov-navy hover:text-gov-gold-dark group transition-colors"
        >
          <span>Service Details</span>
          <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
        </button>
      </div>
    </div>
  );
};
