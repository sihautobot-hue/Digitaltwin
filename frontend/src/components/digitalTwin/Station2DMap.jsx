import React, { useState } from 'react';
import StatusBadge from '../common/StatusBadge';
import { 
  Activity, Zap, Thermometer, Wind, AlertTriangle, ShieldCheck, 
  Users, Layers, Radio, Lock, RefreshCw, CheckCircle2 
} from 'lucide-react';

export const Station2DMap = ({ modules = [], onSelectModule, selectedModuleId }) => {
  const [activeLayer, setActiveLayer] = useState('scada'); // 'scada', 'thermal', 'power', 'hvac'
  const [zoomLevel, setZoomLevel] = useState(1);

  const getModuleFill = (mod) => {
    if (activeLayer === 'thermal') {
      const temp = mod.tempC;
      if (temp < -10) return 'rgba(59, 130, 246, 0.25)'; // Freezing blue
      if (temp < 15) return 'rgba(6, 182, 212, 0.25)'; // Cool cyan
      if (temp < 24) return 'rgba(34, 197, 94, 0.25)'; // Comfortable green
      return 'rgba(239, 68, 68, 0.35)'; // Hot red/amber
    }
    if (activeLayer === 'power') {
      const kw = mod.powerDrawKw;
      if (kw > 80) return 'rgba(239, 68, 68, 0.35)';
      if (kw > 30) return 'rgba(234, 179, 8, 0.3)';
      return 'rgba(34, 197, 94, 0.25)';
    }
    if (activeLayer === 'hvac') {
      return mod.airlockSealStatus === 'SEALED' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.3)';
    }
    // Default SCADA view
    if (mod.status === 'CRITICAL') return 'rgba(239, 68, 68, 0.2)';
    if (mod.status === 'WARNING') return 'rgba(234, 179, 8, 0.15)';
    return 'rgba(30, 30, 30, 0.9)';
  };

  const getModuleBorder = (mod) => {
    if (selectedModuleId === mod.id) return '#00E5FF';
    if (mod.status === 'CRITICAL') return '#FF3344';
    if (mod.status === 'WARNING') return '#FFB800';
    return '#2F80ED';
  };

  return (
    <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg overflow-hidden flex flex-col">
      {/* Blueprint Control Bar */}
      <div className="p-3 bg-[#181818] border-b border-[#2A2A2A] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded bg-[#121212] border border-[#2A2A2A] text-cyan-400">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              2D Polar Station Architecture Blueprint
            </h3>
            <span className="text-[10px] font-scada-mono text-zinc-400">
              PHYSICAL SCADA TELEMETRY MAPPING | 8 REINFORCED MODULES
            </span>
          </div>
        </div>

        {/* Layer Switches */}
        <div className="flex items-center gap-1.5 bg-[#121212] p-1 rounded-md border border-[#2A2A2A] text-xs font-scada-mono">
          <button
            onClick={() => setActiveLayer('scada')}
            className={`px-2.5 py-1 rounded transition ${
              activeLayer === 'scada' ? 'bg-cyan-500/20 text-cyan-400 font-bold border border-cyan-500/30' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            SCADA Overview
          </button>
          <button
            onClick={() => setActiveLayer('thermal')}
            className={`px-2.5 py-1 rounded transition ${
              activeLayer === 'thermal' ? 'bg-amber-500/20 text-amber-400 font-bold border border-amber-500/30' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Thermals
          </button>
          <button
            onClick={() => setActiveLayer('power')}
            className={`px-2.5 py-1 rounded transition ${
              activeLayer === 'power' ? 'bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Power Grid
          </button>
          <button
            onClick={() => setActiveLayer('hvac')}
            className={`px-2.5 py-1 rounded transition ${
              activeLayer === 'hvac' ? 'bg-blue-500/20 text-blue-400 font-bold border border-blue-500/30' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            HVAC & Life Support
          </button>
        </div>
      </div>

      {/* Interactive Blueprint Canvas */}
      <div className="relative w-full h-[460px] bg-[#0E1117] scada-blueprint-bg overflow-auto p-4 flex items-center justify-center">
        {/* Environmental Legend */}
        <div className="absolute top-3 left-3 bg-[#121212]/90 border border-[#2A2A2A] backdrop-blur-sm p-2 rounded text-[10px] font-scada-mono text-zinc-400 z-10 flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            <span>Nominal Operations</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-yellow-500" />
            <span>Telemetry Warning</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <span>Alarm / Isolation Tripped</span>
          </div>
        </div>

        {/* SVG Layout */}
        <svg
          viewBox="0 0 960 440"
          className="w-full max-w-5xl h-auto drop-shadow-2xl select-none"
          style={{ minWidth: '700px' }}
        >
          <defs>
            <pattern id="gridPattern" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(0, 229, 255, 0.05)" strokeWidth="1" />
            </pattern>
            <linearGradient id="corridorGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#00E5FF" stopOpacity="0.6" />
              <stop offset="50%" stopColor="#2F80ED" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#00E5FF" stopOpacity="0.6" />
            </linearGradient>
          </defs>

          {/* Background Grid */}
          <rect width="960" height="440" fill="url(#gridPattern)" />

          {/* Central Connecting Corridor Umbilicals */}
          <g stroke="url(#corridorGrad)" strokeWidth="8" strokeLinecap="round" opacity="0.7">
            {/* Horizontal Spine Top */}
            <line x1="150" y1="130" x2="810" y2="130" strokeDasharray="6,4" />
            {/* Horizontal Spine Bottom */}
            <line x1="150" y1="310" x2="810" y2="310" strokeDasharray="6,4" />
            {/* Vertical Interconnectors */}
            <line x1="150" y1="130" x2="150" y2="310" />
            <line x1="370" y1="130" x2="370" y2="310" />
            <line x1="590" y1="130" x2="590" y2="310" />
            <line x1="810" y1="130" x2="810" y2="310" />
          </g>

          {/* Station Modules */}
          {modules.map((mod) => {
            const isSelected = selectedModuleId === mod.id;
            const borderColor = getModuleBorder(mod);
            const fill = getModuleFill(mod);

            return (
              <g
                key={mod.id}
                onClick={() => onSelectModule && onSelectModule(mod)}
                className="cursor-pointer transition-transform duration-200 hover:scale-[1.01]"
                transform-origin={`${mod.x + mod.w / 2} ${mod.y + mod.h / 2}`}
              >
                {/* Outer Glow for Selected / Critical */}
                {isSelected && (
                  <rect
                    x={mod.x - 4}
                    y={mod.y - 4}
                    width={mod.w + 8}
                    height={mod.h + 8}
                    rx="8"
                    fill="none"
                    stroke="#00E5FF"
                    strokeWidth="2"
                    strokeDasharray="4,4"
                    className="animate-pulse"
                  />
                )}

                {/* Module Body */}
                <rect
                  x={mod.x}
                  y={mod.y}
                  width={mod.w}
                  height={mod.h}
                  rx="6"
                  fill={fill}
                  stroke={borderColor}
                  strokeWidth={isSelected ? '3' : '1.5'}
                  className="transition-all duration-300"
                />

                {/* Header Bar in Module */}
                <rect
                  x={mod.x}
                  y={mod.y}
                  width={mod.w}
                  height="26"
                  rx="6"
                  fill="#141414"
                  opacity="0.9"
                />

                {/* Module Code & Name */}
                <text
                  x={mod.x + 8}
                  y={mod.y + 17}
                  fill="#00E5FF"
                  fontSize="11"
                  fontWeight="bold"
                  fontFamily="JetBrains Mono, monospace"
                >
                  {mod.code}
                </text>

                <text
                  x={mod.x + mod.w - 8}
                  y={mod.y + 17}
                  fill={mod.status === 'CRITICAL' ? '#FF3344' : mod.status === 'WARNING' ? '#FFB800' : '#00FF66'}
                  fontSize="9"
                  fontWeight="bold"
                  textAnchor="end"
                  fontFamily="JetBrains Mono, monospace"
                >
                  ● {mod.status}
                </text>

                {/* Full Title */}
                <text
                  x={mod.x + 10}
                  y={mod.y + 45}
                  fill="#FFFFFF"
                  fontSize="11"
                  fontWeight="600"
                  fontFamily="Inter, sans-serif"
                >
                  {mod.name.length > 22 ? mod.name.slice(0, 20) + '...' : mod.name}
                </text>

                {/* Telemetry Metrics on Block */}
                <g fontFamily="JetBrains Mono, monospace" fontSize="10">
                  {/* Temp */}
                  <text x={mod.x + 10} y={mod.y + 68} fill="#8E8E93">
                    TEMP: <tspan fill="#FFFFFF" fontWeight="bold">{mod.tempC}°C</tspan>
                  </text>

                  {/* Power */}
                  <text x={mod.x + 10} y={mod.y + 86} fill="#8E8E93">
                    PWR: <tspan fill="#00E5FF" fontWeight="bold">{mod.powerDrawKw} kW</tspan>
                  </text>

                  {/* Occupancy / O2 */}
                  <text x={mod.x + 10} y={mod.y + 104} fill="#8E8E93">
                    O2: <tspan fill="#00FF66" fontWeight="bold">{mod.oxygenPercent}%</tspan> | CREW: <tspan fill="#FFFFFF">{mod.occupancy}</tspan>
                  </text>

                  {/* Airlock Status */}
                  <text x={mod.x + 10} y={mod.y + 122} fill="#8E8E93">
                    SEAL: <tspan fill={mod.airlockSealStatus === 'SEALED' ? '#00FF66' : '#FF3344'} fontWeight="bold">{mod.airlockSealStatus}</tspan>
                  </text>
                </g>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Helper Footer */}
      <div className="p-2.5 bg-[#181818] border-t border-[#2A2A2A] flex items-center justify-between text-xs text-zinc-400 font-scada-mono">
        <span className="flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-cyan-400" />
          Click any module to inspect SCADA life support valves and subsystem telemetry
        </span>
        <span className="text-zinc-500">BHARATI DIGITAL TWIN v4.2</span>
      </div>
    </div>
  );
};

export default Station2DMap;
