import React, { useState } from 'react';
import { useStationData } from '../context/StationDataContext';
import DataTable from '../components/common/DataTable';
import StatusBadge from '../components/common/StatusBadge';
import MetricCard from '../components/common/MetricCard';
import { 
  Boxes, Package, AlertCircle, Plus, Minus, 
  PlaneTakeoff, Send, CheckCircle2, ShieldCheck, Filter, Lock, Eye
} from 'lucide-react';

export const Inventory = () => {
  const { stationData, updateInventoryQuantity, rbac, userRole } = useStationData();
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [requestItem, setRequestItem] = useState(null);
  const [requestSent, setRequestSent] = useState(false);

  const inventory = stationData?.inventory?.items || stationData?.inventory || [];

  const categories = ['ALL', ...new Set(inventory.map(i => i.category))];

  const filteredItems = inventory.filter(item => {
    if (selectedCategory === 'ALL') return true;
    return item.category === selectedCategory;
  });

  const criticalCount = inventory.filter(i => i.status === 'CRITICAL').length;
  const warningCount = inventory.filter(i => i.status === 'WARNING').length;

  const handleOpenRequest = (item) => {
    setRequestItem(item);
    setRequestSent(false);
    setShowRequestModal(true);
  };

  const handleSendResupply = (e) => {
    e.preventDefault();
    setRequestSent(true);
    setTimeout(() => {
      setShowRequestModal(false);
    }, 1500);
  };

  const columns = [
    {
      header: 'SKU Code',
      accessor: 'sku',
      className: 'font-scada-mono font-bold text-cyan-600 dark:text-cyan-400'
    },
    {
      header: 'Part / Item Name',
      accessor: 'name',
      className: 'font-semibold text-slate-900 dark:text-white max-w-xs'
    },
    {
      header: 'Category',
      accessor: 'category',
      className: 'font-scada-mono text-slate-500 dark:text-zinc-400'
    },
    {
      header: 'Stock Level',
      accessor: 'quantity',
      render: (qty, row) => (
        <div className="flex items-center gap-2 font-scada-mono">
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (rbac.canEditInventory) {
                updateInventoryQuantity(row.id || row.sku, -1);
              }
            }}
            disabled={!rbac.canEditInventory}
            className={`p-1 rounded border transition ${
              !rbac.canEditInventory
                ? 'bg-slate-100 dark:bg-[#141414] text-slate-300 dark:text-zinc-700 border-slate-200 dark:border-zinc-800 cursor-not-allowed'
                : 'bg-slate-100 dark:bg-[#141414] hover:bg-slate-200 dark:hover:bg-[#252525] border-slate-300 dark:border-[#2A2A2A] text-slate-600 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white'
            }`}
            title={!rbac.canEditInventory ? 'Stock adjustments restricted to Antarctica Edge Commander' : 'Decrease Quantity'}
          >
            <Minus className="w-3 h-3" />
          </button>
          <span className={`font-bold ${qty <= row.minThreshold ? 'text-red-600 dark:text-red-400 font-extrabold' : 'text-slate-900 dark:text-white'}`}>
            {qty} <span className="text-[10px] font-normal text-slate-400 dark:text-zinc-400">{row.unit}</span>
          </span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              if (rbac.canEditInventory) {
                updateInventoryQuantity(row.id || row.sku, 1);
              }
            }}
            disabled={!rbac.canEditInventory}
            className={`p-1 rounded border transition ${
              !rbac.canEditInventory
                ? 'bg-slate-100 dark:bg-[#141414] text-slate-300 dark:text-zinc-700 border-slate-200 dark:border-zinc-800 cursor-not-allowed'
                : 'bg-slate-100 dark:bg-[#141414] hover:bg-slate-200 dark:hover:bg-[#252525] border-slate-300 dark:border-[#2A2A2A] text-slate-600 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white'
            }`}
            title={!rbac.canEditInventory ? 'Stock adjustments restricted to Antarctica Edge Commander' : 'Increase Quantity'}
          >
            <Plus className="w-3 h-3" />
          </button>
        </div>
      )
    },
    {
      header: 'Min Threshold',
      accessor: 'minThreshold',
      render: (thresh, row) => (
        <span className="font-scada-mono text-slate-500 dark:text-zinc-400">{thresh} {row.unit}</span>
      )
    },
    {
      header: 'Container Vault',
      accessor: 'containerId',
      className: 'font-scada-mono text-slate-700 dark:text-zinc-300'
    },
    {
      header: 'Air-Drop',
      accessor: 'airDropCompatible',
      render: (compatible) => (
        <span className={`text-[10px] font-scada-mono font-bold px-2 py-0.5 rounded border ${
          compatible ? 'bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border-cyan-500/30' : 'bg-slate-100 dark:bg-zinc-800 text-slate-400 dark:text-zinc-500 border-slate-200 dark:border-zinc-700'
        }`}>
          {compatible ? 'PARACHUTE READY' : 'SEA ONLY'}
        </span>
      )
    },
    {
      header: 'Status',
      accessor: 'status',
      render: (st) => <StatusBadge status={st} size="sm" />
    },
    {
      header: 'Action',
      accessor: 'sku',
      sortable: false,
      render: (_, row) => (
        <button
          onClick={() => handleOpenRequest(row)}
          className="px-2.5 py-1 rounded bg-slate-100 dark:bg-[#141414] hover:bg-cyan-50 dark:hover:bg-cyan-950/40 text-cyan-700 dark:text-cyan-400 border border-slate-300 dark:border-[#2A2A2A] hover:border-cyan-500/40 text-[11px] font-scada-mono font-bold transition flex items-center gap-1"
        >
          <PlaneTakeoff className="w-3 h-3" />
          {userRole === 'INDIA_COMMAND' ? 'PLANNING' : 'RESUPPLY'}
        </button>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200 dark:border-[#262626]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold text-slate-900 dark:text-white tracking-tight font-display flex items-center gap-2">
              <Boxes className="w-6 h-6 text-cyan-600 dark:text-cyan-400" />
              Polar Logistics & Mission Spare Parts Registry
            </h1>
            <StatusBadge status="ACTIVE" label="MADRID PROTOCOL LOGISTICS" size="sm" />
          </div>
          <p className="text-xs font-scada-mono text-slate-500 dark:text-zinc-400 mt-1">
            CRITICAL SPARES INVENTORY | NCPOR GOA EXPEDITION LOGISTICS INTEGRATION
          </p>
        </div>

        <button
          onClick={() => handleOpenRequest(inventory[0])}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-scada-mono font-bold transition shadow"
        >
          <PlaneTakeoff className="w-4 h-4" />
          {userRole === 'INDIA_COMMAND' ? 'SUPPLY CHAIN MANIFEST (HQ)' : 'REQUEST AIR-DROP MANIFEST'}
        </button>
      </div>

      {/* Role Notice (if India Command Center) */}
      {userRole === 'INDIA_COMMAND' && (
        <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-xl flex items-center gap-2 text-xs text-blue-700 dark:text-blue-300 font-scada-mono">
          <Eye className="w-4 h-4 text-blue-500 flex-shrink-0" />
          <span>
            INDIA COMMAND CENTER VIEW: Supply Chain & Madrid Protocol review mode active. Live inventory mutations are restricted to Antarctic Edge Station Crew.
          </span>
        </div>
      )}

      {/* Overview Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Catalog Items"
          value={inventory.length}
          unit="SKUs"
          status="NORMAL"
          icon={Package}
          trend="100% Tracked in Vaults"
          trendDirection="none"
          subtext="6 Reinforced Containers"
        />

        <MetricCard
          title="Critical Low Stock"
          value={criticalCount}
          unit="ALERTS"
          status={criticalCount > 0 ? 'CRITICAL' : 'NORMAL'}
          icon={AlertCircle}
          trend="Immediate Resupply Req."
          trendDirection="none"
          subtext="Genset 2 Bearings"
        />

        <MetricCard
          title="Warning Level Stock"
          value={warningCount}
          unit="ITEMS"
          status={warningCount > 0 ? 'WARNING' : 'NORMAL'}
          icon={Boxes}
          trend="Below Safety Buffer"
          trendDirection="none"
          subtext="Track Cleats & Seals"
        />

        <MetricCard
          title="Air-Drop Ready Spares"
          value={inventory.filter(i => i.airDropCompatible).length}
          unit="ITEMS"
          status="NORMAL"
          icon={PlaneTakeoff}
          trend="IL-76 Parachute Certified"
          trendDirection="none"
          subtext="MoES Drop Zone Approved"
        />
      </div>

      {/* Category Filter Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        <span className="text-xs font-scada-mono text-slate-400 dark:text-zinc-500 flex items-center gap-1 mr-1">
          <Filter className="w-3.5 h-3.5" /> CATEGORY:
        </span>
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3 py-1 rounded-md text-xs font-scada-mono whitespace-nowrap transition ${
              selectedCategory === cat
                ? 'bg-cyan-500/20 text-cyan-700 dark:text-cyan-400 border border-cyan-500/40 font-bold'
                : 'bg-white dark:bg-[#1E1E1E] text-slate-600 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-zinc-200 border border-slate-200 dark:border-[#2A2A2A]'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Inventory Data Table */}
      <DataTable
        columns={columns}
        data={filteredItems}
        searchPlaceholder="Filter spares by SKU, description, container vault..."
        pageSize={8}
      />

      {/* Resupply Request Modal */}
      {showRequestModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in">
          <div className="w-full max-w-lg bg-white dark:bg-[#1E1E1E] border border-cyan-500/40 rounded-xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 dark:border-[#262626] pb-3">
              <div className="flex items-center gap-2">
                <PlaneTakeoff className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
                <h3 className="text-base font-bold text-slate-900 dark:text-white font-display">
                  {userRole === 'INDIA_COMMAND' ? 'NCPOR Logistics Air-Drop Manifest' : 'Emergency Air-Drop Resupply Manifest'}
                </h3>
              </div>
              <button
                onClick={() => setShowRequestModal(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            {requestSent ? (
              <div className="p-6 text-center space-y-2">
                <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto animate-bounce" />
                <h4 className="text-sm font-bold text-slate-900 dark:text-white font-scada-mono">
                  MANIFEST DISPATCHED TO NCPOR GOA
                </h4>
                <p className="text-xs text-slate-500 dark:text-zinc-400">
                  Transmitted via GSAT-7A secure telecommand. ETA Cape Town / Dronning Maud Land payload calculation generated.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSendResupply} className="space-y-3 font-sans text-xs">
                <div>
                  <label className="block text-slate-500 dark:text-zinc-400 uppercase font-scada-mono mb-1">Target Spare / Part</label>
                  <input
                    type="text"
                    disabled
                    value={`${requestItem?.name || 'Selected Item'} (${requestItem?.sku || 'SKU-001'})`}
                    className="w-full bg-slate-50 dark:bg-[#141414] border border-slate-200 dark:border-[#2A2A2A] rounded p-2 text-slate-800 dark:text-zinc-200 font-scada-mono"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-500 dark:text-zinc-400 uppercase font-scada-mono mb-1">Requested Units</label>
                    <input
                      type="number"
                      min="1"
                      defaultValue="4"
                      className="w-full bg-slate-50 dark:bg-[#141414] border border-slate-200 dark:border-[#2A2A2A] rounded p-2 text-slate-800 dark:text-zinc-200 font-scada-mono focus:border-cyan-500"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-500 dark:text-zinc-400 uppercase font-scada-mono mb-1">Priority Classification</label>
                    <select className="w-full bg-slate-50 dark:bg-[#141414] border border-slate-200 dark:border-[#2A2A2A] rounded p-2 text-slate-800 dark:text-zinc-200 font-scada-mono focus:border-cyan-500">
                      <option>URGENT - Austral Winter Risk</option>
                      <option>ROUTINE - Summer Voyage 45</option>
                      <option>CRITICAL - Life Support L1</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-slate-500 dark:text-zinc-400 uppercase font-scada-mono mb-1">Madrid Protocol Environmental Justification</label>
                  <textarea
                    rows="2"
                    defaultValue="Essential replacement for preventing microgrid brownout and maintaining crew quarters HVAC loop."
                    className="w-full bg-slate-50 dark:bg-[#141414] border border-slate-200 dark:border-[#2A2A2A] rounded p-2 text-slate-800 dark:text-zinc-200 font-sans focus:border-cyan-500"
                  />
                </div>

                <div className="pt-2 flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setShowRequestModal(false)}
                    className="px-4 py-2 rounded bg-slate-100 dark:bg-[#2A2A2A] text-slate-600 dark:text-zinc-300 font-scada-mono"
                  >
                    CANCEL
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded bg-cyan-500 text-black font-scada-mono font-bold hover:bg-cyan-400 flex items-center gap-1.5 shadow"
                  >
                    <Send className="w-3.5 h-3.5" />
                    DISPATCH TELECOMMAND
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Inventory;
