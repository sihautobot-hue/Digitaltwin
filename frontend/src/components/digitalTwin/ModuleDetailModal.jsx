import React from 'react';
import StatusBadge from '../common/StatusBadge';
import { 
  X, Activity, Shield, Zap, Thermometer, Wind, 
  Flame, CheckCircle2, AlertTriangle, Lock, ShieldAlert, 
  Power, Fan, Radio 
} from 'lucide-react';

export const ModuleDetailModal = ({ module, onClose, onToggleIsolation }) => {
  if (!module) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
      <div className="relative w-full max-w-2xl bg-[#1E1E1E] border border-cyan-500/40 rounded-lg shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="p-4 bg-[#141414] border-b border-[#2A2A2A] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded bg-[#1C1C1E] border border-cyan-500/30 text-cyan-400 font-scada-mono font-bold text-sm">
              {module.code}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-white tracking-wide">{module.name}</h3>
                <StatusBadge status={module.status} size="sm" />
              </div>
              <p className="text-xs font-scada-mono text-zinc-400 mt-0.5">
                MODULE ID: {module.id} | OCCUPANCY: {module.occupancy} / {module.maxOccupancy} CREW
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded bg-[#1C1C1E] border border-[#2A2A2A] text-zinc-400 hover:text-white transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-5 overflow-y-auto space-y-5">
          <p className="text-xs text-zinc-300 bg-[#141414] p-3 rounded border border-[#2A2A2A] leading-relaxed">
            {module.description}
          </p>

          {/* Environmental & Life Support SCADA Grid */}
          <div>
            <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-2 font-scada-mono">
              Life Support & Atmospheric Telemetry
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A]">
                <div className="flex items-center justify-between text-zinc-400 text-xs mb-1">
                  <span>Temperature</span>
                  <Thermometer className="w-3.5 h-3.5 text-rose-400" />
                </div>
                <div className="text-lg font-bold font-scada-mono text-white">{module.tempC}°C</div>
                <span className="text-[10px] font-scada-mono text-zinc-500">Target: {module.targetTempC}°C</span>
              </div>

              <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A]">
                <div className="flex items-center justify-between text-zinc-400 text-xs mb-1">
                  <span>Power Draw</span>
                  <Zap className="w-3.5 h-3.5 text-cyan-400" />
                </div>
                <div className="text-lg font-bold font-scada-mono text-cyan-400">{module.powerDrawKw} kW</div>
                <span className="text-[10px] font-scada-mono text-zinc-500">400V 3-Phase</span>
              </div>

              <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A]">
                <div className="flex items-center justify-between text-zinc-400 text-xs mb-1">
                  <span>Oxygen (O2)</span>
                  <Activity className="w-3.5 h-3.5 text-green-400" />
                </div>
                <div className="text-lg font-bold font-scada-mono text-green-400">{module.oxygenPercent}%</div>
                <span className="text-[10px] font-scada-mono text-zinc-500">CO2: {module.co2Ppm} ppm</span>
              </div>

              <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A]">
                <div className="flex items-center justify-between text-zinc-400 text-xs mb-1">
                  <span>Humidity</span>
                  <Wind className="w-3.5 h-3.5 text-blue-400" />
                </div>
                <div className="text-lg font-bold font-scada-mono text-white">{module.humidity}%</div>
                <span className="text-[10px] font-scada-mono text-zinc-500">Relative (RH)</span>
              </div>
            </div>
          </div>

          {/* Safety & Barrier Status */}
          <div>
            <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-2 font-scada-mono">
              Safety Protocols & Airlock Seals
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A] flex items-center justify-between">
                <div>
                  <span className="text-[10px] uppercase text-zinc-500 block font-scada-mono">Airlock Seal</span>
                  <span className="text-xs font-bold font-scada-mono text-white">{module.airlockSealStatus}</span>
                </div>
                <StatusBadge status={module.airlockSealStatus} size="sm" />
              </div>

              <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A] flex items-center justify-between">
                <div>
                  <span className="text-[10px] uppercase text-zinc-500 block font-scada-mono">Fire Suppression</span>
                  <span className="text-xs font-bold font-scada-mono text-white">{module.fireSuppression}</span>
                </div>
                <StatusBadge status={module.fireSuppression} size="sm" />
              </div>

              <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A] flex items-center justify-between">
                <div>
                  <span className="text-[10px] uppercase text-zinc-500 block font-scada-mono">Isolation Valve</span>
                  <span className="text-xs font-bold font-scada-mono text-white">{module.isolationValve}</span>
                </div>
                <StatusBadge status={module.isolationValve === 'OPEN' ? 'NORMAL' : 'WARNING'} size="sm" />
              </div>
            </div>
          </div>

          {/* Subsystem Critical Equipment */}
          <div>
            <h4 className="text-xs font-bold text-zinc-400 uppercase tracking-wider mb-2 font-scada-mono">
              Internal Subsystem Assemblies
            </h4>
            <div className="divide-y divide-[#262626] bg-[#141414] rounded border border-[#2A2A2A] overflow-hidden">
              {module.criticalEquipment?.map((eq, idx) => (
                <div key={idx} className="p-2.5 flex items-center justify-between text-xs">
                  <span className="text-zinc-200 font-medium">{eq.name}</span>
                  <StatusBadge status={eq.status} size="sm" />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Modal Footer Controls */}
        <div className="p-4 bg-[#141414] border-t border-[#2A2A2A] flex items-center justify-between">
          <div className="text-[11px] font-scada-mono text-zinc-500">
            SCADA CHANNEL: {module.code}-TELEMETRY-4
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 rounded text-xs bg-[#242424] hover:bg-[#2C2C2E] text-zinc-300 font-medium transition"
            >
              Close Inspector
            </button>
            <button
              onClick={() => {
                alert(`Simulated emergency SCADA command transmitted: Isolation valve cycling on ${module.code}`);
              }}
              className="px-3 py-1.5 rounded text-xs bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-500/40 font-scada-mono font-bold transition flex items-center gap-1.5"
            >
              <ShieldAlert className="w-3.5 h-3.5" />
              Cycle Isolation Valve
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModuleDetailModal;
