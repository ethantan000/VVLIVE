import React, { useState } from 'react';
import { Play, Square, AlertCircle, Loader2, Radio } from 'lucide-react';
import clsx from 'clsx';
import { CollapsiblePane } from '../common/CollapsiblePane';
import { StatusIndicator } from '../common/StatusIndicator';
import { useDashboard } from '../../context/DashboardContext';

export function StreamControl() {
  const { obsStatus, features, status, startStreaming, stopStreaming } = useDashboard();
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);

  const isOBSConnected = obsStatus?.connected;
  const isStreaming = obsStatus?.streaming;
  const isRecording = obsStatus?.recording;

  const handleGoLive = async () => {
    if (isStarting) return;
    setIsStarting(true);
    try {
      await startStreaming();
    } finally {
      setIsStarting(false);
    }
  };

  const handleStopLive = async () => {
    if (isStopping) return;
    setIsStopping(true);
    try {
      await stopStreaming();
    } finally {
      setIsStopping(false);
    }
  };

  if (!features?.obs_enabled) {
    return (
      <CollapsiblePane
        title="Stream Control"
        icon={Radio}
        storageKey="stream-control"
        defaultExpanded={true}
      >
        <div className="flex items-center gap-3 text-gray-400 py-4">
          <AlertCircle className="w-5 h-5" />
          <span>OBS integration not enabled</span>
        </div>
      </CollapsiblePane>
    );
  }

  return (
    <CollapsiblePane
      title="Stream Control"
      icon={Radio}
      storageKey="stream-control"
      defaultExpanded={true}
    >
      <div className="space-y-4">
        {/* OBS Connection Status */}
        <div className="flex items-center justify-between">
          <span className="text-gray-400">OBS Status</span>
          <StatusIndicator
            status={isOBSConnected ? 'green' : 'red'}
            label={isOBSConnected ? 'Connected' : 'Disconnected'}
          />
        </div>

        {/* Stream Status */}
        <div className="flex items-center justify-between">
          <span className="text-gray-400">Stream Status</span>
          <StatusIndicator
            status={isStreaming ? 'green' : 'gray'}
            pulse={isStreaming}
            label={isStreaming ? 'Live' : 'Offline'}
          />
        </div>

        {/* Recording Status */}
        {isOBSConnected && (
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Recording</span>
            <StatusIndicator
              status={isRecording ? 'red' : 'gray'}
              pulse={isRecording}
              label={isRecording ? 'Recording' : 'Not Recording'}
            />
          </div>
        )}

        {/* Quality State */}
        {status?.quality_state && (
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Quality</span>
            <span className={clsx(
              'font-medium px-2 py-1 rounded text-sm',
              status.quality_state === 'HIGH' && 'bg-green-900/50 text-green-400',
              status.quality_state === 'MEDIUM' && 'bg-blue-900/50 text-blue-400',
              status.quality_state === 'LOW' && 'bg-yellow-900/50 text-yellow-400',
              status.quality_state === 'VERY_LOW' && 'bg-orange-900/50 text-orange-400',
              status.quality_state === 'ERROR' && 'bg-red-900/50 text-red-400'
            )}>
              {status.quality_state}
            </span>
          </div>
        )}

        {/* Control Buttons */}
        <div className="flex gap-3 pt-2">
          <button
            onClick={handleGoLive}
            disabled={!isOBSConnected || isStreaming || isStarting}
            className={clsx(
              'flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-bold transition-all',
              !isOBSConnected || isStreaming
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                : 'bg-green-600 hover:bg-green-500 text-white'
            )}
          >
            {isStarting ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Play className="w-5 h-5" />
            )}
            GO LIVE
          </button>

          <button
            onClick={handleStopLive}
            disabled={!isOBSConnected || !isStreaming || isStopping}
            className={clsx(
              'flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-bold transition-all',
              !isOBSConnected || !isStreaming
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                : 'bg-red-600 hover:bg-red-500 text-white'
            )}
          >
            {isStopping ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Square className="w-5 h-5" />
            )}
            STOP
          </button>
        </div>

        {/* Warning if disconnected */}
        {!isOBSConnected && (
          <div className="flex items-center gap-2 text-yellow-500 text-sm bg-yellow-900/20 p-3 rounded-lg">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>Connect OBS to enable stream control. Make sure WebSocket server is enabled on port 4455.</span>
          </div>
        )}
      </div>
    </CollapsiblePane>
  );
}

export default StreamControl;
