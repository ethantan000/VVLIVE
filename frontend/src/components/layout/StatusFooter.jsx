import React from 'react';
import { formatDuration, intervalToDuration } from 'date-fns';
import clsx from 'clsx';
import { StatusIndicator, getStatusFromValue, getStatusFromBitrate } from '../common/StatusIndicator';
import { useDashboard } from '../../context/DashboardContext';

export function StatusFooter() {
  const { status, metrics, ingestStats, aggregated, isConnected } = useDashboard();

  const isLive = status?.quality_state && status?.quality_state !== 'OFFLINE';

  // Format uptime
  const formatUptime = (seconds) => {
    if (!seconds || seconds <= 0) return '00:00:00';
    const duration = intervalToDuration({ start: 0, end: seconds * 1000 });
    const hours = String(duration.hours || 0).padStart(2, '0');
    const minutes = String(duration.minutes || 0).padStart(2, '0');
    const secs = String(duration.seconds || 0).padStart(2, '0');
    return `${hours}:${minutes}:${secs}`;
  };

  const bitrate = ingestStats?.bitrate_kbps || metrics?.bandwidth_estimate || 0;
  const uplinkCount = metrics?.active_uplinks || 0;
  const healthScore = aggregated?.health_score ?? 100;
  const uptime = status?.time_in_state || 0;

  return (
    <footer className="bg-gray-900 border-t border-gray-700 px-4 py-2">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4 text-sm">
        {/* Live Status */}
        <div className="flex items-center gap-3">
          <StatusIndicator
            status={isLive ? 'green' : 'gray'}
            pulse={isLive}
            size="lg"
          />
          <span className={clsx(
            'font-bold',
            isLive ? 'text-green-500' : 'text-gray-500'
          )}>
            {isLive ? 'LIVE' : 'OFFLINE'}
          </span>
          {isLive && (
            <span className="text-gray-400 font-mono">
              {formatUptime(uptime)}
            </span>
          )}
        </div>

        {/* Divider */}
        <div className="hidden sm:block w-px h-6 bg-gray-700" />

        {/* Bitrate */}
        <div className="flex items-center gap-2">
          <StatusIndicator
            status={getStatusFromBitrate(bitrate)}
            size="sm"
          />
          <span className="text-gray-400">
            <span className="font-mono text-white">{Math.round(bitrate)}</span> kbps
          </span>
        </div>

        {/* Divider */}
        <div className="hidden sm:block w-px h-6 bg-gray-700" />

        {/* Uplinks */}
        <div className="flex items-center gap-2">
          <StatusIndicator
            status={uplinkCount > 0 ? 'green' : 'yellow'}
            size="sm"
          />
          <span className="text-gray-400">
            <span className="font-mono text-white">{uplinkCount}</span> uplink{uplinkCount !== 1 ? 's' : ''}
          </span>
        </div>

        {/* Divider */}
        <div className="hidden sm:block w-px h-6 bg-gray-700" />

        {/* Health Score */}
        <div className="flex items-center gap-2">
          <span className="text-gray-400">Health:</span>
          <span className={clsx(
            'font-bold font-mono',
            healthScore >= 80 ? 'text-green-500' :
            healthScore >= 50 ? 'text-yellow-500' : 'text-red-500'
          )}>
            {Math.round(healthScore)}%
          </span>
        </div>

        {/* Connection indicator (mobile) */}
        <div className="sm:hidden flex items-center gap-2">
          <StatusIndicator
            status={isConnected ? 'green' : 'red'}
            size="sm"
            label={isConnected ? 'OK' : 'Err'}
          />
        </div>
      </div>
    </footer>
  );
}

export default StatusFooter;
