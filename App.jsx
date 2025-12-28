import React, { useState, useEffect } from 'react';
import AdvancedSystemStatusWidget from './AdvancedSystemStatusWidget';

/**
 * Main Application Component
 * 
 * Integrates the Advanced System Status Widget with real-time monitoring
 * of the social media automation architecture.
 */

function App() {
  // System state management - can be populated from API
  const [systemState, setSystemState] = useState({
    instaGraphApi: {
      status: 'operational',
      latency: '142ms',
      rateLimitRemaining: '87%'
    },
    webhooksConfig: {
      status: 'operational',
      activeHooks: 3,
      lastEvent: '2m ago'
    },
    sqlDatabase: {
      status: 'operational',
      activeConnections: 12,
      latency: '8ms'
    },
    groqCloud: {
      status: 'operational',
      model: 'llama-3.1-70b',
      latency: '234ms'
    },
    pinecone: {
      status: 'operational',
      index: 'social-vectors',
      totalVectors: '12,847',
      latency: '45ms'
    },
    scheduler: {
      status: 'operational',
      jobsQueued: 7,
      nextRun: '15m'
    },
    automation: {
      status: 'degraded',
      lastTriggered: '5m ago',
      successRate: '94%'
    },
    geminiApi: {
      status: 'operational',
      latency: '189ms',
      quotaUsedToday: '23%'
    },
    llumaAi: {
      status: 'operational',
      latency: '156ms',
      modelVersion: 'v2.3.1'
    }
  });

  // Fetch real-time system status (optional - connect to your status API)
  useEffect(() => {
    const fetchSystemStatus = async () => {
      try {
        // Uncomment and update with your actual API endpoint
        // const response = await fetch('/api/system-status');
        // const data = await response.json();
        // setSystemState(data);
      } catch (error) {
        console.error('Error fetching system status:', error);
      }
    };

    // Initial fetch
    fetchSystemStatus();

    // Poll every 30 seconds
    const interval = setInterval(fetchSystemStatus, 30000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      {/* Your main app content */}
      <div className="container mx-auto p-8">
        <h1 className="text-4xl font-bold text-white mb-4">
          Social Media Automation Platform
        </h1>
        <p className="text-white/60 mb-8">
          Advanced system monitoring with real-time architecture visualization
        </p>

        {/* Example content to show the floating widget */}
        <div className="grid grid-cols-3 gap-6">
          {[
            { title: 'Posts Scheduled', value: '47', icon: '📅' },
            { title: 'Active Workflows', value: '12', icon: '⚡' },
            { title: 'AI Generations', value: '234', icon: '🧠' },
            { title: 'Success Rate', value: '94%', icon: '✅' },
            { title: 'API Calls Today', value: '1.2K', icon: '📊' },
            { title: 'Uptime', value: '99.8%', icon: '🚀' }
          ].map((stat, i) => (
            <div
              key={i}
              className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 hover:bg-white/10 transition-all"
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-3xl">{stat.icon}</span>
                <span className="text-3xl font-bold text-white">{stat.value}</span>
              </div>
              <h3 className="text-white/80 font-medium text-sm">{stat.title}</h3>
            </div>
          ))}
        </div>

        {/* Additional content sections */}
        <div className="mt-12 grid grid-cols-2 gap-6">
          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
            <h3 className="text-white font-semibold text-xl mb-4">Recent Activity</h3>
            <div className="space-y-3">
              {[
                { action: 'Post published to Instagram', time: '2 min ago', status: 'success' },
                { action: 'AI content generated', time: '5 min ago', status: 'success' },
                { action: 'Webhook received', time: '8 min ago', status: 'success' },
                { action: 'Scheduled job executed', time: '12 min ago', status: 'warning' }
              ].map((activity, idx) => (
                <div key={idx} className="flex items-center gap-3 text-sm">
                  <div className={`w-2 h-2 rounded-full ${
                    activity.status === 'success' ? 'bg-emerald-500' : 'bg-yellow-500'
                  }`}></div>
                  <span className="text-white/80 flex-1">{activity.action}</span>
                  <span className="text-white/40">{activity.time}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
            <h3 className="text-white font-semibold text-xl mb-4">System Health</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-white/60">CPU Usage</span>
                  <span className="text-white">34%</span>
                </div>
                <div className="w-full bg-slate-700/50 rounded-full h-2">
                  <div className="bg-gradient-to-r from-emerald-500 to-blue-500 h-2 rounded-full" style={{ width: '34%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-white/60">Memory Usage</span>
                  <span className="text-white">58%</span>
                </div>
                <div className="w-full bg-slate-700/50 rounded-full h-2">
                  <div className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full" style={{ width: '58%' }}></div>
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-white/60">Network I/O</span>
                  <span className="text-white">23%</span>
                </div>
                <div className="w-full bg-slate-700/50 rounded-full h-2">
                  <div className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full" style={{ width: '23%' }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Advanced System Status Widget - Floating */}
      <AdvancedSystemStatusWidget systemState={systemState} />
    </div>
  );
}

export default App;
