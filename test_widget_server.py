# Quick Test Flask Server for System Status Widget
# Run this to test the widget without full build setup

from flask import Flask, render_template_string, jsonify
from flask_cors import CORS
import random
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Read the demo HTML
with open('system-status-demo.html', 'r', encoding='utf-8') as f:
    DEMO_HTML = f.read()

@app.route('/')
def index():
    """Serve the demo HTML"""
    return render_template_string(DEMO_HTML)

@app.route('/api/system-status')
def get_system_status():
    """Mock API endpoint with randomized data"""
    
    # Randomly select statuses for demo
    statuses = ['operational', 'operational', 'operational', 'degraded', 'down']
    
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'instaGraphApi': {
            'status': random.choice(statuses),
            'latency': f"{random.randint(100, 300)}ms",
            'rateLimitRemaining': f"{random.randint(70, 95)}%"
        },
        'webhooksConfig': {
            'status': random.choice(statuses),
            'activeHooks': random.randint(1, 5),
            'lastEvent': f"{random.randint(1, 30)}m ago"
        },
        'sqlDatabase': {
            'status': random.choice(statuses),
            'activeConnections': random.randint(5, 20),
            'latency': f"{random.randint(5, 50)}ms"
        },
        'groqCloud': {
            'status': random.choice(statuses),
            'model': 'llama-3.1-70b',
            'latency': f"{random.randint(200, 400)}ms"
        },
        'pinecone': {
            'status': random.choice(statuses),
            'index': 'social-vectors',
            'totalVectors': f"{random.randint(10000, 20000):,}",
            'latency': f"{random.randint(30, 100)}ms"
        },
        'scheduler': {
            'status': random.choice(statuses),
            'jobsQueued': random.randint(3, 15),
            'nextRun': f"{random.randint(5, 60)}m"
        },
        'automation': {
            'status': random.choice(statuses),
            'lastTriggered': f"{random.randint(1, 30)}m ago",
            'successRate': f"{random.randint(85, 99)}%"
        },
        'geminiApi': {
            'status': random.choice(statuses),
            'latency': f"{random.randint(150, 300)}ms",
            'quotaUsedToday': f"{random.randint(10, 50)}%"
        },
        'llumaAi': {
            'status': random.choice(statuses),
            'latency': f"{random.randint(100, 250)}ms",
            'modelVersion': 'v2.3.1'
        }
    })

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║  🚀 Advanced System Status Widget - Test Server         ║
    ╠══════════════════════════════════════════════════════════╣
    ║                                                          ║
    ║  Server running at: http://localhost:5555                ║
    ║                                                          ║
    ║  Features:                                               ║
    ║  ✅ Live demo of the status widget                       ║
    ║  ✅ Mock API with randomized data                        ║
    ║  ✅ Updates every 30 seconds                             ║
    ║  ✅ No build tools required                              ║
    ║                                                          ║
    ║  Press Ctrl+C to stop the server                         ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    app.run(debug=True, port=5555, host='0.0.0.0')
