import React, { useState, useRef, useEffect } from 'react';

/**
 * System Status Monitor - Glassmorphism Dashboard Widget
 * 
 * A floating, draggable status dashboard that visualizes the social media
 * scheduler pipeline with animated node connections.
 * 
 * Features:
 * - Glassmorphism UI with backdrop blur
 * - Draggable positioning
 * - Minimizable window
 * - Animated pipeline flow visualization
 * - Real-time status indicators (operational/processing/down)
 */

const SystemStatusMonitor = () => {
  // Widget state
  const [isMinimized, setIsMinimized] = useState(false);
  const [position, setPosition] = useState({ x: window.innerWidth - 420, y: window.innerHeight - 650 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const widgetRef = useRef(null);

  // System nodes with mock status data
  const [systemNodes, setSystemNodes] = useState([
    {
      id: 'user-input',
      name: 'User Input',
      icon: '👤',
      status: 'operational', // operational | processing | down
      latency: '12ms',
      description: 'Post creation interface'
    },
    {
      id: 'vector-db',
      name: 'Vector Database',
      icon: '🗄️',
      status: 'operational',
      latency: '45ms',
      description: 'Pinecone Dense Vectors',
      details: '1,247 vectors'
    },
    {
      id: 'ai-engine',
      name: 'AI Engine',
      icon: '🧠',
      status: 'processing',
      latency: '234ms',
      description: 'RAG + Groq/Gemini',
      details: 'Processing 3 requests'
    },
    {
      id: 'scheduler',
      name: 'Scheduler Backend',
      icon: '⚙️',
      status: 'operational',
      latency: '8ms',
      description: 'APScheduler',
      details: '12 jobs queued'
    },
    {
      id: 'social-api',
      name: 'Social Media APIs',
      icon: '📱',
      status: 'operational',
      latency: '156ms',
      description: 'Instagram Graph API',
      details: 'Rate: 95/200'
    }
  ]);

  // Status colors and animations
  const statusConfig = {
    operational: {
      color: 'bg-emerald-500',
      glow: 'shadow-emerald-500/50',
      pulse: false,
      label: 'Operational',
      bgColor: 'bg-emerald-500/10'
    },
    processing: {
      color: 'bg-amber-400',
      glow: 'shadow-amber-400/50',
      pulse: true,
      label: 'Processing',
      bgColor: 'bg-amber-400/10'
    },
    down: {
      color: 'bg-red-500',
      glow: 'shadow-red-500/50',
      pulse: true,
      label: 'Down',
      bgColor: 'bg-red-500/10'
    }
  };

  // Drag handlers
  const handleMouseDown = (e) => {
    if (e.target.closest('.drag-handle')) {
      setIsDragging(true);
      setDragOffset({
        x: e.clientX - position.x,
        y: e.clientY - position.y
      });
    }
  };

  const handleMouseMove = (e) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragOffset.x,
        y: e.clientY - dragOffset.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragOffset]);

  // Simulate status changes (for demo purposes)
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemNodes(prevNodes => 
        prevNodes.map(node => {
          // Randomly change AI Engine status for demo
          if (node.id === 'ai-engine' && Math.random() > 0.7) {
            return {
              ...node,
              status: node.status === 'processing' ? 'operational' : 'processing',
              latency: `${Math.floor(Math.random() * 300 + 100)}ms`
            };
          }
          return node;
        })
      );
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  // Calculate overall system health
  const systemHealth = () => {
    const operational = systemNodes.filter(n => n.status === 'operational').length;
    const total = systemNodes.length;
    const percentage = Math.round((operational / total) * 100);
    
    if (percentage === 100) return { status: 'Excellent', color: 'text-emerald-400' };
    if (percentage >= 80) return { status: 'Good', color: 'text-lime-400' };
    if (percentage >= 60) return { status: 'Fair', color: 'text-amber-400' };
    return { status: 'Critical', color: 'text-red-400' };
  };

  const health = systemHealth();

  return (
    <div
      ref={widgetRef}
      className="fixed z-50 select-none"
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        cursor: isDragging ? 'grabbing' : 'default'
      }}
    >
      {/* Glassmorphism Container */}
      <div className="backdrop-blur-xl bg-slate-900/40 border border-white/10 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header Bar */}
        <div
          className="drag-handle px-5 py-3 bg-gradient-to-r from-slate-800/50 to-slate-700/50 border-b border-white/5 cursor-grab active:cursor-grabbing flex items-center justify-between"
          onMouseDown={handleMouseDown}
        >
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-red-500"></div>
            <div className="w-2 h-2 rounded-full bg-amber-500"></div>
            <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
            <span className="ml-2 text-white/90 font-semibold text-sm tracking-wide">
              System Status Monitor
            </span>
          </div>
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="text-white/60 hover:text-white/90 transition-colors"
          >
            {isMinimized ? '□' : '_'}
          </button>
        </div>

        {/* Main Content */}
        {!isMinimized && (
          <div className="w-96 p-6">
            {/* System Health Overview */}
            <div className="mb-6 p-4 bg-white/5 rounded-xl border border-white/10">
              <div className="flex items-center justify-between mb-2">
                <span className="text-white/70 text-sm">System Health</span>
                <span className={`font-bold text-lg ${health.color}`}>{health.status}</span>
              </div>
              <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-emerald-500 to-cyan-500 transition-all duration-500"
                  style={{ width: `${(systemNodes.filter(n => n.status === 'operational').length / systemNodes.length) * 100}%` }}
                />
              </div>
            </div>

            {/* Pipeline Visualization */}
            <div className="relative space-y-4">
              {systemNodes.map((node, index) => (
                <div key={node.id} className="relative">
                  {/* Connection Line to Next Node */}
                  {index < systemNodes.length - 1 && (
                    <svg
                      className="absolute left-8 top-16 w-0.5 h-8"
                      style={{ zIndex: 0 }}
                    >
                      <line
                        x1="1"
                        y1="0"
                        x2="1"
                        y2="32"
                        stroke="url(#gradient)"
                        strokeWidth="2"
                        strokeDasharray={node.status === 'operational' ? '0' : '5,5'}
                      >
                        {/* Animate line when processing */}
                        {node.status === 'processing' && (
                          <animate
                            attributeName="stroke-dashoffset"
                            from="0"
                            to="10"
                            dur="0.5s"
                            repeatCount="indefinite"
                          />
                        )}
                      </line>
                      <defs>
                        <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                          <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.8" />
                          <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.4" />
                        </linearGradient>
                      </defs>
                    </svg>
                  )}

                  {/* Node Card */}
                  <div className={`relative z-10 p-4 rounded-xl border backdrop-blur-sm transition-all duration-300 hover:scale-102 ${statusConfig[node.status].bgColor} border-white/10`}>
                    <div className="flex items-start gap-4">
                      {/* Status Indicator */}
                      <div className="relative flex-shrink-0">
                        <div
                          className={`w-12 h-12 rounded-full ${statusConfig[node.status].color} flex items-center justify-center text-2xl shadow-lg ${statusConfig[node.status].glow} ${
                            statusConfig[node.status].pulse ? 'animate-pulse' : ''
                          }`}
                        >
                          {node.icon}
                        </div>
                        {/* Glowing ring for operational status */}
                        {node.status === 'operational' && (
                          <div className="absolute inset-0 rounded-full bg-emerald-500/20 animate-ping" />
                        )}
                      </div>

                      {/* Node Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <h3 className="text-white font-semibold text-sm">{node.name}</h3>
                          <span className="text-xs text-white/50">{node.latency}</span>
                        </div>
                        <p className="text-white/60 text-xs mb-1">{node.description}</p>
                        {node.details && (
                          <p className="text-white/40 text-xs">{node.details}</p>
                        )}
                        <div className="mt-2">
                          <span
                            className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-medium ${statusConfig[node.status].color} bg-white/10`}
                          >
                            {statusConfig[node.status].label}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Footer Stats */}
            <div className="mt-6 pt-4 border-t border-white/10 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-white/60">Live Monitoring</span>
              </div>
              <span className="text-white/40">
                Last update: {new Date().toLocaleTimeString()}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemStatusMonitor;
