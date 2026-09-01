import React, { useState, useEffect } from 'react';
import { useStationData } from '../../context/StationDataContext';
import {
  Radio, Satellite, Clock, AlertTriangle, ShieldAlert,
  Volume2, VolumeX, RefreshCw, User, Bell, ChevronRight
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const Topbar = () => {
  const {
    stationData,
    isLiveTelemetryActive,
    setIsLiveTelemetryActive,
    toggleStationLockdown,
    activeAudioAlarm
  } = useStationData();

  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const latestCriticalAlert = stationData?.alerts?.find(a => !a.acknowledged) || stationData?.alerts?.[0];
  const isLockdown = stationData?.station?.lockdownActive;

  // Format UTC and Polar Local Time
  const utcString = currentTime.toUTCString().slice(17, 25) + ' UTC';
  const polarLocalString = new Date(currentTime.getTime() + 5 * 3600000).toUTCString().slice(17, 25) + ' (UTC+5)';

  return (
    <header className="h-16 bg-[#161616] border-b border-[#262626] px-4 flex items-center justify-between gap-4 z-30 flex-shrink-0">
      {/* Left: Station Identity & Satellite Link */}
      <div className="flex items-center gap-4">
        {/* Live Stream Pulse */}
        <button
          onClick={() => setIsLiveTelemetryActive(!isLiveTelemetryActive)}
          className={`flex items-center gap-2 px-2.5 py-1 rounded-md text-xs font-scada-mono border transition ${isLiveTelemetryActive
            ? 'bg-green-500/10 text-green-400 border-green-500/30'
            : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30'
            }`}
          title="Click to toggle live telemetry polling simulation"
        >
          <span className={`w-2 h-2 rounded-full ${isLiveTelemetryActive ? 'bg-green-500 animate-pulse-green' : 'bg-yellow-500'}`} />
          <span>{isLiveTelemetryActive ? 'LIVE TELEMETRY' : 'PAUSED'}</span>
        </button>

        {/* Satellite Comms Badge */}
        <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-md bg-[#1E1E1E] border border-[#2A2A2A] text-xs font-scada-mono text-zinc-300">
          <Satellite className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-zinc-400">SATCOM:</span>
          <span className="text-cyan-300 font-medium">{stationData?.station?.telemetryLink?.satellite?.slice(0, 8)}</span>
          <span className="text-zinc-500">|</span>
          <span className="text-emerald-400 font-bold">{stationData?.station?.telemetryLink?.latencyMs} ms</span>
        </div>
      </div>

      {/* Center: Live Alert Marquee Ticker */}
      {latestCriticalAlert && (
        <div className="hidden md:flex flex-1 max-w-xl items-center gap-2 px-3 py-1.5 rounded-md bg-[#1C1515] border border-red-500/30 text-xs text-red-300 overflow-hidden">
          <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0 animate-pulse" />
          <span className="font-scada-mono font-bold text-red-400 flex-shrink-0">
            [{latestCriticalAlert.severity}]:
          </span>
          <span className="truncate font-sans text-zinc-200">
            {latestCriticalAlert.title}
          </span>
          <Link
            to="/alerts"
            className="ml-auto text-[10px] font-scada-mono text-red-400 hover:text-red-300 underline flex items-center flex-shrink-0"
          >
            VIEW <ChevronRight className="w-3 h-3" />
          </Link>
        </div>
      )}

      {/* Right: Master Clocks, Emergency Lockdown & Profile */}
      <div className="flex items-center gap-3">
        {/* SCADA Clocks */}
        <div className="hidden sm:flex flex-col items-end text-right font-scada-mono">
          <div className="flex items-center gap-1.5 text-xs font-bold text-white">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span>{utcString}</span>
          </div>
          <span className="text-[10px] text-zinc-400">POLAR STN: {polarLocalString}</span>
        </div>

        {/* Emergency Station Lockdown Button */}
        <button
          onClick={toggleStationLockdown}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-scada-mono font-bold transition shadow-md ${isLockdown
            ? 'bg-red-600 text-white animate-pulse border border-red-400 shadow-scada-red'
            : 'bg-[#221C1D] text-red-400 border border-red-900/60 hover:bg-red-950/50'
            }`}
          title="Toggle Station Emergency Lockdown Protocol"
        >
          <ShieldAlert className="w-4 h-4" />
          <span className="hidden sm:inline">{isLockdown ? 'LOCKDOWN ACTIVE' : 'LOCKDOWN'}</span>
        </button>

        {/* Officer Profile Badge */}
        <div className="flex items-center gap-2 pl-2 border-l border-[#262626]">
          <div className="w-8 h-8 rounded-full bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center text-cyan-300 font-bold text-xs">
            RS
          </div>
          <div className="hidden xl:block text-left font-sans">
            <div className="text-xs font-semibold text-white leading-tight">Dr. Rajeshwar Sharma</div>
            <div className="text-[10px] font-scada-mono text-zinc-400">STATION COMMANDER</div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Topbar;
