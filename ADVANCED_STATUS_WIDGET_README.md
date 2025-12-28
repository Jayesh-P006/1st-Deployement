# Advanced System Status Widget

A premium, floating system status dashboard with glassmorphism design and network visualization for monitoring complex social media automation architecture.

## 🌟 Features

### Visual Design
- **Glassmorphism Aesthetic**: Premium frosted glass effect with semi-transparent dark backgrounds
- **Subtle Gradients**: Smooth color transitions with glowing shadows
- **Network Visualization**: Circuit board layout showing data flow between components
- **Animated Connections**: Glowing SVG lines with particle flow animations

### Interactivity
- **Fully Draggable**: Move the widget anywhere on screen
- **High Z-Index**: Always stays on top (z-index: 9999)
- **Minimizable**: Collapses to a small pulsing icon
- **Hover Effects**: Service nodes scale up on hover with enhanced glow

### Status Indicators
- **Operational**: Green pulsing dot - System running normally
- **Degraded**: Yellow spinning ring - Performance issues detected
- **Down**: Red flashing alert - Critical errors

## 📊 Monitored Services

The widget displays 9 distinct service nodes organized in 3 clusters:

### Database Cluster (Left)
1. **SQL Database**
   - Active Connections
   - Latency
   - Status

2. **Pinecone Status**
   - Index Name
   - Total Vectors
   - Latency

3. **Webhooks Config**
   - Active Hooks
   - Last Event Time
   - Status

### AI Services (Middle)
4. **Groq Cloud Status**
   - Model Name
   - Latency
   - Status

5. **Gemini API Status**
   - Latency
   - Quota Used Today
   - Status

6. **Lluma AI API**
   - Latency
   - Model Version
   - Status

### Workflows & APIs (Right)
7. **Insta Graph API**
   - Latency
   - Rate Limit Remaining
   - Status

8. **Scheduler Workflow**
   - Jobs Queued
   - Next Run Time
   - Status

9. **Automation Workflow**
   - Last Triggered
   - Success Rate
   - Status

## 🚀 Usage

### Basic Implementation

```jsx
import AdvancedSystemStatusWidget from './AdvancedSystemStatusWidget';

function App() {
  return (
    <div>
      {/* Your main application content */}
      
      {/* Add the floating status widget */}
      <AdvancedSystemStatusWidget />
    </div>
  );
}
```

### With Real-Time Data

```jsx
import { useState, useEffect } from 'react';
import AdvancedSystemStatusWidget from './AdvancedSystemStatusWidget';

function App() {
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

  // Fetch system status from your API
  useEffect(() => {
    const fetchStatus = async () => {
      const response = await fetch('/api/system-status');
      const data = await response.json();
      setSystemState(data);
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Update every 30s

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <AdvancedSystemStatusWidget systemState={systemState} />
    </div>
  );
}
```

## 🎨 Customization

### Positioning
The widget starts at a calculated position but can be dragged anywhere. To change the initial position:

```jsx
const [position, setPosition] = useState({ 
  x: 100,  // Distance from left
  y: 50    // Distance from top
});
```

### Colors & Theme
Modify the glassmorphism colors in the component:

```jsx
// Main container background
className="bg-gradient-to-br from-slate-900/80 via-purple-900/60 to-slate-900/80"

// Node glow colors (passed as props)
glowColor="from-blue-500 to-cyan-500"  // For database nodes
glowColor="from-orange-500 to-red-500" // For AI nodes
glowColor="from-pink-500 to-rose-500"  // For API nodes
```

### Connection Lines
Customize the animated connection lines:

```jsx
<linearGradient id="line-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" stopColor="#10b981" stopOpacity="0.6" />
  <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.3" />
</linearGradient>
```

## 🔧 Technical Details

### Dependencies
- React 18+
- Tailwind CSS 3+

### Browser Support
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

### Performance
- Lightweight: ~15KB gzipped
- Smooth animations using CSS transforms
- Efficient SVG rendering
- No heavy dependencies

## 📱 Responsive Behavior

The widget maintains a fixed size (850x700px) and is designed for desktop/tablet viewing. For mobile:

```jsx
// Add responsive handling
const isMobile = window.innerWidth < 768;

if (isMobile) {
  // Adjust dimensions or hide
  style={{ width: '100vw', height: '60vh' }}
}
```

## 🎯 Status Values

### Valid Status Types
- `"operational"` - Green pulsing indicator
- `"degraded"` - Yellow spinning indicator
- `"down"` - Red flashing indicator

### Data Structure Example

```json
{
  "instaGraphApi": {
    "status": "operational",
    "latency": "142ms",
    "rateLimitRemaining": "87%"
  },
  "webhooksConfig": {
    "status": "operational",
    "activeHooks": 3,
    "lastEvent": "2m ago"
  }
}
```

## 🐛 Troubleshooting

### Widget Not Appearing
- Ensure Tailwind CSS is properly configured
- Check z-index conflicts with other elements
- Verify React version compatibility

### Dragging Not Working
- Make sure the `drag-handle` class is on the header
- Check for CSS pointer-events conflicts
- Verify mouse event handlers are attached

### Animations Not Smooth
- Enable GPU acceleration in browser
- Reduce particle count in SVG animations
- Check for performance issues in browser DevTools

## 🚀 Advanced Features

### Auto-Hide on Scroll
```jsx
const [isVisible, setIsVisible] = useState(true);

useEffect(() => {
  const handleScroll = () => {
    setIsVisible(window.scrollY < 100);
  };
  window.addEventListener('scroll', handleScroll);
  return () => window.removeEventListener('scroll', handleScroll);
}, []);
```

### Keyboard Shortcuts
```jsx
useEffect(() => {
  const handleKeyPress = (e) => {
    if (e.ctrlKey && e.key === 'm') {
      setIsMinimized(!isMinimized);
    }
  };
  window.addEventListener('keydown', handleKeyPress);
  return () => window.removeEventListener('keydown', handleKeyPress);
}, [isMinimized]);
```

### Sound Alerts
```jsx
useEffect(() => {
  if (services.automation.status === 'down') {
    const audio = new Audio('/alert.mp3');
    audio.play();
  }
}, [services.automation.status]);
```

## 📄 License

MIT License - Use freely in your projects

## 🤝 Contributing

Feel free to customize and extend this component for your specific needs!

---

**Built with ❤️ for modern web applications**
