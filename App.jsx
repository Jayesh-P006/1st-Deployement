import React from 'react';
import SystemStatusMonitor from './SystemStatusMonitor';

/**
 * Example usage of the SystemStatusMonitor component
 * 
 * This demo shows how to integrate the status monitor into your app.
 */

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Your main app content */}
      <div className="container mx-auto p-8">
        <h1 className="text-4xl font-bold text-white mb-4">
          Social Media Scheduler
        </h1>
        <p className="text-white/60 mb-8">
          The status monitor will appear in the bottom-right corner
        </p>

        {/* Example cards to show the monitor is floating above content */}
        <div className="grid grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 hover:bg-white/10 transition-all"
            >
              <h3 className="text-white font-semibold mb-2">Sample Card {i}</h3>
              <p className="text-white/60 text-sm">
                This is placeholder content to demonstrate the floating status monitor.
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Status Monitor - Floating Widget */}
      <SystemStatusMonitor />
    </div>
  );
}

export default App;
