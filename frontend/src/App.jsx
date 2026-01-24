import React, { useState } from 'react';
import {
  Play, Square, Layers, Monitor, Mic, MicOff, Video, VideoOff,
  RefreshCw, AlertCircle, Check, Loader2, Settings as SettingsIcon,
  Wifi, WifiOff, Radio, Activity
} from 'lucide-react';
import clsx from 'clsx';
import { DashboardProvider, useDashboard } from './context/DashboardContext';
import TopNavBar from './components/layout/TopNavBar';
import StatusFooter from './components/layout/StatusFooter';
import StreamControl from './components/dashboard/StreamControl';
import IngestControls from './components/dashboard/IngestControls';
import SceneSwitcher from './components/dashboard/SceneSwitcher';
import BitrateGraph from './components/dashboard/BitrateGraph';
import PreviewPane from './components/dashboard/PreviewPane';
import { StatusIndicator } from './components/common/StatusIndicator';

function DashboardPage() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-4">
      {/* Left Column */}
      <div className="space-y-4">
        <StreamControl />
        <IngestControls />
        <BitrateGraph />
      </div>

      {/* Right Column */}
      <div className="space-y-4">
        <SceneSwitcher />
        <PreviewPane />
      </div>
    </div>
  );
}

function RemoteOBSPage() {
  const { obsStatus, features, screenshot, switchScene, startStreaming, stopStreaming } = useDashboard();
  const [switchingTo, setSwitchingTo] = useState(null);
  const [isStarting, setIsStarting] = useState(false);
  const [isStopping, setIsStopping] = useState(false);

  const isConnected = obsStatus?.connected;
  const isStreaming = obsStatus?.streaming;
  const isRecording = obsStatus?.recording;
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

  const handleGoLive = async () => {
    setIsStarting(true);
    try {
      await startStreaming();
    } finally {
      setIsStarting(false);
    }
  };

  const handleStopLive = async () => {
    setIsStopping(true);
    try {
      await stopStreaming();
    } finally {
      setIsStopping(false);
    }
  };

  if (!features?.obs_enabled) {
    return (
      <div className="p-4">
        <div className="bg-gray-800 rounded-lg p-8 text-center">
          <AlertCircle className="w-16 h-16 text-gray-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-4">OBS Integration Disabled</h2>
          <p className="text-gray-400">
            Enable OBS integration in the backend configuration to use Remote OBS control.
          </p>
          <p className="text-gray-500 text-sm mt-2">
            Set FEATURE_OBS_INTEGRATION=true in .env
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Connection Status Banner */}
      <div className={clsx(
        'rounded-lg p-4 flex items-center justify-between',
        isConnected ? 'bg-green-900/30 border border-green-700' : 'bg-red-900/30 border border-red-700'
      )}>
        <div className="flex items-center gap-3">
          {isConnected ? (
            <Wifi className="w-6 h-6 text-green-400" />
          ) : (
            <WifiOff className="w-6 h-6 text-red-400" />
          )}
          <div>
            <h3 className={clsx('font-bold', isConnected ? 'text-green-400' : 'text-red-400')}>
              {isConnected ? 'OBS Connected' : 'OBS Disconnected'}
            </h3>
            <p className="text-gray-400 text-sm">
              {isConnected ? `Current Scene: ${currentScene || 'Unknown'}` : 'Waiting for connection...'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {isStreaming && (
            <span className="flex items-center gap-2 px-3 py-1 bg-red-600 text-white rounded-full text-sm font-bold animate-pulse">
              <Radio className="w-4 h-4" /> LIVE
            </span>
          )}
          {isRecording && (
            <span className="flex items-center gap-2 px-3 py-1 bg-red-800 text-white rounded-full text-sm font-bold">
              <Video className="w-4 h-4" /> REC
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Large Preview */}
        <div className="lg:col-span-2 bg-gray-800 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
            <Monitor className="w-5 h-5 text-gray-400" />
            Live Preview
          </h3>
          <div className="aspect-video bg-gray-900 rounded-lg overflow-hidden border border-gray-700">
            {screenshot ? (
              <img
                src={`data:image/jpeg;base64,${screenshot}`}
                alt="OBS Preview"
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center gap-3">
                <Monitor className="w-16 h-16 text-gray-600" />
                <p className="text-gray-500">
                  {isConnected ? 'Loading preview...' : 'Connect OBS to view preview'}
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Control Panel */}
        <div className="space-y-4">
          {/* Stream Controls */}
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              <Radio className="w-5 h-5 text-gray-400" />
              Stream Control
            </h3>
            <div className="space-y-3">
              <button
                onClick={handleGoLive}
                disabled={!isConnected || isStreaming || isStarting}
                className={clsx(
                  'w-full flex items-center justify-center gap-2 py-4 rounded-lg font-bold text-lg transition-all',
                  !isConnected || isStreaming
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-500 text-white'
                )}
              >
                {isStarting ? <Loader2 className="w-6 h-6 animate-spin" /> : <Play className="w-6 h-6" />}
                GO LIVE
              </button>
              <button
                onClick={handleStopLive}
                disabled={!isConnected || !isStreaming || isStopping}
                className={clsx(
                  'w-full flex items-center justify-center gap-2 py-4 rounded-lg font-bold text-lg transition-all',
                  !isConnected || !isStreaming
                    ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                    : 'bg-red-600 hover:bg-red-500 text-white'
                )}
              >
                {isStopping ? <Loader2 className="w-6 h-6 animate-spin" /> : <Square className="w-6 h-6" />}
                STOP STREAM
              </button>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
              <Activity className="w-5 h-5 text-gray-400" />
              Status
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Connection</span>
                <StatusIndicator status={isConnected ? 'green' : 'red'} label={isConnected ? 'OK' : 'Disconnected'} />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Streaming</span>
                <StatusIndicator status={isStreaming ? 'green' : 'gray'} pulse={isStreaming} label={isStreaming ? 'Live' : 'Offline'} />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Recording</span>
                <StatusIndicator status={isRecording ? 'red' : 'gray'} label={isRecording ? 'Recording' : 'Off'} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scene Switcher */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
          <Layers className="w-5 h-5 text-gray-400" />
          Scenes
        </h3>
        {isConnected && scenes.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {scenes.map((scene) => {
              const isActive = scene === currentScene;
              const isSwitching = switchingTo === scene;
              return (
                <button
                  key={scene}
                  onClick={() => handleSceneSwitch(scene)}
                  disabled={isActive || switchingTo !== null}
                  className={clsx(
                    'flex items-center justify-center gap-2 py-4 px-4 rounded-lg font-medium transition-all',
                    isActive
                      ? 'bg-blue-600 text-white ring-2 ring-blue-400'
                      : switchingTo
                        ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                        : 'bg-gray-700 hover:bg-gray-600 text-white'
                  )}
                >
                  {isSwitching && <Loader2 className="w-4 h-4 animate-spin" />}
                  {isActive && <Check className="w-4 h-4" />}
                  <span className="truncate">{scene}</span>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            {isConnected ? 'No scenes found' : 'Connect to OBS to view scenes'}
          </div>
        )}
      </div>
    </div>
  );
}

function SettingsPage() {
  const { features, obsStatus, ingestStats, isConnected } = useDashboard();

  return (
    <div className="p-4 max-w-4xl mx-auto space-y-6">
      {/* Connection Status */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Connection Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Backend API</span>
              <StatusIndicator status={isConnected ? 'green' : 'red'} label={isConnected ? 'Connected' : 'Disconnected'} />
            </div>
            <p className="text-gray-500 text-sm">FastAPI server at port 8000</p>
          </div>
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">OBS WebSocket</span>
              <StatusIndicator status={obsStatus?.connected ? 'green' : 'red'} label={obsStatus?.connected ? 'Connected' : 'Disconnected'} />
            </div>
            <p className="text-gray-500 text-sm">Port 4455</p>
          </div>
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Ingest Monitor</span>
              <StatusIndicator status={ingestStats?.connected ? 'green' : 'yellow'} label={ingestStats?.connected ? 'Receiving' : 'Waiting'} />
            </div>
            <p className="text-gray-500 text-sm">{ingestStats?.server_type || 'nginx'} stats</p>
          </div>
          <div className="bg-gray-900 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-gray-400">Streaming</span>
              <StatusIndicator status={obsStatus?.streaming ? 'green' : 'gray'} pulse={obsStatus?.streaming} label={obsStatus?.streaming ? 'Live' : 'Offline'} />
            </div>
            <p className="text-gray-500 text-sm">{obsStatus?.current_scene || 'No scene'}</p>
          </div>
        </div>
      </div>

      {/* Feature Flags */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Enabled Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            { key: 'obs_enabled', label: 'OBS Integration', desc: 'WebSocket control of OBS Studio' },
            { key: 'ingest_enabled', label: 'Ingest Monitoring', desc: 'Monitor nginx-rtmp/SRT stats' },
            { key: 'dual_metrics', label: 'Dual Metrics', desc: 'Combine MPTCP + ingest metrics' },
            { key: 'health_score', label: 'Health Score', desc: 'Calculate stream health' },
            { key: 'srt_bonding', label: 'SRTLA Transport', desc: 'SRT link aggregation' },
          ].map(({ key, label, desc }) => (
            <div key={key} className="flex items-center justify-between bg-gray-900 rounded-lg p-3">
              <div>
                <span className="text-white font-medium">{label}</span>
                <p className="text-gray-500 text-xs">{desc}</p>
              </div>
              <StatusIndicator
                status={features?.[key] ? 'green' : 'gray'}
                label={features?.[key] ? 'Enabled' : 'Disabled'}
              />
            </div>
          ))}
        </div>
      </div>

      {/* OBS Settings */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">OBS Configuration</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-gray-700">
            <span className="text-gray-400">Host</span>
            <span className="text-white font-mono">localhost:4455</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-700">
            <span className="text-gray-400">Connection State</span>
            <span className="text-white">{obsStatus?.state || 'unknown'}</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-700">
            <span className="text-gray-400">Current Scene</span>
            <span className="text-blue-400">{obsStatus?.current_scene || 'N/A'}</span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-gray-400">Available Scenes</span>
            <span className="text-white">{obsStatus?.scenes?.length || 0}</span>
          </div>
        </div>
      </div>

      {/* Ingest Settings */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">Ingest Configuration</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-gray-700">
            <span className="text-gray-400">Server Type</span>
            <span className="text-white">{ingestStats?.server_type || 'nginx'}</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-700">
            <span className="text-gray-400">Poll Success Rate</span>
            <span className="text-white">{ingestStats?.poll_success_rate?.toFixed(1) || 0}%</span>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-700">
            <span className="text-gray-400">Current Bitrate</span>
            <span className="text-white font-mono">{Math.round(ingestStats?.bitrate_kbps || 0)} kbps</span>
          </div>
          <div className="flex items-center justify-between py-2">
            <span className="text-gray-400">Connection Active</span>
            <StatusIndicator status={ingestStats?.connected ? 'green' : 'gray'} label={ingestStats?.connected ? 'Yes' : 'No'} />
          </div>
        </div>
      </div>

      {/* About */}
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-bold text-white mb-4">About</h2>
        <div className="space-y-2 text-gray-400">
          <p><span className="text-white">VVLIVE Dashboard</span> v1.0.0</p>
          <p>IRL Bonded Streaming Control Panel</p>
          <p className="text-gray-500 text-sm mt-4">
            Built with React, Tailwind CSS, Recharts, and FastAPI backend.
            Inspired by NOALBS and IRLToolkit patterns.
          </p>
        </div>
      </div>
    </div>
  );
}

function AppContent() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderPage = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardPage />;
      case 'obs':
        return <RemoteOBSPage />;
      case 'settings':
        return <SettingsPage />;
      default:
        return <DashboardPage />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col">
      <TopNavBar activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto">
        {renderPage()}
      </main>

      <StatusFooter />
    </div>
  );
}

function App() {
  return (
    <DashboardProvider>
      <AppContent />
    </DashboardProvider>
  );
}

export default App;
