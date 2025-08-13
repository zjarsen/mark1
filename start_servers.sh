#!/bin/bash
# Start both backend API and frontend servers for Mantle Trading Dashboard

echo "🚀 Starting Mantle Trading System Servers..."

# Kill any existing processes on these ports
echo "🧹 Cleaning up existing processes..."
pkill -f "python.*api_server.py" 2>/dev/null || true
pkill -f "python.*-m http.server" 2>/dev/null || true

# Start backend API server
echo "🔧 Starting backend API server on port 5000..."
cd backend
python3 api_server.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Start frontend server
echo "🌐 Starting frontend server on port 8000..."
python3 -m http.server 8000 &
FRONTEND_PID=$!

echo ""
echo "✅ Servers started successfully!"
echo ""
echo "📡 Backend API: http://localhost:5000"
echo "   - Health check: http://localhost:5000/api/health"
echo "   - API endpoints ready for dashboard"
echo ""
echo "🌐 Frontend Dashboard: http://localhost:8000/frontend/mantle_dashboard.html"
echo "   - Open this URL in your browser"
echo "   - Dashboard will connect to backend automatically"
echo ""
echo "🔑 To use the system:"
echo "   1. Open the dashboard URL in your browser"
echo "   2. Click 'Check API Status' and enter your TwitterAPI.io key"
echo "   3. Configure your data pull settings"
echo "   4. Start pulling real data!"
echo ""
echo "🛑 To stop servers:"
echo "   - Press Ctrl+C in this terminal"
echo "   - Or run: pkill -f 'python.*api_server.py' && pkill -f 'python.*http.server'"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "✅ Servers stopped."
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT

# Wait for processes to finish
echo "🖥️  Servers running... Press Ctrl+C to stop"
wait