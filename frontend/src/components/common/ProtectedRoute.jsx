import React from 'react';
import { useStationData } from '../../context/StationDataContext';
import { ShieldAlert, Lock, ArrowLeft, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

export const ProtectedRoute = ({ children, requiredRole = 'SYSTEM_ADMIN' }) => {
  const { userRole, setUserRole, currentUser } = useStationData();

  if (userRole !== requiredRole) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center p-4">
        <div className="w-full max-w-xl bg-white dark:bg-[#1A1A1A] border border-red-500/30 rounded-2xl p-6 md:p-8 shadow-2xl relative overflow-hidden text-center">
          <div className="absolute top-0 inset-x-0 h-1.5 bg-gradient-to-r from-red-600 via-amber-500 to-red-600" />
          
          <div className="mx-auto w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/40 flex items-center justify-center text-red-500 mb-4 shadow-scada-red">
            <ShieldAlert className="w-9 h-9 animate-pulse" />
          </div>

          <h2 className="text-xl font-bold text-slate-900 dark:text-white tracking-tight">
            RESTRICTED ACCESS – SYSTEM ADMIN CONSOLE
          </h2>
          <p className="text-xs font-scada-mono text-red-500 font-semibold mt-1">
            HTTP 403 / RBAC PERMISSION LEVEL INSUFFICIENT
          </p>

          <div className="my-6 p-4 rounded-xl bg-slate-50 dark:bg-[#141414] border border-slate-200 dark:border-[#2A2A2A] text-left text-xs space-y-2 font-scada-mono">
            <div className="flex justify-between">
              <span className="text-slate-500 dark:text-zinc-500">CURRENT USER:</span>
              <span className="font-bold text-slate-800 dark:text-zinc-200">{currentUser?.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 dark:text-zinc-500">ACTIVE ROLE:</span>
              <span className="font-bold text-amber-500">{userRole}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 dark:text-zinc-500">REQUIRED CLEARANCE:</span>
              <span className="font-bold text-purple-400">{requiredRole}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 dark:text-zinc-500">SECURITY PROTOCOL:</span>
              <span className="text-slate-700 dark:text-zinc-300">Madrid Protocol SCADA RBAC Level 3</span>
            </div>
          </div>

          <p className="text-xs text-slate-600 dark:text-zinc-400 mb-6 leading-relaxed">
            The Administration Console is strictly reserved for the Cyber Cell & Network Operations System Administrator. 
            For evaluation, you can switch your simulated role to System Admin below.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => setUserRole('SYSTEM_ADMIN')}
              className="w-full sm:w-auto px-5 py-2.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-scada-mono font-bold transition flex items-center justify-center gap-2 shadow-lg shadow-purple-600/25"
            >
              <ShieldCheck className="w-4 h-4" />
              SWITCH TO SYSTEM ADMIN (EVALUATION)
            </button>

            <Link
              to="/dashboard"
              className="w-full sm:w-auto px-4 py-2.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-[#252525] dark:hover:bg-[#2C2C2C] border border-slate-300 dark:border-[#3A3A3A] text-slate-800 dark:text-zinc-200 text-xs font-scada-mono font-semibold transition flex items-center justify-center gap-1.5"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              RETURN TO DASHBOARD
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return children;
};

export default ProtectedRoute;
