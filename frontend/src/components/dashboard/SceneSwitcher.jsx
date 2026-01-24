import React, { useState } from 'react';
import { Layers, AlertCircle, Loader2, Check } from 'lucide-react';
import clsx from 'clsx';
import { CollapsiblePane } from '../common/CollapsiblePane';
import { StatusIndicator } from '../common/StatusIndicator';
import { useDashboard } from '../../context/DashboardContext';

export function SceneSwitcher() {
  const { obsStatus, features, switchScene } = useDashboard();
  const [switchingTo, setSwitchingTo] = useState(null);

  const isConnected = obsStatus?.connected;
  const currentScene = obsStatus?.current_scene;
  const scenes = obsStatus?.scenes || [];

  const handleSceneSwitch = async (sceneName) => {
    if (sceneName === currentScene || switchingTo) return;

    setSwitchingTo(sceneName);
    try {
      await switchScene(sceneName);
    } finally {
      setSwitchingTo(null);
    }
  };

  if (!features?.obs_enabled) {
    return (
      <CollapsiblePane
        title="Scene Switcher"
        icon={Layers}
        storageKey="scene-switcher"
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
      title="Scene Switcher"
      icon={Layers}
      storageKey="scene-switcher"
      defaultExpanded={true}
    >
      <div className="space-y-4">
        {/* OBS Connection Status */}
        <div className="flex items-center justify-between">
          <span className="text-gray-400">OBS Status</span>
          <StatusIndicator
            status={isConnected ? 'green' : 'red'}
            label={isConnected ? 'Connected' : 'Disconnected'}
          />
        </div>

        {/* Current Scene */}
        {currentScene && (
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Current Scene</span>
            <span className="text-blue-400 font-medium">{currentScene}</span>
          </div>
        )}

        {/* Streaming Status */}
        {isConnected && (
          <div className="flex items-center justify-between">
            <span className="text-gray-400">Streaming</span>
            <StatusIndicator
              status={obsStatus?.streaming ? 'green' : 'gray'}
              pulse={obsStatus?.streaming}
              label={obsStatus?.streaming ? 'Live' : 'Offline'}
            />
          </div>
        )}

        {/* Scene Buttons */}
        {isConnected ? (
          <div className="grid grid-cols-2 gap-2">
            {scenes.length > 0 ? (
              scenes.map((scene) => {
                const isActive = scene === currentScene;
                const isSwitching = switchingTo === scene;

                return (
                  <button
                    key={scene}
                    onClick={() => handleSceneSwitch(scene)}
                    disabled={isActive || switchingTo !== null}
                    className={clsx(
                      'flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-medium transition-all',
                      isActive
                        ? 'bg-blue-600 text-white ring-2 ring-blue-400'
                        : switchingTo !== null
                          ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                          : 'bg-gray-700 hover:bg-gray-600 text-white'
                    )}
                  >
                    {isSwitching && <Loader2 className="w-4 h-4 animate-spin" />}
                    {isActive && <Check className="w-4 h-4" />}
                    <span className="truncate">{scene}</span>
                  </button>
                );
              })
            ) : (
              <div className="col-span-2 text-center text-gray-500 py-4">
                No scenes available - check OBS
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 py-6 text-gray-500">
            <AlertCircle className="w-8 h-8" />
            <span>Connect OBS to switch scenes</span>
            <p className="text-xs text-gray-600 text-center">
              Make sure OBS WebSocket server is enabled on port 4455
            </p>
          </div>
        )}
      </div>
    </CollapsiblePane>
  );
}

export default SceneSwitcher;
