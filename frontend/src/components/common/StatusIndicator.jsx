import React from 'react';
import clsx from 'clsx';

const statusColors = {
  green: {
    dot: 'bg-green-500',
    pulse: 'bg-green-400',
    text: 'text-green-500'
  },
  yellow: {
    dot: 'bg-yellow-500',
    pulse: 'bg-yellow-400',
    text: 'text-yellow-500'
  },
  red: {
    dot: 'bg-red-500',
    pulse: 'bg-red-400',
    text: 'text-red-500'
  },
  blue: {
    dot: 'bg-blue-500',
    pulse: 'bg-blue-400',
    text: 'text-blue-500'
  },
  gray: {
    dot: 'bg-gray-500',
    pulse: 'bg-gray-400',
    text: 'text-gray-500'
  }
};

export function StatusIndicator({
  status = 'gray',
  pulse = false,
  size = 'md',
  label,
  className
}) {
  const colors = statusColors[status] || statusColors.gray;

  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4'
  };

  const dotSize = sizeClasses[size] || sizeClasses.md;

  return (
    <div className={clsx('flex items-center gap-2', className)}>
      <span className="relative flex">
        {pulse && (
          <span
            className={clsx(
              'absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping',
              colors.pulse
            )}
          />
        )}
        <span
          className={clsx(
            'relative inline-flex rounded-full',
            dotSize,
            colors.dot
          )}
        />
      </span>
      {label && (
        <span className={clsx('text-sm font-medium', colors.text)}>
          {label}
        </span>
      )}
    </div>
  );
}

export function getStatusFromValue(value, thresholds = { good: 80, warning: 50 }) {
  if (value >= thresholds.good) return 'green';
  if (value >= thresholds.warning) return 'yellow';
  return 'red';
}

export function getStatusFromBitrate(bitrate, target = 2500) {
  if (!bitrate || bitrate === 0) return 'gray';
  const ratio = bitrate / target;
  if (ratio >= 0.9) return 'green';
  if (ratio >= 0.5) return 'yellow';
  return 'red';
}

export default StatusIndicator;
