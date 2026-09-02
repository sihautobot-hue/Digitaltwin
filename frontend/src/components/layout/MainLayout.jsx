import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import { useStationData } from '../../context/StationDataContext';
import { ShieldAlert } from 'lucide-react';

export const MainLayout = () => {
  const { stationData } = useStationData();
  const isLockdown = stationData?.station?.lockdownActive;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 dark:bg-[#121212] text-slate-900 dark:text-zinc-100 scada-grid-bg transition-colors">
      {/* Left Navigation Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex flex-col flex-1 min-w-0 h-full overflow-hidden">
        {/* Top Control Bar */}
        <Topbar />

        {/* Lockdown Banner Notification (if triggered) */}
        {isLockdown && (
          <div className="bg-red-600/90 text-white px-4 py-1.5 flex items-center justify-between text-xs font-scada-mono font-bold animate-pulse border-b border-red-400">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4" />
              <span>DEFCON-1 EMERGENCY STATION LOCKDOWN IN EFFECT | ALL EXTERIOR AIRLOCKS SEALED</span>
            </div>
            <span>STATION PROTOCOL: SHELTER-IN-HABITAT</span>
          </div>
        )}

        {/* Scrollable Page Outlet */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;
