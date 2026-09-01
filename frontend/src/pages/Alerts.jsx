import React, { useState } from 'react';
import { useStationData } from '../context/StationDataContext';
import StatusBadge from '../components/common/StatusBadge';
import MetricCard from '../components/common/MetricCard';
import { 
  Bell, AlertTriangle, AlertCircle, CheckCircle2, ShieldAlert, 
  Bot, Clock, User, Download, Filter, Volume2, VolumeX, CheckSquare 
} from 'lucide-react';

export const Alerts = () => {
  const { stationData, acknowledgeAlert, activeAudioAlarm } = useStationData();
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [ackFilter, setAckFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const alerts = stationData?.alerts || [];

  const filteredAlerts = alerts.filter(a => {
    if (severityFilter !== 'ALL' && a.severity !== severityFilter) return false;
    if (ackFilter === 'UNACK' && a.acknowledged) return false;
    if (ackFilter === 'ACKED' && !a.acknowledged) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return (
        a.title.toLowerCase().includes(q) ||
        a.code.toLowerCase().includes(q) ||
        a.subsystem.toLowerCase().includes(q) ||
        a.message.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const criticalCount = alerts.filter(a => a.severity === 'CRITICAL' && !a.acknowledged).length;
  const warningCount = alerts.filter(a => a.severity === 'WARNING' && !a.acknowledged).length;
  const totalUnack = alerts.filter(a => !a.acknowledged).length;

  const handleAcknowledgeAll = () => {
    alerts.filter(a => !a.acknowledged).forEach(a => {
      acknowledgeAlert(a.id, 'Cmdr. Rajeshwar Sharma');
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#262626]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight font-display flex items-center gap-2">
              <Bell className="w-6 h-6 text-red-400" />
              SCADA Alarm Monitor & Neural Predictive Logs
            </h1>
            {criticalCount > 0 ? (
              <StatusBadge status="CRITICAL" label={`${criticalCount} CRITICAL ACTIVE`} size="md" />
            ) : (
              <StatusBadge status="NORMAL" label="ALL ALARMS NOMINAL" size="md" />
            )}
          </div>
          <p className="text-xs font-scada-mono text-zinc-400 mt-1">
            REAL-TIME EVENT LOGGING | AI ROOT-CAUSE DIAGNOSTICS | OPERATOR AUDIT TRAIL
          </p>
        </div>

        <div className="flex items-center gap-2">
          {totalUnack > 0 && (
            <button
              onClick={handleAcknowledgeAll}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-red-600/20 hover:bg-red-600/30 text-red-300 border border-red-500/40 text-xs font-scada-mono font-bold transition"
            >
              <CheckSquare className="w-4 h-4" />
              ACKNOWLEDGE ALL ({totalUnack})
            </button>
          )}
        </div>
      </div>

      {/* Alarm Status KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Unacknowledged Alarms"
          value={totalUnack}
          unit="EVENTS"
          status={totalUnack > 0 ? 'CRITICAL' : 'NORMAL'}
          icon={AlertTriangle}
          trend={`${criticalCount} Critical | ${warningCount} Warning`}
          trendDirection="none"
          subtext="Requires Officer Signature"
        />

        <MetricCard
          title="Critical Alarms"
          value={criticalCount}
          unit="ACTIVE"
          status={criticalCount > 0 ? 'CRITICAL' : 'NORMAL'}
          icon={ShieldAlert}
          trend="Helipad De-ice CKT-06"
          trendDirection="none"
          subtext="DEFCON-2 Protocol"
        />

        <MetricCard
          title="AI Diagnostics Engine"
          value="96.4%"
          status="NORMAL"
          icon={Bot}
          trend="Neural Root-Cause Analyzer"
          trendDirection="none"
          subtext="Subsystem Correlation Active"
        />

        <MetricCard
          title="Total Event Logs"
          value={alerts.length}
          unit="RECORDS"
          status="NORMAL"
          icon={Clock}
          trend="Zero Lost Packets"
          trendDirection="none"
          subtext="Satellite Sync Streamed"
        />
      </div>

      {/* Filter Toolbar */}
      <div className="p-4 bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Search */}
        <input
          type="text"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          placeholder="Search by title, code (e.g. HELI_DEICE), subsystem..."
          className="bg-[#121212] border border-[#2A2A2A] focus:border-cyan-500 rounded-md px-3 py-1.5 text-xs font-sans text-zinc-200 outline-none w-full md:w-80 placeholder:text-zinc-600"
        />

        {/* Severity and Ack Filters */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-scada-mono">
          <span className="text-zinc-500 text-xs">SEVERITY:</span>
          {['ALL', 'CRITICAL', 'WARNING', 'NORMAL'].map(st => (
            <button
              key={st}
              onClick={() => setSeverityFilter(st)}
              className={`px-2.5 py-1 rounded transition ${
                severityFilter === st
                  ? 'bg-cyan-500/20 text-cyan-400 font-bold border border-cyan-500/40'
                  : 'bg-[#141414] text-zinc-400 hover:text-white border border-[#2A2A2A]'
              }`}
            >
              {st}
            </button>
          ))}

          <div className="h-4 w-px bg-[#333] mx-1 hidden sm:block" />

          <span className="text-zinc-500 text-xs">STATUS:</span>
          {['ALL', 'UNACK', 'ACKED'].map(ack => (
            <button
              key={ack}
              onClick={() => setAckFilter(ack)}
              className={`px-2.5 py-1 rounded transition ${
                ackFilter === ack
                  ? 'bg-amber-500/20 text-amber-400 font-bold border border-amber-500/40'
                  : 'bg-[#141414] text-zinc-400 hover:text-white border border-[#2A2A2A]'
              }`}
            >
              {ack}
            </button>
          ))}
        </div>
      </div>

      {/* Alert Feed List */}
      <div className="space-y-3">
        {filteredAlerts.length > 0 ? (
          filteredAlerts.map(alert => {
            const isCrit = alert.severity === 'CRITICAL';
            const isWarn = alert.severity === 'WARNING';

            return (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border transition-all ${
                  !alert.acknowledged && isCrit
                    ? 'bg-red-950/20 border-red-500/50 shadow-scada-red'
                    : !alert.acknowledged && isWarn
                    ? 'bg-yellow-950/20 border-yellow-500/50'
                    : 'bg-[#1E1E1E] border-[#2A2A2A]'
                }`}
              >
                <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
                  {/* Left: Code, Title, Message */}
                  <div className="space-y-2 flex-1">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <StatusBadge status={alert.severity} size="sm" />
                      <span className="text-xs font-scada-mono font-bold text-cyan-400">{alert.code}</span>
                      <span className="text-zinc-500 font-scada-mono text-xs">|</span>
                      <span className="text-xs font-scada-mono text-zinc-400">{alert.subsystem}</span>
                      <span className="text-zinc-500 font-scada-mono text-xs">|</span>
                      <span className="text-xs font-scada-mono text-zinc-500">
                        {new Date(alert.timestamp).toUTCString()}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-white tracking-wide">{alert.title}</h3>
                    <p className="text-xs text-zinc-300 leading-relaxed">{alert.message}</p>

                    {/* AI Diagnosis Box */}
                    {alert.aiDiagnosis && (
                      <div className="p-3 bg-[#141414] rounded-md border border-[#2A2A2A] space-y-1.5 text-xs">
                        <div className="flex items-center justify-between text-zinc-400 font-scada-mono">
                          <span className="flex items-center gap-1.5 text-cyan-400 font-bold">
                            <Bot className="w-3.5 h-3.5" />
                            AI ROOT CAUSE INFERENCE
                          </span>
                          <span className="text-emerald-400 font-bold">
                            PROBABILITY: {(alert.rootCauseProbability * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-zinc-300 font-sans">{alert.aiDiagnosis}</p>
                        {alert.recommendedAction && (
                          <div className="text-[11px] text-amber-300 font-scada-mono pt-1">
                            ► ACTION: {alert.recommendedAction}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Right: Acknowledge Button or Signature */}
                  <div className="flex lg:flex-col items-center lg:items-end justify-between gap-2 flex-shrink-0 pt-2 lg:pt-0 border-t lg:border-t-0 border-[#262626]">
                    {!alert.acknowledged ? (
                      <button
                        onClick={() => acknowledgeAlert(alert.id, 'Cmdr. Rajeshwar Sharma')}
                        className="px-4 py-2 rounded bg-red-600 hover:bg-red-500 text-white text-xs font-scada-mono font-bold tracking-wider transition shadow-scada-red flex items-center gap-1.5"
                      >
                        <CheckCircle2 className="w-4 h-4" />
                        ACKNOWLEDGE ALARM
                      </button>
                    ) : (
                      <div className="text-right font-scada-mono">
                        <span className="inline-flex items-center gap-1 text-xs text-green-400 font-bold bg-green-500/10 px-2.5 py-1 rounded border border-green-500/30">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          ACKNOWLEDGED
                        </span>
                        <div className="text-[10px] text-zinc-500 mt-1">
                          BY: {alert.acknowledgedBy || 'Operator'}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="p-12 text-center bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg text-zinc-500 font-scada-mono">
            NO SCADA ALARMS MATCH SELECTED CRITERIA
          </div>
        )}
      </div>
    </div>
  );
};

export default Alerts;
