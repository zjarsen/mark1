#!/bin/bash

# Mantle Trading Platform - Development Server
# Starts local HTTP server for the dashboard

echo "🚀 Starting Mantle Trading Platform..."
echo "📁 Project Directory: $(pwd)"
echo ""

# Check if in correct directory
if [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "Expected structure:"
    echo "  frontend/"
    echo "  backend/"
    echo "  config/"
    echo "  data/"
    exit 1
fi

# Start HTTP server
echo "🌐 Starting HTTP server on port 8000..."
echo "📊 Dashboard URL: http://localhost:8000/frontend/mantle_dashboard.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo "----------------------------------------"

python3 -m http.server 8000