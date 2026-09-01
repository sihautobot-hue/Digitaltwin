import React, { useState } from 'react';
import { useStationData } from '../context/StationDataContext';
import MetricCard from '../components/common/MetricCard';
import StatusBadge from '../components/common/StatusBadge';
import { LinearTankMeter, CircularGauge } from '../components/common/SCADAGauge';
import { 
  Fuel, Droplet, Gauge, Flame, ShieldAlert, ArrowRightLeft, 
  RotateCw, CheckCircle2, AlertTriangle, Play, Square, Layers 
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart,
  Line
} from 'recharts';

export const FuelPage = () => {
  const { stationData, togglePump } = useStationData();
  const [selectedTank, setSelectedTank] = useState(null);

  const { fuel } = stationData;
  const summary = fuel?.summary;
  const tanks = fuel?.tanks || [];
  const pumps = fuel?.pumps || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#262626]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight font-display flex items-center gap-2">
              <Fuel className="w-6 h-6 text-cyan-400" />
              Cryogenic Fuel Farm & Hydrocarbon SCADA
            </h1>
            <StatusBadge status={summary?.fuelQualityStatus} label="HYDROCARBONS NOMINAL" size="sm" />
          </div>
          <p className="text-xs font-scada-mono text-zinc-400 mt-1">
            TOTAL STORAGE: 180,000L | 4 CRYOGENIC POLAR TANKS | TRACE HEATED LINES
          </p>
        </div>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Usable Fuel"
          value={summary?.totalCurrentLitres?.toLocaleString()}
          unit="L"
          status={summary?.overallPercent < 50 ? 'WARNING' : 'NORMAL'}
          progress={summary?.overallPercent}
          icon={Fuel}
          trend={`${summary?.overallPercent}% of 180,000L`}
          trendDirection="none"
          subtext="Safe threshold: 40,000L"
        />

        <MetricCard
          title="Daily Burn Rate"
          value={summary?.dailyBurnRateLitres}
          unit="L / 24h"
          status="NORMAL"
          icon={Droplet}
          trend="CAT 3406 Active Feed"
          trendDirection="none"
          subtext="Specific Gravity: 0.812"
        />

        <MetricCard
          title="Days Autonomy"
          value={summary?.daysRemaining}
          unit="DAYS"
          status={summary?.daysRemaining < 100 ? 'WARNING' : 'NORMAL'}
          icon={Gauge}
          trend={`Winter Target: ${summary?.winterTargetDays}d`}
          trendDirection="up"
          subtext="+35.5 Days Safety Buffer"
        />

        <MetricCard
          title="Hydrocarbon Purity"
          value={summary?.purityIndex}
          unit="%"
          status="NORMAL"
          icon={Flame}
          trend="Trace Heater: Active (-15°C)"
          trendDirection="none"
          subtext="Zero Water Contamination"
        />
      </div>

      {/* Tanks Grid (4 Cryogenic Tanks) */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-white tracking-wide uppercase font-scada-mono flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded bg-cyan-400" />
            Cryogenic Storage Reservoirs (Tanks A - D)
          </h3>
          <span className="text-xs font-scada-mono text-zinc-500">
            DOUBLE-WALLED VACUUM INSULATED
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {tanks.map(tank => (
            <LinearTankMeter
              key={tank.id}
              tank={tank}
              onClick={() => setSelectedTank(tank)}
            />
          ))}
        </div>
      </div>

      {/* SCADA Transfer Pumps & Consumption History */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pump Switchboard */}
        <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider font-scada-mono flex items-center gap-2">
                <ArrowRightLeft className="w-4 h-4 text-cyan-400" />
                Transfer Pumps & Valves
              </h3>
              <StatusBadge status="ACTIVE" label="PUMPS ONLINE" size="sm" />
            </div>
            <p className="text-xs text-zinc-400 mb-4">
              Autonomous hydraulic transfer circuits between storage reservoirs and day headers.
            </p>

            <div className="space-y-3 font-scada-mono text-xs">
              {pumps.map(pump => {
                const isRunning = pump.flowRateLpm > 0;

                return (
                  <div
                    key={pump.id}
                    className="p-3 bg-[#141414] border border-[#2A2A2A] rounded-md flex items-center justify-between"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-cyan-400">{pump.id}</span>
                        <StatusBadge status={isRunning ? 'NORMAL' : 'STANDBY'} size="sm" />
                      </div>
                      <span className="text-zinc-200 font-semibold block mt-0.5">{pump.name}</span>
                      <div className="text-[10px] text-zinc-400 mt-1">
                        FLOW: <span className="text-emerald-400 font-bold">{pump.flowRateLpm} L/min</span> | PSI: {pump.pressurePsi}
                      </div>
                    </div>

                    <button
                      onClick={() => togglePump(pump.id)}
                      className={`px-3 py-1.5 rounded text-xs font-bold transition flex items-center gap-1.5 ${
                        isRunning
                          ? 'bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/40'
                          : 'bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/40'
                      }`}
                    >
                      {isRunning ? <Square className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                      {isRunning ? 'STOP' : 'START'}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-4 p-2.5 bg-[#141414] rounded border border-[#2A2A2A] text-[11px] font-scada-mono text-zinc-400 flex items-center justify-between">
            <span>LEAK DETECTION SENSORS:</span>
            <span className="text-green-400 font-bold">ALL 12 ZONES DRY</span>
          </div>
        </div>

        {/* 6-Month Fuel Consumption Curve */}
        <div className="lg:col-span-2 bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white tracking-wide uppercase font-scada-mono">
                Austral Winter Monthly Fuel Drawdown
              </h3>
              <p className="text-xs text-zinc-400">Correlation with Katabatic blizzard days and heating requirements</p>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={fuel?.consumptionHistory || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                <XAxis dataKey="month" stroke="#71717A" tick={{ fontSize: 11, fill: '#71717A' }} />
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
                <Bar dataKey="consumedL" name="Litres Consumed" fill="#00E5FF" radius={[4, 4, 0, 0]} />
                <Bar dataKey="blizzardDays" name="Blizzard Days" fill="#FF3344" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FuelPage;
