import React, { useState } from 'react';
import { useStationData } from '../context/StationDataContext';
import MetricCard from '../components/common/MetricCard';
import StatusBadge from '../components/common/StatusBadge';
import { CircularGauge } from '../components/common/SCADAGauge';
import MaitriStationDigitalTwin from '../components/digitalTwin/MaitriStationDigitalTwin';
import ModuleDetailModal from '../components/digitalTwin/ModuleDetailModal';
import { Link } from 'react-router-dom';
import {
  Thermometer,
  Wind,
  Zap,
  Fuel,
  Activity,
  AlertTriangle,
  Radio,
  Layers,
  ChevronRight,
  CheckCircle2,
  BatteryCharging,
  Cpu,
  Clock,
  ShieldCheck,
  TrendingDown
} from 'lucide-react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';

export const Dashboard = () => {
  const { stationData, acknowledgeAlert } = useStationData();
  const [selectedModule, setSelectedModule] = useState(null);

  const { station, weather, power, fuel, digitalTwin, alerts } = stationData;

  const unackAlerts = alerts?.filter(a => !a.acknowledged) || [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#262626]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight font-display">
              {station?.name}
            </h1>
            <StatusBadge status={station?.securityStatus} label="MISSION ACTIVE" size="md" />
          </div>
          <p className="text-xs font-scada-mono text-zinc-400 mt-1">
            LAT: {station?.coordinates?.latitude} | LONG: {station?.coordinates?.longitude} | ELEVATION: {station?.coordinates?.elevationMeters}m | {station?.season}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to="/digital-twin"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#1E1E1E] border border-cyan-500/40 text-cyan-400 text-xs font-scada-mono hover:bg-cyan-950/40 transition"
          >
            <Cpu className="w-3.5 h-3.5" />
            FULL 2D TWIN
          </Link>
          <Link
            to="/reports"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-cyan-500 text-black text-xs font-scada-mono font-bold hover:bg-cyan-400 transition"
          >
            EXPORT SITREP
          </Link>
        </div>
      </div>

      {/* Top SCADA Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1: Outdoor Temp */}
        <MetricCard
          title="Atmosphere & Chill"
          value={weather?.current?.outdoorTempC}
          unit="°C"
          status={weather?.current?.outdoorTempC < -40 ? 'CRITICAL' : 'NORMAL'}
          statusLabel={weather?.current?.outdoorTempC < -40 ? 'EXTREME COLD' : 'NORMAL'}
          icon={Thermometer}
          trend={`Wind Chill: ${weather?.current?.windChillC}°C`}
          trendDirection="down"
          subtext={`Indoor Core: ${weather?.current?.indoorTempC}°C`}
        />

        {/* Metric 2: Katabatic Wind */}
        <MetricCard
          title="Katabatic Wind"
          value={weather?.current?.windSpeedKnots}
          unit="kts"
          status={weather?.current?.windSpeedKnots > 50 ? 'CRITICAL' : 'NORMAL'}
          statusLabel={`GUSTS ${weather?.current?.windGustKnots} KTS`}
          icon={Wind}
          trend={`Dir: ${weather?.current?.windDirection} (${weather?.current?.windDirectionDeg}°)`}
          trendDirection="up"
          subtext={`Pressure: ${weather?.current?.barometricPressureHpa} hPa`}
        />

        {/* Metric 3: Power Grid Load */}
        <MetricCard
          title="Power Grid Load"
          value={power?.overview?.totalLoadKw}
          unit="kW"
          status={power?.overview?.gridStatus}
          icon={Zap}
          progress={power?.overview?.loadPercentage}
          trend={`${power?.overview?.loadPercentage}% Capacity (${power?.overview?.totalCapacityKw}kW)`}
          trendDirection="none"
          subtext={`BESS Battery: ${power?.overview?.bessSocPercent}%`}
        />

        {/* Metric 4: Fuel Farm Reserve */}
        <MetricCard
          title="Cryo Fuel Reserve"
          value={fuel?.summary?.totalCurrentLitres?.toLocaleString()}
          unit="L"
          status={fuel?.summary?.overallPercent < 50 ? 'WARNING' : 'NORMAL'}
          icon={Fuel}
          progress={fuel?.summary?.overallPercent}
          trend={`${fuel?.summary?.daysRemaining} Days Autonomy`}
          trendDirection="none"
          subtext={`Burn: ${fuel?.summary?.dailyBurnRateLitres} L/day`}
        />
      </div>

      {/* Main Mission Control Grid: 2D Digital Twin Model + Microgrid & BESS Hub */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: 2D Station Digital Twin Isometric Visual Model */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white tracking-wide uppercase font-scada-mono flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded bg-cyan-400" />
              Live Station 2D Digital Twin Telemetry Model
            </h2>
            <Link
              to="/digital-twin"
              className="text-xs font-scada-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              EXPAND VIEW <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Isometric 2D Digital Twin Model */}
          <MaitriStationDigitalTwin
            modules={digitalTwin?.modules}
            onSelectModule={(mod) => setSelectedModule(mod)}
            selectedModuleId={selectedModule?.id}
          />
        </div>

        {/* Right 1 Col: Power Balance & Battery Gauges */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white tracking-wide uppercase font-scada-mono flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded bg-emerald-400" />
              Microgrid Balance
            </h2>
            <Link
              to="/power"
              className="text-xs font-scada-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              GENSETS <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-4 space-y-4">
            {/* Battery Circular Gauge */}
            <div className="flex items-center justify-around border-b border-[#262626] pb-4">
              <CircularGauge
                value={power?.overview?.bessSocPercent}
                max={100}
                size={110}
                label="BESS BATTERY"
                unit="%"
                status="NORMAL"
                sublabel={`${power?.overview?.bessCurrentKwh?.toFixed(0)} / ${power?.overview?.bessCapacityKwh} kWh`}
              />

              <CircularGauge
                value={power?.overview?.gridFrequencyHz}
                min={48}
                max={52}
                size={110}
                label="BUS FREQUENCY"
                unit="Hz"
                status="NORMAL"
                sublabel={`${power?.overview?.busVoltageV} V (3-Phase)`}
              />
            </div>

            {/* Power Source Contribution List */}
            <div className="space-y-2.5 font-scada-mono text-xs">
              <span className="text-[10px] text-zinc-500 uppercase tracking-wider block font-bold">
                Generation Contributors
              </span>

              {power?.sources?.map(src => (
                <div key={src.id} className="p-2 bg-[#141414] rounded border border-[#2A2A2A] flex items-center justify-between">
                  <div>
                    <div className="text-zinc-200 font-semibold">{src.name}</div>
                    <span className="text-[10px] text-zinc-400">{src.type}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-cyan-400 font-bold">{src.loadKw} kW</div>
                    <StatusBadge status={src.status} size="sm" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Section: 24h Meteorology Trend & Active SCADA Event Queue */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 24-Hour Weather Chart */}
        <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-4 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-sm font-semibold text-white tracking-wide uppercase font-scada-mono">
                24-Hour Extreme Weather Telemetry
              </h3>
              <p className="text-xs text-zinc-400">Temperature & Katabatic Wind Velocity Gradient</p>
            </div>
            <Link
              to="/weather"
              className="text-xs font-scada-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              MET RADAR <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={weather?.history24h || []}>
                <defs>
                  <linearGradient id="windGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00E5FF" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#00E5FF" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="tempGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#FF3344" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#FF3344" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                <XAxis dataKey="time" stroke="#71717A" tick={{ fontSize: 11, fill: '#71717A' }} />
                <YAxis stroke="#71717A" tick={{ fontSize: 11, fill: '#71717A' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#181818',
                    borderColor: '#2A2A2A',
                    color: '#fff',
                    fontFamily: 'JetBrains Mono',
                    fontSize: '12px',
                    borderRadius: '6px'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="windKnots"
                  name="Wind Speed (kts)"
                  stroke="#00E5FF"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#windGrad)"
                />
                <Area
                  type="monotone"
                  dataKey="tempC"
                  name="Outdoor Temp (°C)"
                  stroke="#FF3344"
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#tempGrad)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Live SCADA Alerts & Anomaly Queue */}
        <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-4 flex flex-col">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-white tracking-wide uppercase font-scada-mono">
                Active System Alarms & AI Diagnostics
              </h3>
              {unackAlerts.length > 0 && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/20 text-red-400 border border-red-500/40 font-scada-mono font-bold animate-pulse">
                  {unackAlerts.length} UNACK
                </span>
              )}
            </div>
            <Link
              to="/alerts"
              className="text-xs font-scada-mono text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
            >
              LOG CONSOLE <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-2.5 overflow-y-auto max-h-60 flex-1 pr-1">
            {alerts?.slice(0, 4).map(alert => (
              <div
                key={alert.id}
                className={`p-3 rounded-lg border transition ${
                  alert.severity === 'CRITICAL'
                    ? 'bg-red-950/20 border-red-500/40'
                    : alert.severity === 'WARNING'
                    ? 'bg-yellow-950/20 border-yellow-500/40'
                    : 'bg-[#141414] border-[#2A2A2A]'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <StatusBadge status={alert.severity} size="sm" />
                      <span className="text-xs font-bold text-white">{alert.title}</span>
                    </div>
                    <p className="text-xs text-zinc-300 line-clamp-1">{alert.message}</p>
                    <div className="text-[10px] font-scada-mono text-zinc-400 flex items-center gap-2">
                      <span>{alert.subsystem}</span>
                      <span>•</span>
                      <span>AI CONFIDENCE: {(alert.rootCauseProbability * 100).toFixed(0)}%</span>
                    </div>
                  </div>

                  {!alert.acknowledged ? (
                    <button
                      onClick={() => acknowledgeAlert(alert.id, 'Cmdr. Rajeshwar Sharma')}
                      className="px-2.5 py-1 rounded bg-red-500/20 hover:bg-red-500/40 text-red-400 text-[11px] font-scada-mono font-bold border border-red-500/40 transition flex-shrink-0"
                    >
                      ACK
                    </button>
                  ) : (
                    <span className="flex items-center gap-1 text-[10px] font-scada-mono text-green-400 flex-shrink-0">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      ACKED
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Module Detail Modal */}
      <ModuleDetailModal
        module={selectedModule}
        onClose={() => setSelectedModule(null)}
      />
    </div>
  );
};

export default Dashboard;
