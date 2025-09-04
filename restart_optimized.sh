#!/bin/bash

echo "🔄 Restarting AI Ultimate Assistant with optimizations..."

# Kill existing process
echo "📴 Stopping existing server..."
pkill -f "python.*main.py" || true

# Wait a moment
sleep 2

# Start with optimizations
echo "🚀 Starting optimized server..."
python3 start_optimized.py &

echo "✅ Server restarted with optimizations!"
echo "🌐 Access at: http://localhost:8000"
echo "📊 Performance improvements:"
echo "   - Disabled file watching"
echo "   - Added Gmail API caching"
echo "   - Batch API requests"
echo "   - Reduced redundant calls" 