#!/bin/bash
# Stop all running OCR PDF services

echo "🛑 Stopping OCR PDF services..."

# Check for PIDs file
if [ -f "logs/pids.txt" ]; then
    echo "Found PID file, stopping services..."
    while read pid; do
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping process $pid..."
            kill $pid
        fi
    done < logs/pids.txt
    rm logs/pids.txt
fi

# Kill by process name as backup
echo "Cleaning up any remaining processes..."
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "rq worker" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true

echo "✅ All services stopped"
echo ""
echo "Note: Redis container is still running. To stop it:"
echo "  docker stop ocr-redis"
echo "  docker rm ocr-redis"

