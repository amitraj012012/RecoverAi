import React, { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  CreditCard,
  Layers,
  Sparkles,
  Sliders,
  Users,
  BarChart3,
  Settings,
  LogOut,
  Menu,
  X,
  ShieldCheck,
} from 'lucide-react';

const navigationItems = [
  { name: 'Overview', href: '/app/overview', icon: LayoutDashboard },
  { name: 'Payments', href: '/app/payments', icon: CreditCard },
  { name: 'Recovery Cases', href: '/app/recovery-cases', icon: Layers },
  { name: 'AI Decisions', href: '/app/ai-decisions', icon: Sparkles },
  { name: 'Simulator', href: '/app/simulator', icon: Sliders },
  { name: 'Customers', href: '/app/customers', icon: Users },
  { name: 'Analytics', href: '/app/analytics', icon: BarChart3 },
  { name: 'Settings', href: '/app/settings', icon: Settings },
];

export const DashboardLayout: React.FC = () => {
  const { user, signOut, isMockMode } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  const handleLogout = async () => {
    await signOut();
  };

  const getWorkspaceTitle = (): string => {
    if (!user?.email) return 'Enterprise Workspace';
    const namePart = user.email.split('@')[0].replace(/[^a-zA-Z0-9]/g, ' ').trim();
    if (!namePart) return 'Enterprise Workspace';
    return `${namePart.charAt(0).toUpperCase() + namePart.slice(1)} Workspace`;
  };

  const getShortMerchantId = (): string => {
    if (!user?.id) return 'Active';
    if (user.id.length > 18) {
      return `${user.id.slice(0, 8)}...${user.id.slice(-4)}`;
    }
    return user.id;
  };

  const getUserInitials = (): string => {
    if (!user?.email) return 'MW';
    const clean = user.email.replace(/[^a-zA-Z0-9]/g, '');
    return clean.slice(0, 2).toUpperCase() || 'MW';
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col lg:flex-row">
      {/* Mobile Top Header */}
      <div className="lg:hidden bg-[#0B1220] text-white px-4 py-3 flex items-center justify-between border-b border-slate-800 sticky top-0 z-30">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#2563EB] flex items-center justify-center font-bold text-white text-base">
            R
          </div>
          <span className="font-bold text-base tracking-tight">RecoverAI</span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 focus:outline-none"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Sidebar Navigation */}
      <aside
        className={`fixed inset-y-0 left-0 z-20 w-64 bg-[#0B1220] text-white flex flex-col justify-between transition-transform transform lg:translate-x-0 lg:static lg:inset-auto ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div>
          <div className="hidden lg:flex items-center justify-between px-6 h-16 border-b border-slate-800">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-lg bg-[#2563EB] flex items-center justify-center font-bold text-white text-lg shadow-sm">
                R
              </div>
              <div>
                <div className="font-bold text-base tracking-tight">RecoverAI</div>
                <div className="text-[10px] font-semibold tracking-wider text-slate-400 uppercase">
                  Merchant Workspace
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="px-3 py-4 space-y-1">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              return (
                <NavLink
                  key={item.name}
                  to={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center px-3 py-2.5 text-xs font-semibold rounded-lg transition-colors ${
                    isActive
                      ? 'bg-[#2563EB] text-white'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-4 h-4 mr-3 shrink-0" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* User Footer & Logout */}
        <div className="p-4 border-t border-slate-800 space-y-3">
          {isMockMode && (
            <div className="px-2.5 py-1.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-[10px] font-medium text-amber-300 flex items-center space-x-1.5">
              <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
              <span>Demo / Synthetic Mode</span>
            </div>
          )}

          <div className="flex items-center justify-between">
            <div className="truncate mr-2">
              <div className="text-xs font-semibold text-white truncate">
                {user?.email || 'merchant@demo.com'}
              </div>
              <div className="text-[10px] font-mono text-slate-400 truncate">
                ID: {getShortMerchantId()}
              </div>
            </div>

            <button
              onClick={handleLogout}
              title="Sign Out"
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Workspace Viewport */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <header className="hidden lg:flex items-center justify-between px-8 h-16 bg-white border-b border-[#E2E8F0] sticky top-0 z-10">
          <div>
            <span className="text-xs text-[#64748B] font-medium">Active Workspace</span>
            <h1 className="text-sm font-bold text-[#0F172A] capitalize">
              {location.pathname.split('/').pop()?.replace('-', ' ') || 'Overview'}
            </h1>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-right">
              <div className="text-xs font-semibold text-[#0F172A]">
                {getWorkspaceTitle()}
              </div>
              <div className="text-[10px] text-[#64748B] font-mono">
                Merchant ID: {getShortMerchantId()}
              </div>
            </div>
            <div className="w-8 h-8 rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center font-bold text-xs text-[#2563EB]">
              {getUserInitials()}
            </div>
          </div>
        </header>

        <div className="p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto space-y-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
