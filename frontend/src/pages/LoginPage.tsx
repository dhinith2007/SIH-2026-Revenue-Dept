import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Lock,
  User,
  Shield,
  RefreshCw,
  ArrowRight,
  FileCheck2,
  LandPlot,
  Building,
  AlertCircle,
  KeyRound,
  ShieldCheck,
} from 'lucide-react';
import { MAHARASHTRA_REVENUE_SERVICES } from '../data/mockServices';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();

  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [captchaInput, setCaptchaInput] = useState('');
  const [captchaCode, setCaptchaCode] = useState('7M9K2P');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // If already authenticated, redirect to dashboard
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const refreshCaptcha = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let result = '';
    for (let i = 0; i < 6; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setCaptchaCode(result);
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim() || !password.trim()) {
      setError('Please provide your Username/Email/Mobile and Password.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await login(identifier.trim(), password.trim());
      const from = (location.state as any)?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err?.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoLogin = async (demoIdent: string, demoPw: string) => {
    setIdentifier(demoIdent);
    setPassword(demoPw);
    setLoading(true);
    setError(null);
    try {
      await login(demoIdent, demoPw);
      const from = (location.state as any)?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err?.message || 'Demo login failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-10">
      {/* Top Welcome & Department Hero */}
      <div className="bg-gradient-to-r from-gov-navy via-gov-navy-light to-gov-navy rounded-xl p-6 sm:p-8 text-white shadow-md border-b-4 border-gov-gold">
        <div className="max-w-3xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-gov-gold/20 text-gov-gold-pale rounded-full text-xs font-semibold uppercase tracking-wider mb-3 border border-gov-gold/40">
            <span>GovMesh SIH26129 Prototype</span>
            <span>•</span>
            <span>Department 1 (Revenue & Forest)</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Revenue & Forest Department Portal
          </h2>
          <p className="text-slate-200 text-sm sm:text-base mt-2 leading-relaxed">
            Welcome to the simulated departmental officer system for the Government of Maharashtra. Access land record verifications, citizen revenue certificates, and GovMesh cross-departmental address update workflows with role-based access control.
          </p>
        </div>
      </div>

      {/* Main Login & Portal Intro Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Col: Portal Highlights & Services */}
        <div className="lg:col-span-7 space-y-6">
          <div className="bg-white rounded-lg p-6 border border-slate-200 shadow-sm">
            <h3 className="text-base font-bold text-gov-navy mb-3 flex items-center gap-2">
              <Building className="w-5 h-5 text-gov-gold" />
              <span>Departmental Officer Portal Functions</span>
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed mb-4">
              This portal provides role-restricted access for designated Revenue Officers (Tahsildars, Nayab Tahsildars, Circle Officers, and Talathis) across Maharashtra to process citizen applications and execute verified departmental address synchronization.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-start gap-2.5">
                <FileCheck2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-bold text-slate-800">Address Change Sync</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    Process simulated address updates received via GovMesh interoperability.
                  </div>
                </div>
              </div>

              <div className="p-3 bg-slate-50 rounded border border-slate-100 flex items-start gap-2.5">
                <LandPlot className="w-4 h-4 text-gov-navy flex-shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-bold text-slate-800">Land & 7/12 Records</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">
                    Cross-verify village land registers, survey plots, and mutation ferfar entries.
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Revenue Services Quick Spotlight */}
          <div className="bg-white rounded-lg p-6 border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold text-gov-navy uppercase tracking-wide">
                Key Revenue Services Catalog
              </h3>
              <button
                onClick={() => navigate('/services')}
                className="text-xs text-gov-gold-dark font-semibold hover:underline flex items-center gap-1"
              >
                <span>View All 9 Services</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {MAHARASHTRA_REVENUE_SERVICES.slice(0, 4).map((srv) => (
                <div
                  key={srv.id}
                  className="p-3 border border-slate-100 rounded-md bg-slate-50 hover:bg-slate-100/80 transition-colors"
                >
                  <div className="text-xs font-bold text-slate-800 truncate">{srv.name}</div>
                  <div className="text-[10px] text-slate-500 mt-0.5">{srv.marathiName}</div>
                  <div className="text-[10px] text-gov-gold-dark font-medium mt-1">
                    Timeline: {srv.deliveryDays} Days
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Col: Department Login Form */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white rounded-xl border-2 border-slate-200 shadow-md p-6 sm:p-7 relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1.5 bg-gov-gold"></div>

            <div className="text-center pb-4 mb-4 border-b border-slate-100">
              <div className="w-12 h-12 rounded-full bg-gov-navy/10 text-gov-navy mx-auto flex items-center justify-center mb-2">
                <Shield className="w-6 h-6 text-gov-navy" />
              </div>
              <h3 className="text-lg font-bold text-slate-900">Departmental Officer Login</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Sign in with Username, Email, or Mobile
              </p>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded text-rose-800 text-xs flex items-start gap-2 animate-fade-in">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleLoginSubmit} className="space-y-4">
              {/* Username / Mobile / Email Field */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Username / Mobile / Email ID
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <User className="w-4 h-4" />
                  </div>
                  <input
                    type="text"
                    value={identifier}
                    onChange={(e) => setIdentifier(e.target.value)}
                    placeholder="e.g. revenue.officer or officer.pune@revenue.gov.in"
                    className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-gov-navy focus:border-gov-navy outline-none"
                    required
                  />
                </div>
              </div>

              {/* Password Field */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Password
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password"
                    className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-gov-navy focus:border-gov-navy outline-none"
                    required
                  />
                </div>
              </div>

              {/* CAPTCHA Shell */}
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Security Code (CAPTCHA)
                </label>
                <div className="flex items-center gap-2 mb-2">
                  <div className="flex-1 bg-slate-200 border border-slate-300 rounded py-1.5 px-4 text-center font-mono font-bold tracking-widest text-slate-800 select-none line-through decoration-slate-400 text-sm">
                    {captchaCode}
                  </div>
                  <button
                    type="button"
                    onClick={refreshCaptcha}
                    className="p-2 border border-slate-200 rounded hover:bg-slate-100 text-slate-600 transition-colors"
                    title="Refresh CAPTCHA"
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                </div>
                <input
                  type="text"
                  value={captchaInput}
                  onChange={(e) => setCaptchaInput(e.target.value)}
                  placeholder="Enter 6-character code"
                  className="w-full px-3 py-2 border border-slate-300 rounded text-xs focus:ring-2 focus:ring-gov-navy outline-none uppercase font-mono"
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2.5 bg-gov-navy hover:bg-gov-navy-light text-white font-bold rounded text-xs tracking-wider uppercase transition-colors shadow-sm focus:ring-2 focus:ring-offset-2 focus:ring-gov-navy flex items-center justify-center gap-2"
              >
                <KeyRound className="w-4 h-4 text-gov-gold" />
                <span>{loading ? 'Authenticating Officer...' : 'Sign In to Department Portal'}</span>
              </button>
            </form>
          </div>

          {/* Quick Demo Role Switcher Box for SIH Demonstration */}
          <div className="bg-slate-50 rounded-xl border border-slate-300 p-4 shadow-sm">
            <div className="flex items-center gap-2 text-xs font-bold text-gov-navy uppercase tracking-wide mb-2.5">
              <ShieldCheck className="w-4 h-4 text-gov-gold" />
              <span>SIH Demonstration: One-Click Demo Logins</span>
            </div>
            <p className="text-[11px] text-slate-500 mb-3">
              Click any role to test distinct RBAC permissions and route access:
            </p>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                onClick={() => handleQuickDemoLogin('revenue.officer', 'Officer@2026')}
                className="p-2 bg-white hover:bg-slate-100 text-left border border-slate-200 rounded font-semibold text-slate-800 transition-colors shadow-2xs"
              >
                <div className="text-gov-navy font-bold text-[11px]">Revenue Officer</div>
                <div className="text-[10px] text-slate-400">@revenue.officer</div>
              </button>

              <button
                onClick={() => handleQuickDemoLogin('senior.officer', 'Senior@2026')}
                className="p-2 bg-white hover:bg-slate-100 text-left border border-slate-200 rounded font-semibold text-slate-800 transition-colors shadow-2xs"
              >
                <div className="text-gov-navy font-bold text-[11px]">Senior Officer</div>
                <div className="text-[10px] text-slate-400">@senior.officer</div>
              </button>

              <button
                onClick={() => handleQuickDemoLogin('revenue.admin', 'Admin@2026')}
                className="p-2 bg-white hover:bg-slate-100 text-left border border-slate-200 rounded font-semibold text-slate-800 transition-colors shadow-2xs"
              >
                <div className="text-gov-navy font-bold text-[11px]">Administrator</div>
                <div className="text-[10px] text-slate-400">@revenue.admin</div>
              </button>

              <button
                onClick={() => handleQuickDemoLogin('revenue.auditor', 'Auditor@2026')}
                className="p-2 bg-white hover:bg-slate-100 text-left border border-slate-200 rounded font-semibold text-slate-800 transition-colors shadow-2xs"
              >
                <div className="text-gov-navy font-bold text-[11px]">Read-only Auditor</div>
                <div className="text-[10px] text-slate-400">@revenue.auditor</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
