import React, { useState } from 'react';
import { 
  Zap, Fuel, Droplet, Radio, Boxes, Wrench, Building, 
  Layers, Eye, CheckCircle2, AlertTriangle, ChevronDown,
  Compass, Shield
} from 'lucide-react';
import { useStationData } from '../../context/StationDataContext';

const ICON_MAP = {
  Zap: Zap,
  Fuel: Fuel,
  Droplet: Droplet,
  Radio: Radio,
  Boxes: Boxes,
  Wrench: Wrench,
  Building: Building
};

export const MaitriStationDigitalTwin = ({ 
  modules = [], 
  onSelectModule, 
  selectedModuleId 
}) => {
  const { activeStation } = useStationData();
  const [showLabels, setShowLabels] = useState(true);
  const [viewMode, setViewMode] = useState('2D');
  const [hoveredModule, setHoveredModule] = useState(null);

  // Default facility pin coordinates if missing in json
  const defaultFacilityPinsMaitri = [
    {
      id: 'MOD-PWR',
      name: 'Power House',
      code: 'PWR-GEN',
      status: 'Normal',
      statusType: 'NORMAL',
      xPercent: 24,
      yPercent: 28,
      icon: 'Zap',
      tempC: 26.4,
      powerDrawKw: 142.5,
      occupancy: 2,
      description: 'Triple-redundant polar diesel generation room, 60kW solar PV array, and micro-wind turbines.'
    },
    {
      id: 'MOD-HAB',
      name: 'Main Habitat Core',
      code: 'HAB-CORE',
      status: 'Normal',
      statusType: 'NORMAL',
      xPercent: 48,
      yPercent: 34,
      icon: 'Building',
      tempC: 18.6,
      oxygenPercent: 20.9,
      occupancy: 18,
      description: 'Living quarters, mess galley, medical bay with Indian Tricolour flag mast.'
    },
    {
      id: 'MOD-FUEL',
      name: 'Fuel Farm',
      code: 'FUEL-FARM',
      status: 'Warning',
      statusType: 'WARNING',
      xPercent: 64,
      yPercent: 32,
      icon: 'Fuel',
      tempC: -14.8,
      occupancy: 0,
      description: 'Double-walled cryogenic fuel storage tanks holding Arctic grade Special Polar Diesel.'
    },
    {
      id: 'MOD-COM',
      name: 'Comms Unit',
      code: 'COMMS-SAT',
      status: 'Normal',
      statusType: 'NORMAL',
      xPercent: 16,
      yPercent: 44,
      icon: 'Radio',
      tempC: 18.2,
      occupancy: 1,
      description: 'Primary high-gain satellite dish tracking GSAT and Iridium communication links.'
    },
    {
      id: 'MOD-PUMP',
      name: 'Water Pump House',
      code: 'WTR-PUMP',
      status: 'Normal',
      statusType: 'NORMAL',
      xPercent: 23,
      yPercent: 55,
      icon: 'Droplet',
      tempC: 4.5,
      occupancy: 0,
      description: 'Heated intake pump drawing fresh water from Lake Priyadarshini water source.'
    },
    {
      id: 'MOD-LOG',
      name: 'Storage / Logistics',
      code: 'LOG-DEPOT',
      status: 'Warning',
      statusType: 'WARNING',
      xPercent: 46,
      yPercent: 56,
      icon: 'Boxes',
      tempC: -2.0,
      occupancy: 1,
      description: 'Heavy cargo container staging area, ration store, and polar spare parts vault.'
    },
    {
      id: 'MOD-WRK',
      name: 'Workshop',
      code: 'VEH-SHOP',
      status: 'Normal',
      statusType: 'NORMAL',
      xPercent: 68,
      yPercent: 58,
      icon: 'Wrench',
      tempC: 12.0,
      occupancy: 2,
      description: 'Mechanical repair hangar for PistenBully tracked vehicles and Arctic snowmobiles.'
    }
  ];

  const defaultFacilityPinsBharati = [
    {
      id: 'MOD-BHR-HAB',
      name: 'Stilted Habitat Core',
      code: 'HAB-STILT',
      status: 'Normal',
      statusType: 'NORMAL',
      xPercent: 48,
      yPercent: 34,
      icon: 'Building',
      tempC: 22.0,
      oxygenPercent: 21.0,
      occupancy: 20,
      description: 'Elevated double-deck modular container core on hydraulic stilts to prevent snow drifting.'
    },
    {
      id: 'MOD-BHR-PWR',
      name: 'Powerhouse & BESS',
      code: 'PWR-BESS',
      status: 'Normal',
      statusType: 'NORMAL',
      xPercent: 24,
      yPercent: 28,
      icon: 'Zap',
      tempC: 25.1,
      occupancy: 2,
      powerDrawKw: 168.4,
      description: 'Cogeneration diesel units, waste-heat hydronic loops, and 600kWh LiFePO4 battery array.'
    },
    {
      id: 'MOD-BHR-FUEL',
      name: 'Larsemann Fuel Farm',
      code: 'FUEL-FARM',
      status: 'Normal',
      statusType: 'NORMAL',
      xPercent: 64,
      yPercent: 32,
      icon: 'Fuel',
      tempC: -12.4,
      occupancy: 0,
      description: 'Quadruple cylindrical vacuum tanks insulated for -60°C polar fuel storage.'
    },
    {
      id: 'MOD-BHR-COM',
      name: 'Coastal GSAT-7A Radome',
      code: 'COMMS-RAD',
      status: 'Normal',
      statusType: 'NORMAL',
      xPercent: 16,
      yPercent: 44,
      icon: 'Radio',
      tempC: 19.5,
      occupancy: 1,
      description: 'Dual Ka-band tracking radomes maintaining 2Mbps connection with NCPOR headquarters in Goa.'
    },
    {
      id: 'MOD-BHR-WTR',
      name: 'Desalination & Intake',
      code: 'DESAL-WTR',
      status: 'Normal',
      statusType: 'NORMAL',
      xPercent: 23,
      yPercent: 55,
      icon: 'Droplet',
      tempC: 6.2,
      occupancy: 0,
      description: 'Reverse osmosis sea water desalination and lake filtration system with heated conduits.'
    },
    {
      id: 'MOD-BHR-LOG',
      name: 'Madrid Logistics Staging',
      code: 'LOG-STG',
      status: 'Warning',
      statusType: 'WARNING',
      xPercent: 46,
      yPercent: 56,
      icon: 'Boxes',
      tempC: 1.5,
      occupancy: 1,
      description: 'Insulated container logistics depot housing winter survival supplies and expedition rations.'
    },
    {
      id: 'MOD-BHR-WRK',
      name: 'Submersible ROV Bay',
      code: 'ROV-SHOP',
      status: 'Normal',
      statusType: 'NORMAL',
      xPercent: 68,
      yPercent: 58,
      icon: 'Wrench',
      tempC: 14.2,
      occupancy: 3,
      description: 'Maintenance workshop for deep-sea oceanographic ROVs and PistenBully Polar tractors.'
    }
  ];

  const defaultFacilityPins = activeStation === 'bharati' ? defaultFacilityPinsBharati : defaultFacilityPinsMaitri;

  const displayModules = (modules && modules.length > 0) ? modules.map((m, i) => ({
    ...defaultFacilityPins[i % defaultFacilityPins.length],
    ...m,
    xPercent: m.xPercent || defaultFacilityPins[i % defaultFacilityPins.length].xPercent,
    yPercent: m.yPercent || defaultFacilityPins[i % defaultFacilityPins.length].yPercent,
    icon: m.icon || defaultFacilityPins[i % defaultFacilityPins.length].icon
  })) : defaultFacilityPins;

  const getStatusColor = (statusType) => {
    const normalized = String(statusType || '').toUpperCase();
    switch (normalized) {
      case 'CRITICAL':
      case 'ALARM':
        return {
          dot: 'bg-red-500',
          text: 'text-red-500 dark:text-red-400',
          border: 'border-red-500/60',
          bg: 'bg-white/95 dark:bg-[#151515]/95',
          badgeText: 'Status: Critical'
        };
      case 'WARNING':
      case 'STANDBY':
        return {
          dot: 'bg-yellow-500',
          text: 'text-yellow-600 dark:text-yellow-400',
          border: 'border-yellow-500/50',
          bg: 'bg-white/95 dark:bg-[#151515]/95',
          badgeText: 'Status: Warning'
        };
      case 'OFFLINE':
        return {
          dot: 'bg-zinc-500',
          text: 'text-zinc-500 dark:text-zinc-400',
          border: 'border-zinc-400 dark:border-zinc-600',
          bg: 'bg-white/95 dark:bg-[#151515]/95',
          badgeText: 'Status: Offline'
        };
      default:
        return {
          dot: 'bg-green-500',
          text: 'text-green-600 dark:text-green-400',
          border: 'border-green-500/40',
          bg: 'bg-white/95 dark:bg-[#151515]/95',
          badgeText: 'Status: Normal'
        };
    }
  };

  const stationTitle = activeStation === 'bharati' ? 'Bharati Research Station' : 'Maitri Research Station';
  const stationLocation = activeStation === 'bharati' ? 'Larsemann Hills, Princess Elizabeth Land' : 'Schirmacher Oasis, Queen Maud Land';

  return (
    <div className="bg-white dark:bg-[#181D26] border border-slate-200 dark:border-[#232B3B] rounded-xl overflow-hidden shadow-xl flex flex-col relative transition-colors">
      {/* Top Header Controls */}
      <div className="px-4 py-3 bg-slate-50/90 dark:bg-[#131722]/80 border-b border-slate-200 dark:border-[#232B3B] flex items-center justify-between z-20 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5">
            <span className={`w-2 h-2 rounded-full ${activeStation === 'maitri' ? 'bg-amber-500' : 'bg-cyan-500'} animate-pulse`} />
            <h2 className="text-sm font-bold text-slate-900 dark:text-white tracking-wide">
              {stationTitle} – 2D Digital Twin View
            </h2>
          </div>
          <span className="hidden sm:inline text-[10px] font-scada-mono text-slate-500 dark:text-zinc-400">
            | {stationLocation}
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs font-sans">
          {/* Labels Toggle */}
          <div className="flex items-center gap-2">
            <span className="text-slate-600 dark:text-zinc-400 text-xs font-medium">Labels</span>
            <button
              onClick={() => setShowLabels(!showLabels)}
              className={`w-9 h-5 rounded-full transition-colors relative flex items-center p-0.5 ${
                showLabels ? 'bg-blue-600' : 'bg-slate-300 dark:bg-zinc-700'
              }`}
            >
              <div
                className={`w-4 h-4 rounded-full bg-white shadow transition-transform ${
                  showLabels ? 'translate-x-4' : 'translate-x-0'
                }`}
              />
            </button>
          </div>

          {/* View Dropdown */}
          <div className="flex items-center gap-1 bg-white dark:bg-[#1A2232] border border-slate-300 dark:border-[#2B374E] px-2.5 py-1 rounded-md text-slate-800 dark:text-zinc-200 shadow-sm">
            <span className="text-slate-500 dark:text-zinc-400 text-xs">View:</span>
            <span className="font-semibold text-xs">{viewMode}</span>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 dark:text-zinc-400" />
          </div>
        </div>
      </div>

      {/* Main Interactive Digital Twin Canvas Area */}
      <div className="relative w-full aspect-[16/9] min-h-[380px] bg-[#0E131F] overflow-hidden select-none group">
        {/* Base Isometric High-Res Terrain Render */}
        <img
          src="/assets/maitri_twin_base.jpg"
          alt="Antarctic Station 2D Digital Twin"
          className="w-full h-full object-cover object-center filter brightness-[0.97] contrast-[1.02]"
        />

        {/* SVG Pipeline Connection Network & Nodes Overlay */}
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none z-10"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient id="pipeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#2563EB" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#00E5FF" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#2563EB" stopOpacity="0.8" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="0.8" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Umbilical Pipeline Network Tracks */}
          <g stroke="url(#pipeGrad)" strokeWidth="0.35" strokeDasharray="1.2 0.8" fill="none" opacity="0.85" filter="url(#glow)">
            {/* Power House -> Main Station */}
            <path d="M 28 32 L 36 34 L 46 38" />
            {/* Comms Unit -> Main Station */}
            <path d="M 18 52 L 32 50 L 46 42" />
            {/* Water Pump House -> Main Station */}
            <path d="M 26 62 L 38 58 L 48 46" />
            {/* Main Station -> Fuel Farm */}
            <path d="M 58 36 L 68 36 L 74 38" />
            {/* Storage Depot -> Main Station */}
            <path d="M 48 64 L 50 52 L 52 44" />
            {/* Storage Depot -> Workshop */}
            <path d="M 56 68 L 68 66 L 76 64" />
          </g>

          {/* Connection Hub Junction Nodes */}
          {[
            { cx: 36, cy: 34 },
            { cx: 32, cy: 50 },
            { cx: 38, cy: 58 },
            { cx: 68, cy: 36 },
            { cx: 50, cy: 52 },
            { cx: 68, cy: 66 },
          ].map((node, i) => (
            <g key={i}>
              <circle cx={node.cx} cy={node.cy} r="1.2" fill="#131B2A" stroke="#00E5FF" strokeWidth="0.3" />
              <circle cx={node.cx} cy={node.cy} r="0.5" fill="#00E5FF" className="animate-pulse" />
            </g>
          ))}
        </svg>

        {/* Interactive Module Pins & Callout Badges */}
        {displayModules.map((mod) => {
          const style = getStatusColor(mod.statusType || mod.status);
          const isSelected = selectedModuleId === mod.id;
          const isHovered = hoveredModule === mod.id;
          const IconComponent = ICON_MAP[mod.icon] || Zap;

          return (
            <div
              key={mod.id}
              style={{
                left: `${mod.xPercent}%`,
                top: `${mod.yPercent}%`
              }}
              className="absolute -translate-x-1/2 -translate-y-1/2 z-20 transition-all duration-300"
              onMouseEnter={() => setHoveredModule(mod.id)}
              onMouseLeave={() => setHoveredModule(null)}
              onClick={() => onSelectModule && onSelectModule(mod)}
            >
              {/* Circular Anchor Node */}
              <div className="relative flex items-center justify-center cursor-pointer group/pin">
                <div
                  className={`w-7 h-7 rounded-full bg-[#121824]/90 border ${
                    isSelected ? 'border-cyan-400 scale-125' : style.border
                  } shadow-lg flex items-center justify-center transition-all duration-200 group-hover/pin:scale-125`}
                >
                  <IconComponent className={`w-3.5 h-3.5 ${style.text}`} />
                </div>

                {/* Pulsing Beacon Ring */}
                <div
                  className={`absolute -inset-1 rounded-full ${style.dot} opacity-30 animate-ping pointer-events-none`}
                />
              </div>

              {/* Attached Floating Status Callout Card */}
              {showLabels && (
                <div
                  className={`mt-1.5 min-w-[130px] rounded-lg px-2.5 py-1.5 shadow-2xl border ${
                    isSelected ? 'border-cyan-400 bg-white/95 dark:bg-[#162032]' : `${style.border} ${style.bg}`
                  } backdrop-blur-md cursor-pointer transition-all duration-200 hover:scale-105 ${
                    isHovered || isSelected ? 'ring-1 ring-cyan-400' : ''
                  }`}
                >
                  <div className="text-[11px] font-bold text-slate-900 dark:text-white whitespace-nowrap leading-tight">
                    {mod.name}
                  </div>
                  <div className="flex items-center gap-1.5 mt-0.5">
                    <span className={`w-1.5 h-1.5 rounded-full ${style.dot}`} />
                    <span className={`text-[10px] font-medium ${style.text} whitespace-nowrap font-scada-mono`}>
                      {style.badgeText}
                    </span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Bottom Legend Bar */}
      <div className="px-4 py-2.5 bg-slate-50/90 dark:bg-[#131722]/90 border-t border-slate-200 dark:border-[#232B3B] flex flex-wrap items-center justify-between gap-3 text-xs z-20">
        <div className="flex items-center gap-4 text-xs font-sans">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-slate-700 dark:text-zinc-300 text-xs">Normal</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-yellow-500" />
            <span className="text-slate-700 dark:text-zinc-300 text-xs">Warning</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-slate-700 dark:text-zinc-300 text-xs">Critical</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-zinc-400 dark:bg-zinc-500" />
            <span className="text-slate-700 dark:text-zinc-300 text-xs">Offline</span>
          </div>
        </div>

        <div className="text-[11px] text-slate-500 dark:text-zinc-400 font-sans">
          Click on any module to inspect live telemetry & subsystem controls
        </div>
      </div>
    </div>
  );
};

export default MaitriStationDigitalTwin;
