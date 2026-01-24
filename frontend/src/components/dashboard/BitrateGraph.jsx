import React, { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { TrendingUp, AlertCircle } from 'lucide-react';
import { CollapsiblePane } from '../common/CollapsiblePane';
import { useDashboard } from '../../context/DashboardContext';
import { useBitrateHistory } from '../../hooks/useBitrateHistory';

const LOW_BITRATE_THRESHOLD = 1500;

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 shadow-lg">
        <p className="text-gray-400 text-xs mb-1">
          {new Date(label).toLocaleTimeString()}
        </p>
        <p className="text-white font-mono font-bold">
          {Math.round(payload[0].value)} kbps
        </p>
      </div>
    );
  }
  return null;
}

export function BitrateGraph() {
  const { ingestStats, features } = useDashboard();
  const currentBitrate = ingestStats?.bitrate_kbps || 0;

  const { history, getStats } = useBitrateHistory(currentBitrate);
  const stats = getStats();

  // Format data for Recharts
  const chartData = useMemo(() => {
    return history.map((point, index) => ({
      time: point.time,
      bitrate: point.bitrate,
      index
    }));
  }, [history]);

  // Calculate Y-axis domain
  const yDomain = useMemo(() => {
    const maxBitrate = Math.max(...history.map(h => h.bitrate), 3000);
    return [0, Math.ceil(maxBitrate / 1000) * 1000 + 500];
  }, [history]);

  if (!features?.ingest_enabled) {
    return (
      <CollapsiblePane
        title="Bitrate History"
        icon={TrendingUp}
        storageKey="bitrate-graph"
        defaultExpanded={true}
      >
        <div className="flex items-center gap-3 text-gray-400 py-4">
          <AlertCircle className="w-5 h-5" />
          <span>Ingest monitoring not enabled</span>
        </div>
      </CollapsiblePane>
    );
  }

  return (
    <CollapsiblePane
      title="Bitrate History"
      icon={TrendingUp}
      storageKey="bitrate-graph"
      defaultExpanded={true}
    >
      <div className="space-y-4">
        {/* Stats Row */}
        <div className="grid grid-cols-4 gap-2">
          <div className="bg-gray-900 rounded-lg p-2 text-center">
            <div className="text-gray-500 text-xs">Current</div>
            <div className="text-blue-400 font-mono font-bold">
              {Math.round(stats.current)}
            </div>
          </div>
          <div className="bg-gray-900 rounded-lg p-2 text-center">
            <div className="text-gray-500 text-xs">Average</div>
            <div className="text-white font-mono font-bold">
              {Math.round(stats.avg)}
            </div>
          </div>
          <div className="bg-gray-900 rounded-lg p-2 text-center">
            <div className="text-gray-500 text-xs">Min</div>
            <div className="text-red-400 font-mono font-bold">
              {Math.round(stats.min)}
            </div>
          </div>
          <div className="bg-gray-900 rounded-lg p-2 text-center">
            <div className="text-gray-500 text-xs">Max</div>
            <div className="text-green-400 font-mono font-bold">
              {Math.round(stats.max)}
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="h-48 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="bitrateGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
                </linearGradient>
              </defs>

              <CartesianGrid
                strokeDasharray="3 3"
                stroke="#374151"
                vertical={false}
              />

              <XAxis
                dataKey="time"
                tick={false}
                axisLine={{ stroke: '#374151' }}
                tickLine={false}
              />

              <YAxis
                domain={yDomain}
                tick={{ fill: '#9CA3AF', fontSize: 11 }}
                axisLine={{ stroke: '#374151' }}
                tickLine={false}
                tickFormatter={(value) => `${value / 1000}k`}
                width={35}
              />

              <Tooltip content={<CustomTooltip />} />

              <ReferenceLine
                y={LOW_BITRATE_THRESHOLD}
                stroke="#EF4444"
                strokeDasharray="5 5"
                strokeOpacity={0.5}
                label={{
                  value: 'Low',
                  fill: '#EF4444',
                  fontSize: 10,
                  position: 'right'
                }}
              />

              <Area
                type="monotone"
                dataKey="bitrate"
                stroke="#3B82F6"
                strokeWidth={2}
                fill="url(#bitrateGradient)"
                animationDuration={300}
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-4 text-xs text-gray-500">
          <span>Last 60 seconds</span>
          <span className="text-red-400">--- Low threshold ({LOW_BITRATE_THRESHOLD} kbps)</span>
        </div>
      </div>
    </CollapsiblePane>
  );
}

export default BitrateGraph;
