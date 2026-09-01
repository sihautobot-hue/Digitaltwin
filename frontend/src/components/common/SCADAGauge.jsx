import React from 'react';

/**
 * Circular SCADA Radial Gauge
 */
export const CircularGauge = ({
  value = 0,
  min = 0,
  max = 100,
  size = 120,
  strokeWidth = 10,
  label = '',
  unit = '%',
  status = 'NORMAL',
  sublabel = ''
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedValue = Math.min(max, Math.max(min, value));
  const percentage = ((clampedValue - min) / (max - min)) * 100;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  let strokeColor = '#00E5FF'; // Cyan default
  if (status === 'NORMAL') strokeColor = '#00FF66';
  else if (status === 'WARNING') strokeColor = '#FFB800';
  else if (status === 'CRITICAL') strokeColor = '#FF3344';

  return (
    <div className="flex flex-col items-center justify-center p-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="transform -rotate-90" width={size} height={size}>
          {/* Background Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="#262626"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Active Fill Arc */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-700 ease-out"
          />
        </svg>

        {/* Center Readout */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-lg font-bold font-scada-mono text-white tracking-tight leading-none">
            {typeof value === 'number' ? value.toFixed(1) : value}
          </span>
          {unit && <span className="text-[10px] font-scada-mono text-zinc-400 font-medium">{unit}</span>}
        </div>
      </div>

      {label && <span className="mt-2 text-xs font-semibold text-zinc-300 uppercase tracking-wider text-center">{label}</span>}
      {sublabel && <span className="text-[11px] font-scada-mono text-zinc-500 text-center">{sublabel}</span>}
    </div>
  );
};

/**
 * Industrial Cryogenic Linear Fuel Tank Visualization
 */
export const LinearTankMeter = ({
  tank,
  onClick
}) => {
  const percentage = tank.percentage || 0;
  const isWarning = tank.status === 'WARNING';
  const isCritical = tank.status === 'CRITICAL';
  
  let fillGradient = 'from-emerald-600 to-green-400';
  let badgeColor = 'text-green-400 border-green-500/30';
  
  if (isWarning) {
    fillGradient = 'from-amber-600 to-yellow-400';
    badgeColor = 'text-yellow-400 border-yellow-500/30';
  } else if (isCritical) {
    fillGradient = 'from-rose-600 to-red-500';
    badgeColor = 'text-red-400 border-red-500/30';
  }

  return (
    <div
      onClick={onClick}
      className={`bg-[#1E1E1E] border border-[#2A2A2A] hover:border-zinc-500 rounded-lg p-4 transition cursor-pointer relative overflow-hidden`}
    >
      <div className="flex items-center justify-between mb-3">
        <div>
          <span className="text-xs font-scada-mono font-bold text-cyan-400">{tank.id}</span>
          <h4 className="text-sm font-semibold text-white mt-0.5">{tank.name}</h4>
          <p className="text-[11px] text-zinc-400">{tank.fuelType}</p>
        </div>
        <div className={`text-xs px-2 py-0.5 rounded border font-scada-mono uppercase ${badgeColor}`}>
          {tank.status}
        </div>
      </div>

      {/* Industrial Tank Physical Body */}
      <div className="relative h-28 bg-[#141414] rounded-md border border-[#333] p-1.5 flex flex-col justify-end overflow-hidden">
        {/* Measurement Grid Marks */}
        <div className="absolute inset-y-0 right-2 flex flex-col justify-between text-[9px] font-scada-mono text-zinc-600 select-none pointer-events-none py-1">
          <span>100% - 45kL</span>
          <span>75% - 33kL</span>
          <span>50% - 22kL</span>
          <span>25% - 11kL</span>
          <span>0% - 0kL</span>
        </div>

        {/* Liquid Fill Level */}
        <div
          className={`w-[75%] rounded bg-gradient-to-t ${fillGradient} transition-all duration-700 relative opacity-90`}
          style={{ height: `${percentage}%` }}
        >
          {/* Animated Surface Ripple Line */}
          <div className="absolute top-0 inset-x-0 h-1 bg-white/40 animate-pulse" />
        </div>

        {/* Digital Overlay */}
        <div className="absolute bottom-2 left-3 font-scada-mono">
          <div className="text-lg font-bold text-white leading-tight">
            {tank.currentLitres?.toLocaleString()} <span className="text-xs font-normal text-zinc-400">L</span>
          </div>
          <div className="text-xs text-cyan-400 font-semibold">{percentage}% CAPACITY</div>
        </div>
      </div>

      {/* Telemetry Footer */}
      <div className="grid grid-cols-3 gap-2 mt-3 text-[11px] font-scada-mono text-zinc-400 pt-2 border-t border-[#2A2A2A]">
        <div>
          <span className="text-zinc-500 block text-[10px]">TEMP</span>
          <span className="text-zinc-200">{tank.temperatureC}°C</span>
        </div>
        <div>
          <span className="text-zinc-500 block text-[10px]">PRESSURE</span>
          <span className="text-zinc-200">{tank.pressureBar} bar</span>
        </div>
        <div>
          <span className="text-zinc-500 block text-[10px]">PUMP</span>
          <span className={tank.pumpState === 'ACTIVE' ? 'text-green-400 font-bold' : 'text-zinc-400'}>
            {tank.pumpState}
          </span>
        </div>
      </div>
    </div>
  );
};

/**
 * 360-Degree Katabatic Wind Radar Compass
 */
export const WindCompass = ({
  directionDeg = 158,
  directionCode = 'SSE',
  speedKnots = 58,
  gustKnots = 84
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-4 bg-[#181818] border border-[#2A2A2A] rounded-lg">
      <div className="relative w-44 h-44 rounded-full border-2 border-[#2F3336] bg-[#121212] flex items-center justify-center scada-blueprint-bg shadow-inner">
        {/* Cardinal Points */}
        <span className="absolute top-1 text-[11px] font-scada-mono font-bold text-cyan-400">N (000°)</span>
        <span className="absolute bottom-1 text-[11px] font-scada-mono font-bold text-zinc-400">S (180°)</span>
        <span className="absolute right-2 text-[11px] font-scada-mono font-bold text-zinc-400">E (090°)</span>
        <span className="absolute left-2 text-[11px] font-scada-mono font-bold text-zinc-400">W (270°)</span>

        {/* Concentric Wind Circles */}
        <div className="w-32 h-32 rounded-full border border-dashed border-[#2A2A2A]" />
        <div className="absolute w-20 h-20 rounded-full border border-dashed border-[#333]" />

        {/* Rotating Wind Arrow Vector */}
        <div
          className="absolute inset-0 flex items-center justify-center transition-transform duration-700 pointer-events-none"
          style={{ transform: `rotate(${directionDeg}deg)` }}
        >
          <div className="relative w-1 h-36 flex flex-col items-center justify-start">
            <div className="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-b-[14px] border-b-cyan-400 filter drop-shadow-[0_0_6px_#00E5FF]" />
            <div className="w-0.5 h-16 bg-cyan-400" />
            <div className="w-2 h-2 rounded-full bg-cyan-400 mt-auto" />
          </div>
        </div>

        {/* Center Readout */}
        <div className="z-10 bg-[#1E1E1E] border border-cyan-500/40 rounded-full w-16 h-16 flex flex-col items-center justify-center text-center shadow-lg">
          <span className="text-xs font-bold font-scada-mono text-cyan-400">{directionCode}</span>
          <span className="text-[10px] font-scada-mono text-zinc-400">{directionDeg}°</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 w-full mt-4 text-center font-scada-mono border-t border-[#2A2A2A] pt-3">
        <div>
          <span className="text-zinc-500 text-[10px] uppercase block">Current Velocity</span>
          <span className="text-lg font-bold text-white">{speedKnots} <span className="text-xs font-normal text-zinc-400">kts</span></span>
        </div>
        <div>
          <span className="text-zinc-500 text-[10px] uppercase block">Peak Gust</span>
          <span className="text-lg font-bold text-red-400">{gustKnots} <span className="text-xs font-normal text-zinc-400">kts</span></span>
        </div>
      </div>
    </div>
  );
};
