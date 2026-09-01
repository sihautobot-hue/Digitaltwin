import React from 'react';
import { useStationData } from '../context/StationDataContext';
import MetricCard from '../components/common/MetricCard';
import StatusBadge from '../components/common/StatusBadge';
import { CircularGauge } from '../components/common/SCADAGauge';
import { 
  Zap, BatteryCharging, Wind, Sun, Power, 
  Activity, ShieldCheck, AlertTriangle, Play, Square, 
  RotateCw, ToggleLeft, ToggleRight 
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

export const PowerPage = () => {
  const { stationData, toggleGenerator, toggleCircuit } = useStationData();

  const { power } = stationData;
  const overview = power?.overview;
  const sources = power?.sources || [];
  const circuits = power?.distributionCircuits || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#262626]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight font-display flex items-center gap-2">
              <Zap className="w-6 h-6 text-cyan-400" />
              Station Microgrid & Polar Genset Switchboard
            </h1>
            <StatusBadge status={overview?.gridStatus} label="MICROGRID STABLE" size="sm" />
          </div>
          <p className="text-xs font-scada-mono text-zinc-400 mt-1">
            400V AC 3-PHASE | 50.00 HZ SYNC | TRIPLE REDUNDANT GENSET ARRAY | 600 KWH BESS
          </p>
        </div>
      </div>

      {/* Top SCADA Electrical Grid Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Demand Load"
          value={overview?.totalLoadKw}
          unit="kW"
          status="NORMAL"
          progress={overview?.loadPercentage}
          icon={Zap}
          trend={`${overview?.loadPercentage}% of ${overview?.totalCapacityKw} kW`}
          trendDirection="none"
          subtext="Power Factor: 0.95 cosφ"
        />

        <MetricCard
          title="BESS Storage (LiFePO4)"
          value={overview?.bessSocPercent}
          unit="%"
          status="NORMAL"
          progress={overview?.bessSocPercent}
          icon={BatteryCharging}
          trend={`${overview?.bessCurrentKwh?.toFixed(0)} / ${overview?.bessCapacityKwh} kWh`}
          trendDirection="none"
          subtext={`Cycle Health: ${overview?.bessHealthPercent}%`}
        />

        <MetricCard
          title="Bus Frequency"
          value={overview?.gridFrequencyHz}
          unit="Hz"
          status="NORMAL"
          icon={Activity}
          trend="Nominal (50.00 Hz)"
          trendDirection="none"
          subtext={`Delta: +0.04 Hz`}
        />

        <MetricCard
          title="Bus Voltage"
          value={overview?.busVoltageV}
          unit="V"
          status="NORMAL"
          icon={Power}
          trend="3-Phase Line-to-Line"
          trendDirection="none"
          subtext="Voltage THD: < 1.4%"
        />
      </div>

      {/* Power Sources Grid (Gensets + Wind Array + Solar Array) */}
      <div>
        <h3 className="text-sm font-bold text-white tracking-wide uppercase font-scada-mono mb-3 flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded bg-cyan-400" />
          Generation Assets & Telemetry Gauges
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sources.map(src => {
            const isActive = src.loadKw > 0;

            return (
              <div
                key={src.id}
                className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-4 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-scada-mono font-bold text-cyan-400">{src.id}</span>
                    <StatusBadge status={src.status} size="sm" />
                  </div>

                  <h4 className="text-sm font-semibold text-white mb-1">{src.name}</h4>
                  <p className="text-[11px] text-zinc-400 mb-3">{src.type}</p>

                  {/* Progress Bar */}
                  <div className="space-y-1 mb-3">
                    <div className="flex justify-between text-xs font-scada-mono">
                      <span className="text-zinc-400">LOAD:</span>
                      <span className="text-cyan-400 font-bold">{src.loadKw} / {src.maxKw} kW ({src.loadPercent}%)</span>
                    </div>
                    <div className="w-full bg-[#141414] rounded-full h-2 border border-[#2A2A2A] overflow-hidden">
                      <div
                        className="h-full bg-cyan-500 rounded-full transition-all duration-500"
                        style={{ width: `${Math.min(100, src.loadPercent)}%` }}
                      />
                    </div>
                  </div>

                  {/* Telemetry Readouts */}
                  <div className="grid grid-cols-3 gap-2 text-center text-[11px] font-scada-mono text-zinc-300 py-2 border-t border-[#262626] bg-[#141414] rounded p-2">
                    <div>
                      <span className="text-zinc-500 block text-[10px]">RPM</span>
                      <span className="font-bold text-white">{src.rpm}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px]">COOLANT</span>
                      <span className="font-bold text-white">{src.coolantTempC}°C</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px]">BURN</span>
                      <span className="font-bold text-white">{src.fuelRateLph} L/h</span>
                    </div>
                  </div>

                  {src.note && (
                    <div className="mt-2.5 p-2 rounded bg-yellow-950/20 border border-yellow-500/30 text-[11px] text-yellow-300 flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 flex-shrink-0" />
                      <span>{src.note}</span>
                    </div>
                  )}
                </div>

                {/* Generator Control Button */}
                {src.type.includes('Diesel') && (
                  <div className="mt-4 pt-3 border-t border-[#262626] flex items-center justify-between">
                    <span className="text-[11px] font-scada-mono text-zinc-500">
                      HEALTH: {src.healthScore}%
                    </span>
                    <button
                      onClick={() => toggleGenerator(src.id)}
                      className={`px-3 py-1 rounded text-xs font-scada-mono font-bold transition flex items-center gap-1.5 ${
                        isActive
                          ? 'bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/40'
                          : 'bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/40'
                      }`}
                    >
                      {isActive ? <Square className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                      {isActive ? 'STANDBY GENSET' : 'START GENSET'}
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Load Shedding Priority Circuits & 24h Power Curve */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Load Priority Matrix & Circuit Breakers */}
        <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white tracking-wide uppercase font-scada-mono">
                Load Shedding & Distribution Circuits
              </h3>
              <p className="text-xs text-zinc-400">Automated trip matrix based on station DEFCON level</p>
            </div>
          </div>

          <div className="space-y-2.5 font-scada-mono text-xs">
            {circuits.map(ckt => (
              <div
                key={ckt.id}
                className="p-3 bg-[#141414] border border-[#2A2A2A] rounded-md flex items-center justify-between"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-cyan-400 font-bold">{ckt.id}</span>
                    <StatusBadge status={ckt.priority} size="sm" />
                    <span className="text-zinc-200 font-semibold">{ckt.name}</span>
                  </div>
                  <div className="text-[11px] text-zinc-400 mt-1">
                    DRAW: <span className="text-white font-bold">{ckt.currentKw} kW</span> / {ckt.capacityKw} kW
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className={`text-xs font-bold ${ckt.breakerClosed ? 'text-green-400' : 'text-red-400'}`}>
                    {ckt.breakerClosed ? 'CLOSED' : 'OPEN'}
                  </span>
                  <button
                    onClick={() => toggleCircuit(ckt.id)}
                    className={`p-1.5 rounded transition ${
                      ckt.breakerClosed
                        ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                        : 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                    }`}
                    title={ckt.breakerClosed ? 'Trip Breaker' : 'Close Breaker'}
                  >
                    {ckt.breakerClosed ? (
                      <ToggleRight className="w-6 h-6" />
                    ) : (
                      <ToggleLeft className="w-6 h-6" />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 24h Power Generation Stack Chart */}
        <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white tracking-wide uppercase font-scada-mono">
                24-Hour Energy Generation & Storage Stack
              </h3>
              <p className="text-xs text-zinc-400">Diesel Genset vs Micro-Wind contribution in kW</p>
            </div>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={power?.history24h || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                <XAxis dataKey="time" stroke="#71717A" tick={{ fontSize: 11, fill: '#71717A' }} />
                <YAxis stroke="#71717A" tick={{ fontSize: 11, fill: '#71717A' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#181818',
                    borderColor: '#2A2A2A',
                    color: '#fff',
                    fontFamily: 'JetBrains Mono',
                    fontSize: '12px'
                  }}
                />
                <Area type="monotone" dataKey="gensetKw" name="Diesel Genset (kW)" stackId="1" stroke="#00E5FF" fill="#00E5FF" fillOpacity={0.6} />
                <Area type="monotone" dataKey="windKw" name="Micro-Wind (kW)" stackId="1" stroke="#00FF66" fill="#00FF66" fillOpacity={0.6} />
                <Area type="monotone" dataKey="bessKw" name="BESS Battery (kW)" stackId="1" stroke="#FFB800" fill="#FFB800" fillOpacity={0.6} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PowerPage;
