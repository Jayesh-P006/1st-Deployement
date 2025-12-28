# System Status Monitor - React Component

A beautiful, glassmorphism-styled floating dashboard widget for monitoring your Social Media Scheduler pipeline.

## 🎨 Features

- **Glassmorphism Design**: Translucent dark background with backdrop blur
- **Draggable**: Click and drag from the header to reposition
- **Minimizable**: Click the minimize button to collapse/expand
- **Pipeline Visualization**: Connected nodes showing data flow
- **Animated Status**: Real-time status indicators with glowing effects
- **Responsive**: Adapts to different screen sizes

## 📦 Installation

### 1. Install Dependencies

```bash
npm install react
# or
yarn add react
```

### 2. Tailwind CSS Setup

Make sure your `tailwind.config.js` includes:

```js
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      animation: {
        'pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ping': 'ping 1s cubic-bezier(0, 0, 0.2, 1) infinite',
      },
      backdropBlur: {
        xl: '20px',
      },
    },
  },
  plugins: [],
}
```

### 3. Add Component

Copy `SystemStatusMonitor.jsx` to your project.

## 🚀 Usage

### Basic Usage

```jsx
import SystemStatusMonitor from './components/SystemStatusMonitor';

function App() {
  return (
    <div className="min-h-screen bg-gray-900">
      {/* Your app content */}
      <SystemStatusMonitor />
    </div>
  );
}
```

### With Custom Initial Position

```jsx
// Modify the initial state in SystemStatusMonitor.jsx
const [position, setPosition] = useState({ 
  x: 20,  // 20px from left
  y: 20   // 20px from top
});
```

## 🎛️ Status Types

The component supports three status types:

1. **Operational** (Green)
   - Glowing green indicator
   - Smooth animations
   - Shows system is running normally

2. **Processing** (Yellow)
   - Pulsing yellow indicator
   - Animated connection lines
   - Shows system is actively working

3. **Down** (Red)
   - Pulsing red alert
   - Dashed connection lines
   - Shows system failure or offline

## 🔧 Customization

### Change Node Data

Modify the `systemNodes` state in `SystemStatusMonitor.jsx`:

```jsx
const [systemNodes, setSystemNodes] = useState([
  {
    id: 'your-node',
    name: 'Your Service Name',
    icon: '🚀',  // Any emoji
    status: 'operational',  // operational | processing | down
    latency: '50ms',
    description: 'Service description',
    details: 'Additional info'
  },
  // ... more nodes
]);
```

### Change Colors

Update `statusConfig` object:

```jsx
const statusConfig = {
  operational: {
    color: 'bg-blue-500',      // Change color
    glow: 'shadow-blue-500/50',
    pulse: false,
    label: 'Online',
    bgColor: 'bg-blue-500/10'
  },
  // ... other statuses
};
```

### Adjust Size

Change the container width in the JSX:

```jsx
<div className="w-96 p-6">  {/* Change w-96 to w-80, w-[500px], etc. */}
```

## 🔗 Integration with Real API

Replace mock data with real API calls:

```jsx
useEffect(() => {
  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/system-status');
      const data = await response.json();
      
      setSystemNodes(prevNodes =>
        prevNodes.map(node => ({
          ...node,
          status: data[node.id]?.status || 'down',
          latency: data[node.id]?.latency || 'N/A',
          details: data[node.id]?.details
        }))
      );
    } catch (error) {
      console.error('Failed to fetch status:', error);
    }
  };

  // Poll every 5 seconds
  const interval = setInterval(fetchStatus, 5000);
  fetchStatus(); // Initial fetch

  return () => clearInterval(interval);
}, []);
```

## 📊 Backend API Example

Your Flask backend should return:

```python
@app.route('/api/system-status')
def system_status():
    return jsonify({
        'vector-db': {
            'status': 'operational',
            'latency': '45ms',
            'details': '1,247 vectors'
        },
        'ai-engine': {
            'status': 'processing',
            'latency': '234ms',
            'details': 'Processing 3 requests'
        },
        # ... other nodes
    })
```

## 🎨 Style Variants

### Horizontal Layout

Change the flex direction in the pipeline section:

```jsx
<div className="flex gap-6 overflow-x-auto">
  {/* Nodes will be horizontal */}
</div>
```

### Different Theme

```jsx
// Light theme variant
<div className="backdrop-blur-xl bg-white/40 border border-gray-300">
  {/* Content with dark text colors */}
</div>
```

## 🐛 Troubleshooting

**Widget not draggable?**
- Ensure the drag-handle class is on the header element
- Check that mouse events are not blocked by other elements

**Animations not working?**
- Verify Tailwind CSS animations are properly configured
- Check browser compatibility for backdrop-filter

**Status not updating?**
- Verify your API endpoint is returning correct data
- Check console for fetch errors
- Ensure polling interval is set correctly

## 📝 License

MIT - Feel free to use in your projects!

## 🙏 Credits

Created for Social Media Scheduler application
Design inspiration: Glassmorphism UI trend
