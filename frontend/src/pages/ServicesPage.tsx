import React, { useState } from 'react';
import { Search, Filter } from 'lucide-react';
import { MAHARASHTRA_REVENUE_SERVICES } from '../data/mockServices';
import { ServiceCard } from '../components/services/ServiceCard';
import { RevenueServiceItem } from '../types/service';

export const ServicesPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [selectedService, setSelectedService] = useState<RevenueServiceItem | null>(null);

  const filteredServices = MAHARASHTRA_REVENUE_SERVICES.filter((srv) => {
    const matchesSearch =
      srv.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      srv.marathiName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      srv.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      srv.description.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory =
      categoryFilter === 'ALL' || srv.category === categoryFilter;

    return matchesSearch && matchesCategory;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-200">
        <div>
          <div className="text-xs font-semibold text-gov-gold-dark uppercase tracking-wider">
            Maharashtra Right to Public Services Act (RTS) • Department Catalog
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-gov-navy mt-0.5">
            Revenue & Forest Department Services
          </h2>
        </div>
      </div>

      {/* Filter and Search */}
      <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm flex flex-col sm:flex-row items-center gap-3">
        <div className="relative flex-1 w-full">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search service name in English or मराठी, service code, or description..."
            className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-gov-navy outline-none"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-500 flex-shrink-0" />
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="w-full sm:w-48 py-2 px-3 border border-slate-300 rounded text-xs bg-white text-slate-700 font-medium outline-none"
          >
            <option value="ALL">All Categories ({MAHARASHTRA_REVENUE_SERVICES.length})</option>
            <option value="CERTIFICATE">Certificates</option>
            <option value="LAND_REVENUE">Land Records / 7-12</option>
            <option value="SOCIAL_WELFARE">Social Welfare</option>
            <option value="TAX_EXEMPTION">Tax & Solvency</option>
          </select>
        </div>
      </div>

      {/* Grid of Services */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredServices.map((service) => (
          <ServiceCard
            key={service.id}
            service={service}
            onApplyClick={(srv) => setSelectedService(srv)}
          />
        ))}
      </div>

      {/* Modal for Service Details */}
      {selectedService && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-start justify-between pb-3 mb-3 border-b border-slate-100">
              <div>
                <span className="text-xs font-mono font-bold text-gov-navy px-2 py-0.5 bg-slate-100 rounded">
                  {selectedService.code}
                </span>
                <h3 className="text-base font-bold text-slate-900 mt-1.5">
                  {selectedService.name}
                </h3>
                <div className="text-xs text-gov-gold-dark font-medium">
                  {selectedService.marathiName}
                </div>
              </div>
              <button
                onClick={() => setSelectedService(null)}
                className="text-slate-400 hover:text-slate-600 font-bold text-lg px-2"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed mb-4">
              {selectedService.description}
            </p>

            <div className="space-y-2.5 text-xs text-slate-700 bg-slate-50 p-3.5 rounded-lg border border-slate-200 mb-4">
              <div>
                <strong>Issuing Authority:</strong> {selectedService.issuingAuthority}
              </div>
              <div>
                <strong>Statutory Timeline (RTS Act):</strong> {selectedService.deliveryDays} Working Days
              </div>
              <div>
                <strong>Mandatory Verification Documents:</strong>
                <ul className="list-disc list-inside mt-1 space-y-0.5 text-slate-600">
                  {selectedService.requiredDocuments.map((doc, i) => (
                    <li key={i}>{doc}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="text-[11px] text-slate-500 italic mb-4">
              * Phase 01 Notice: Citizen application submissions are accepted via GovMesh API during live interoperability demonstration.
            </div>

            <button
              onClick={() => setSelectedService(null)}
              className="w-full py-2 bg-gov-navy text-white text-xs font-bold rounded"
            >
              Close Service Details
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
