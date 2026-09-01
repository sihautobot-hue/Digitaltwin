import React, { useState } from 'react';
import { useStationData } from '../context/StationDataContext';
import StatusBadge from '../components/common/StatusBadge';
import { 
  FileText, Printer, Download, Compass, CheckCircle2, 
  Calendar, User, Shield, AlertTriangle, Zap, Fuel, Activity 
} from 'lucide-react';

export const Reports = () => {
  const { stationData, exportTelemetryJSON } = useStationData();
  const [reportType, setReportType] = useState('SITREP'); // 'SITREP', 'ENERGY_AUDIT', 'SHIFT_LOG'

  const { station, weather, power, fuel, reports, alerts, digitalTwin } = stationData;
  const sitrep = reports?.sitrep;

  const handlePrint = () => {
    window.print();
  };

  const handleExportCSV = () => {
    const csvContent = "data:text/csv;charset=utf-8," + 
      "Subsystem,Parameter,Value,Unit,Status\n" +
      `Station,Active Personnel,${digitalTwin?.stationBlueprint?.activePersonnelCount},Crew,NOMINAL\n` +
      `Weather,Surface Temperature,${weather?.current?.outdoorTempC},C,${weather?.current?.outdoorTempC < -40 ? 'CRITICAL' : 'NORMAL'}\n` +
      `Weather,Katabatic Wind Speed,${weather?.current?.windSpeedKnots},kts,CRITICAL\n` +
      `Power,Total Load,${power?.overview?.totalLoadKw},kW,NORMAL\n` +
      `Power,BESS Battery SOC,${power?.overview?.bessSocPercent},%,NORMAL\n` +
      `Fuel,Total Usable Litres,${fuel?.summary?.totalCurrentLitres},L,NORMAL\n` +
      `Fuel,Days Autonomy,${fuel?.summary?.daysRemaining},Days,NORMAL\n`;
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `bharati-sitrep-telemetry-${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="space-y-6">
      {/* Header (Hidden on Print) */}
      <div className="no-print flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#262626]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight font-display flex items-center gap-2">
              <FileText className="w-6 h-6 text-cyan-400" />
              SCADA SITREP & Official Mission Logs
            </h1>
            <StatusBadge status="ACTIVE" label="PDF PRINT OPTIMIZED" size="sm" />
          </div>
          <p className="text-xs font-scada-mono text-zinc-400 mt-1">
            NATIONAL CENTRE FOR POLAR AND OCEAN RESEARCH | 45TH INDIAN SCIENTIFIC EXPEDITION
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#1E1E1E] hover:bg-[#252525] border border-[#2A2A2A] text-zinc-300 text-xs font-scada-mono transition"
          >
            <Download className="w-4 h-4" />
            CSV DATA
          </button>
          <button
            onClick={exportTelemetryJSON}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#1E1E1E] hover:bg-[#252525] border border-[#2A2A2A] text-cyan-400 text-xs font-scada-mono transition"
          >
            <Download className="w-4 h-4" />
            JSON DUMP
          </button>
          <button
            onClick={handlePrint}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-md bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-scada-mono font-bold transition shadow-scada-glow"
          >
            <Printer className="w-4 h-4" />
            PRINT / SAVE AS PDF
          </button>
        </div>
      </div>

      {/* Report Template Selector (Hidden on Print) */}
      <div className="no-print flex items-center gap-2 bg-[#1E1E1E] p-1.5 rounded-md border border-[#2A2A2A] text-xs font-scada-mono">
        <button
          onClick={() => setReportType('SITREP')}
          className={`px-3 py-1.5 rounded transition ${
            reportType === 'SITREP' ? 'bg-cyan-500/20 text-cyan-400 font-bold border border-cyan-500/40' : 'text-zinc-400'
          }`}
        >
          Daily SITREP (Situation Report)
        </button>
        <button
          onClick={() => setReportType('ENERGY_AUDIT')}
          className={`px-3 py-1.5 rounded transition ${
            reportType === 'ENERGY_AUDIT' ? 'bg-cyan-500/20 text-cyan-400 font-bold border border-cyan-500/40' : 'text-zinc-400'
          }`}
        >
          Austral Winter Energy Audit
        </button>
        <button
          onClick={() => setReportType('SHIFT_LOG')}
          className={`px-3 py-1.5 rounded transition ${
            reportType === 'SHIFT_LOG' ? 'bg-cyan-500/20 text-cyan-400 font-bold border border-cyan-500/40' : 'text-zinc-400'
          }`}
        >
          Chief Engineer Shift Handover
        </button>
      </div>

      {/* Printable Report Document Sheet */}
      <div className="bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg p-8 shadow-2xl max-w-4xl mx-auto space-y-6 scada-card text-zinc-100">
        {/* Document Formal Header */}
        <div className="border-b-2 border-cyan-500/60 pb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Compass className="w-7 h-7 text-cyan-400" />
              <div>
                <h2 className="text-lg font-extrabold text-white tracking-wide uppercase">
                  {station?.name} ({station?.code})
                </h2>
                <p className="text-xs text-zinc-400">
                  NATIONAL CENTRE FOR POLAR & OCEAN RESEARCH (NCPOR), GOA
                </p>
              </div>
            </div>
          </div>

          <div className="text-right font-scada-mono text-xs text-zinc-300">
            <div className="text-cyan-400 font-bold">{sitrep?.reportId}</div>
            <div>DATE: {sitrep?.date}</div>
            <div className="text-[11px] text-zinc-400">{station?.coordinates?.region}</div>
          </div>
        </div>

        {/* Executive Meta Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-scada-mono text-xs">
          <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A]">
            <span className="text-zinc-500 block text-[10px]">STATION DEFCON</span>
            <span className="text-red-400 font-bold">{sitrep?.stationStatus}</span>
          </div>
          <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A]">
            <span className="text-zinc-500 block text-[10px]">CREW ACCOUNTABILITY</span>
            <span className="text-green-400 font-bold">{sitrep?.personnelAccountability}</span>
          </div>
          <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A]">
            <span className="text-zinc-500 block text-[10px]">PREPARED BY</span>
            <span className="text-zinc-200 font-bold">{sitrep?.preparedBy}</span>
          </div>
          <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A]">
            <span className="text-zinc-500 block text-[10px]">AUTHORIZED BY</span>
            <span className="text-zinc-200 font-bold">{sitrep?.authorizedBy}</span>
          </div>
        </div>

        {/* Section 1: Meteorology & Environmental Extremes */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider font-scada-mono border-b border-[#2A2A2A] pb-1">
            1. Meteorological Telemetry & Synoptic Observations
          </h3>
          <div className="p-3.5 bg-[#141414] rounded border border-[#2A2A2A] text-xs font-scada-mono space-y-1.5 text-zinc-300">
            <div className="flex justify-between">
              <span>Outdoor Surface Temp: <strong>{weather?.current?.outdoorTempC}°C</strong> (Wind Chill: {weather?.current?.windChillC}°C)</span>
              <span>Barometer: <strong>{weather?.current?.barometricPressureHpa} hPa ({weather?.current?.pressureTrend})</strong></span>
            </div>
            <div className="flex justify-between">
              <span>Katabatic Wind Vector: <strong>{weather?.current?.windSpeedKnots} kts ({weather?.current?.windDirection})</strong></span>
              <span>Peak Gust: <strong className="text-red-400">{weather?.current?.windGustKnots} kts</strong></span>
            </div>
            <div className="text-[11px] text-zinc-400 pt-1">
              Active Advisory: {weather?.current?.blizzardAlert?.advisory}
            </div>
          </div>
        </div>

        {/* Section 2: Power Grid & Microgrid Generation */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider font-scada-mono border-b border-[#2A2A2A] pb-1">
            2. Power Grid Generation & Microgrid Balance
          </h3>
          <div className="p-3.5 bg-[#141414] rounded border border-[#2A2A2A] text-xs font-scada-mono space-y-1.5 text-zinc-300">
            <p>{sitrep?.powerGridSummary}</p>
            <div className="grid grid-cols-3 gap-2 pt-1 text-[11px]">
              <div>Genset Alpha: <strong className="text-green-400">98.4 kW (Active)</strong></div>
              <div>Micro-Wind Array: <strong className="text-green-400">48.4 kW (Active)</strong></div>
              <div>BESS SOC: <strong className="text-cyan-400">{power?.overview?.bessSocPercent}% (529.2 kWh)</strong></div>
            </div>
          </div>
        </div>

        {/* Section 3: Cryo Fuel & Winter Autonomy */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider font-scada-mono border-b border-[#2A2A2A] pb-1">
            3. Cryogenic Hydrocarbons & Polar Fuel Status
          </h3>
          <div className="p-3.5 bg-[#141414] rounded border border-[#2A2A2A] text-xs font-scada-mono space-y-1.5 text-zinc-300">
            <p>{sitrep?.fuelSummary}</p>
            <div className="grid grid-cols-2 gap-2 pt-1 text-[11px]">
              <div>Total Capacity: 180,000 Litres (74.58% Filled)</div>
              <div>Estimated Winter Buffer: +35.5 Days Beyond Madrid Target</div>
            </div>
          </div>
        </div>

        {/* Section 4: Critical Subsystem Incidents */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-wider font-scada-mono border-b border-[#2A2A2A] pb-1">
            4. Critical Subsystem Alarms & Anomaly Resolutions
          </h3>
          <div className="p-3.5 bg-[#141414] rounded border border-[#2A2A2A] text-xs font-scada-mono space-y-2 text-zinc-300">
            <p className="text-red-300 font-semibold">{sitrep?.criticalIncidents}</p>
            <div className="space-y-1 text-[11px] text-zinc-400">
              {alerts?.slice(0, 3).map((a, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span>[{a.severity}] {a.code}: {a.title}</span>
                  <span className={a.acknowledged ? 'text-green-400' : 'text-red-400'}>
                    {a.acknowledged ? 'ACKNOWLEDGED' : 'PENDING ACTION'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Official Signatures */}
        <div className="pt-8 border-t border-[#2A2A2A] grid grid-cols-2 gap-8 font-scada-mono text-xs text-zinc-400">
          <div>
            <div className="h-10 border-b border-dashed border-zinc-600 flex items-end pb-1 text-cyan-400 font-serif italic">
              Cmdr. Ananya Rao
            </div>
            <div className="mt-1">Chief Engineer / SCADA Lead Officer</div>
            <div className="text-[10px] text-zinc-500">DIGITAL SIGNATURE: 0x9482F...E4A</div>
          </div>

          <div>
            <div className="h-10 border-b border-dashed border-zinc-600 flex items-end pb-1 text-cyan-400 font-serif italic">
              Dr. Rajeshwar Sharma
            </div>
            <div className="mt-1">Station Commander (Expedition 45)</div>
            <div className="text-[10px] text-zinc-500">DIGITAL SIGNATURE: 0x3198A...C1B</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Reports;
