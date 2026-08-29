import React, { useState, useMemo } from 'react';
import { Search, ChevronLeft, ChevronRight, ArrowUpDown, Download, Filter } from 'lucide-react';

export const DataTable = ({
  columns = [],
  data = [],
  searchKey = 'name',
  searchPlaceholder = 'Search records...',
  defaultSortKey,
  defaultSortOrder = 'asc',
  pageSize = 8,
  title,
  subtitle,
  actions,
  className = ''
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortKey, setSortKey] = useState(defaultSortKey || (columns[0] ? columns[0].accessor : ''));
  const [sortOrder, setSortOrder] = useState(defaultSortOrder);
  const [currentPage, setCurrentPage] = useState(1);

  // Filter Data
  const filteredData = useMemo(() => {
    if (!searchTerm) return data;
    return data.filter(row => {
      if (typeof searchKey === 'function') {
        return searchKey(row, searchTerm);
      }
      const val = row[searchKey];
      if (val === undefined || val === null) {
        // search all string values in row as fallback
        return Object.values(row).some(v => 
          String(v).toLowerCase().includes(searchTerm.toLowerCase())
        );
      }
      return String(val).toLowerCase().includes(searchTerm.toLowerCase());
    });
  }, [data, searchTerm, searchKey]);

  // Sort Data
  const sortedData = useMemo(() => {
    if (!sortKey) return filteredData;
    return [...filteredData].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (aVal === bVal) return 0;
      if (aVal === undefined || aVal === null) return 1;
      if (bVal === undefined || bVal === null) return -1;

      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
      }

      return sortOrder === 'asc'
        ? String(aVal).localeCompare(String(bVal))
        : String(bVal).localeCompare(String(aVal));
    });
  }, [filteredData, sortKey, sortOrder]);

  // Pagination
  const totalPages = Math.ceil(sortedData.length / pageSize) || 1;
  const paginatedData = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, currentPage, pageSize]);

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortOrder(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortOrder('asc');
    }
  };

  const exportCSV = () => {
    if (!sortedData.length) return;
    const headers = columns.map(c => c.header).join(',');
    const rows = sortedData.map(row => 
      columns.map(c => {
        const val = row[c.accessor];
        return typeof val === 'string' && val.includes(',') ? `"${val}"` : val ?? '';
      }).join(',')
    ).join('\n');

    const blob = new Blob([`${headers}\n${rows}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `scada-table-export-${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className={`bg-[#1E1E1E] border border-[#2A2A2A] rounded-lg overflow-hidden flex flex-col ${className}`}>
      {/* Header Bar */}
      <div className="p-4 border-b border-[#2A2A2A] flex flex-col md:flex-row md:items-center justify-between gap-3 bg-[#181818]">
        <div>
          {title && <h3 className="text-sm font-semibold text-white tracking-wide uppercase">{title}</h3>}
          {subtitle && <p className="text-xs text-zinc-400 mt-0.5">{subtitle}</p>}
        </div>

        <div className="flex items-center gap-2">
          {/* Search Input */}
          <div className="relative flex-1 md:w-64">
            <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={e => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              placeholder={searchPlaceholder}
              className="w-full bg-[#121212] border border-[#2A2A2A] focus:border-cyan-500 text-xs text-zinc-200 pl-9 pr-3 py-1.5 rounded-md outline-none transition font-sans placeholder:text-zinc-600"
            />
          </div>

          {/* Export CSV */}
          <button
            onClick={exportCSV}
            title="Export CSV"
            className="p-1.5 rounded-md bg-[#121212] border border-[#2A2A2A] hover:border-zinc-500 text-zinc-300 hover:text-white transition"
          >
            <Download className="w-4 h-4" />
          </button>

          {actions}
        </div>
      </div>

      {/* Table Element */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-zinc-300">
          <thead className="bg-[#141414] text-zinc-400 font-scada-mono uppercase text-[11px] border-b border-[#2A2A2A]">
            <tr>
              {columns.map(col => (
                <th
                  key={col.accessor || col.header}
                  onClick={() => col.sortable !== false && handleSort(col.accessor)}
                  className={`px-4 py-3 font-semibold ${
                    col.sortable !== false ? 'cursor-pointer hover:text-cyan-400 select-none' : ''
                  } ${col.headerClassName || ''}`}
                >
                  <div className="flex items-center gap-1.5">
                    <span>{col.header}</span>
                    {col.sortable !== false && (
                      <ArrowUpDown className={`w-3 h-3 ${sortKey === col.accessor ? 'text-cyan-400' : 'text-zinc-600'}`} />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[#262626]">
            {paginatedData.length > 0 ? (
              paginatedData.map((row, idx) => (
                <tr
                  key={row.id || row.sku || idx}
                  className="hover:bg-[#242424] transition-colors"
                >
                  {columns.map(col => (
                    <td
                      key={col.accessor || col.header}
                      className={`px-4 py-3 ${col.className || ''}`}
                    >
                      {col.render ? col.render(row[col.accessor], row) : (row[col.accessor] ?? '---')}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={columns.length} className="px-4 py-8 text-center text-zinc-500 font-scada-mono">
                  NO SCADA TELEMETRY RECORDS MATCH FILTER
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="p-3 border-t border-[#2A2A2A] bg-[#181818] flex items-center justify-between text-xs text-zinc-400 font-scada-mono">
        <div>
          Showing <span className="text-zinc-200 font-semibold">{sortedData.length > 0 ? (currentPage - 1) * pageSize + 1 : 0}</span> to{' '}
          <span className="text-zinc-200 font-semibold">{Math.min(currentPage * pageSize, sortedData.length)}</span> of{' '}
          <span className="text-zinc-200 font-semibold">{sortedData.length}</span> entries
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="p-1 rounded bg-[#121212] border border-[#2A2A2A] disabled:opacity-30 disabled:cursor-not-allowed hover:border-zinc-500 text-zinc-300"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span>
            Page {currentPage} / {totalPages}
          </span>
          <button
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="p-1 rounded bg-[#121212] border border-[#2A2A2A] disabled:opacity-30 disabled:cursor-not-allowed hover:border-zinc-500 text-zinc-300"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default DataTable;
