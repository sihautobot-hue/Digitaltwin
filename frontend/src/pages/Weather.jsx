import React from 'react';
import { useStationData } from '../context/StationDataContext';
import MetricCard from '../components/common/MetricCard';
import StatusBadge from '../components/common/StatusBadge';
import { CircularGauge, WindCompass } from '../components/common/SCADAGauge';
import DataTable from '../components/common/DataTable';
import {
  CloudSnow,
  Wind,
  Thermometer,
  Gauge,
  Sun,
  Eye,
  AlertTriangle,
  Radio,
  Compass,
  TrendingDown,
  Sparkles,
  ShieldAlert
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  AreaChart,
  Area
} from 'recharts';

export const Weather = () => {
  const { stationData } = useStationData();
  const { weather, station } = stationData;
  const current = weather?.current;

  const forecastColumns = [
    { header: 'Period', accessor: 'day', className: 'font-bold text-white' },
    {
      header: 'Temp Range',
      accessor: 'highC',
      render: (_, row) => (
        <span className="font-scada-mono text-zinc-300">
          {row.highC}°C / <span className="text-blue-400">{row.lowC}°C</span>
        </span>
      )
    },
    {
      header: 'Wind Velocity',
      accessor: 'windKnots',
      render: (v) => <span className="font-scada-mono text-cyan-400 font-bold">{v} kts</span>
    },
    { header: 'Condition', accessor: 'condition' },
    {
      header: 'Alert Level',
      accessor: 'status',
      render: (st) => <StatusBadge status={st} size="sm" />
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#262626]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight font-display flex items-center gap-2">
              <CloudSnow className="w-6 h-6 text-cyan-400" />
              Polar Meteorology & Katabatic Wind Observatory
            </h1>
            <StatusBadge status={current?.blizzardAlert?.level} size="md" />
          </div>
          <p className="text-xs font-scada-mono text-zinc-400 mt-1">
            AUTOMATED WEATHER MAST (AWS) | PRINCESS ELIZABETH LAND | POLAR NIGHT
          </p>
        </div>
      </div>

      {/* Extreme Weather Alarm Banner */}
      {current?.blizzardAlert && (
        <div className="p-4 rounded-lg bg-red-950/30 border border-red-500/50 flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-scada-red">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded bg-red-500/20 text-red-400 border border-red-500/30 mt-0.5">
              <ShieldAlert className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-white uppercase font-scada-mono">
                  {current.blizzardAlert.title}
                </span>
                <StatusBadge status={current.blizzardAlert.level} size="sm" />
              </div>
              <p className="text-xs text-zinc-300 mt-1">{current.blizzardAlert.advisory}</p>
            </div>
          </div>

          <div className="text-right font-scada-mono text-xs text-zinc-400 border-t md:border-t-0 md:border-l border-red-900/60 pt-2 md:pt-0 md:pl-4">
            <span className="text-zinc-500 block text-[10px]">PROJECTED PEAK IMPACT</span>
            <span className="text-red-400 font-bold text-sm">+{current.blizzardAlert.etaHours} HOURS</span>
          </div>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Surface Temperature"
          value={current?.outdoorTempC}
          unit="°C"
          status={current?.outdoorTempC < -40 ? 'CRITICAL' : 'NORMAL'}
          icon={Thermometer}
          trend={`Wind Chill: ${current?.windChillC}°C`}
          trendDirection="down"
          subtext="Station Core: 21.2°C"
        />

        <MetricCard
          title="Katabatic Wind Velocity"
          value={current?.windSpeedKnots}
          unit="kts"
          status="CRITICAL"
          icon={Wind}
          trend={`Peak Gust: ${current?.windGustKnots} kts`}
          trendDirection="up"
          subtext={`Speed: ${current?.windSpeedKmh} km/h`}
        />

        <MetricCard
          title="Barometric Pressure"
          value={current?.barometricPressureHpa}
          unit="hPa"
          status="WARNING"
          icon={Gauge}
          trend={current?.pressureTrend}
          trendDirection="down"
          subtext="Steep Katabatic Drop"
        />

        <MetricCard
          title="Geomagnetic Kp Index"
          value={`Kp ${current?.geomagneticKp}`}
          status={current?.geomagneticStatus}
          icon={Sparkles}
          trend={`Aurora: ${current?.auroraProbability}%`}
          trendDirection="none"
          subtext="Ionospheric Scintillation"
        />
      </div>

      {/* Center Row: 360 Wind Compass + Barometer & Aurora Telemetry */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Katabatic Wind Radar Compass */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-wider font-scada-mono flex items-center gap-1.5">
            <Compass className="w-4 h-4 text-cyan-400" />
            360° Wind Vector & Anemometer
          </h3>
          <WindCompass
            directionDeg={current?.windDirectionDeg}
            directionCode={current?.windDirection}
            speedKnots={current?.windSpeedKnots}
            gustKnots={current?.windGustKnots}
          />
        </div>

        {/* Space Weather & Atmospheric Gauges */}
        <div className="lg:col-span-2 bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-5 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-bold text-zinc-400 uppercase tracking-wider font-scada-mono mb-4">
              Upper Atmosphere & Space Weather Telemetry
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 border-b border-[#262626] pb-6">
              <CircularGauge
                value={current?.auroraProbability}
                size={110}
                label="AURORA INTENSITY"
                unit="%"
                status="NORMAL"
                sublabel="High Electron Flux"
              />

              <CircularGauge
                value={current?.humidityPercent}
                size={110}
                label="RELATIVE HUMIDITY"
                unit="%"
                status="NORMAL"
                sublabel="Sublimation Active"
              />

              <CircularGauge
                value={current?.visibilityMeters}
                max={5000}
                size={110}
                label="VISIBILITY"
                unit="m"
                status={current?.visibilityMeters < 1000 ? 'CRITICAL' : 'NORMAL'}
                sublabel="Blowing Snow"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 text-xs font-scada-mono text-zinc-300">
            <div className="p-2.5 bg-[#141414] rounded border border-[#2A2A2A]">
              <span className="text-[10px] text-zinc-500 block">POLAR CYCLE</span>
              <span className="font-bold text-white">{station?.polarCycle}</span>
            </div>
            <div className="p-2.5 bg-[#141414] rounded border border-[#2A2A2A]">
              <span className="text-[10px] text-zinc-500 block">UV INDEX</span>
              <span className="font-bold text-cyan-400">{current?.uvIndex} (Polar Night)</span>
            </div>
            <div className="p-2.5 bg-[#141414] rounded border border-[#2A2A2A]">
              <span className="text-[10px] text-zinc-500 block">PRESSURE DELTA</span>
              <span className="font-bold text-red-400">-4.1 hPa / 3h</span>
            </div>
            <div className="p-2.5 bg-[#141414] rounded border border-[#2A2A2A]">
              <span className="text-[10px] text-zinc-500 block">RADOME HEATING</span>
              <span className="font-bold text-green-400">ACTIVE (4.2 kW)</span>
            </div>
          </div>
        </div>
      </div>

      {/* 24-Hour Trends Chart */}
      <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-semibold text-white tracking-wide uppercase font-scada-mono">
              24-Hour Barometric Pressure & Chill Gradient
            </h3>
            <p className="text-xs text-zinc-400">Historical trend mapping leading into current Katabatic front</p>
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={weather?.history24h || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
              <XAxis dataKey="time" stroke="#71717A" tick={{ fontSize: 11, fill: '#71717A' }} />
              <YAxis yAxisId="left" stroke="#71717A" tick={{ fontSize: 11, fill: '#71717A' }} />
              <YAxis yAxisId="right" orientation="right" stroke="#71717A" tick={{ fontSize: 11, fill: '#71717A' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#181818',
                  borderColor: '#2A2A2A',
                  color: '#fff',
                  fontFamily: 'JetBrains Mono',
                  fontSize: '12px'
                }}
              />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="pressureHpa"
                name="Pressure (hPa)"
                stroke="#FFB800"
                strokeWidth={2}
                dot={{ r: 4, fill: '#FFB800' }}
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="windChillC"
                name="Wind Chill (°C)"
                stroke="#00E5FF"
                strokeWidth={2}
                dot={{ r: 4, fill: '#00E5FF' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 7-Day Polar Meteorological Forecast */}
      <DataTable
        title="7-Day Polar Meteorological Forecast"
        subtitle="Simulated synoptic atmospheric projection for Larsemann Hills region"
        columns={forecastColumns}
        data={weather?.forecast7Days || []}
        pageSize={7}
      />
    </div>
  );
};

export default Weather;
