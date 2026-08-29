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
  AlertOctagon
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
];

export const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
  const { stationData } = useStationData();

  const unackCriticalCount = stationData?.alerts?.filter(
    a => a.severity === 'CRITICAL' && !a.acknowledged
  ).length || 0;

  const totalUnack = stationData?.alerts?.filter(a => !a.acknowledged).length || 0;

  return (
    <aside
      className={`relative z-40 bg-[#161616] border-r border-[#262626] transition-all duration-300 flex flex-col flex-shrink-0 ${collapsed ? 'w-20' : 'w-64'
        }`}
    >
      {/* Station Brand Header */}
      <div className="h-16 border-b border-[#262626] px-4 flex items-center justify-between bg-[#141414]">
        {!collapsed ? (
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-9 h-9 rounded-md bg-gradient-to-br from-cyan-500/20 to-blue-600/30 border border-cyan-500/40 flex items-center justify-center text-cyan-400 flex-shrink-0">
              <Compass className="w-5 h-5 animate-pulse-slow" />
            </div>
            <div className="truncate">
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-sm text-white tracking-wide">BHARATI-TWIN</span>
                <span className="text-[10px] font-scada-mono px-1 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                  {stationData?.station?.code || 'SIH26060'}
                </span>
              </div>
              <p className="text-[10px] font-scada-mono text-zinc-400 truncate">
                POLAR SCADA CONTROL
              </p>
            </div>
          </div>
        ) : (
          <div className="mx-auto w-9 h-9 rounded-md bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
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

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${isActive
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-semibold shadow-scada-glow'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-[#1E1E1E] border border-transparent'
                }`
              }
              title={collapsed ? item.label : undefined}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />

              {!collapsed && (
                <div className="flex-1 flex items-center justify-between truncate">
                  <span className="truncate">{item.label}</span>

                  {item.showUnackAlertCount && totalUnack > 0 && (
                    <span
                      className={`text-[10px] font-scada-mono font-bold px-1.5 py-0.5 rounded-full ${unackCriticalCount > 0
                          ? 'bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse'
                          : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40'
                        }`}
                    >
                      {totalUnack}
                    </span>
                  )}

                  {item.badge && (
                    <span className="text-[9px] font-scada-mono px-1 py-0.2 rounded bg-cyan-950/60 text-cyan-300 border border-cyan-800">
                      {item.badge}
                    </span>
                  )}
                </div>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Station Vital Indicator Footer */}
      {!collapsed ? (
        <div className="p-3 border-t border-[#262626] bg-[#141414] text-[11px] font-scada-mono space-y-2">
          <div className="flex items-center justify-between text-zinc-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse-green" />
              STATION STATUS
            </span>
            <span className="text-green-400 font-bold">NOMINAL</span>
          </div>

          <div className="flex items-center justify-between text-zinc-500 text-[10px]">
            <span>POLAR CYCLE</span>
            <span className="text-zinc-300">POLAR NIGHT</span>
          </div>

          <div className="flex items-center justify-between text-zinc-500 text-[10px]">
            <span>COORDINATES</span>
            <span className="text-cyan-400">69°S, 76°E</span>
          </div>
        </div>
      ) : (
        <div className="p-2 border-t border-[#262626] bg-[#141414] flex justify-center">
          <span className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse-green" title="Station Nominal" />
        </div>
      )}
    </aside>
  );
};

export default Sidebar;
