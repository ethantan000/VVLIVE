import React, { useState } from 'react';
import { Monitor, ImageOff, RefreshCw, Maximize2, AlertCircle } from 'lucide-react';
import clsx from 'clsx';
import { CollapsiblePane } from '../common/CollapsiblePane';
import { useDashboard } from '../../context/DashboardContext';

export function PreviewPane() {
  const { screenshot, obsStatus, features } = useDashboard();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const isOBSConnected = obsStatus?.connected;

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const response = await fetch('/api/obs/screenshot?width=1280&height=720');
      // Screenshot will be updated via polling
    } catch (err) {
      console.error('Failed to refresh screenshot:', err);
    } finally {
      setTimeout(() => setIsRefreshing(false), 500);
    }
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // OBS not enabled
  if (!features?.obs_enabled) {
    return (
      <CollapsiblePane
        title="Preview"
        icon={Monitor}
        storageKey="preview-pane"
        defaultExpanded={true}
      >
        <div className="aspect-video bg-gray-900 rounded-lg flex flex-col items-center justify-center gap-4 border border-gray-700">
          <AlertCircle className="w-12 h-12 text-gray-600" />
          <div className="text-center">
            <p className="text-gray-400 font-medium">OBS Not Enabled</p>
            <p className="text-gray-600 text-sm mt-1">
              Enable OBS integration to view preview
            </p>
          </div>
        </div>
      </CollapsiblePane>
    );
  }

  // OBS not connected
  if (!isOBSConnected) {
    return (
      <CollapsiblePane
        title="Preview"
        icon={Monitor}
        storageKey="preview-pane"
        defaultExpanded={true}
      >
        <div className="aspect-video bg-gray-900 rounded-lg flex flex-col items-center justify-center gap-4 border border-gray-700">
          <ImageOff className="w-12 h-12 text-gray-600" />
          <div className="text-center">
            <p className="text-gray-400 font-medium">OBS Not Connected</p>
            <p className="text-gray-600 text-sm mt-1">
              Connect to OBS to view live preview
            </p>
          </div>
        </div>
      </CollapsiblePane>
    );
  }

  return (
    <>
      <CollapsiblePane
        title="Preview"
        icon={Monitor}
        storageKey="preview-pane"
        defaultExpanded={true}
      >
        <div className="space-y-3">
          {/* Preview Image */}
          <div
            className="aspect-video bg-gray-900 rounded-lg overflow-hidden border border-gray-700 relative cursor-pointer"
            onClick={toggleFullscreen}
          >
            {screenshot ? (
              <img
                src={`data:image/jpeg;base64,${screenshot}`}
                alt="OBS Preview"
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center gap-3">
                <ImageOff className="w-10 h-10 text-gray-600" />
                <p className="text-gray-500 text-sm">Loading preview...</p>
              </div>
            )}

            {/* Overlay buttons */}
            <div className="absolute top-2 right-2 flex gap-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleRefresh();
                }}
                className="p-2 bg-gray-800/80 hover:bg-gray-700 rounded-lg transition-colors"
                title="Refresh"
              >
                <RefreshCw className={clsx('w-4 h-4 text-gray-300', isRefreshing && 'animate-spin')} />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFullscreen();
                }}
                className="p-2 bg-gray-800/80 hover:bg-gray-700 rounded-lg transition-colors"
                title="Fullscreen"
              >
                <Maximize2 className="w-4 h-4 text-gray-300" />
              </button>
            </div>
          </div>

          {/* Scene info */}
          {obsStatus?.current_scene && (
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">Current Scene:</span>
              <span className="text-blue-400 font-medium">{obsStatus.current_scene}</span>
            </div>
          )}
        </div>
      </CollapsiblePane>

      {/* Fullscreen Modal */}
      {isFullscreen && (
        <div
          className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center p-4"
          onClick={toggleFullscreen}
        >
          <button
            className="absolute top-4 right-4 p-2 text-white hover:text-gray-300"
            onClick={toggleFullscreen}
          >
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          {screenshot ? (
            <img
              src={`data:image/jpeg;base64,${screenshot}`}
              alt="OBS Preview Fullscreen"
              className="max-w-full max-h-full object-contain"
              onClick={(e) => e.stopPropagation()}
            />
          ) : (
            <div className="text-gray-500">No preview available</div>
          )}
        </div>
      )}
    </>
  );
}

export default PreviewPane;
