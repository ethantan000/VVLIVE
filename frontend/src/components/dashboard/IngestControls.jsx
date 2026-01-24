import React, { useState } from 'react';
import { Activity, VolumeX, Volume2, Wrench, AlertCircle, Loader2 } from 'lucide-react';
import clsx from 'clsx';
import { CollapsiblePane } from '../common/CollapsiblePane';
import { StatusIndicator, getStatusFromBitrate } from '../common/StatusIndicator';
import { useDashboard } from '../../context/DashboardContext';
import { useApiPost } from '../../hooks/useApi';

export function IngestControls() {
  const { ingestStats, features, metrics } = useDashboard();
  const [isMuted, setIsMuted] = useState(false);
  const [isFixing, setIsFixing] = useState(false);

  const { post: muteIngest } = useApiPost('/ingest/mute');
  const { post: fixIngest } = useApiPost('/ingest/fix');

  const bitrate = ingestStats?.bitrate_kbps || 0;
  const isConnected = ingestStats?.connected ?? false;
  const fps = ingestStats?.fps || 0;
  const droppedFrames = ingestStats?.dropped_frames || 0;
  const uplinkCount = metrics?.active_uplinks || 0;

  const handleMuteToggle = async () => {
    const result = await muteIngest({ mute: !isMuted });
    if (result.success) {
      setIsMuted(!isMuted);
    }
  };

  const handleFix = async () => {
    setIsFixing(true);
    try {
      await fixIngest({});
    } finally {
      setIsFixing(false);
    }
  };

  if (!features?.ingest_enabled) {
    return (
      <CollapsiblePane
        title="Ingest Monitor"
        icon={Activity}
        storageKey="ingest-controls"
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
      title="Ingest Monitor"
      icon={Activity}
      storageKey="ingest-controls"
      defaultExpanded={true}
    >
      <div className="space-y-4">
        {/* Connection Status */}
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Connection</span>
          <StatusIndicator
            status={isConnected ? 'green' : 'red'}
            pulse={isConnected}
            label={isConnected ? 'Receiving' : 'No Signal'}
          />
        </div>

        {/* Bitrate Display */}
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-gray-400 text-sm">Bitrate</span>
            <StatusIndicator status={getStatusFromBitrate(bitrate)} size="sm" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className={clsx(
              'text-4xl font-bold font-mono',
              bitrate > 2000 ? 'text-green-500' :
              bitrate > 1000 ? 'text-yellow-500' :
              bitrate > 0 ? 'text-red-500' : 'text-gray-500'
            )}>
              {Math.round(bitrate)}
            </span>
            <span className="text-gray-500 text-lg">kbps</span>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-gray-900 rounded-lg p-3 text-center">
            <div className="text-gray-400 text-xs mb-1">FPS</div>
            <div className="text-white font-mono font-bold">{fps.toFixed(1)}</div>
          </div>
          <div className="bg-gray-900 rounded-lg p-3 text-center">
            <div className="text-gray-400 text-xs mb-1">Dropped</div>
            <div className={clsx(
              'font-mono font-bold',
              droppedFrames > 100 ? 'text-red-500' :
              droppedFrames > 10 ? 'text-yellow-500' : 'text-white'
            )}>
              {droppedFrames}
            </div>
          </div>
          <div className="bg-gray-900 rounded-lg p-3 text-center">
            <div className="text-gray-400 text-xs mb-1">Uplinks</div>
            <div className={clsx(
              'font-mono font-bold',
              uplinkCount >= 2 ? 'text-green-500' :
              uplinkCount === 1 ? 'text-yellow-500' : 'text-red-500'
            )}>
              {uplinkCount}
            </div>
          </div>
        </div>

        {/* Control Buttons */}
        <div className="flex gap-3 pt-2">
          <button
            onClick={handleMuteToggle}
            className={clsx(
              'flex-1 flex items-center justify-center gap-2 py-2 rounded-lg font-medium transition-all',
              isMuted
                ? 'bg-red-600 hover:bg-red-500 text-white'
                : 'bg-gray-700 hover:bg-gray-600 text-white'
            )}
          >
            {isMuted ? (
              <>
                <VolumeX className="w-4 h-4" />
                Muted
              </>
            ) : (
              <>
                <Volume2 className="w-4 h-4" />
                Mute
              </>
            )}
          </button>

          <button
            onClick={handleFix}
            disabled={isFixing}
            className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg font-medium bg-blue-600 hover:bg-blue-500 text-white transition-all disabled:opacity-50"
          >
            {isFixing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Wrench className="w-4 h-4" />
            )}
            Fix
          </button>
        </div>
      </div>
    </CollapsiblePane>
  );
}

export default IngestControls;
