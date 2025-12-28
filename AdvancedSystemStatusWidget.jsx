import React, { useState, useRef, useEffect } from 'react';

/**
 * Advanced System Status Widget
 * 
 * A premium floating, draggable system status dashboard with glassmorphism design
 * and network visualization layout for monitoring complex social media automation.
 * 
 * Features:
 * - Glassmorphism UI with frosted glass effect
 * - Fully draggable and floating (high z-index)
 * - Minimizable to pulse icon
 * - Network/circuit board layout with glowing connection lines
 * - Animated status indicators (green pulse, yellow spinner, red flash)
 * - 9 distinct service nodes with detailed metrics
 */

const AdvancedSystemStatusWidget = ({ systemState = {} }) => {
  // Widget UI state
  const [isMinimized, setIsMinimized] = useState(false);
  const [position, setPosition] = useState({ x: window.innerWidth - 900, y: 50 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const widgetRef = useRef(null);

  // Parse system state with fallback defaults
  const parseSystemState = () => {
    return {
      instaGraphApi: {
        status: systemState?.instaGraphApi?.status || 'operational',
        latency: systemState?.instaGraphApi?.latency || '142ms',
        rateLimitRemaining: systemState?.instaGraphApi?.rateLimitRemaining || '87%'
      },
      webhooksConfig: {
        status: systemState?.webhooksConfig?.status || 'operational',
        activeHooks: systemState?.webhooksConfig?.activeHooks || 3,
        lastEvent: systemState?.webhooksConfig?.lastEvent || '2m ago'
      },
      sqlDatabase: {
        status: systemState?.sqlDatabase?.status || 'operational',
        activeConnections: systemState?.sqlDatabase?.activeConnections || 12,
        latency: systemState?.sqlDatabase?.latency || '8ms'
      },
      groqCloud: {
        status: systemState?.groqCloud?.status || 'operational',
        model: systemState?.groqCloud?.model || 'llama-3.1-70b',
        latency: systemState?.groqCloud?.latency || '234ms'
      },
      pinecone: {
        status: systemState?.pinecone?.status || 'operational',
        index: systemState?.pinecone?.index || 'social-vectors',
        totalVectors: systemState?.pinecone?.totalVectors || '12,847',
        latency: systemState?.pinecone?.latency || '45ms'
      },
      scheduler: {
        status: systemState?.scheduler?.status || 'operational',
        jobsQueued: systemState?.scheduler?.jobsQueued || 7,
        nextRun: systemState?.scheduler?.nextRun || '15m'
      },
      automation: {
        status: systemState?.automation?.status || 'degraded',
        lastTriggered: systemState?.automation?.lastTriggered || '5m ago',
        successRate: systemState?.automation?.successRate || '94%'
      },
      geminiApi: {
        status: systemState?.geminiApi?.status || 'operational',
        latency: systemState?.geminiApi?.latency || '189ms',
        quotaUsedToday: systemState?.geminiApi?.quotaUsedToday || '23%'
      },
      llumaAi: {
        status: systemState?.llumaAi?.status || 'operational',
        latency: systemState?.llumaAi?.latency || '156ms',
        modelVersion: systemState?.llumaAi?.modelVersion || 'v2.3.1'
      }
    };
  };

  const services = parseSystemState();

  // Drag functionality
  useEffect(() => {
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

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, dragOffset]);

  const handleMouseDown = (e) => {
    if (e.target.closest('.drag-handle')) {
      const rect = widgetRef.current.getBoundingClientRect();
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      });
      setIsDragging(true);
    }
  };

  // Status indicator component
  const StatusIndicator = ({ status }) => {
    const statusStyles = {
      operational: {
        bg: 'bg-emerald-500',
        animation: 'animate-pulse',
        shadow: 'shadow-lg shadow-emerald-500/50',
        label: 'Operational'
      },
      degraded: {
        bg: 'bg-yellow-500',
        animation: 'animate-spin',
        shadow: 'shadow-lg shadow-yellow-500/50',
        label: 'Degraded'
      },
      down: {
        bg: 'bg-red-500',
        animation: 'animate-ping',
        shadow: 'shadow-lg shadow-red-500/50',
        label: 'Down'
      }
    };

    const style = statusStyles[status] || statusStyles.operational;

    return (
      <div className="relative inline-flex items-center justify-center w-3 h-3">
        <div className={`absolute w-3 h-3 rounded-full ${style.bg} ${style.animation} opacity-75`}></div>
        <div className={`relative w-2 h-2 rounded-full ${style.bg} ${style.shadow}`}></div>
      </div>
    );
  };

  // Service Node Component
  const ServiceNode = ({ title, status, icon, details, position, glowColor }) => (
    <div 
      className={`absolute ${position} transform transition-all duration-300 hover:scale-105`}
      style={{ zIndex: 10 }}
    >
      <div className="relative group">
        {/* Glow effect */}
        <div className={`absolute inset-0 bg-gradient-to-br ${glowColor} rounded-xl blur-xl opacity-30 group-hover:opacity-50 transition-opacity`}></div>
        
        {/* Node card */}
        <div className="relative bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-xl p-4 min-w-[220px] shadow-2xl">
          <div className="flex items-start gap-3">
            <div className="text-2xl mt-1">{icon}</div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <StatusIndicator status={status} />
                <h3 className="text-white font-semibold text-sm">{title}</h3>
              </div>
              <div className="space-y-1">
                {details.map((detail, idx) => (
                  <p key={idx} className="text-xs text-slate-300/80 font-mono">
                    {detail}
                  </p>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Connection Line SVG Component
  const ConnectionLine = ({ from, to, active = true }) => (
    <svg
      className="absolute inset-0 pointer-events-none"
      style={{ zIndex: 5 }}
    >
      <defs>
        <linearGradient id={`gradient-${from}-${to}`} x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={active ? "#10b981" : "#475569"} stopOpacity="0.6" />
          <stop offset="100%" stopColor={active ? "#3b82f6" : "#475569"} stopOpacity="0.3" />
        </linearGradient>
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge>
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>
      <line
        x1={from.x}
        y1={from.y}
        x2={to.x}
        y2={to.y}
        stroke={`url(#gradient-${from.x}-${to.x})`}
        strokeWidth="2"
        filter="url(#glow)"
        className={active ? "animate-pulse" : ""}
      />
      {active && (
        <circle r="4" fill="#10b981" filter="url(#glow)">
          <animateMotion
            dur="3s"
            repeatCount="indefinite"
            path={`M ${from.x} ${from.y} L ${to.x} ${to.y}`}
          />
        </circle>
      )}
    </svg>
  );

  // Minimized pulse icon
  if (isMinimized) {
    return (
      <div
        ref={widgetRef}
        style={{
          position: 'fixed',
          left: `${position.x}px`,
          top: `${position.y}px`,
          zIndex: 9999,
          cursor: isDragging ? 'grabbing' : 'grab'
        }}
        onMouseDown={handleMouseDown}
        className="drag-handle"
      >
        <div
          onClick={() => setIsMinimized(false)}
          className="relative w-16 h-16 bg-gradient-to-br from-purple-600 to-blue-600 rounded-full shadow-2xl cursor-pointer hover:scale-110 transition-transform"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full animate-pulse opacity-50"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
        </div>
      </div>
    );
  }

  // Full dashboard view
  return (
    <div
      ref={widgetRef}
      style={{
        position: 'fixed',
        left: `${position.x}px`,
        top: `${position.y}px`,
        zIndex: 9999,
        width: '850px',
        height: '700px'
      }}
      onMouseDown={handleMouseDown}
    >
      {/* Main glassmorphism container */}
      <div className="relative w-full h-full bg-gradient-to-br from-slate-900/80 via-purple-900/60 to-slate-900/80 backdrop-blur-2xl border border-white/20 rounded-2xl shadow-2xl overflow-hidden">
        
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute inset-0" style={{
            backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)',
            backgroundSize: '40px 40px'
          }}></div>
        </div>

        {/* Header bar - draggable */}
        <div className="drag-handle relative z-20 flex items-center justify-between px-6 py-4 bg-slate-900/40 backdrop-blur-sm border-b border-white/10 cursor-move">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-emerald-500 to-blue-500 rounded-lg blur-md opacity-50"></div>
              <div className="relative bg-gradient-to-r from-emerald-500 to-blue-500 p-2 rounded-lg">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            </div>
            <div>
              <h2 className="text-white font-bold text-lg">System Architecture Monitor</h2>
              <p className="text-slate-400 text-xs">Real-time network visualization</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsMinimized(true)}
              className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            </button>
          </div>
        </div>

        {/* Network visualization area */}
        <div className="relative h-[calc(100%-76px)] p-8 overflow-hidden">
          
          {/* SVG Connection lines layer */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 1 }}>
            <defs>
              <linearGradient id="line-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#10b981" stopOpacity="0.6" />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.3" />
              </linearGradient>
              <filter id="glow">
                <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>
            
            {/* Database cluster connections */}
            <line x1="150" y1="100" x2="150" y2="200" stroke="url(#line-gradient)" strokeWidth="2" filter="url(#glow)" className="animate-pulse" />
            <line x1="150" y1="200" x2="150" y2="300" stroke="url(#line-gradient)" strokeWidth="2" filter="url(#glow)" className="animate-pulse" />
            
            {/* AI cluster connections */}
            <line x1="425" y1="100" x2="425" y2="200" stroke="url(#line-gradient)" strokeWidth="2" filter="url(#glow)" className="animate-pulse" />
            <line x1="425" y1="200" x2="425" y2="300" stroke="url(#line-gradient)" strokeWidth="2" filter="url(#glow)" className="animate-pulse" />
            
            {/* APIs cluster connections */}
            <line x1="675" y1="100" x2="675" y2="200" stroke="url(#line-gradient)" strokeWidth="2" filter="url(#glow)" className="animate-pulse" />
            
            {/* Cross-cluster connections */}
            <line x1="250" y1="150" x2="350" y2="150" stroke="url(#line-gradient)" strokeWidth="2" filter="url(#glow)" className="animate-pulse" />
            <line x1="250" y1="250" x2="350" y2="250" stroke="url(#line-gradient)" strokeWidth="2" filter="url(#glow)" className="animate-pulse" />
            <line x1="525" y1="150" x2="600" y2="150" stroke="url(#line-gradient)" strokeWidth="2" filter="url(#glow)" className="animate-pulse" />
            <line x1="525" y1="250" x2="600" y2="400" stroke="url(#line-gradient)" strokeWidth="2" filter="url(#glow)" className="animate-pulse" />
            
            {/* Animated flow particles */}
            <circle r="4" fill="#10b981" filter="url(#glow)">
              <animateMotion dur="4s" repeatCount="indefinite" path="M 150 100 L 150 300" />
            </circle>
            <circle r="4" fill="#3b82f6" filter="url(#glow)">
              <animateMotion dur="3s" repeatCount="indefinite" path="M 250 150 L 350 150" />
            </circle>
            <circle r="4" fill="#8b5cf6" filter="url(#glow)">
              <animateMotion dur="5s" repeatCount="indefinite" path="M 425 100 L 425 300" />
            </circle>
          </svg>

          {/* Service nodes positioned in network layout */}
          
          {/* DATABASE CLUSTER (Left column) */}
          <ServiceNode
            title="SQL Database"
            status={services.sqlDatabase.status}
            icon="🗄️"
            details={[
              `Connections: ${services.sqlDatabase.activeConnections}`,
              `Latency: ${services.sqlDatabase.latency}`,
              `Status: ${services.sqlDatabase.status}`
            ]}
            position="top-[20px] left-[20px]"
            glowColor="from-blue-500 to-cyan-500"
          />
          
          <ServiceNode
            title="Pinecone Status"
            status={services.pinecone.status}
            icon="🔷"
            details={[
              `Index: ${services.pinecone.index}`,
              `Vectors: ${services.pinecone.totalVectors}`,
              `Latency: ${services.pinecone.latency}`
            ]}
            position="top-[140px] left-[20px]"
            glowColor="from-purple-500 to-pink-500"
          />
          
          <ServiceNode
            title="Webhooks Config"
            status={services.webhooksConfig.status}
            icon="🔗"
            details={[
              `Active Hooks: ${services.webhooksConfig.activeHooks}`,
              `Last Event: ${services.webhooksConfig.lastEvent}`,
              `Status: ${services.webhooksConfig.status}`
            ]}
            position="top-[260px] left-[20px]"
            glowColor="from-emerald-500 to-teal-500"
          />

          {/* AI CLUSTER (Middle column) */}
          <ServiceNode
            title="Groq Cloud Status"
            status={services.groqCloud.status}
            icon="🧠"
            details={[
              `Model: ${services.groqCloud.model}`,
              `Latency: ${services.groqCloud.latency}`,
              `Status: ${services.groqCloud.status}`
            ]}
            position="top-[20px] left-[280px]"
            glowColor="from-orange-500 to-red-500"
          />
          
          <ServiceNode
            title="Gemini API Status"
            status={services.geminiApi.status}
            icon="✨"
            details={[
              `Latency: ${services.geminiApi.latency}`,
              `Quota: ${services.geminiApi.quotaUsedToday}`,
              `Status: ${services.geminiApi.status}`
            ]}
            position="top-[140px] left-[280px]"
            glowColor="from-blue-500 to-indigo-500"
          />
          
          <ServiceNode
            title="Lluma AI API"
            status={services.llumaAi.status}
            icon="🤖"
            details={[
              `Latency: ${services.llumaAi.latency}`,
              `Version: ${services.llumaAi.modelVersion}`,
              `Status: ${services.llumaAi.status}`
            ]}
            position="top-[260px] left-[280px]"
            glowColor="from-violet-500 to-purple-500"
          />

          {/* WORKFLOWS & APIs CLUSTER (Right column) */}
          <ServiceNode
            title="Insta Graph API"
            status={services.instaGraphApi.status}
            icon="📱"
            details={[
              `Latency: ${services.instaGraphApi.latency}`,
              `Rate Limit: ${services.instaGraphApi.rateLimitRemaining}`,
              `Status: ${services.instaGraphApi.status}`
            ]}
            position="top-[20px] left-[540px]"
            glowColor="from-pink-500 to-rose-500"
          />
          
          <ServiceNode
            title="Scheduler Workflow"
            status={services.scheduler.status}
            icon="⏰"
            details={[
              `Jobs Queued: ${services.scheduler.jobsQueued}`,
              `Next Run: ${services.scheduler.nextRun}`,
              `Status: ${services.scheduler.status}`
            ]}
            position="top-[140px] left-[540px]"
            glowColor="from-yellow-500 to-amber-500"
          />
          
          <ServiceNode
            title="Automation Workflow"
            status={services.automation.status}
            icon="⚡"
            details={[
              `Last: ${services.automation.lastTriggered}`,
              `Success: ${services.automation.successRate}`,
              `Status: ${services.automation.status}`
            ]}
            position="top-[340px] left-[540px]"
            glowColor="from-cyan-500 to-blue-500"
          />

          {/* Cluster labels */}
          <div className="absolute bottom-4 left-4 text-slate-400 text-xs font-semibold tracking-wider">
            DATABASE CLUSTER
          </div>
          <div className="absolute bottom-4 left-[300px] text-slate-400 text-xs font-semibold tracking-wider">
            AI SERVICES
          </div>
          <div className="absolute bottom-4 right-4 text-slate-400 text-xs font-semibold tracking-wider">
            WORKFLOWS & APIs
          </div>

        </div>

        {/* Status legend */}
        <div className="absolute bottom-20 right-8 bg-slate-900/60 backdrop-blur-xl border border-white/10 rounded-lg p-3 space-y-2">
          <div className="flex items-center gap-2 text-xs text-slate-300">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span>Operational</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-300">
            <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
            <span>Degraded</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-300">
            <div className="w-2 h-2 rounded-full bg-red-500 animate-ping"></div>
            <span>Down</span>
          </div>
        </div>

      </div>

      {/* Custom animations */}
      <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes ping {
          0% { transform: scale(1); opacity: 1; }
          75%, 100% { transform: scale(2); opacity: 0; }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default AdvancedSystemStatusWidget;
