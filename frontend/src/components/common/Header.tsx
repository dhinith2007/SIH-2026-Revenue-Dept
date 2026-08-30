import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Globe, ChevronDown, Check, User as UserIcon, LogOut, LogIn } from 'lucide-react';
import { PrototypeBanner } from './PrototypeBanner';
import { NotificationCenter } from '../notifications/NotificationCenter';
import { useAuth } from '../../context/AuthContext';

interface HeaderProps {
  currentLang?: 'en' | 'mr';
  onLanguageChange?: (lang: 'en' | 'mr') => void;
}

export const Header: React.FC<HeaderProps> = ({ currentLang = 'en', onLanguageChange }) => {
  const [lang, setLang] = useState<'en' | 'mr'>(currentLang);
  const [isLangDropdownOpen, setIsLangDropdownOpen] = useState(false);
  const { user, role, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleSelectLang = (selected: 'en' | 'mr') => {
    setLang(selected);
    setIsLangDropdownOpen(false);
    if (onLanguageChange) {
      onLanguageChange(selected);
    }
  };

  const getRoleDisplayName = (r: string | null) => {
    switch (r) {
      case 'REVENUE_OFFICER':
        return 'Revenue Officer';
      case 'SENIOR_REVENUE_OFFICER':
        return 'Senior Officer';
      case 'DEPARTMENT_ADMINISTRATOR':
        return 'Administrator';
      case 'READ_ONLY_AUDITOR':
        return 'Auditor (Read-Only)';
      default:
        return 'Officer';
    }
  };

  return (
    <header className="w-full bg-white shadow-sm border-b border-gov-border">
      <PrototypeBanner />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Left: Official Government & Department Identity */}
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 flex-shrink-0 bg-gov-navy rounded-full border-2 border-gov-gold flex items-center justify-center shadow-inner">
            <img
              src="/mahagov-seal.svg"
              alt="Government of Maharashtra Seal"
              className="w-10 h-10 object-contain"
              onError={(e) => {
                (e.target as HTMLElement).style.display = 'none';
              }}
            />
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-gov-gold-dark">
                {lang === 'mr' ? 'महाराष्ट्र शासन' : 'Government of Maharashtra'}
              </span>
              <span className="text-slate-300">|</span>
              <span className="text-xs font-medium text-slate-500">
                {lang === 'mr' ? 'शासकीय विभाग' : 'State Department'}
              </span>
            </div>

            <h1 className="text-lg md:text-xl font-bold text-gov-navy leading-tight tracking-tight">
              {lang === 'mr' ? 'महसूल व वन विभाग' : 'Revenue & Forest Department'}
            </h1>

            <p className="text-xs text-slate-600 font-medium">
              {lang === 'mr'
                ? 'विभागीय अधिकारी पोर्टल — जमीन महसूल व नागरिक सेवा'
                : 'Departmental Officer Portal — Land Revenue & Citizen Services'}
            </p>
          </div>
        </div>

        {/* Right: Controls, User Session, Language */}
        <div className="flex flex-wrap items-center gap-3 self-end md:self-center">
          {isAuthenticated && <NotificationCenter />}

          {isAuthenticated && user ? (
            /* Authenticated User Pill */
            <div className="flex items-center gap-3 bg-slate-50 border border-slate-200 rounded-lg p-1.5 pr-3 shadow-sm">
              <button
                onClick={() => navigate('/profile')}
                className="flex items-center gap-2 text-left hover:opacity-80 transition-opacity"
                title="View Profile"
              >
                <div className="w-8 h-8 rounded-full bg-gov-navy text-gov-gold flex items-center justify-center font-bold text-xs shadow-sm border border-gov-gold/40">
                  <UserIcon className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900 leading-tight">
                    {user.full_name.split(' (')[0]}
                  </div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className="text-[10px] font-bold px-1.5 py-0.2 bg-gov-navy text-gov-gold-light rounded">
                      {getRoleDisplayName(role)}
                    </span>
                    <span className="text-[10px] text-slate-400 hidden sm:inline">
                      • {user.division.split(' (')[0]}
                    </span>
                  </div>
                </div>
              </button>

              <div className="h-6 w-px bg-slate-200 ml-1"></div>

              <button
                onClick={logout}
                className="text-slate-500 hover:text-rose-600 p-1.5 rounded hover:bg-slate-100 transition-colors"
                title="Sign Out"
                aria-label="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <button
              onClick={() => navigate('/login')}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gov-navy hover:bg-gov-navy-light text-white rounded text-xs font-bold transition-colors shadow-sm"
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Officer Sign In</span>
            </button>
          )}

          {/* Language Selector Dropdown */}
          <div className="relative">
            <button
              onClick={() => setIsLangDropdownOpen(!isLangDropdownOpen)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md text-xs font-medium transition-colors border border-slate-200 focus:outline-none"
              aria-label="Select Portal Language"
            >
              <Globe className="w-3.5 h-3.5 text-gov-navy" />
              <span>{lang === 'en' ? 'English' : 'मराठी'}</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {isLangDropdownOpen && (
              <div className="absolute right-0 mt-1 w-32 bg-white rounded-md shadow-lg border border-slate-200 py-1 z-50">
                <button
                  onClick={() => handleSelectLang('en')}
                  className="w-full text-left px-3 py-1.5 text-xs text-slate-700 hover:bg-slate-50 flex items-center justify-between"
                >
                  <span>English</span>
                  {lang === 'en' && <Check className="w-3.5 h-3.5 text-gov-navy" />}
                </button>
                <button
                  onClick={() => handleSelectLang('mr')}
                  className="w-full text-left px-3 py-1.5 text-xs text-slate-700 hover:bg-slate-50 flex items-center justify-between"
                >
                  <span>मराठी (Marathi)</span>
                  {lang === 'mr' && <Check className="w-3.5 h-3.5 text-gov-navy" />}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
