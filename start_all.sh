#!/bin/bash

# Farby pre výstup
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 ILUMINATI SYSTEM STARTUP${NC}"
echo "=================================="

# 1. Cleanup
# 1. Cleanup
echo -e "${YELLOW}🧹 Čistím staré procesy...${NC}"
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8009 | xargs kill -9 2>/dev/null
lsof -ti:8010 | xargs kill -9 2>/dev/null
sleep 2

# 2. Backend Setup
echo -e "${BLUE}🔧 Kontrola Backend prostredia...${NC}"
cd backend
if [ ! -d "venv" ]; then
    echo "  - Vytváram virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

echo "  - Inštalujem závislosti (Python)..."
pip install -r requirements.txt > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}  ✅ Backend závislosti OK${NC}"
else
    echo -e "${RED}  ❌ Chyba pri inštalácii backend závislostí${NC}"
    exit 1
fi

# 3. Frontend Setup
echo -e "${BLUE}🔧 Kontrola Frontend prostredia...${NC}"
cd ../frontend
if [ ! -d "node_modules" ]; then
    echo "  - Inštalujem node_modules..."
    npm install
else
    echo "  - Aktualizujem node_modules..."
    npm install > /dev/null 2>&1
fi

# 4. Spustenie serverov
echo "=================================="
echo -e "${GREEN}▶️  Spúšťam servery...${NC}"

# Backend
cd ../backend
source venv/bin/activate
# Spusti backend na pozadí a ulož PID
python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "  Backend beží (PID: $BACKEND_PID) -> http://localhost:8000"

# Frontend
cd ../frontend
# Spusti frontend na pozadí a ulož PID
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "  Frontend beží (PID: $FRONTEND_PID) -> http://localhost:8009"

echo "=================================="
echo -e "${GREEN}✅ Všetko beží!${NC}"
echo -e "Logs: logs/backend.log, logs/frontend.log"
echo -e "${YELLOW}Stlač Ctrl+C pre ukončenie${NC}"

# Trap pre ukončenie
trap "echo 'Ukončujem...'; kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT SIGTERM

# Čakaj na procesy
wait
