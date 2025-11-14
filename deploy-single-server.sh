#!/bin/bash
# Deploy script for single-server hosting (FastAPI serves React)
# This script builds the frontend and copies it to backend/static/

set -e  # Exit on error

echo "================================================"
echo "OCR PDF - Single Server Deployment"
echo "================================================"
echo ""

# Check if we're in the project root
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Step 1: Build frontend
echo "📦 Step 1: Building frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo "Building React app..."
npm run build

if [ ! -d "dist" ]; then
    echo "❌ Error: Frontend build failed (no dist/ directory)"
    exit 1
fi

echo "✅ Frontend built successfully"
echo ""

# Step 2: Copy to backend
echo "📁 Step 2: Copying frontend to backend/static/..."
cd ..
mkdir -p backend/static
rm -rf backend/static/*
cp -r frontend/dist/* backend/static/

echo "✅ Frontend copied to backend/static/"
echo ""

# Step 3: Check backend dependencies
echo "🐍 Step 3: Checking backend dependencies..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing/updating Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "✅ Backend dependencies ready"
echo ""

# Step 4: Instructions
echo "================================================"
echo "✅ Deployment prepared successfully!"
echo "================================================"
echo ""
echo "To start the server:"
echo ""
echo "  cd backend"
echo "  source venv/bin/activate"
echo ""
echo "  # Start Redis (in separate terminal):"
echo "  docker run -p 6379:6379 redis"
echo ""
echo "  # Start RQ worker (in separate terminal):"
echo "  rq worker app.workers"
echo ""
echo "  # Start server:"
echo "  uvicorn serve_frontend:app --host 0.0.0.0 --port 8000"
echo ""
echo "Then visit: http://localhost:8000"
echo ""
echo "Both frontend and API will be served from port 8000:"
echo "  - Frontend: http://localhost:8000/"
echo "  - API: http://localhost:8000/api/v1/..."
echo "  - Docs: http://localhost:8000/api/docs"
echo ""

