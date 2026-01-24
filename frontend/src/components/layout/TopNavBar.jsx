import React from 'react';
import { Radio, Settings, Monitor, LayoutDashboard } from 'lucide-react';
import clsx from 'clsx';
import { StatusIndicator } from '../common/StatusIndicator';
import { useDashboard } from '../../context/DashboardContext';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'obs', label: 'Remote OBS', icon: Monitor },
  { id: 'settings', label: 'Settings', icon: Settings }
];

export function TopNavBar({ activeTab = 'dashboard', onTabChange }) {
  const { status, isConnected, features } = useDashboard();

  const isLive = status?.quality_state === 'EXCELLENT' ||
                 status?.quality_state === 'GOOD' ||
                 status?.quality_state === 'MEDIUM';

  return (
    <nav className="bg-gray-900 border-b border-gray-700">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <Radio className="w-8 h-8 text-blue-500" />
            <span className="text-xl font-bold text-white">VVLIVE</span>
            {isLive && (
              <span className="ml-2 px-2 py-1 text-xs font-bold bg-red-600 text-white rounded animate-pulse">
                LIVE
              </span>
            )}
          </div>

          {/* Navigation Tabs */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map(item => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              const isDisabled = item.id === 'obs' && !features?.obs_enabled;

              return (
                <button
                  key={item.id}
                  onClick={() => !isDisabled && onTabChange?.(item.id)}
                  disabled={isDisabled}
                  className={clsx(
                    'flex items-center gap-2 px-4 py-2 rounded-lg transition-colors',
                    isActive
                      ? 'bg-blue-600 text-white'
                      : isDisabled
                        ? 'text-gray-600 cursor-not-allowed'
                        : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  )}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>

          {/* Connection Status */}
          <div className="flex items-center gap-4">
            <StatusIndicator
              status={isConnected ? 'green' : 'red'}
              pulse={isConnected}
              label={isConnected ? 'Connected' : 'Disconnected'}
            />
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      <div className="md:hidden flex border-t border-gray-700">
        {navItems.map(item => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          const isDisabled = item.id === 'obs' && !features?.obs_enabled;

          return (
            <button
              key={item.id}
              onClick={() => !isDisabled && onTabChange?.(item.id)}
              disabled={isDisabled}
              className={clsx(
                'flex-1 flex flex-col items-center gap-1 py-3 transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : isDisabled
                    ? 'text-gray-600'
                    : 'text-gray-400 hover:bg-gray-800'
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="text-xs">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

export default TopNavBar;
