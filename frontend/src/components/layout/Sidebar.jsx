import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { useStationData } from '../../context/StationDataContext';
import {
  LayoutDashboard,
  Cpu,
  CloudSnow,
  Fuel,
  Zap,
  Boxes,
  Bell,
  TrendingUp,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  Shield,
  Radio,
  Compass,
  Lock,
  ShieldCheck,
  Building2
} from 'lucide-react';

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Mission Overview', icon: LayoutDashboard },
  { path: '/digital-twin', label: '2D Digital Twin', icon: Cpu, badge: 'LIVE 2D' },
  { path: '/weather', label: 'Polar Weather', icon: CloudSnow },
  { path: '/power', label: 'Power & Gensets', icon: Zap },
  { path: '/fuel', label: 'Cryo Fuel Farm', icon: Fuel },
  { path: '/inventory', label: 'Logistics & Spares', icon: Boxes },
  { path: '/alerts', label: 'Alarms & AI Logs', icon: Bell, showUnackAlertCount: true },
  { path: '/prediction', label: 'AI Forecast Twin', icon: TrendingUp, badge: 'AI' },
  { path: '/reports', label: 'SITREP & Export', icon: FileText },
  { path: '/settings', label: 'System & Sync', icon: Settings },
  { path: '/admin', label: 'Admin Console', icon: ShieldCheck, badge: 'RBAC', adminOnly: true },
];

export const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
  const { stationData, activeStation, userRole, rbac } = useStationData();

  const unackCriticalCount = stationData?.alerts?.filter(
    a => a.severity === 'CRITICAL' && !a.acknowledged
  ).length || 0;

  const totalUnack = stationData?.alerts?.filter(a => !a.acknowledged).length || 0;

  const brandName = activeStation === 'maitri' ? 'MAITRI-TWIN' : 'BHARATI-TWIN';
  const stationCode = activeStation === 'maitri' ? 'SIH26060-MTR' : 'SIH26060-BHR';

  return (
    <aside
      className={`relative z-40 bg-[#161616] dark:bg-[#161616] border-r border-[#262626] dark:border-[#262626] transition-all duration-300 flex flex-col flex-shrink-0 text-zinc-100 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Station Brand Header */}
      <div className="h-16 border-b border-[#262626] px-4 flex items-center justify-between bg-[#141414]">
        {!collapsed ? (
          <div className="flex items-center gap-3 overflow-hidden">
            <div className={`w-9 h-9 rounded-md flex items-center justify-center flex-shrink-0 border ${
              activeStation === 'maitri'
                ? 'bg-gradient-to-br from-amber-500/20 to-orange-600/30 border-amber-500/40 text-amber-400'
                : 'bg-gradient-to-br from-cyan-500/20 to-blue-600/30 border-cyan-500/40 text-cyan-400'
            }`}>
              <Compass className="w-5 h-5 animate-pulse-slow" />
            </div>
            <div className="truncate">
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-sm text-white tracking-wide">{brandName}</span>
                <span className={`text-[10px] font-scada-mono px-1 rounded border ${
                  activeStation === 'maitri'
                    ? 'bg-amber-950/60 text-amber-400 border-amber-800'
                    : 'bg-cyan-950/60 text-cyan-400 border-cyan-800'
                }`}>
                  {activeStation === 'maitri' ? 'MTR' : 'BHR'}
                </span>
              </div>
              <p className="text-[10px] font-scada-mono text-zinc-400 truncate">
                POLAR SCADA CONTROL
              </p>
            </div>
          </div>
        ) : (
          <div className={`mx-auto w-9 h-9 rounded-md flex items-center justify-center border ${
            activeStation === 'maitri'
              ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
              : 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'
          }`}>
            <Compass className="w-5 h-5" />
          </div>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded bg-[#1F1F1F] border border-[#2F2F2F] text-zinc-400 hover:text-white transition"
          title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-1.5">
        {NAV_ITEMS.map(item => {
          const Icon = item.icon;
          const isAdminRoute = item.adminOnly;
          const isLockedForRole = isAdminRoute && !rbac.canAccessAdmin;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-semibold shadow-scada-glow'
                    : isLockedForRole
                    ? 'text-zinc-500 hover:text-zinc-400 hover:bg-[#1A1A1A] border border-transparent opacity-80'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-[#1E1E1E] border border-transparent'
                }`
              }
              title={collapsed ? item.label : undefined}
            >
              <Icon className={`w-4 h-4 flex-shrink-0 ${
                isAdminRoute ? (rbac.canAccessAdmin ? 'text-purple-400' : 'text-zinc-500') : ''
              }`} />
              
              {!collapsed && (
                <span className="flex-1 truncate font-sans">
                  {item.label}
                </span>
              )}

              {/* Unacknowledged Alerts Count */}
              {!collapsed && item.showUnackAlertCount && totalUnack > 0 && (
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-scada-mono font-bold ${
                    unackCriticalCount > 0
                      ? 'bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse'
                      : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40'
                  }`}
                >
                  {totalUnack}
                </span>
              )}

              {/* Admin Lock / Unlock Badge */}
              {!collapsed && isAdminRoute && (
                <span className={`text-[9px] font-scada-mono px-1.5 py-0.5 rounded border flex items-center gap-1 ${
                  rbac.canAccessAdmin
                    ? 'bg-purple-950/60 text-purple-300 border-purple-800'
                    : 'bg-zinc-800 text-zinc-400 border-zinc-700'
                }`}>
                  {rbac.canAccessAdmin ? <ShieldCheck className="w-2.5 h-2.5" /> : <Lock className="w-2.5 h-2.5" />}
                  {item.badge}
                </span>
              )}

              {/* Standard Badges */}
              {!collapsed && item.badge && !isAdminRoute && (
                <span className="text-[9px] font-scada-mono px-1.5 py-0.5 rounded bg-[#2A2A2A] text-zinc-300 border border-[#3A3A3A]">
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer Station Health & Telemetry Status Card */}
      {!collapsed && (
        <div className="p-3 border-t border-[#262626] bg-[#141414] space-y-2">
          {/* Active Station Mode */}
          <div className="flex items-center justify-between text-[11px] font-scada-mono">
            <span className="text-zinc-500">STATION:</span>
            <span className={`font-bold flex items-center gap-1 ${
              activeStation === 'maitri' ? 'text-amber-400' : 'text-cyan-400'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${
                activeStation === 'maitri' ? 'bg-amber-400' : 'bg-cyan-400'
              } animate-pulse`} />
              {activeStation === 'maitri' ? 'MAITRI' : 'BHARATI'}
            </span>
          </div>

          {/* User Role Pill */}
          <div className="flex items-center justify-between text-[11px] font-scada-mono">
            <span className="text-zinc-500">ROLE:</span>
            <span className={`font-bold text-[10px] ${
              userRole === 'ANTARCTICA_EDGE'
                ? 'text-emerald-400'
                : userRole === 'INDIA_COMMAND'
                ? 'text-blue-400'
                : 'text-purple-400'
            }`}>
              {userRole === 'ANTARCTICA_EDGE' ? 'EDGE COMMANDER' : userRole === 'INDIA_COMMAND' ? 'INDIA HQ DIRECT' : 'SYSTEM ADMIN'}
            </span>
          </div>

          {/* Sync Mode */}
          <div className="flex items-center justify-between text-[11px] font-scada-mono">
            <span className="text-zinc-500">SAT FEED:</span>
            <span className="text-zinc-300">
              {rbac.isDelayedFeed ? '12m Mirror' : 'Real-Time Edge'}
            </span>
          </div>

          {/* Offline Cache Indicator */}
          <div className="p-2 rounded bg-[#1C1C1E] border border-[#2C2C2E] flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            <span className="text-[10px] font-scada-mono text-cyan-300">
              OFFLINE CACHE ACTIVE
            </span>
          </div>
        </div>
      )}
    </aside>
  );
};

export default Sidebar;
