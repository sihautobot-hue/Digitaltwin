import React from 'react';

/**
 * Strict SCADA Color Coding Badge
 * Normal / Active = text-green-500 & bg-green-500/10 (🟢)
 * Warning / Delayed = text-yellow-500 & bg-yellow-500/10 (🟡)
 * Critical / Offline = text-red-500 & bg-red-500/10 (🔴)
 */
export const StatusBadge = ({ status, label, showDot = true, size = 'md', className = '' }) => {
  const normalized = String(status || '').toUpperCase();

  let colorClasses = 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30';
  let dotColor = 'bg-cyan-400';
  let dotAnimation = '';

  if (
    normalized === 'NORMAL' ||
    normalized === 'ACTIVE' ||
    normalized === 'ONLINE' ||
    normalized === 'ARMED' ||
    normalized === 'SEALED' ||
    normalized === 'OPEN' ||
    normalized === 'NOMINAL' ||
    normalized === 'OK'
  ) {
    colorClasses = 'text-green-500 bg-green-500/10 border-green-500/30';
    dotColor = 'bg-green-500';
    dotAnimation = 'animate-pulse-green';
  } else if (
    normalized === 'WARNING' ||
    normalized === 'DELAYED' ||
    normalized === 'STANDBY' ||
    normalized === 'RESTRICTED' ||
    normalized === 'ELEVATED' ||
    normalized === 'MEDIUM'
  ) {
    colorClasses = 'text-yellow-500 bg-yellow-500/10 border-yellow-500/30';
    dotColor = 'bg-yellow-500';
    dotAnimation = 'animate-pulse';
  } else if (
    normalized === 'CRITICAL' ||
    normalized === 'OFFLINE' ||
    normalized === 'ALARM' ||
    normalized === 'FAULT' ||
    normalized === 'TRIPPED' ||
    normalized === 'HIGH' ||
    normalized === 'BLIZZARD_LEVEL_3'
  ) {
    colorClasses = 'text-red-500 bg-red-500/10 border-red-500/30';
    dotColor = 'bg-red-500';
    dotAnimation = 'animate-scada-blink-red';
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 space-x-1.5',
    md: 'text-xs px-2.5 py-1 space-x-2',
    lg: 'text-sm px-3 py-1.5 space-x-2.5',
  }[size] || 'text-xs px-2.5 py-1 space-x-2';

  const displayText = label || status || 'UNKNOWN';

  return (
    <span
      className={`inline-flex items-center font-scada-mono font-medium tracking-wide uppercase rounded-md border ${colorClasses} ${sizeClasses} ${className}`}
    >
      {showDot && (
        <span className="relative flex h-2 w-2">
          <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 ${dotColor} ${dotAnimation}`}></span>
          <span className={`relative inline-flex rounded-full h-2 w-2 ${dotColor}`}></span>
        </span>
      )}
      <span>{displayText}</span>
    </span>
  );
};

export default StatusBadge;
