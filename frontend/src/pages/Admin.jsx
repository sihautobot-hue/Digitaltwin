import React, { useState, useMemo } from 'react';
import { useStationData } from '../context/StationDataContext';
import StatusBadge from '../components/common/StatusBadge';
import {
  Shield, ShieldCheck, ShieldAlert, Lock, UserCheck,
  Search, Filter, Download, Sliders, CheckCircle2,
  AlertTriangle, RefreshCw, KeyRound, Server, Radio,
  Clock, Database, EyeOff, User, Building2, HardDrive
} from 'lucide-react';

export const Admin = () => {
  const {
    stationData,
    data,
    updateUserRole,
    updateSystemConfig,
    currentUser,
    switchUser,
    activeStation
  } = useStationData();

  const [activeTab, setActiveTab] = useState('AUDIT_LOGS'); // 'AUDIT_LOGS' | 'PERMISSIONS' | 'DATA_SAFETY'
  const [logFilterAction, setLogFilterAction] = useState('ALL');
  const [logSearchQuery, setLogSearchQuery] = useState('');
  const [configSaveNotice, setConfigSaveNotice] = useState(false);

  const users = data.users || [];
  const auditLogs = data.auditLogs || [];
  const settings = stationData.settings || {};

  // Filtered Audit Logs
  const filteredLogs = useMemo(() => {
    return auditLogs.filter(log => {
      const matchesAction = logFilterAction === 'ALL' || log.action === logFilterAction;
      const searchLower = logSearchQuery.toLowerCase();
      const matchesSearch =
        !logSearchQuery ||
        log.userName?.toLowerCase().includes(searchLower) ||
        log.ipAddress?.toLowerCase().includes(searchLower) ||
        log.action?.toLowerCase().includes(searchLower) ||
        log.details?.toLowerCase().includes(searchLower) ||
        log.location?.toLowerCase().includes(searchLower);
      return matchesAction && matchesSearch;
    });
  }, [auditLogs, logFilterAction, logSearchQuery]);

  // Export logs to CSV
  const handleExportCSV = () => {
    const headers = ['Timestamp', 'User Name', 'Role', 'Action', 'IP Address', 'Location', 'Severity', 'Details'];
    const rows = filteredLogs.map(l => [
      l.timestamp,
      `"${l.userName}"`,
      l.userRole,
      l.action,
      l.ipAddress,
      `"${l.location}"`,
      l.severity,
      `"${l.details?.replace(/"/g, '""')}"`
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `polar_scada_audit_log_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleSaveConfig = (e) => {
    e.preventDefault();
    setConfigSaveNotice(true);
    setTimeout(() => setConfigSaveNotice(false), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200 dark:border-[#262626]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold text-slate-900 dark:text-white tracking-tight font-display flex items-center gap-2">
              <ShieldCheck className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              Mission Control – System Administration & Security Console
            </h1>
            <span className="px-2 py-0.5 rounded text-[10px] font-scada-mono font-bold bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/30">
              SYS-ADMIN CLEARANCE
            </span>
          </div>
          <p className="text-xs font-scada-mono text-slate-500 dark:text-zinc-400 mt-1">
            RBAC PERMISSION ENGINE | AUDIT TRAIL LOGS | HARDWARE TELEMETRY SAFETY ENFORCEMENT
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-[#1E1E1E] p-1 rounded-lg border border-slate-200 dark:border-[#2A2A2A] text-xs font-scada-mono">
          <button
            onClick={() => setActiveTab('AUDIT_LOGS')}
            className={`px-3 py-1.5 rounded-md transition font-semibold flex items-center gap-1.5 ${
              activeTab === 'AUDIT_LOGS'
                ? 'bg-purple-600 text-white shadow'
                : 'text-slate-600 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            Activity Logs & Audit
          </button>
          <button
            onClick={() => setActiveTab('PERMISSIONS')}
            className={`px-3 py-1.5 rounded-md transition font-semibold flex items-center gap-1.5 ${
              activeTab === 'PERMISSIONS'
                ? 'bg-purple-600 text-white shadow'
                : 'text-slate-600 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <UserCheck className="w-3.5 h-3.5" />
            User Permissions
          </button>
          <button
            onClick={() => setActiveTab('DATA_SAFETY')}
            className={`px-3 py-1.5 rounded-md transition font-semibold flex items-center gap-1.5 ${
              activeTab === 'DATA_SAFETY'
                ? 'bg-purple-600 text-white shadow'
                : 'text-slate-600 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Lock className="w-3.5 h-3.5" />
            Telemetry Safety Rule
          </button>
        </div>
      </div>

      {/* =========================================================================
          TAB 1: ACTIVITY LOGS & AUDIT TRAIL
      ========================================================================= */}
      {activeTab === 'AUDIT_LOGS' && (
        <div className="space-y-4">
          {/* Controls Bar: Filter, Search, CSV Export */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white dark:bg-[#1E1E1E] p-3 rounded-xl border border-slate-200 dark:border-[#2A2A2A] shadow-sm">
            <div className="flex items-center gap-2 flex-1 max-w-md">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-400 dark:text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search user, action, IP, location..."
                  value={logSearchQuery}
                  onChange={(e) => setLogSearchQuery(e.target.value)}
                  className="w-full bg-slate-50 dark:bg-[#141414] border border-slate-200 dark:border-[#2A2A2A] rounded-lg pl-9 pr-3 py-1.5 text-xs font-scada-mono text-slate-800 dark:text-zinc-200 outline-none focus:border-purple-500 transition"
                />
              </div>

              {/* Action Filter Dropdown */}
              <div className="relative">
                <select
                  value={logFilterAction}
                  onChange={(e) => setLogFilterAction(e.target.value)}
                  className="bg-slate-50 dark:bg-[#141414] border border-slate-200 dark:border-[#2A2A2A] rounded-lg px-2.5 py-1.5 text-xs font-scada-mono text-slate-800 dark:text-zinc-200 outline-none focus:border-purple-500 transition"
                >
                  <option value="ALL">All Actions ({auditLogs.length})</option>
                  <option value="LOGIN_SUCCESS">Login Success</option>
                  <option value="ROLE_ASSIGNMENT">Role Assignment</option>
                  <option value="ALERT_ACKNOWLEDGED">Alert Acknowledged</option>
                  <option value="LOCKDOWN_TRIGGERED">Lockdown Triggered</option>
                  <option value="DIESEL_GENSET_SWITCH">Diesel Genset Switch</option>
                  <option value="SYSTEM_CONFIG_UPDATE">System Config Update</option>
                  <option value="SYNC_WINDOW_ADJUST">Sync Window Adjust</option>
                </select>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleExportCSV}
                className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-[#252525] dark:hover:bg-[#2C2C2C] border border-slate-300 dark:border-[#3A3A3A] text-xs font-scada-mono text-slate-800 dark:text-zinc-200 transition flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5 text-purple-600 dark:text-purple-400" />
                EXPORT CSV
              </button>
            </div>
          </div>

          {/* Audit Logs Table */}
          <div className="bg-white dark:bg-[#1E1E1E] border border-slate-200 dark:border-[#2A2A2A] rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-scada-mono">
                <thead className="bg-slate-50 dark:bg-[#141414] text-slate-500 dark:text-zinc-400 border-b border-slate-200 dark:border-[#2A2A2A]">
                  <tr>
                    <th className="px-4 py-3 font-semibold">TIMESTAMP (UTC)</th>
                    <th className="px-4 py-3 font-semibold">USER & ROLE</th>
                    <th className="px-4 py-3 font-semibold">ACTION</th>
                    <th className="px-4 py-3 font-semibold">IP & LOCATION</th>
                    <th className="px-4 py-3 font-semibold">SEVERITY</th>
                    <th className="px-4 py-3 font-semibold">EVENT DETAILS</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-[#262626]">
                  {filteredLogs.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="px-4 py-8 text-center text-slate-400 dark:text-zinc-500">
                        No audit events matching current filter criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredLogs.map(log => (
                      <tr key={log.id} className="hover:bg-slate-50/70 dark:hover:bg-[#222222] transition">
                        <td className="px-4 py-3 text-slate-600 dark:text-zinc-400 whitespace-nowrap">
                          {log.timestamp?.replace('T', ' ').replace('Z', '')}
                        </td>
                        <td className="px-4 py-3">
                          <div className="font-bold text-slate-900 dark:text-white leading-tight font-sans">
                            {log.userName}
                          </div>
                          <span className={`inline-block mt-0.5 text-[9px] px-1 py-0.2 rounded border font-scada-mono ${
                            log.userRole === 'ANTARCTICA_EDGE'
                              ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
                              : log.userRole === 'INDIA_COMMAND'
                              ? 'text-blue-600 dark:text-blue-400 bg-blue-500/10 border-blue-500/30'
                              : 'text-purple-600 dark:text-purple-400 bg-purple-500/10 border-purple-500/30'
                          }`}>
                            {log.userRole}
                          </span>
                        </td>
                        <td className="px-4 py-3 font-bold text-slate-800 dark:text-zinc-200 whitespace-nowrap">
                          {log.action}
                        </td>
                        <td className="px-4 py-3">
                          <div className="text-cyan-700 dark:text-cyan-400">{log.ipAddress}</div>
                          <div className="text-[10px] text-slate-500 dark:text-zinc-500 font-sans truncate max-w-[180px]">
                            {log.location}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                            log.severity === 'SECURITY'
                              ? 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/30 animate-pulse'
                              : log.severity === 'WARNING'
                              ? 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/30'
                              : 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30'
                          }`}>
                            {log.severity}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-slate-700 dark:text-zinc-300 font-sans max-w-xs leading-relaxed">
                          {log.details}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 2: USER PERMISSION MANAGEMENT
      ========================================================================= */}
      {activeTab === 'PERMISSIONS' && (
        <div className="space-y-4">
          <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-4 flex items-start gap-3 text-xs text-purple-900 dark:text-purple-200">
            <Shield className="w-5 h-5 text-purple-600 dark:text-purple-400 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-bold text-sm mb-0.5">Role-Based Access Control (RBAC) Policy</div>
              <p className="leading-relaxed text-slate-700 dark:text-purple-200">
                Personnel assigned to <strong>Antarctica Edge</strong> have write access to station local telemetry, alerts, and lockdown triggers. 
                Personnel assigned to <strong>India Command Center</strong> are restricted to read-only satellite mirrors and AI predictions.
                <strong> System Admin</strong> manages user credentials and satellite network parameters.
              </p>
            </div>
          </div>

          <div className="bg-white dark:bg-[#1E1E1E] border border-slate-200 dark:border-[#2A2A2A] rounded-xl overflow-hidden shadow-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-sans">
                <thead className="bg-slate-50 dark:bg-[#141414] text-slate-500 dark:text-zinc-400 border-b border-slate-200 dark:border-[#2A2A2A] font-scada-mono">
                  <tr>
                    <th className="px-4 py-3 font-semibold">OFFICER / USER</th>
                    <th className="px-4 py-3 font-semibold">DESIGNATION & EMAIL</th>
                    <th className="px-4 py-3 font-semibold">BASE LOCATION</th>
                    <th className="px-4 py-3 font-semibold">ASSIGNED ROLE</th>
                    <th className="px-4 py-3 font-semibold">SIMULATE SESSION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-[#262626]">
                  {users.map(u => {
                    const isCurrent = currentUser?.id === u.id;
                    return (
                      <tr key={u.id} className="hover:bg-slate-50/70 dark:hover:bg-[#222222] transition">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-full bg-purple-100 dark:bg-purple-950/80 border border-purple-500/40 flex items-center justify-center font-bold text-xs text-purple-700 dark:text-purple-300">
                              {u.avatarInitials || u.name?.slice(0, 2)}
                            </div>
                            <div>
                              <div className="font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
                                <span>{u.name}</span>
                                {isCurrent && (
                                  <span className="text-[9px] px-1 py-0.2 rounded bg-green-500/10 text-green-600 dark:text-green-400 border border-green-500/30 font-scada-mono font-semibold">
                                    YOU
                                  </span>
                                )}
                              </div>
                              <div className="text-[10px] font-scada-mono text-slate-400 dark:text-zinc-500">{u.id}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="text-slate-800 dark:text-zinc-200">{u.title}</div>
                          <div className="text-[10px] font-scada-mono text-slate-400 dark:text-zinc-500">{u.email}</div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="text-slate-700 dark:text-zinc-300 font-medium">{u.location}</div>
                          <div className="text-[10px] font-scada-mono text-cyan-600 dark:text-cyan-400">{u.ipAddress}</div>
                        </td>
                        <td className="px-4 py-3">
                          <select
                            value={u.role}
                            onChange={(e) => updateUserRole(u.id, e.target.value)}
                            className={`px-2.5 py-1.5 rounded-lg border text-xs font-scada-mono font-bold outline-none transition ${
                              u.role === 'ANTARCTICA_EDGE'
                                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30'
                                : u.role === 'INDIA_COMMAND'
                                ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/30'
                                : 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30'
                            }`}
                          >
                            <option value="ANTARCTICA_EDGE">Antarctica Edge User</option>
                            <option value="INDIA_COMMAND">India Command Center</option>
                            <option value="SYSTEM_ADMIN">System Admin</option>
                          </select>
                        </td>
                        <td className="px-4 py-3">
                          <button
                            onClick={() => switchUser(u.id)}
                            className={`px-2.5 py-1 rounded text-xs font-scada-mono font-semibold transition border ${
                              isCurrent
                                ? 'bg-slate-100 dark:bg-[#252525] text-slate-400 dark:text-zinc-500 border-slate-300 dark:border-[#333] cursor-default'
                                : 'bg-slate-100 hover:bg-slate-200 dark:bg-[#2A2A2A] dark:hover:bg-[#333] text-purple-600 dark:text-purple-300 border-slate-300 dark:border-[#3A3A3A]'
                            }`}
                          >
                            {isCurrent ? 'Active User' : 'Login As'}
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          TAB 3: STRICT DATA SAFETY TELEMETRY PANEL (ENFORCED IMMUTABLE)
      ========================================================================= */}
      {activeTab === 'DATA_SAFETY' && (
        <div className="space-y-6">
          {/* Strict Data Safety Rule Enforced in UI Banner */}
          <div className="bg-red-500/10 border-2 border-red-500/40 rounded-xl p-5 shadow-lg relative overflow-hidden">
            <div className="flex items-start gap-4">
              <div className="p-2.5 rounded-xl bg-red-500/20 text-red-600 dark:text-red-400 flex-shrink-0">
                <ShieldAlert className="w-8 h-8 animate-pulse" />
              </div>
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-red-600 dark:text-red-400 uppercase font-scada-mono tracking-wide">
                    Strict Telemetry Data Safety Protocol – Hardware Immutability Enforced
                  </h3>
                  <span className="px-2 py-0.5 rounded bg-red-600 text-white text-[10px] font-scada-mono font-bold">
                    LOCKED
                  </span>
                </div>
                <p className="text-xs text-slate-700 dark:text-zinc-300 leading-relaxed font-sans">
                  The System Administrator is <strong>strictly PROHIBITED</strong> from modifying or falsifying any environmental, energy, fuel, or logistics telemetry data. 
                  All sensor feeds represent raw physical outputs transmitted directly from field micro-controllers and automated weather stations. 
                  Per <strong>NCPOR scientific integrity standards</strong> and the <strong>Antarctic Madrid Protocol</strong>, all telemetry inputs below are permanently hardware-locked and immutable.
                </p>
                <div className="text-[11px] font-scada-mono text-slate-500 dark:text-zinc-400 pt-1">
                  RULE ID: SCADA-SAFETY-IMMUTABLE-01 // AUDIT HASH ENFORCED
                </div>
              </div>
            </div>
          </div>

          {/* Locked Hardware Telemetry Inputs Grid (Strictly Disabled) */}
          <div className="bg-white dark:bg-[#1E1E1E] border border-slate-200 dark:border-[#2A2A2A] rounded-xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-[#262626] pb-3">
              <div>
                <h4 className="text-sm font-bold text-slate-900 dark:text-white uppercase font-scada-mono flex items-center gap-2">
                  <Lock className="w-4 h-4 text-red-500" />
                  Physical Telemetry Sensor Registers (Read-Only / Hardware Immutable)
                </h4>
                <p className="text-xs text-slate-500 dark:text-zinc-400">
                  Data fields are disabled and greyed out. Modification attempts are rejected by local SCADA bus.
                </p>
              </div>
              <span className="px-2.5 py-1 rounded-md bg-slate-100 dark:bg-[#141414] border border-slate-300 dark:border-[#333] text-[11px] font-scada-mono text-slate-600 dark:text-zinc-400 flex items-center gap-1.5">
                <Lock className="w-3.5 h-3.5 text-red-500" />
                Hardware Locked
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Telemetry 1: Outdoor Temperature */}
              <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-[#141414] border border-slate-200 dark:border-[#262626] opacity-75 cursor-not-allowed">
                <div className="flex items-center justify-between text-[11px] font-scada-mono text-slate-500 dark:text-zinc-400 mb-1">
                  <span>OUTDOOR TEMP SENSOR</span>
                  <Lock className="w-3 h-3 text-red-400" />
                </div>
                <input
                  type="text"
                  disabled
                  value={`${stationData.weather?.current?.outdoorTempC ?? -42.8} °C`}
                  className="w-full bg-slate-100 dark:bg-[#1C1C1E] border border-slate-300 dark:border-[#333] rounded px-2.5 py-1.5 text-xs font-scada-mono font-bold text-slate-500 dark:text-zinc-400 cursor-not-allowed"
                />
                <span className="text-[9px] font-scada-mono text-slate-400 dark:text-zinc-500 mt-1 block">
                  Sensor: Pt100 RTD Probe #1
                </span>
              </div>

              {/* Telemetry 2: Katabatic Wind Velocity */}
              <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-[#141414] border border-slate-200 dark:border-[#262626] opacity-75 cursor-not-allowed">
                <div className="flex items-center justify-between text-[11px] font-scada-mono text-slate-500 dark:text-zinc-400 mb-1">
                  <span>KATABATIC ANEMOMETER</span>
                  <Lock className="w-3 h-3 text-red-400" />
                </div>
                <input
                  type="text"
                  disabled
                  value={`${stationData.weather?.current?.windSpeedKnots ?? 58.4} kts (${stationData.weather?.current?.windDirection ?? 'SSE'})`}
                  className="w-full bg-slate-100 dark:bg-[#1C1C1E] border border-slate-300 dark:border-[#333] rounded px-2.5 py-1.5 text-xs font-scada-mono font-bold text-slate-500 dark:text-zinc-400 cursor-not-allowed"
                />
                <span className="text-[9px] font-scada-mono text-slate-400 dark:text-zinc-500 mt-1 block">
                  Sensor: Ultrasonic Sonic-3D
                </span>
              </div>

              {/* Telemetry 3: Microgrid Power Output */}
              <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-[#141414] border border-slate-200 dark:border-[#262626] opacity-75 cursor-not-allowed">
                <div className="flex items-center justify-between text-[11px] font-scada-mono text-slate-500 dark:text-zinc-400 mb-1">
                  <span>MICROGRID DEMAND LOAD</span>
                  <Lock className="w-3 h-3 text-red-400" />
                </div>
                <input
                  type="text"
                  disabled
                  value={`${stationData.power?.overview?.totalLoadKw ?? 146.8} kW`}
                  className="w-full bg-slate-100 dark:bg-[#1C1C1E] border border-slate-300 dark:border-[#333] rounded px-2.5 py-1.5 text-xs font-scada-mono font-bold text-slate-500 dark:text-zinc-400 cursor-not-allowed"
                />
                <span className="text-[9px] font-scada-mono text-slate-400 dark:text-zinc-500 mt-1 block">
                  Meter: Schneider PowerLogic PM8000
                </span>
              </div>

              {/* Telemetry 4: Cryogenic Fuel Reserve */}
              <div className="p-3.5 rounded-lg bg-slate-50 dark:bg-[#141414] border border-slate-200 dark:border-[#262626] opacity-75 cursor-not-allowed">
                <div className="flex items-center justify-between text-[11px] font-scada-mono text-slate-500 dark:text-zinc-400 mb-1">
                  <span>CRYO FUEL VOLUME</span>
                  <Lock className="w-3 h-3 text-red-400" />
                </div>
                <input
                  type="text"
                  disabled
                  value={`${stationData.fuel?.summary?.totalCurrentLitres?.toLocaleString() ?? '134,250'} Litres`}
                  className="w-full bg-slate-100 dark:bg-[#1C1C1E] border border-slate-300 dark:border-[#333] rounded px-2.5 py-1.5 text-xs font-scada-mono font-bold text-slate-500 dark:text-zinc-400 cursor-not-allowed"
                />
                <span className="text-[9px] font-scada-mono text-slate-400 dark:text-zinc-500 mt-1 block">
                  Gauge: Endress+Hauser Radar FMR50
                </span>
              </div>
            </div>
          </div>

          {/* Permitted System Configurations (Editable by Admin) */}
          <div className="bg-white dark:bg-[#1E1E1E] border border-purple-500/30 rounded-xl p-5 shadow-sm space-y-4">
            <div className="border-b border-slate-200 dark:border-[#262626] pb-3 flex items-center justify-between">
              <div>
                <h4 className="text-sm font-bold text-slate-900 dark:text-white uppercase font-scada-mono flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-purple-500" />
                  Permitted System & Network Configurations
                </h4>
                <p className="text-xs text-slate-500 dark:text-zinc-400">
                  The Admin is permitted to adjust network sync frequencies, simulated telemetry jitter, and alarm buzzers.
                </p>
              </div>
              {configSaveNotice && (
                <span className="flex items-center gap-1 text-xs font-scada-mono text-green-600 dark:text-green-400 font-bold animate-in fade-in">
                  <CheckCircle2 className="w-4 h-4" /> CONFIG SAVED & AUDITED
                </span>
              )}
            </div>

            <form onSubmit={handleSaveConfig} className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Config 1: Satellite Store-and-Forward Batch Window */}
              <div className="space-y-1.5">
                <label className="text-xs font-scada-mono font-semibold uppercase text-slate-700 dark:text-zinc-300 block">
                  Satellite Sync Window (NCPOR Mirror)
                </label>
                <select
                  value={settings.satelliteSyncWindowMinutes || 15}
                  onChange={(e) => updateSystemConfig('satelliteSyncWindowMinutes', Number(e.target.value))}
                  className="w-full bg-slate-50 dark:bg-[#141414] border border-slate-300 dark:border-[#2A2A2A] rounded-lg px-3 py-2 text-xs font-scada-mono text-slate-900 dark:text-white outline-none focus:border-purple-500"
                >
                  <option value={5}>Every 5 Minutes (High Priority Orbit)</option>
                  <option value={15}>Every 15 Minutes (Standard Austral Winter)</option>
                  <option value={30}>Every 30 Minutes (Conserve Satellite Power)</option>
                  <option value={60}>Every 60 Minutes (Extreme Storm Mode)</option>
                </select>
                <span className="text-[10px] text-slate-400 dark:text-zinc-500 block">
                  Defines satellite batching window for India Command Center mirror.
                </span>
              </div>

              {/* Config 2: Simulated Polling Interval */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-scada-mono font-semibold uppercase text-slate-700 dark:text-zinc-300">
                  <span>Telemetry Jitter Frequency</span>
                  <span className="text-purple-600 dark:text-purple-400">{settings.pollingIntervalSeconds || 3}s</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="15"
                  value={settings.pollingIntervalSeconds || 3}
                  onChange={(e) => updateSystemConfig('pollingIntervalSeconds', Number(e.target.value))}
                  className="w-full accent-purple-600 cursor-pointer"
                />
                <span className="text-[10px] text-slate-400 dark:text-zinc-500 block">
                  Adjusts client-side micro-telemetry sensor refresh rate.
                </span>
              </div>

              {/* Config 3: Audio Alarm Buzzer */}
              <div className="space-y-1.5">
                <label className="text-xs font-scada-mono font-semibold uppercase text-slate-700 dark:text-zinc-300 block">
                  SCADA Audible Strobe Buzzer
                </label>
                <div className="flex items-center gap-3 pt-1">
                  <button
                    type="button"
                    onClick={() => updateSystemConfig('audioAlarmsEnabled', !settings.audioAlarmsEnabled)}
                    className={`px-4 py-2 rounded-lg text-xs font-scada-mono font-bold transition border ${
                      settings.audioAlarmsEnabled
                        ? 'bg-purple-600 text-white border-purple-500'
                        : 'bg-slate-100 dark:bg-[#141414] text-slate-500 dark:text-zinc-400 border-slate-300 dark:border-[#2A2A2A]'
                    }`}
                  >
                    {settings.audioAlarmsEnabled ? '🔊 AUDIO ALARMS ON' : '🔇 AUDIO MUTED'}
                  </button>
                  <span className="text-[10px] text-slate-400 dark:text-zinc-500">
                    Buzzer triggers on unacknowledged CRITICAL alerts.
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="md:col-span-3 pt-3 border-t border-slate-200 dark:border-[#262626] flex justify-end gap-3">
                <button
                  type="submit"
                  className="px-5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-scada-mono font-bold transition shadow"
                >
                  SAVE SYSTEM CONFIGURATIONS
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Admin;
