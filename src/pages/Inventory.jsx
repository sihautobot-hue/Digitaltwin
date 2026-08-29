import React, { useState } from 'react';
import { useStationData } from '../context/StationDataContext';
import DataTable from '../components/common/DataTable';
import StatusBadge from '../components/common/StatusBadge';
import MetricCard from '../components/common/MetricCard';
import { 
  Boxes, Package, AlertCircle, Plus, Minus, 
  PlaneTakeoff, Send, CheckCircle2, ShieldCheck, Filter 
} from 'lucide-react';

export const Inventory = () => {
  const { stationData, updateInventoryItem } = useStationData();
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [requestItem, setRequestItem] = useState(null);
  const [requestSent, setRequestSent] = useState(false);

  const inventory = stationData?.inventory || [];

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
      className: 'font-scada-mono font-bold text-cyan-400'
    },
    {
      header: 'Part / Item Name',
      accessor: 'name',
      className: 'font-semibold text-white max-w-xs'
    },
    {
      header: 'Category',
      accessor: 'category',
      className: 'font-scada-mono text-zinc-400'
    },
    {
      header: 'Stock Level',
      accessor: 'quantity',
      render: (qty, row) => (
        <div className="flex items-center gap-2 font-scada-mono">
          <button
            onClick={(e) => {
              e.stopPropagation();
              updateInventoryItem(row.sku, -1);
            }}
            className="p-1 rounded bg-[#141414] hover:bg-[#252525] border border-[#2A2A2A] text-zinc-400 hover:text-white transition"
          >
            <Minus className="w-3 h-3" />
          </button>
          <span className={`font-bold ${qty <= row.minThreshold ? 'text-red-400 font-extrabold' : 'text-white'}`}>
            {qty} <span className="text-[10px] font-normal text-zinc-400">{row.unit}</span>
          </span>
          <button
            onClick={(e) => {
              e.stopPropagation();
              updateInventoryItem(row.sku, 1);
            }}
            className="p-1 rounded bg-[#141414] hover:bg-[#252525] border border-[#2A2A2A] text-zinc-400 hover:text-white transition"
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
        <span className="font-scada-mono text-zinc-400">{thresh} {row.unit}</span>
      )
    },
    {
      header: 'Container Vault',
      accessor: 'containerId',
      className: 'font-scada-mono text-zinc-300'
    },
    {
      header: 'Air-Drop',
      accessor: 'airDropCompatible',
      render: (compatible) => (
        <span className={`text-[10px] font-scada-mono font-bold px-2 py-0.5 rounded border ${
          compatible ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' : 'bg-zinc-800 text-zinc-500 border-zinc-700'
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
          className="px-2.5 py-1 rounded bg-[#141414] hover:bg-cyan-950/40 text-cyan-400 border border-[#2A2A2A] hover:border-cyan-500/40 text-[11px] font-scada-mono font-bold transition flex items-center gap-1"
        >
          <PlaneTakeoff className="w-3 h-3" />
          RESUPPLY
        </button>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-[#262626]">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight font-display flex items-center gap-2">
              <Boxes className="w-6 h-6 text-cyan-400" />
              Polar Logistics & Mission Spare Parts Registry
            </h1>
            <StatusBadge status="ACTIVE" label="MADRID PROTOCOL LOGISTICS" size="sm" />
          </div>
          <p className="text-xs font-scada-mono text-zinc-400 mt-1">
            CRITICAL SPARES INVENTORY | NCPOR GOA EXPEDITION LOGISTICS INTEGRATION
          </p>
        </div>

        <button
          onClick={() => handleOpenRequest(inventory[0])}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-scada-mono font-bold transition shadow-scada-glow"
        >
          <PlaneTakeoff className="w-4 h-4" />
          REQUEST AIR-DROP MANIFEST
        </button>
      </div>

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
          subtext="Cape Town / Goa Drop"
        />
      </div>

      {/* Category Filter Chips */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-scada-mono">
        <span className="text-zinc-500 text-xs flex items-center gap-1">
          <Filter className="w-3.5 h-3.5" /> CATEGORY:
        </span>
        {categories.map(cat => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-3 py-1 rounded-md transition whitespace-nowrap ${
              selectedCategory === cat
                ? 'bg-cyan-500/20 text-cyan-400 font-bold border border-cyan-500/40'
                : 'bg-[#1E1E1E] text-zinc-400 hover:text-white border border-[#2A2A2A]'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Main Inventory Table */}
      <DataTable
        title="Spares & Consumables Warehouse Ledger"
        subtitle="Live telemetry tracking quantity vs critical minimum thresholds"
        columns={columns}
        data={filteredItems}
        pageSize={8}
      />

      {/* Resupply Modal */}
      {showRequestModal && requestItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fadeIn">
          <div className="w-full max-w-lg bg-[#1E1E1E] border border-cyan-500/40 rounded-lg shadow-2xl p-6 relative">
            <h3 className="text-base font-bold text-white mb-2 flex items-center gap-2 font-display">
              <PlaneTakeoff className="w-5 h-5 text-cyan-400" />
              Air-Drop Emergency Resupply Manifest
            </h3>
            <p className="text-xs text-zinc-400 mb-4">
              Authorize IL-76 Antarctic Cargo Airdrop dispatch from Cape Town / NCPOR Goa.
            </p>

            {requestSent ? (
              <div className="p-6 bg-[#141414] rounded border border-green-500/40 text-center space-y-2">
                <CheckCircle2 className="w-10 h-10 text-green-400 mx-auto animate-bounce" />
                <h4 className="text-sm font-bold text-white font-scada-mono">MANIFEST SUBMITTED TO NCPOR LOGISTICS</h4>
                <p className="text-xs text-zinc-400">Air-drop flight slot scheduled upon storm subsidence.</p>
              </div>
            ) : (
              <form onSubmit={handleSendResupply} className="space-y-4 font-scada-mono text-xs">
                <div className="p-3 bg-[#141414] rounded border border-[#2A2A2A] space-y-1">
                  <div className="text-cyan-400 font-bold">{requestItem.sku}</div>
                  <div className="text-white font-semibold">{requestItem.name}</div>
                  <div className="text-zinc-400">Supplier: {requestItem.supplier}</div>
                </div>

                <div>
                  <label className="block text-zinc-400 mb-1">Requested Quantity ({requestItem.unit})</label>
                  <input
                    type="number"
                    defaultValue={10}
                    min={1}
                    className="w-full bg-[#141414] border border-[#2A2A2A] focus:border-cyan-500 rounded p-2 text-white outline-none"
                  />
                </div>

                <div>
                  <label className="block text-zinc-400 mb-1">Drop Priority Level</label>
                  <select className="w-full bg-[#141414] border border-[#2A2A2A] focus:border-cyan-500 rounded p-2 text-white outline-none">
                    <option>PRIORITY 1 - IMMEDIATE POLAR FLIGHT</option>
                    <option>PRIORITY 2 - NEXT ROUTINE VOYAGE</option>
                    <option>PRIORITY 3 - AUSTRAL SUMMER RESUPPLY</option>
                  </select>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowRequestModal(false)}
                    className="px-3 py-1.5 rounded bg-[#252525] text-zinc-300"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 rounded bg-cyan-500 text-black font-bold flex items-center gap-1.5"
                  >
                    <Send className="w-3.5 h-3.5" />
                    Transmit Air-Drop Order
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
