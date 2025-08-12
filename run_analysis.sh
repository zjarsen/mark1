#!/bin/bash

# Mantle Trading Platform - Quick Analysis Runner
# Runs the trading analysis and opens dashboard

echo "📊 Mantle Trading Strategy Analysis"
echo "===================================="

# Check if in correct directory
if [ ! -d "backend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Run analysis
echo "🔄 Running analysis with current criteria..."
cd backend
python3 mantle_csv_system_simple.py
cd ..

echo ""
echo "✅ Analysis complete!"
echo "📈 Results saved to: data/post_evaluations.csv"
echo "⚙️ Criteria used: config/evaluation_criteria.json"
echo ""
echo "🌐 View results at: http://localhost:8000/frontend/mantle_dashboard.html"
echo ""
echo "To start the dashboard server, run: ./run_server.sh"