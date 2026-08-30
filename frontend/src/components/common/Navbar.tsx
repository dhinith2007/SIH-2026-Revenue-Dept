import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Layers,
  History,
  Activity,
  Users,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Menu,
  X,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Navbar: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { role, isAuthenticated } = useAuth();

  // Define role-specific navigation items
  const getNavItems = () => {
    if (!isAuthenticated || !role) {
      return [
        { name: 'Revenue Services', path: '/services', icon: Layers },
        { name: 'System Health', path: '/health', icon: Activity },
      ];
    }

    switch (role) {
      case 'DEPARTMENT_ADMINISTRATOR':
        return [
          { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
          { name: 'User Management', path: '/admin/users', icon: Users },
          { name: 'Completed Ledger', path: '/applications/completed', icon: CheckCircle2 },
          { name: 'System Health', path: '/health', icon: Activity },
          { name: 'Audit Log', path: '/audit', icon: History },
        ];
      case 'SENIOR_REVENUE_OFFICER':
        return [
          { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
          { name: 'All Applications', path: '/applications', icon: FileText },
          { name: 'Action Required', path: '/applications/action-required', icon: AlertTriangle },
          { name: 'Completed Ledger', path: '/applications/completed', icon: CheckCircle2 },
          { name: 'Rejected Register', path: '/applications/rejected', icon: XCircle },
          { name: 'Audit Log', path: '/audit', icon: History },
        ];
      case 'READ_ONLY_AUDITOR':
        return [
          { name: 'Audit Log', path: '/audit', icon: History },
          { name: 'Completed Ledger', path: '/applications/completed', icon: CheckCircle2 },
          { name: 'Rejected Register', path: '/applications/rejected', icon: XCircle },
          { name: 'System Health', path: '/health', icon: Activity },
        ];
      case 'REVENUE_OFFICER':
      default:
        return [
          { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
          { name: 'Applications Queue', path: '/applications', icon: FileText },
          { name: 'Action Required', path: '/applications/action-required', icon: AlertTriangle },
          { name: 'Completed Ledger', path: '/applications/completed', icon: CheckCircle2 },
          { name: 'Rejected Register', path: '/applications/rejected', icon: XCircle },
          { name: 'Audit Log', path: '/audit', icon: History },
        ];
    }
  };

  const navItems = getNavItems();

  return (
    <nav className="bg-gov-navy text-white shadow-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-12">
          {/* Left Navigation Links */}
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-3.5 py-2 rounded text-xs font-semibold tracking-wide transition-colors ${
                      isActive
                        ? 'bg-gov-navy-light text-gov-gold-light border-b-2 border-gov-gold shadow-sm'
                        : 'text-slate-200 hover:bg-gov-navy-muted/50 hover:text-white'
                    }`
                  }
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </div>

          {/* Right Status Badge */}
          <div className="hidden md:flex items-center space-x-3">
            {isAuthenticated && role && (
              <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-gov-navy-light text-gov-gold-pale border border-gov-navy-muted">
                Role: {role.replace(/_/g, ' ')}
              </span>
            )}
          </div>

          {/* Mobile Menu Toggle Button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-1.5 rounded-md text-slate-200 hover:text-white hover:bg-gov-navy-light focus:outline-none"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-gov-navy-dark border-t border-gov-navy-light px-4 pt-2 pb-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium ${
                    isActive
                      ? 'bg-gov-navy-light text-gov-gold font-semibold'
                      : 'text-slate-200 hover:bg-gov-navy-muted'
                  }`
                }
              >
                <Icon className="w-4 h-4" />
                <span>{item.name}</span>
              </NavLink>
            );
          })}
        </div>
      )}
    </nav>
  );
};
