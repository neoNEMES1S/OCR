#!/bin/bash
# Diagnostic script to check if everything is running correctly

echo "🔍 OCR PDF System Diagnostics"
echo "=============================="
echo ""

# Check Redis
echo "1️⃣ Checking Redis..."
if redis-cli ping >/dev/null 2>&1; then
    echo "   ✅ Redis is running"
else
    echo "   ❌ Redis is NOT running!"
    echo "      Start with: brew services start redis"
fi
echo ""

# Check Backend
echo "2️⃣ Checking Backend API..."
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "   ✅ Backend API is responding"
    curl -s http://localhost:8000/health | python3 -m json.tool
else
    echo "   ❌ Backend API is NOT responding!"
    echo "      Start with: cd backend && uvicorn app.main:app --reload"
fi
echo ""

# Check Frontend
echo "3️⃣ Checking Frontend..."
if curl -s http://localhost:3000 >/dev/null 2>&1; then
    echo "   ✅ Frontend is running"
else
    echo "   ❌ Frontend is NOT running!"
    echo "      Start with: cd frontend && npm run dev"
fi
echo ""

# Check RQ Worker
echo "4️⃣ Checking RQ Worker..."
if ps aux | grep -v grep | grep "rq worker" >/dev/null; then
    echo "   ✅ RQ Worker is running"
    PID=$(ps aux | grep -v grep | grep "rq worker" | awk '{print $2}')
    echo "      PID: $PID"
else
    echo "   ❌ RQ Worker is NOT running!"
    echo "      Start with: cd backend && source venv/bin/activate && rq worker app.workers"
fi
echo ""

# Check Settings
echo "5️⃣ Checking Settings..."
if [ -f "backend/settings.json" ]; then
    echo "   ✅ Settings file exists"
    echo "   Contents:"
    cat backend/settings.json | python3 -m json.tool 2>/dev/null || cat backend/settings.json
else
    echo "   ⚠️  No settings.json file"
    echo "      Configure via UI: http://localhost:3000/settings"
fi
echo ""

# Check Logs
echo "6️⃣ Recent Logs..."
if [ -d "logs" ]; then
    echo "   📝 Backend (last 5 lines):"
    if [ -f "logs/backend.log" ]; then
        tail -n 5 logs/backend.log | sed 's/^/      /'
    else
        echo "      No backend log yet"
    fi
    echo ""
    echo "   📝 Worker (last 5 lines):"
    if [ -f "logs/worker.log" ]; then
        tail -n 5 logs/worker.log | sed 's/^/      /'
    else
        echo "      No worker log yet"
    fi
else
    echo "   ⚠️  No logs directory"
fi
echo ""

# Check for PDFs in configured folder
echo "7️⃣ Checking PDF Files..."
if [ -f "backend/settings.json" ]; then
    FOLDER=$(python3 -c "import json; print(json.load(open('backend/settings.json')).get('FOLDER_PATH', '/tmp/pdfs'))" 2>/dev/null)
    
    if [ -d "$FOLDER" ]; then
        PDF_COUNT=$(find "$FOLDER" -name "*.pdf" -type f 2>/dev/null | wc -l | tr -d ' ')
        echo "   📁 Folder: $FOLDER"
        echo "   📄 PDF Files: $PDF_COUNT"
        
        if [ "$PDF_COUNT" -gt 0 ]; then
            echo "   ✅ Found PDFs!"
            echo "   Sample files:"
            find "$FOLDER" -name "*.pdf" -type f 2>/dev/null | head -3 | sed 's/^/      /'
        else
            echo "   ⚠️  No PDF files found in folder"
        fi
    else
        echo "   ❌ Folder does not exist: $FOLDER"
    fi
else
    echo "   ⚠️  Configure folder path first"
fi
echo ""

# Summary
echo "=============================="
echo "📊 Summary"
echo "=============================="
echo ""

REDIS_OK=$(redis-cli ping >/dev/null 2>&1 && echo "1" || echo "0")
BACKEND_OK=$(curl -s http://localhost:8000/health >/dev/null 2>&1 && echo "1" || echo "0")
FRONTEND_OK=$(curl -s http://localhost:3000 >/dev/null 2>&1 && echo "1" || echo "0")
WORKER_OK=$(ps aux | grep -v grep | grep "rq worker" >/dev/null && echo "1" || echo "0")

TOTAL=$((REDIS_OK + BACKEND_OK + FRONTEND_OK + WORKER_OK))

echo "Status: $TOTAL/4 services running"
echo ""

if [ "$TOTAL" -eq 4 ]; then
    echo "✅ All services are running!"
    echo "   Visit: http://localhost:3000"
else
    echo "⚠️  Some services are not running:"
    [ "$REDIS_OK" -eq 0 ] && echo "   - Redis"
    [ "$BACKEND_OK" -eq 0 ] && echo "   - Backend API"
    [ "$FRONTEND_OK" -eq 0 ] && echo "   - Frontend"
    [ "$WORKER_OK" -eq 0 ] && echo "   - RQ Worker"
    echo ""
    echo "   Run: ./test-local.sh"
fi
echo ""

