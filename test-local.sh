#!/bin/bash
# Local testing script - simulates separate hosting (like Vercel + Supabase)
# Runs frontend on :3000 and backend on :8000 separately

set -e

echo "🧪 Testing OCR PDF Application (Separate Hosting Mode)"
echo "========================================================"
echo ""
echo "This simulates how it will work on Vercel + Supabase:"
echo "  - Backend: http://localhost:8000 (API)"
echo "  - Frontend: http://localhost:3000 (React app with Tailwind CSS)"
echo ""
echo "✨ New Features:"
echo "  - Beautiful animated landing page (BackgroundPaths)"
echo "  - Tailwind CSS styling"
echo "  - shadcn/ui components"
echo ""

# Check if we're in project root
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "⚠️  Warning: Port $1 is already in use"
        return 1
    fi
    return 0
}

# Check ports
echo "📡 Checking ports..."
check_port 3000 || echo "   Frontend port 3000 in use - will fail if not available"
check_port 8000 || echo "   Backend port 8000 in use - will fail if not available"
check_port 6379 || echo "   Redis port 6379 in use - this is OK if Redis is running"
echo ""

# Check Redis
echo "🔍 Checking Redis..."
if redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is NOT running!"
    echo ""
    echo "Start Redis first:"
    echo "  docker run -d -p 6379:6379 redis"
    echo ""
    read -p "Do you want to start Redis now with Docker? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting Redis..."
        docker run -d -p 6379:6379 --name ocr-redis redis:7-alpine
        sleep 2
        echo "✅ Redis started"
    else
        echo "Please start Redis manually and run this script again."
        exit 1
    fi
fi
echo ""

# Setup backend
echo "🐍 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "✅ Backend ready"
echo ""

# Setup frontend
echo "📦 Setting up frontend..."
cd ../frontend

# Check if Tailwind CSS dependencies are installed
if [ ! -d "node_modules" ] || [ ! -d "node_modules/tailwindcss" ]; then
    echo "Installing npm dependencies (including Tailwind CSS & shadcn/ui)..."
    npm install
else
    # Check if package.json has been updated recently
    if [ "package.json" -nt "node_modules/.package-lock.json" ] 2>/dev/null || [ ! -f "node_modules/.package-lock.json" ]; then
        echo "New dependencies detected, updating..."
        npm install
    else
        echo "Dependencies already installed"
    fi
fi

echo "✅ Frontend ready with Tailwind CSS & shadcn/ui"
echo ""

# Instructions
echo "========================================================"
echo "✅ Setup complete! Ready to start services."
echo "========================================================"
echo ""
echo "You need to run these in 3 SEPARATE TERMINALS:"
echo ""
echo "Terminal 1 - Backend API:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "Terminal 2 - RQ Worker:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  rq worker app.workers"
echo ""
echo "Terminal 3 - Frontend:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Then open: http://localhost:3000"
echo ""
echo "Would you like me to start all services now?"
read -p "Start all services? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting all services..."
    echo ""
    
    # Create logs directory
    mkdir -p ../logs
    
    # Start backend
    cd ../backend
    source venv/bin/activate
    echo "Starting backend on :8000..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1 &
    BACKEND_PID=$!
    echo "✅ Backend started (PID: $BACKEND_PID)"
    
    # Start worker
    echo "Starting RQ worker..."
    rq worker app.workers > ../logs/worker.log 2>&1 &
    WORKER_PID=$!
    echo "✅ Worker started (PID: $WORKER_PID)"
    
    # Wait for backend to be ready
    echo "Waiting for backend to be ready..."
    sleep 3
    
    # Start frontend
    cd ../frontend
    echo "Starting frontend on :3000..."
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "✅ Frontend started (PID: $FRONTEND_PID)"
    
    # Wait for frontend to be ready
    sleep 3
    
    echo ""
    echo "========================================================"
    echo "🎉 All services are running!"
    echo "========================================================"
    echo ""
    echo "📊 Service Status:"
    echo "  - Backend API:  http://localhost:8000 (PID: $BACKEND_PID)"
    echo "  - API Docs:     http://localhost:8000/docs"
    echo "  - RQ Worker:    Running (PID: $WORKER_PID)"
    echo "  - Frontend:     http://localhost:3000 (PID: $FRONTEND_PID)"
    echo ""
    echo "🎨 Pages Available:"
    echo "  - Home (Landing):  http://localhost:3000/"
    echo "  - Search:          http://localhost:3000/search"
    echo "  - Settings:        http://localhost:3000/settings"
    echo ""
    echo "📝 Logs:"
    echo "  - Backend:  tail -f logs/backend.log"
    echo "  - Worker:   tail -f logs/worker.log"
    echo "  - Frontend: tail -f logs/frontend.log"
    echo ""
    echo "🛑 To stop all services:"
    echo "  kill $BACKEND_PID $WORKER_PID $FRONTEND_PID"
    echo ""
    echo "Or use: pkill -f 'uvicorn|rq worker|vite'"
    echo ""
    
    # Save PIDs to file
    echo "$BACKEND_PID" > ../logs/pids.txt
    echo "$WORKER_PID" >> ../logs/pids.txt
    echo "$FRONTEND_PID" >> ../logs/pids.txt
    
    echo "Opening browser in 3 seconds..."
    sleep 3
    
    # Try to open browser
    if command -v open >/dev/null 2>&1; then
        open http://localhost:3000
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open http://localhost:3000
    else
        echo "Please open http://localhost:3000 in your browser"
    fi
    
    echo ""
    echo "Press Ctrl+C to view logs, or close this terminal when done."
    echo ""
    
    # Tail the logs
    tail -f ../logs/backend.log ../logs/worker.log ../logs/frontend.log
else
    echo ""
    echo "OK! Start the services manually using the commands above."
    echo ""
fi

