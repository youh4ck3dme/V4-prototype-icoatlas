#!/bin/bash
# ICO Atlas V4 - Development Startup Script
# Starts both backend and frontend concurrently

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   ICO Atlas V4 - Starting Development     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Check if running from project root
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Error: Must run from project root directory${NC}"
    echo "Current directory: $(pwd)"
    exit 1
fi

# ============================================
# PRE-FLIGHT CHECKS
# ============================================
echo -e "${BLUE}Running pre-flight checks...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found${NC}"
    exit 1
fi

# Check backend venv
if [ ! -d "backend/venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating...${NC}"
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
fi

# Check .env file
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from template...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example backend/.env
        # Generate secret key
        SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s/your-secret-key-here-change-this-in-production/$SECRET_KEY/" backend/.env
        else
            sed -i "s/your-secret-key-here-change-this-in-production/$SECRET_KEY/" backend/.env
        fi
        echo -e "${GREEN}✅ Created .env with generated secret key${NC}"
    else
        echo -e "${RED}❌ .env.example not found${NC}"
        exit 1
    fi
fi

# Check node_modules
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Node modules not found. Installing...${NC}"
    cd frontend
    npm install
    cd ..
fi

# Check for Redis (optional)
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✅ Redis is running${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis installed but not running (using in-memory cache)${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Redis not installed (using in-memory cache)${NC}"
fi

# Initialize database if needed
if [ ! -f "backend/sql_app.db" ]; then
    echo -e "${YELLOW}⚠️  Database not found. Initializing...${NC}"
    cd backend
    source venv/bin/activate
    python3 -c "from services.database import init_database; init_database(); print('✅ Database initialized')"
    deactivate
    cd ..
fi

echo -e "${GREEN}✅ Pre-flight checks complete${NC}"
echo ""

# ============================================
# CLEANUP OLD PROCESSES
# ============================================
echo -e "${BLUE}Cleaning up old processes...${NC}"

# Kill old backend processes
pkill -f "uvicorn main:app" 2>/dev/null || true

# Kill old frontend processes  
pkill -f "vite" 2>/dev/null || true

sleep 1
echo -e "${GREEN}✅ Cleanup complete${NC}"
echo ""

# ============================================
# START SERVICES
# ============================================
echo -e "${BLUE}Starting services...${NC}"
echo ""

# Create log directory
mkdir -p logs

# Start backend
echo -e "${BLUE}[1/2] Starting Backend API...${NC}"
cd backend
source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
deactivate
cd ..

# Wait for backend to start
echo -n "Waiting for backend"
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✅ Backend API started (PID: $BACKEND_PID)${NC}"
        break
    fi
    echo -n "."
    sleep 1
    
    if [ $i -eq 30 ]; then
        echo ""
        echo -e "${RED}❌ Backend failed to start. Check logs/backend.log${NC}"
        tail -20 logs/backend.log
        exit 1
    fi
done

# Start frontend
echo -e "${BLUE}[2/2] Starting Frontend Dev Server...${NC}"
cd frontend
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo -n "Waiting for frontend"
for i in {1..30}; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo ""
        echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
        break
    fi
    echo -n "."
    sleep 1
    
    if [ $i -eq 30 ]; then
        echo ""
        echo -e "${YELLOW}⚠️  Frontend may still be starting. Check logs/frontend.log${NC}"
        break
    fi
done

echo ""

# ============================================
# SUCCESS MESSAGE
# ============================================
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     🚀 ICO Atlas V4 is now running!       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Services:${NC}"
echo "  • Backend API:  http://localhost:8000"
echo "  • API Docs:     http://localhost:8000/api/docs"
echo "  • Frontend:     http://localhost:5173"
echo ""
echo -e "${BLUE}Process IDs:${NC}"
echo "  • Backend:  $BACKEND_PID"
echo "  • Frontend: $FRONTEND_PID"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo "  • Backend:  tail -f logs/backend.log"
echo "  • Frontend: tail -f logs/frontend.log"
echo ""
echo -e "${BLUE}To stop services:${NC}"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  or run: pkill -f 'uvicorn main:app' && pkill -f 'vite'"
echo ""
echo -e "${YELLOW}Press Ctrl+C to view logs, or open http://localhost:5173 in your browser${NC}"
echo ""

# Save PIDs to file for easy cleanup
echo "$BACKEND_PID" > .backend.pid
echo "$FRONTEND_PID" > .frontend.pid

# Follow logs
trap "echo ''; echo 'Services still running. Use: kill $BACKEND_PID $FRONTEND_PID'; exit 0" INT

tail -f logs/backend.log logs/frontend.log
