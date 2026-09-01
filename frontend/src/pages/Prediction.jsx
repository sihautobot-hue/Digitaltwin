import React, { useState } from 'react';
import { useStationData } from '../context/StationDataContext';
import MetricCard from '../components/common/MetricCard';
import StatusBadge from '../components/common/StatusBadge';
import { 
  TrendingUp, Bot, BrainCircuit, Activity, AlertTriangle, 
  ShieldCheck, Fuel, Zap, Sparkles, Gauge, Wind, Clock 
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  AreaChart,
  Area
} from 'recharts';

export const Prediction = () => {
  const { stationData } = useStationData();
  const [selectedScenarioIndex, setSelectedScenarioIndex] = useState(0);

  const { prediction } = stationData;
  const storm = prediction?.stormImpactForecast;
  const scenarios = prediction?.fuelDepletionSimulation || [];
  const degradation = prediction?.componentDegradationRul || [];
  const forecast72h = prediction?.hourlyForecast72h || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#262626]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight font-display flex items-center gap-2">
              <BrainCircuit className="w-6 h-6 text-cyan-400" />
              AI Digital Twin Forecast & Neural Degradation Matrix
            </h1>
            <StatusBadge status="ACTIVE" label="NEURAL MODELS RUNNING" size="sm" />
          </div>
          <p className="text-xs font-scada-mono text-zinc-400 mt-1">
            PHYSICS-INFORMED NEURAL NETWORK (PINN) | 72-HOUR MONTE CARLO KATABATIC PREDICTION
          </p>
        </div>
      </div>

      {/* Top AI Forecast KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Predicted Peak Gust"
          value={storm?.predictedPeakWindKnots}
          unit="kts"
          status="CRITICAL"
          icon={Wind}
          trend={`ETA: ${new Date(storm?.predictedPeakTime).toUTCString().slice(17, 22)} UTC`}
          trendDirection="up"
          subtext="Katabatic Front Surge"
        />

        <MetricCard
          title="Min Projected Temp"
          value={storm?.projectedOutdoorTempC}
          unit="°C"
          status="CRITICAL"
          icon={Activity}
          trend="Thermal Drop: -5.4°C"
          trendDirection="down"
          subtext="Madrid Station Model"
        />

        <MetricCard
          title="Peak Heating Load"
          value={storm?.simulatedHeatingDemandKw}
          unit="kW"
          status="WARNING"
          icon={Zap}
          trend={`Grid Stress: ${storm?.powerGridStressIndex}`}
          trendDirection="up"
          subtext="Trace heaters + HVAC"
        />

        <MetricCard
          title="Wind Array Yield"
          value={storm?.windTurbineProductionForecastKw}
          unit="kW"
          status="NORMAL"
          icon={Sparkles}
          trend="High Generation Expected"
          trendDirection="up"
          subtext="4x 15kW Turbines Active"
        />
      </div>

      {/* 72-Hour Katabatic Storm Power & Fuel Neural Simulation Chart */}
      <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-sm font-semibold text-white tracking-wide uppercase font-scada-mono flex items-center gap-2">
              <Bot className="w-4 h-4 text-cyan-400" />
              72-Hour Continuous Neural Telemetry Forecast
            </h3>
            <p className="text-xs text-zinc-400">
              Correlating Katabatic wind intensity with electrical grid demand and fuel burn rate
            </p>
          </div>
          <span className="text-xs font-scada-mono text-cyan-400 bg-cyan-950/60 px-2.5 py-1 rounded border border-cyan-800">
            MODEL CONFIDENCE: 94.2%
          </span>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={forecast72h}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
              <XAxis dataKey="hour" stroke="#71717A" tick={{ fontSize: 11, fill: '#71717A' }} />
              <YAxis yAxisId="power" stroke="#00E5FF" tick={{ fontSize: 11, fill: '#00E5FF' }} />
              <YAxis yAxisId="wind" orientation="right" stroke="#FF3344" tick={{ fontSize: 11, fill: '#FF3344' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#181818',
                  borderColor: '#2A2A2A',
                  color: '#fff',
                  fontFamily: 'JetBrains Mono',
                  fontSize: '12px'
                }}
              />
              <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'JetBrains Mono' }} />
              <Line
                yAxisId="power"
                type="monotone"
                dataKey="powerKw"
                name="Projected Power Draw (kW)"
                stroke="#00E5FF"
                strokeWidth={2}
                dot={{ r: 3, fill: '#00E5FF' }}
              />
              <Line
                yAxisId="wind"
                type="monotone"
                dataKey="windKnots"
                name="Katabatic Wind (kts)"
                stroke="#FF3344"
                strokeWidth={2}
                dot={{ r: 3, fill: '#FF3344' }}
              />
              <Line
                yAxisId="power"
                type="monotone"
                dataKey="fuelRateLph"
                name="Genset Burn Rate (L/h)"
                stroke="#FFB800"
                strokeWidth={2}
                dot={{ r: 3, fill: '#FFB800' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Multi-Scenario Fuel Exhaustion Horizons & Component RUL (Remaining Useful Life) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Fuel Depletion Scenarios */}
        <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white tracking-wide uppercase font-scada-mono flex items-center gap-2">
                <Fuel className="w-4 h-4 text-cyan-400" />
                Monte Carlo Fuel Exhaustion Scenarios
              </h3>
              <p className="text-xs text-zinc-400">
                Predictive winterization buffer under varying meteorological stress conditions
              </p>
            </div>
          </div>

          <div className="space-y-3 font-scada-mono text-xs">
            {scenarios.map((sc, idx) => (
              <div
                key={idx}
                onClick={() => setSelectedScenarioIndex(idx)}
                className={`p-3.5 rounded-lg border transition cursor-pointer ${
                  selectedScenarioIndex === idx
                    ? 'bg-cyan-950/20 border-cyan-500/50 shadow-scada-glow'
                    : 'bg-[#141414] border-[#2A2A2A] hover:border-zinc-500'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-bold text-white text-xs">{sc.scenario}</span>
                  <span className="text-cyan-400 font-bold">{sc.confidencePercent}% CONFIDENCE</span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] text-zinc-300">
                  <div className="p-2 bg-[#1C1C1E] rounded">
                    <span className="text-zinc-500 block text-[10px]">DAYS UNTIL CRITICAL</span>
                    <span className="text-base font-bold text-white">{sc.daysUntilDry} DAYS</span>
                  </div>
                  <div className="p-2 bg-[#1C1C1E] rounded">
                    <span className="text-zinc-500 block text-[10px]">SAFE RESERVE BREACH</span>
                    <span className="text-xs font-bold text-amber-400">{sc.safeReserveBreachDate}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Component Health & RUL Degradation Models */}
        <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-white tracking-wide uppercase font-scada-mono flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                Component Remaining Useful Life (RUL)
              </h3>
              <p className="text-xs text-zinc-400">
                Vibration FFT harmonic analysis & predictive maintenance degradation score
              </p>
            </div>
          </div>

          <div className="space-y-3 font-scada-mono text-xs">
            {degradation.map((comp, idx) => (
              <div
                key={idx}
                className="p-3 bg-[#141414] border border-[#2A2A2A] rounded-lg space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <StatusBadge status={comp.criticality} size="sm" />
                    <span className="text-zinc-200 font-semibold text-xs">{comp.component}</span>
                  </div>
                  <span className="text-cyan-400 font-bold">{comp.currentHealth}% HEALTH</span>
                </div>

                {/* Health Bar */}
                <div className="w-full bg-[#202020] rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      comp.currentHealth > 90 ? 'bg-green-500' : comp.currentHealth > 80 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${comp.currentHealth}%` }}
                  />
                </div>

                <div className="flex justify-between text-[11px] text-zinc-400">
                  <span>EST. RUL: <strong className="text-white">{comp.rulOperatingHours} Operating Hours</strong></span>
                  <span>30d Failure Prob: <strong className={comp.failureProbability30d > 0.5 ? 'text-red-400' : 'text-zinc-300'}>{(comp.failureProbability30d * 100).toFixed(0)}%</strong></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Prediction;
