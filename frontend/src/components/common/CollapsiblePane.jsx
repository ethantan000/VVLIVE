import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';
import clsx from 'clsx';

export function CollapsiblePane({
  title,
  children,
  defaultExpanded = true,
  storageKey,
  className,
  headerClassName,
  icon: Icon
}) {
  const [isExpanded, setIsExpanded] = useState(() => {
    if (storageKey) {
      const stored = localStorage.getItem(`pane-${storageKey}`);
      if (stored !== null) {
        return stored === 'true';
      }
    }
    return defaultExpanded;
  });

  useEffect(() => {
    if (storageKey) {
      localStorage.setItem(`pane-${storageKey}`, String(isExpanded));
    }
  }, [isExpanded, storageKey]);

  const toggleExpanded = () => {
    setIsExpanded(prev => !prev);
  };

  return (
    <div className={clsx('bg-gray-800 rounded-lg overflow-hidden', className)}>
      <button
        onClick={toggleExpanded}
        className={clsx(
          'w-full flex items-center justify-between p-4 hover:bg-gray-750 transition-colors',
          'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset',
          headerClassName
        )}
      >
        <div className="flex items-center gap-3">
          {Icon && <Icon className="w-5 h-5 text-gray-400" />}
          <h3 className="text-lg font-semibold text-white">{title}</h3>
        </div>
        <div className="text-gray-400">
          {isExpanded ? (
            <ChevronDown className="w-5 h-5" />
          ) : (
            <ChevronRight className="w-5 h-5" />
          )}
        </div>
      </button>

      <div
        className={clsx(
          'transition-all duration-300 ease-in-out overflow-hidden',
          isExpanded ? 'max-h-[1000px] opacity-100' : 'max-h-0 opacity-0'
        )}
      >
        <div className="p-4 pt-0 border-t border-gray-700">
          {children}
        </div>
      </div>
    </div>
  );
}

export default CollapsiblePane;
