import React, { useState } from 'react';
import { useStationData } from '../context/StationDataContext';
import StatusBadge from '../components/common/StatusBadge';
import MetricCard from '../components/common/MetricCard';
import { 
  Settings as SettingsIcon, Database, Satellite, Volume2, 
  VolumeX, RefreshCw, Trash2, CheckCircle2, ShieldAlert, 
  Download, Activity, Sliders, Cpu 
} from 'lucide-react';

export const SettingsPage = () => {
  const { 
    stationData, 
    updateSettings, 
    resetToDefaultData, 
    exportTelemetryJSON,
    isLiveTelemetryActive,
    setIsLiveTelemetryActive,
    toggleStationLockdown
  } = useStationData();

  const [resetSuccess, setResetSuccess] = useState(false);
  const settings = stationData?.settings || {};
  const station = stationData?.station || {};

  const handleReset = () => {
    if (window.confirm('Reset all SCADA station telemetry, alarms, and state to default factory values?')) {
      resetToDefaultData();
      setResetSuccess(true);
      setTimeout(() => setResetSuccess(false), 2000);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#262626]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight font-display flex items-center gap-2">
              <SettingsIcon className="w-6 h-6 text-cyan-400" />
              SCADA System Configuration & Offline Cache
            </h1>
            <StatusBadge status="ACTIVE" label="OFFLINE-FIRST ENGINE" size="sm" />
          </div>
          <p className="text-xs font-scada-mono text-zinc-400 mt-1">
            TELEMETRY POLLING | SATELLITE BANDWIDTH THROTTLE | LOCAL STORAGE DATA LAYER
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={exportTelemetryJSON}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#1E1E1E] hover:bg-[#252525] border border-[#2A2A2A] text-cyan-400 text-xs font-scada-mono transition"
          >
            <Download className="w-4 h-4" />
            EXPORT CACHE JSON
          </button>
        </div>
      </div>

      {/* Sync Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="Satellite Cache Mode"
          value="LOCAL-FIRST"
          status="NORMAL"
          icon={Database}
          trend="Zero Data Loss Buffer"
          trendDirection="none"
          subtext="Persisted in Browser LocalStorage"
        />

        <MetricCard
          title="Telemetry Polling"
          value={`${settings.pollingIntervalSeconds || 3}s`}
          status={isLiveTelemetryActive ? 'NORMAL' : 'WARNING'}
          icon={Activity}
          trend={isLiveTelemetryActive ? 'Live Stream Active' : 'Polling Suspended'}
          trendDirection="none"
          subtext="Simulated Sensor Jitter"
        />

        <MetricCard
          title="Station Security Mode"
          value={station.lockdownActive ? 'LOCKDOWN' : 'NORMAL'}
          status={station.lockdownActive ? 'CRITICAL' : 'NORMAL'}
          icon={ShieldAlert}
          trend="DEFCON-2 Blizzard Mode"
          trendDirection="none"
          subtext="Madrid Protocol Protocol"
        />
      </div>

      {/* Main Settings Sections */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Section 1: Telemetry Stream Controls */}
        <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-5 space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider font-scada-mono flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            Telemetry Stream Simulation
          </h3>

          <div className="space-y-4 font-scada-mono text-xs">
            {/* Live Toggle */}
            <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A] flex items-center justify-between">
              <div>
                <span className="text-white font-bold block">Live Telemetry Simulation</span>
                <span className="text-zinc-500 text-[11px]">Generate real-time sensor micro-fluctuations</span>
              </div>
              <button
                onClick={() => setIsLiveTelemetryActive(!isLiveTelemetryActive)}
                className={`px-3 py-1.5 rounded font-bold transition ${
                  isLiveTelemetryActive
                    ? 'bg-green-500/20 text-green-400 border border-green-500/40'
                    : 'bg-zinc-800 text-zinc-400 border border-zinc-700'
                }`}
              >
                {isLiveTelemetryActive ? 'STREAM ACTIVE' : 'PAUSED'}
              </button>
            </div>

            {/* Polling Interval Slider */}
            <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A] space-y-2">
              <div className="flex justify-between">
                <span className="text-white font-bold">Telemetry Polling Interval</span>
                <span className="text-cyan-400 font-bold">{settings.pollingIntervalSeconds || 3} Seconds</span>
              </div>
              <input
                type="range"
                min="1"
                max="15"
                step="1"
                value={settings.pollingIntervalSeconds || 3}
                onChange={e => updateSettings({ pollingIntervalSeconds: Number(e.target.value) })}
                className="w-full accent-cyan-400 cursor-pointer"
              />
              <div className="flex justify-between text-[10px] text-zinc-500">
                <span>1s (High Frequency)</span>
                <span>15s (Low Satellite Bandwidth)</span>
              </div>
            </div>

            {/* Simulated Satellite Bandwidth */}
            <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A] space-y-2">
              <span className="text-white font-bold block">Simulated Inmarsat/GSAT Bandwidth</span>
              <div className="grid grid-cols-3 gap-2">
                {[256, 512, 2048].map(bw => (
                  <button
                    key={bw}
                    onClick={() => updateSettings({ simulatedBandwidthKbps: bw })}
                    className={`p-2 rounded text-center transition ${
                      settings.simulatedBandwidthKbps === bw
                        ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 font-bold'
                        : 'bg-[#1C1C1E] text-zinc-400 border border-[#2A2A2A]'
                    }`}
                  >
                    {bw} Kbps
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Audio Alarms & Station Lockdown Protocol */}
        <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-5 space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider font-scada-mono flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-red-400" />
            Station Emergency & Alarm Control
          </h3>

          <div className="space-y-4 font-scada-mono text-xs">
            {/* Audio Alarm Switch */}
            <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A] flex items-center justify-between">
              <div>
                <span className="text-white font-bold block">SCADA Audio Alarm Buzzer</span>
                <span className="text-zinc-500 text-[11px]">Audio chime on unacknowledged critical alerts</span>
              </div>
              <button
                onClick={() => updateSettings({ audioAlarmsEnabled: !settings.audioAlarmsEnabled })}
                className={`px-3 py-1.5 rounded font-bold transition flex items-center gap-1.5 ${
                  settings.audioAlarmsEnabled
                    ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                    : 'bg-zinc-800 text-zinc-400 border border-zinc-700'
                }`}
              >
                {settings.audioAlarmsEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                {settings.audioAlarmsEnabled ? 'ENABLED' : 'MUTED'}
              </button>
            </div>

            {/* Station Emergency Lockdown */}
            <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A] flex items-center justify-between">
              <div>
                <span className="text-white font-bold block">Station Lockdown Mode</span>
                <span className="text-zinc-500 text-[11px]">Seal all exterior hatches & activate DEFCON-1</span>
              </div>
              <button
                onClick={toggleStationLockdown}
                className={`px-3 py-1.5 rounded font-bold transition ${
                  station.lockdownActive
                    ? 'bg-red-600 text-white border border-red-400 shadow-scada-red animate-pulse'
                    : 'bg-zinc-800 text-zinc-400 border border-zinc-700 hover:text-white'
                }`}
              >
                {station.lockdownActive ? 'LOCKDOWN ACTIVE' : 'DISARMED'}
              </button>
            </div>

            {/* Offline Cache Purge / Factory Reset */}
            <div className="p-3 bg-red-950/20 rounded border border-red-900/40 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-red-300 font-bold block">Reset SCADA Telemetry State</span>
                  <span className="text-zinc-400 text-[11px]">Flush localStorage cache back to dummyData.json</span>
                </div>
                <button
                  onClick={handleReset}
                  className="px-3 py-1.5 rounded bg-red-600/30 hover:bg-red-600/50 text-red-300 border border-red-500/40 font-bold transition flex items-center gap-1.5"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  RESET
                </button>
              </div>

              {resetSuccess && (
                <div className="text-[11px] text-green-400 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  State reset to default JSON telemetry successfully!
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Station Technical Profile */}
      <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-5 space-y-3 font-scada-mono text-xs">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Cpu className="w-4 h-4 text-cyan-400" />
          Station Technical Specification & Metadata
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-zinc-300">
          <div className="p-2.5 bg-[#141414] rounded border border-[#2A2A2A]">
            <span className="text-zinc-500 text-[10px] block">STATION IDENTIFIER</span>
            <span className="font-bold text-white">{station.name} ({station.code})</span>
          </div>
          <div className="p-2.5 bg-[#141414] rounded border border-[#2A2A2A]">
            <span className="text-zinc-500 text-[10px] block">OPERATING AGENCY</span>
            <span className="font-bold text-white">{station.country}</span>
          </div>
          <div className="p-2.5 bg-[#141414] rounded border border-[#2A2A2A]">
            <span className="text-zinc-500 text-[10px] block">GEOGRAPHIC LOCATION</span>
            <span className="font-bold text-cyan-400">{station.coordinates?.region}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
