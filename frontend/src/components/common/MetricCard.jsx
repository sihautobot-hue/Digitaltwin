import React from 'react';
import StatusBadge from './StatusBadge';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export const MetricCard = ({
  title,
  value,
  unit = '',
  status = 'NORMAL',
  statusLabel,
  icon: Icon,
  trend,
  trendDirection = 'none', // 'up', 'down', 'none'
  subtext,
  progress, // 0 - 100 percentage
  actionButton,
  className = '',
  onClick
}) => {
  const normalized = String(status || '').toUpperCase();

  let borderGlow = 'border-slate-200 dark:border-[#2A2A2A] hover:border-cyan-500/40';
  let accentBar = 'bg-cyan-500';
  let valueColor = 'text-slate-900 dark:text-white';

  if (normalized === 'NORMAL' || normalized === 'ACTIVE' || normalized === 'ONLINE') {
    borderGlow = 'border-slate-200 dark:border-[#2A2A2A] hover:border-green-500/50';
    accentBar = 'bg-green-500';
  } else if (normalized === 'WARNING' || normalized === 'STANDBY' || normalized === 'DELAYED') {
    borderGlow = 'border-slate-200 dark:border-[#2A2A2A] hover:border-yellow-500/50';
    accentBar = 'bg-yellow-500';
  } else if (normalized === 'CRITICAL' || normalized === 'OFFLINE' || normalized === 'ALARM') {
    borderGlow = 'border-red-200 dark:border-[#2A2A2A] hover:border-red-500/60 shadow-scada-red';
    accentBar = 'bg-red-500';
    valueColor = 'text-red-600 dark:text-red-400';
  }

  return (
    <div
      onClick={onClick}
      className={`relative overflow-hidden rounded-xl bg-white dark:bg-[#1E1E1E] border ${borderGlow} p-4 shadow-sm transition-all duration-200 ${
        onClick ? 'cursor-pointer hover:bg-slate-50 dark:hover:bg-[#232323]' : ''
      } ${className}`}
    >
      {/* Top Accent Line */}
      <div className={`absolute top-0 left-0 right-0 h-1 ${accentBar} opacity-80`} />

      {/* Header */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          {Icon && (
            <div className="p-1.5 rounded-lg bg-slate-100 dark:bg-[#141414] border border-slate-200 dark:border-[#2A2A2A] text-slate-600 dark:text-zinc-300">
              <Icon className="w-4 h-4" />
            </div>
          )}
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-zinc-400">
            {title}
          </span>
        </div>

        {status && <StatusBadge status={status} label={statusLabel} size="sm" />}
      </div>

      {/* Value Readout */}
      <div className="flex items-baseline gap-1.5 my-1">
        <span className={`text-2xl lg:text-3xl font-bold font-scada-mono tracking-tight ${valueColor}`}>
          {value !== undefined && value !== null ? value : '---'}
        </span>
        {unit && (
          <span className="text-xs font-scada-mono font-medium text-slate-400 dark:text-zinc-400">
            {unit}
          </span>
        )}
      </div>

      {/* Progress Bar (if provided) */}
      {typeof progress === 'number' && (
        <div className="w-full bg-slate-100 dark:bg-[#141414] rounded-full h-1.5 my-2.5 overflow-hidden border border-slate-200 dark:border-[#2A2A2A]">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              progress > 80
                ? 'bg-green-500'
                : progress > 40
                ? 'bg-cyan-500'
                : progress > 20
                ? 'bg-yellow-500'
                : 'bg-red-500'
            }`}
            style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          />
        </div>
      )}

      {/* Footer / Trend */}
      <div className="flex items-center justify-between text-xs text-slate-500 dark:text-zinc-400 mt-2">
        {trend && (
          <div className="flex items-center gap-1 font-scada-mono">
            {trendDirection === 'up' && <TrendingUp className="w-3.5 h-3.5 text-emerald-500 dark:text-emerald-400" />}
            {trendDirection === 'down' && <TrendingDown className="w-3.5 h-3.5 text-rose-500 dark:text-rose-400" />}
            {trendDirection === 'none' && <Minus className="w-3.5 h-3.5 text-slate-400 dark:text-zinc-500" />}
            <span className={trendDirection === 'up' ? 'text-emerald-600 dark:text-emerald-400' : trendDirection === 'down' ? 'text-rose-600 dark:text-rose-400' : 'text-slate-500 dark:text-zinc-400'}>
              {trend}
            </span>
          </div>
        )}

        {subtext && <span className="text-slate-400 dark:text-zinc-400 truncate text-[11px]">{subtext}</span>}

        {actionButton && <div className="ml-auto">{actionButton}</div>}
      </div>
    </div>
  );
};

export default MetricCard;
