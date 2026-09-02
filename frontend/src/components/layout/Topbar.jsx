import React, { useState, useEffect, useRef } from 'react';
import { useStationData } from '../../context/StationDataContext';
import {
  Satellite, Clock, AlertTriangle, ShieldAlert,
  Sun, Moon, ChevronDown, Check, User, ShieldCheck,
  Building2, Radio, Lock, Eye, AlertOctagon, HelpCircle
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const Topbar = () => {
  const {
    stationData,
    activeStation,
    setActiveStation,
    theme,
    toggleTheme,
    currentUser,
    userRole,
    setUserRole,
    rbac,
    isLiveTelemetryActive,
    setIsLiveTelemetryActive,
    toggleStationLockdown
  } = useStationData();

  const [currentTime, setCurrentTime] = useState(new Date());
  const [stationDropdownOpen, setStationDropdownOpen] = useState(false);
  const [roleDropdownOpen, setRoleDropdownOpen] = useState(false);

  const stationMenuRef = useRef(null);
  const roleMenuRef = useRef(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (stationMenuRef.current && !stationMenuRef.current.contains(e.target)) {
        setStationDropdownOpen(false);
      }
      if (roleMenuRef.current && !roleMenuRef.current.contains(e.target)) {
        setRoleDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // SCADA Master Clock Tick
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const latestCriticalAlert = stationData?.alerts?.find(a => !a.acknowledged) || stationData?.alerts?.[0];
  const isLockdown = stationData?.station?.lockdownActive;

  // Format UTC and Polar Local Time
  const utcString = currentTime.toUTCString().slice(17, 25) + ' UTC';
  const polarLocalString = new Date(currentTime.getTime() + 5 * 3600000).toUTCString().slice(17, 25) + ' (UTC+5)';

  const stationOptions = [
    {
      id: 'maitri',
      name: 'Maitri Station',
      code: 'SIH26060-MTR',
      region: 'Schirmacher Oasis, Queen Maud Land',
      coords: "-70°45'57\" S, 11°44'09\" E",
      badgeColor: 'text-amber-400 bg-amber-500/10 border-amber-500/30'
    },
    {
      id: 'bharati',
      name: 'Bharati Station',
      code: 'SIH26060-BHR',
      region: 'Larsemann Hills, Princess Elizabeth Land',
      coords: "-69°24'27\" S, 76°11'43\" E",
      badgeColor: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30'
    }
  ];

  const roleOptions = [
    {
      role: 'ANTARCTICA_EDGE',
      label: 'Antarctica Edge User',
      desc: 'Station Commander / Scientist (Full realtime, alert ACK, lockdown, inventory input)',
      badgeColor: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
    },
    {
      role: 'INDIA_COMMAND',
      label: 'India Command Center',
      desc: 'NCPOR Goa HQ (Delayed satellite mirror, read-only telemetry, AI forecasts)',
      badgeColor: 'bg-blue-500/10 text-blue-400 border-blue-500/30'
    },
    {
      role: 'SYSTEM_ADMIN',
      label: 'System Admin',
      desc: 'Cyber Cell & Network Ops (Full /admin route access, audit logs, role management)',
      badgeColor: 'bg-purple-500/10 text-purple-400 border-purple-500/30'
    }
  ];

  return (
    <header className="h-16 bg-white dark:bg-[#161616] border-b border-slate-200 dark:border-[#262626] px-3 md:px-4 flex items-center justify-between gap-3 z-30 flex-shrink-0 transition-colors">
      {/* Left: Station Toggle Dropdown & Satellite Link */}
      <div className="flex items-center gap-3">
        {/* Persistent Station Selector Dropdown */}
        <div className="relative" ref={stationMenuRef}>
          <button
            onClick={() => setStationDropdownOpen(!stationDropdownOpen)}
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-[#1E1E1E] dark:hover:bg-[#252525] border border-slate-300 dark:border-[#2A2A2A] text-xs font-scada-mono transition"
            title="Toggle Polar Station Telemetry Stream"
          >
            <Building2 className="w-4 h-4 text-cyan-600 dark:text-cyan-400 flex-shrink-0" />
            <div className="text-left hidden sm:block">
              <div className="font-bold text-slate-800 dark:text-white leading-tight flex items-center gap-1.5">
                <span>{activeStation === 'maitri' ? 'Maitri Station' : 'Bharati Station'}</span>
                <span className={`text-[9px] px-1 py-0.2 rounded border font-semibold ${
                  activeStation === 'maitri' 
                    ? 'text-amber-600 dark:text-amber-400 border-amber-500/30 bg-amber-500/10' 
                    : 'text-cyan-600 dark:text-cyan-400 border-cyan-500/30 bg-cyan-500/10'
                }`}>
                  {activeStation === 'maitri' ? 'MTR' : 'BHR'}
                </span>
              </div>
            </div>
            <ChevronDown className={`w-3.5 h-3.5 text-slate-400 dark:text-zinc-400 transition-transform ${stationDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {/* Station Dropdown Menu */}
          {stationDropdownOpen && (
            <div className="absolute left-0 mt-2 w-72 rounded-xl bg-white dark:bg-[#1A1A1A] border border-slate-200 dark:border-[#2F2F2F] shadow-2xl py-1.5 z-50 animate-in fade-in zoom-in-95">
              <div className="px-3 py-1.5 border-b border-slate-100 dark:border-[#262626] text-[10px] font-scada-mono text-slate-400 dark:text-zinc-400 uppercase tracking-wider">
                Select Active Polar Research Station
              </div>
              {stationOptions.map(st => {
                const isSelected = activeStation === st.id;
                return (
                  <button
                    key={st.id}
                    onClick={() => {
                      setActiveStation(st.id);
                      setStationDropdownOpen(false);
                    }}
                    className={`w-full px-3 py-2 text-left flex items-start justify-between transition ${
                      isSelected 
                        ? 'bg-cyan-500/10 dark:bg-cyan-950/40 text-cyan-600 dark:text-cyan-400' 
                        : 'hover:bg-slate-50 dark:hover:bg-[#222222] text-slate-700 dark:text-zinc-200'
                    }`}
                  >
                    <div>
                      <div className="text-xs font-bold flex items-center gap-1.5">
                        <span>{st.name}</span>
                        <span className="text-[10px] font-scada-mono text-slate-400 dark:text-zinc-400">({st.code})</span>
                      </div>
                      <div className="text-[10px] text-slate-500 dark:text-zinc-400 mt-0.5">{st.region}</div>
                      <div className="text-[9px] font-scada-mono text-slate-400 dark:text-zinc-500">{st.coords}</div>
                    </div>
                    {isSelected && <Check className="w-4 h-4 text-cyan-500 flex-shrink-0 mt-0.5" />}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Live Stream Pulse */}
        <button
          onClick={() => setIsLiveTelemetryActive(!isLiveTelemetryActive)}
          className={`hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-md text-xs font-scada-mono border transition ${
            isLiveTelemetryActive
              ? 'bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/30'
              : 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/30'
          }`}
          title="Click to toggle live telemetry polling simulation"
        >
          <span className={`w-2 h-2 rounded-full ${isLiveTelemetryActive ? 'bg-green-500 animate-pulse-green' : 'bg-yellow-500'}`} />
          <span>{isLiveTelemetryActive ? 'LIVE TELEMETRY' : 'PAUSED'}</span>
        </button>

        {/* India Command Delayed Stream Indicator (RBAC) */}
        {rbac.isDelayedFeed && (
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-blue-500/15 border border-blue-500/40 text-blue-600 dark:text-blue-300 text-xs font-scada-mono font-medium animate-pulse" title="Simulated Store-and-Forward delay for India Command Center mirror">
            <Radio className="w-3.5 h-3.5 text-blue-500" />
            <span className="hidden lg:inline">INDIA HQ FEED:</span>
            <span>~12M SYNC DELAY (READ-ONLY)</span>
          </div>
        )}
      </div>

      {/* Center: Live Alert Marquee Ticker */}
      {latestCriticalAlert && !rbac.isDelayedFeed && (
        <div className="hidden xl:flex flex-1 max-w-md items-center gap-2 px-3 py-1.5 rounded-md bg-red-500/10 border border-red-500/30 text-xs text-red-600 dark:text-red-300 overflow-hidden">
          <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0 animate-pulse" />
          <span className="font-scada-mono font-bold text-red-600 dark:text-red-400 flex-shrink-0">
            [{latestCriticalAlert.severity}]:
          </span>
          <span className="truncate font-sans text-slate-700 dark:text-zinc-200">
            {latestCriticalAlert.title}
          </span>
          <Link
            to="/alerts"
            className="ml-auto text-[10px] font-scada-mono text-red-600 dark:text-red-400 hover:underline flex items-center flex-shrink-0"
          >
            VIEW
          </Link>
        </div>
      )}

      {/* Right: RBAC Role Switcher, Theme Toggle, Clocks & Lockdown */}
      <div className="flex items-center gap-2.5">
        {/* RBAC Role Selector Dropdown */}
        <div className="relative" ref={roleMenuRef}>
          <button
            onClick={() => setRoleDropdownOpen(!roleDropdownOpen)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-scada-mono transition ${
              userRole === 'ANTARCTICA_EDGE'
                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20'
                : userRole === 'INDIA_COMMAND'
                ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30 hover:bg-blue-500/20'
                : 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30 hover:bg-purple-500/20'
            }`}
            title="Switch Active Simulated Role (RBAC)"
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span className="font-bold hidden sm:inline">
              {userRole === 'ANTARCTICA_EDGE' ? 'EDGE COMMANDER' : userRole === 'INDIA_COMMAND' ? 'INDIA HQ DIRECTOR' : 'SYS ADMIN'}
            </span>
            <ChevronDown className="w-3 h-3 opacity-70" />
          </button>

          {/* Role Dropdown Menu */}
          {roleDropdownOpen && (
            <div className="absolute right-0 mt-2 w-80 rounded-xl bg-white dark:bg-[#1A1A1A] border border-slate-200 dark:border-[#2F2F2F] shadow-2xl py-1.5 z-50 animate-in fade-in zoom-in-95">
              <div className="px-3 py-1.5 border-b border-slate-100 dark:border-[#262626] text-[10px] font-scada-mono text-slate-400 dark:text-zinc-400 uppercase tracking-wider">
                Switch Role-Based Access (RBAC)
              </div>
              {roleOptions.map(opt => {
                const isSelected = userRole === opt.role;
                return (
                  <button
                    key={opt.role}
                    onClick={() => {
                      setUserRole(opt.role);
                      setRoleDropdownOpen(false);
                    }}
                    className={`w-full px-3 py-2 text-left flex items-start justify-between transition ${
                      isSelected 
                        ? 'bg-slate-100 dark:bg-[#252525]' 
                        : 'hover:bg-slate-50 dark:hover:bg-[#202020]'
                    }`}
                  >
                    <div>
                      <div className="text-xs font-bold flex items-center gap-1.5">
                        <span className="text-slate-900 dark:text-white">{opt.label}</span>
                        <span className={`text-[9px] px-1 rounded border font-scada-mono ${opt.badgeColor}`}>
                          {opt.role.split('_')[0]}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-500 dark:text-zinc-400 mt-0.5 leading-snug">
                        {opt.desc}
                      </div>
                    </div>
                    {isSelected && <Check className="w-4 h-4 text-cyan-500 flex-shrink-0 mt-1" />}
                  </button>
                );
              })}
              {userRole === 'SYSTEM_ADMIN' && (
                <div className="mt-1 pt-1 border-t border-slate-100 dark:border-[#262626] px-3 py-1">
                  <Link
                    to="/admin"
                    onClick={() => setRoleDropdownOpen(false)}
                    className="text-xs text-purple-600 dark:text-purple-400 hover:underline flex items-center gap-1 font-bold"
                  >
                    Open Admin Console →
                  </Link>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Theme Toggle Button (Sun / Moon) */}
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-[#1E1E1E] dark:hover:bg-[#252525] border border-slate-300 dark:border-[#2A2A2A] text-slate-700 dark:text-zinc-300 transition"
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? (
            <Sun className="w-4 h-4 text-amber-400 hover:rotate-45 transition-transform" />
          ) : (
            <Moon className="w-4 h-4 text-slate-700 hover:-rotate-12 transition-transform" />
          )}
        </button>

        {/* SCADA Clocks */}
        <div className="hidden lg:flex flex-col items-end text-right font-scada-mono">
          <div className="flex items-center gap-1 text-xs font-bold text-slate-800 dark:text-white">
            <Clock className="w-3 h-3 text-cyan-600 dark:text-cyan-400" />
            <span>{utcString}</span>
          </div>
          <span className="text-[10px] text-slate-500 dark:text-zinc-400">POLAR: {polarLocalString}</span>
        </div>

        {/* Emergency Station Lockdown Button (Disabled for India Command) */}
        <button
          onClick={rbac.canTriggerLockdown ? toggleStationLockdown : undefined}
          disabled={!rbac.canTriggerLockdown}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-scada-mono font-bold transition shadow-md ${
            !rbac.canTriggerLockdown
              ? 'bg-slate-100 dark:bg-[#1A1A1A] text-slate-400 dark:text-zinc-600 border border-slate-200 dark:border-[#2A2A2A] cursor-not-allowed opacity-60'
              : isLockdown
              ? 'bg-red-600 text-white animate-pulse border border-red-400 shadow-scada-red'
              : 'bg-red-50 dark:bg-[#221C1D] text-red-600 dark:text-red-400 border border-red-200 dark:border-red-900/60 hover:bg-red-100 dark:hover:bg-red-950/50'
          }`}
          title={
            !rbac.canTriggerLockdown
              ? 'Emergency lockdown restricted to on-site Antarctica Edge Commander'
              : 'Toggle Station Emergency Lockdown Protocol'
          }
        >
          {rbac.canTriggerLockdown ? (
            <ShieldAlert className="w-4 h-4" />
          ) : (
            <Lock className="w-3.5 h-3.5" />
          )}
          <span className="hidden sm:inline">{isLockdown ? 'LOCKDOWN ACTIVE' : 'LOCKDOWN'}</span>
        </button>

        {/* Officer Profile Badge */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-200 dark:border-[#262626]">
          <div className="w-8 h-8 rounded-full bg-cyan-100 dark:bg-cyan-950/80 border border-cyan-400/40 flex items-center justify-center text-cyan-800 dark:text-cyan-300 font-bold text-xs">
            {currentUser?.avatarInitials || currentUser?.name?.split(' ').map(n => n[0]).slice(0, 2).join('') || 'OP'}
          </div>
          <div className="hidden 2xl:block text-left font-sans">
            <div className="text-xs font-semibold text-slate-800 dark:text-white leading-tight">
              {currentUser?.name || 'Mission Officer'}
            </div>
            <div className="text-[10px] font-scada-mono text-slate-500 dark:text-zinc-400">
              {currentUser?.title?.slice(0, 24) || 'SCADA CONTROLLER'}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
