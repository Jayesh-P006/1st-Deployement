# Visual Layout Reference - Advanced System Status Widget

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚡ System Architecture Monitor                                        [—]  ║
║  Real-time network visualization                                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   ┌─────────────────┐         ┌─────────────────┐         ┌──────────────┐║
║   │  🗄️ SQL Database │         │  🧠 Groq Cloud  │         │ 📱 Instagram │║
║   │  ● Operational   │         │  ● Operational  │         │ ● Operational│║
║   │  Connections: 12 │ ─────>  │  Model: llama   │ ─────>  │ Latency: 142 │║
║   │  Latency: 8ms    │         │  Latency: 234ms │         │ Rate: 87%    │║
║   └─────────────────┘         └─────────────────┘         └──────────────┘║
║          │                             │                           │        ║
║          │                             │                           │        ║
║          v                             v                           v        ║
║   ┌─────────────────┐         ┌─────────────────┐         ┌──────────────┐║
║   │  🔷 Pinecone    │         │  ✨ Gemini API  │         │ ⏰ Scheduler  │║
║   │  ● Operational   │         │  ● Operational  │         │ ● Operational│║
║   │  Index: social   │ ─────>  │  Latency: 189ms │ ─────>  │ Jobs: 7      │║
║   │  Vectors: 12,847 │         │  Quota: 23%     │         │ Next: 15m    │║
║   └─────────────────┘         └─────────────────┘         └──────────────┘║
║          │                             │                                    ║
║          │                             │                                    ║
║          v                             v                                    ║
║   ┌─────────────────┐         ┌─────────────────┐                         ║
║   │  🔗 Webhooks    │         │  🤖 Lluma AI    │                         ║
║   │  ● Operational   │         │  ● Operational  │                         ║
║   │  Active: 3       │ ─────>  │  Latency: 156ms │ ─────>  ┌──────────────┐║
║   │  Last: 2m ago    │         │  Ver: v2.3.1    │         │ ⚡ Automation│║
║   └─────────────────┘         └─────────────────┘         │ ● Degraded   │║
║                                                            │ Last: 5m ago │║
║   DATABASE CLUSTER          AI SERVICES                   │ Success: 94% │║
║                                                            └──────────────┘║
║                                                        WORKFLOWS & APIs     ║
║                                                                              ║
║                                                     [Legend]                 ║
║                                                     ● Operational            ║
║                                                     ● Degraded               ║
║                                                     ● Down                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

DIMENSIONS: 850px × 700px
POSITION: Top-right by default (draggable)
Z-INDEX: 9999 (always on top)
```

## Color Coding

### Status Indicators

**🟢 Operational** (Green Pulse)
```
Color: #10b981 (Emerald 500)
Animation: Steady pulse (2s cycle)
Meaning: System running normally
```

**🟡 Degraded** (Yellow Spinner)
```
Color: #f59e0b (Amber 500)
Animation: Continuous rotation
Meaning: Performance issues detected
```

**🔴 Down** (Red Flash)
```
Color: #ef4444 (Red 500)
Animation: Expanding ping (1s cycle)
Meaning: Critical error or offline
```

### Node Glow Colors

**Database Cluster** (Left Column)
- SQL Database: Blue → Cyan gradient
- Pinecone: Purple → Pink gradient
- Webhooks: Emerald → Teal gradient

**AI Services** (Middle Column)
- Groq Cloud: Orange → Red gradient
- Gemini API: Blue → Indigo gradient
- Lluma AI: Violet → Purple gradient

**Workflows & APIs** (Right Column)
- Instagram API: Pink → Rose gradient
- Scheduler: Yellow → Amber gradient
- Automation: Cyan → Blue gradient

## Connection Lines

```
Style: Glowing SVG lines with gradient
Color: Emerald 500 → Blue 500
Animation: Particles flowing along paths
Thickness: 2px with blur filter
```

## Glassmorphism Effect

```css
Background: Linear gradient
  - from-slate-900/80 (dark with 80% opacity)
  - via-purple-900/60 (purple with 60% opacity)
  - to-slate-900/80 (dark with 80% opacity)

Backdrop: Blur (2xl = 40px blur radius)
Border: White with 20% opacity
Shadow: Multiple layered shadows (2xl)
```

## Node Card Structure

```
┌────────────────────────────────────┐
│ [Icon] [●] [Title]                │ ← Header with status
│                                    │
│   Detail 1: Value                  │ ← Metric rows
│   Detail 2: Value                  │ ← (font-mono)
│   Detail 3: Value                  │
└────────────────────────────────────┘
         ↑
    Glow effect on hover
```

## Header Bar

```
┌────────────────────────────────────────────────────┐
│ [⚡] System Architecture Monitor              [—] │
│     Real-time network visualization               │
└────────────────────────────────────────────────────┘
       ↑                                         ↑
   Logo/Icon                              Minimize button
   
Background: Semi-transparent slate with backdrop blur
Cursor: Move (indicates draggable)
```

## Minimized State

```
    ┌─────────┐
    │    ⚡   │  ← 64×64px pulse icon
    │         │
    └─────────┘
       ↑
   Click to expand
   Pulse animation
   Gradient background
```

## Layout Coordinates

### Database Cluster (Left)
- SQL Database: `top-[20px] left-[20px]`
- Pinecone: `top-[140px] left-[20px]`
- Webhooks: `top-[260px] left-[20px]`

### AI Services (Middle)
- Groq Cloud: `top-[20px] left-[280px]`
- Gemini API: `top-[140px] left-[280px]`
- Lluma AI: `top-[260px] left-[280px]`

### Workflows & APIs (Right)
- Instagram API: `top-[20px] left-[540px]`
- Scheduler: `top-[140px] left-[540px]`
- Automation: `top-[340px] left-[540px]`

## Spacing & Sizing

```
Widget:           850px × 700px
Node Cards:       min-width 220px, auto height
Node Spacing:     120px vertical, 260px horizontal
Icon Size:        24px (text-2xl)
Status Dot:       8px diameter (w-2 h-2)
Border Radius:    
  - Widget: 16px (rounded-2xl)
  - Nodes: 12px (rounded-xl)
  - Header: 8px (rounded-lg)
```

## Typography

```
Widget Title:     18px, bold, white
Widget Subtitle:  12px, regular, slate-400
Node Title:       14px, semibold, white
Node Metrics:     12px, mono, slate-300/80
Cluster Labels:   12px, semibold, slate-400, uppercase
```

## Hover Effects

```css
Node Card:
  - Scale: 1 → 1.05
  - Glow opacity: 0.3 → 0.5
  - Transition: 300ms

Header Button:
  - Background: transparent → white/10
  - Transition: colors

Minimized Icon:
  - Scale: 1 → 1.1
  - Cursor: pointer
```

## Animation Timing

```
Pulse (Operational):    2s infinite
Spin (Degraded):        1s infinite linear
Ping (Down):            1s infinite cubic-bezier
Particle Flow:          3-5s infinite along path
Hover Scale:            300ms ease
Drag Movement:          Instant (no transition)
```

## Z-Index Layers

```
Background Pattern:     1
Connection Lines:       5
Service Nodes:          10
Header Bar:             20
Entire Widget:          9999 (always on top)
```

## Responsive Behavior

```
Desktop (>= 1024px):    Full widget (850×700)
Tablet (768-1023px):    Scaled down (70%)
Mobile (< 768px):       Hidden or minimal view
                        (recommend full-screen modal)
```

## Accessibility Features

```
Contrast Ratios:        All text meets WCAG AA
Status Colors:          Distinct for colorblind users
Cursor Indicators:      Shows draggable/clickable areas
Semantic HTML:          Proper heading hierarchy
Keyboard Support:       [TODO] Add keyboard shortcuts
```

## Performance Considerations

```
SVG Animations:         GPU-accelerated
Backdrop Blur:          CSS filter (modern browsers)
Re-renders:             Optimized with React memo
Particle Count:         Limited to 3-5 for performance
Update Frequency:       30 seconds (configurable)
```

## Browser Compatibility

```
✅ Chrome/Edge 90+      Full support
✅ Firefox 88+          Full support  
✅ Safari 14+           Full support
⚠️  IE 11               Not supported (no backdrop-blur)
```

---

## Quick Customization Examples

### Change to Blue Theme
```jsx
// Main container
"bg-gradient-to-br from-blue-900/80 via-indigo-900/60 to-blue-900/80"
```

### Adjust Initial Position
```jsx
{ x: window.innerWidth - 900, y: 50 }  // Top-right
{ x: 50, y: 50 }                       // Top-left
{ x: 50, y: window.innerHeight - 750 } // Bottom-left
```

### Modify Node Layout (Vertical Stack)
```jsx
position="top-[50px] left-[20px]"    // Node 1
position="top-[150px] left-[20px]"   // Node 2
position="top-[250px] left-[20px]"   // Node 3
// ... continues vertically
```

---

**This visual reference matches the implementation in `AdvancedSystemStatusWidget.jsx`**
