import React, { useState } from 'react';
import { useStationData } from '../context/StationDataContext';
import MaitriStationDigitalTwin from '../components/digitalTwin/MaitriStationDigitalTwin';
import ModuleDetailModal from '../components/digitalTwin/ModuleDetailModal';
import StatusBadge from '../components/common/StatusBadge';
import MetricCard from '../components/common/MetricCard';
import { 
  Cpu, Activity, Zap, Thermometer, Shield, Users, 
  Layers, Lock, AlertTriangle, CheckCircle2, ChevronRight,
  Droplet, Radio, Boxes, Wrench, Building2 
} from 'lucide-react';

export const DigitalTwin = () => {
  const { stationData } = useStationData();
  const [selectedModule, setSelectedModule] = useState(null);
  const [filterStatus, setFilterStatus] = useState('ALL');

  const { digitalTwin, station } = stationData;
  const modules = digitalTwin?.modules || [];

  const filteredModules = modules.filter(m => {
    if (filterStatus === 'ALL') return true;
    return (m.status || '').toUpperCase() === filterStatus.toUpperCase();
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#262626]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight font-display flex items-center gap-2">
              <Building2 className="w-6 h-6 text-cyan-400" />
              2D Station Physical Digital Twin
            </h1>
            <StatusBadge status="ACTIVE" label="LIVE SYNC" size="sm" />
          </div>
          <p className="text-xs font-scada-mono text-zinc-400 mt-1">
            REAL-TIME PHYSICAL TELEMETRY MAPPING | 7 REINFORCED MODULES | POLAR RESEARCH BASE
          </p>
        </div>

        {/* Filter Toolbar */}
        <div className="flex items-center gap-2 bg-[#1E1E1E] p-1 rounded-md border border-[#2A2A2A] text-xs font-scada-mono">
          {['ALL', 'NORMAL', 'WARNING', 'CRITICAL'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className={`px-3 py-1 rounded transition ${
                filterStatus === st
                  ? 'bg-cyan-500/20 text-cyan-400 font-bold border border-cyan-500/30'
                  : 'text-zinc-400 hover:text-zinc-200'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Top Station Overview Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          title="Total Facilities"
          value={digitalTwin?.stationBlueprint?.totalModules || 7}
          unit="UNITS"
          status="NORMAL"
          subtext="Connected via Heated Pipeline Grid"
          icon={Layers}
        />

        <MetricCard
          title="Station Integrity"
          value={digitalTwin?.stationBlueprint?.structuralIntegrityScore || 98.4}
          unit="%"
          status="NORMAL"
          progress={digitalTwin?.stationBlueprint?.structuralIntegrityScore || 98.4}
          subtext="No hull micro-fissures"
          icon={Shield}
        />

        <MetricCard
          title="Active Personnel"
          value={digitalTwin?.stationBlueprint?.activePersonnelCount || 24}
          unit="CREW"
          status="NORMAL"
          subtext="All 24 accounted for"
          icon={Users}
        />

        <MetricCard
          title="Active Facility Alarms"
          value={digitalTwin?.stationBlueprint?.activeAlarmsCount || 2}
          unit="ACTIVE"
          status={(digitalTwin?.stationBlueprint?.activeAlarmsCount || 2) > 0 ? 'WARNING' : 'NORMAL'}
          subtext="Fuel Farm & Logistics Staging"
          icon={AlertTriangle}
        />
      </div>

      {/* 2D Digital Twin Interactive Visual Model */}
      <div className="space-y-2">
        <MaitriStationDigitalTwin
          modules={modules}
          onSelectModule={(mod) => setSelectedModule(mod)}
          selectedModuleId={selectedModule?.id}
        />
      </div>

      {/* Physical Module Grid Cards */}
      <div>
        <h3 className="text-sm font-bold text-white tracking-wide uppercase font-scada-mono mb-3 flex items-center gap-2">
          <span className="w-2 h-2 rounded bg-cyan-400" />
          Individual Facility Telemetry ({filteredModules.length} Subsystems)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {filteredModules.map((mod) => (
            <div
              key={mod.id}
              onClick={() => setSelectedModule(mod)}
              className="bg-[#1E1E1E] border border-[#2A2A2A] hover:border-cyan-500/60 rounded-lg p-4 cursor-pointer transition flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-scada-mono font-bold text-cyan-400 group-hover:text-cyan-300">
                    {mod.code}
                  </span>
                  <StatusBadge status={mod.status} size="sm" />
                </div>

                <h4 className="text-sm font-semibold text-white mb-2 leading-tight">
                  {mod.name}
                </h4>

                <p className="text-xs text-zinc-400 line-clamp-2 mb-3">
                  {mod.description}
                </p>

                <div className="space-y-1.5 text-xs font-scada-mono text-zinc-300 pt-2 border-t border-[#262626]">
                  {mod.tempC !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-zinc-500">TEMP:</span>
                      <span className="font-bold text-white">{mod.tempC}°C</span>
                    </div>
                  )}
                  {mod.powerDrawKw !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-zinc-500">POWER DRAW:</span>
                      <span className="font-bold text-cyan-400">{mod.powerDrawKw} kW</span>
                    </div>
                  )}
                  {mod.oxygenPercent !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-zinc-500">OXYGEN (O2):</span>
                      <span className="font-bold text-green-400">{mod.oxygenPercent}%</span>
                    </div>
                  )}
                  {mod.occupancy !== undefined && (
                    <div className="flex justify-between">
                      <span className="text-zinc-500">CREW OCCUPANCY:</span>
                      <span className="font-bold text-zinc-200">{mod.occupancy}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-[#262626] flex items-center justify-between text-[10px] font-scada-mono text-zinc-500">
                <span>STATUS: {mod.status}</span>
                <span className="text-cyan-400 group-hover:underline flex items-center gap-0.5">
                  INSPECT →
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Module Detail Inspector Modal */}
      <ModuleDetailModal
        module={selectedModule}
        onClose={() => setSelectedModule(null)}
      />
    </div>
  );
};

export default DigitalTwin;
