import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Construction, ArrowLeft, Layers, ShieldCheck, Clock } from 'lucide-react';

interface PlaceholderPageProps {
  title: string;
  marathiTitle?: string;
  plannedPhase: string;
  description: string;
  deliverables?: string[];
}

export const PlaceholderPage: React.FC<PlaceholderPageProps> = ({
  title,
  marathiTitle,
  plannedPhase,
  description,
  deliverables = [],
}) => {
  const navigate = useNavigate();

  return (
    <div className="max-w-3xl mx-auto py-10">
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 text-center">
        <div className="w-16 h-16 rounded-full bg-gov-gold/10 text-gov-gold mx-auto flex items-center justify-center mb-4">
          <Construction className="w-8 h-8 text-gov-gold" />
        </div>

        <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 text-slate-700 rounded-full text-xs font-semibold uppercase tracking-wider mb-2">
          <Clock className="w-3.5 h-3.5 text-gov-navy" />
          <span>Scheduled for {plannedPhase}</span>
        </div>

        <h2 className="text-2xl font-bold text-gov-navy">{title}</h2>
        {marathiTitle && (
          <p className="text-xs text-gov-gold-dark font-medium mt-0.5">{marathiTitle}</p>
        )}

        <p className="text-xs sm:text-sm text-slate-600 max-w-xl mx-auto mt-3 leading-relaxed">
          {description}
        </p>

        {deliverables.length > 0 && (
          <div className="mt-6 text-left bg-slate-50 border border-slate-200 rounded-lg p-4 max-w-lg mx-auto">
            <div className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Target Deliverables in {plannedPhase}:</span>
            </div>
            <ul className="space-y-1.5 text-xs text-slate-600">
              {deliverables.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <span className="text-gov-gold font-bold">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="mt-8 flex justify-center gap-3">
          <button
            onClick={() => navigate('/dashboard')}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-gov-navy hover:bg-gov-navy-light text-white text-xs font-bold rounded shadow-sm transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Dashboard</span>
          </button>
          <button
            onClick={() => navigate('/services')}
            className="inline-flex items-center gap-1.5 px-4 py-2 border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold rounded shadow-sm transition-colors"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Browse Services</span>
          </button>
        </div>
      </div>
    </div>
  );
};
