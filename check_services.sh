#!/bin/bash
# ICO Atlas V4 - Service Health Check Script
# Verifies all required and optional services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
REQUIRED_PASSED=0
REQUIRED_FAILED=0
OPTIONAL_PASSED=0
OPTIONAL_FAILED=0

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   ICO Atlas V4 - Service Health Check     ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo ""

# Function to check command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check service
check_required() {
    local name=$1
    local command=$2
    
    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $name${NC}"
        ((REQUIRED_PASSED++))
        return 0
    else
        echo -e "${RED}❌ $name${NC}"
        ((REQUIRED_FAILED++))
        return 1
    fi
}

check_optional() {
    local name=$1
    local command=$2
    
    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $name${NC}"
        ((OPTIONAL_PASSED++))
        return 0
    else
        echo -e "${YELLOW}⚠️  $name (optional - using fallback)${NC}"
        ((OPTIONAL_FAILED++))
        return 1
    fi
}

# ============================================
# REQUIRED SERVICES
# ============================================
echo -e "${BLUE}Required Services:${NC}"
echo "-------------------------------------------"

# Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    check_required "Python $PYTHON_VERSION" "python3 --version"
else
    check_required "Python" "false"
fi

# Node.js
if command_exists node; then
    NODE_VERSION=$(node --version 2>&1)
    check_required "Node.js $NODE_VERSION" "node --version"
else
    check_required "Node.js" "false"
fi

# npm
if command_exists npm; then
    NPM_VERSION=$(npm --version 2>&1)
    check_required "npm $NPM_VERSION" "npm --version"
else
    check_required "npm" "false"
fi

# Python venv
check_required "Python venv (backend)" "test -d backend/venv"

# Node modules
check_required "Node modules (frontend)" "test -d frontend/node_modules"

# .env file
check_required "Environment config (.env)" "test -f backend/.env"

echo ""

# ============================================
# OPTIONAL SERVICES
# ============================================
echo -e "${BLUE}Optional Services:${NC}"
echo "-------------------------------------------"

# Redis
if command_exists redis-cli; then
    check_optional "Redis Server" "redis-cli ping"
else
    check_optional "Redis Server" "false"
fi

# PostgreSQL
if command_exists psql; then
    POSTGRES_VERSION=$(psql --version 2>&1 | awk '{print $3}')
    check_optional "PostgreSQL $POSTGRES_VERSION" "psql --version"
else
    check_optional "PostgreSQL" "false"
fi

echo ""

# ============================================
# BACKEND CHECKS
# ============================================
echo -e "${BLUE}Backend Status:${NC}"
echo "-------------------------------------------"

# Check if backend is running
if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
    HEALTH_STATUS=$(curl -s http://localhost:8000/api/health | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "unknown")
    check_required "Backend API (port 8000) - $HEALTH_STATUS" "curl -s http://localhost:8000/api/health"
else
    echo -e "${YELLOW}⚠️  Backend API not running (start with: cd backend && uvicorn main:app)${NC}"
fi

# Check database file
if [ -f "backend/sql_app.db" ]; then
    DB_SIZE=$(du -h backend/sql_app.db | awk '{print $1}')
    echo -e "${GREEN}✅ SQLite Database ($DB_SIZE)${NC}"
else
    echo -e "${YELLOW}⚠️  SQLite Database (will be created on first run)${NC}"
fi

echo ""

# ============================================
# FRONTEND CHECKS
# ============================================
echo -e "${BLUE}Frontend Status:${NC}"
echo "-------------------------------------------"

# Check if frontend is running
if curl -s http://localhost:5173 >/dev/null 2>&1; then
    check_required "Frontend Dev Server (port 5173)" "curl -s http://localhost:5173"
elif curl -s http://localhost:3000 >/dev/null 2>&1; then
    check_required "Frontend Dev Server (port 3000)" "curl -s http://localhost:3000"
else
    echo -e "${YELLOW}⚠️  Frontend not running (start with: cd frontend && npm run dev)${NC}"
fi

# Check build directory
if [ -d "frontend/dist" ]; then
    DIST_SIZE=$(du -sh frontend/dist | awk '{print $1}')
    echo -e "${GREEN}✅ Production Build ($DIST_SIZE)${NC}"
else
    echo -e "${YELLOW}⚠️  Production Build (run: cd frontend && npm run build)${NC}"
fi

echo ""

# ============================================
# SUMMARY
# ============================================
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Summary                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

TOTAL_REQUIRED=$((REQUIRED_PASSED + REQUIRED_FAILED))
TOTAL_OPTIONAL=$((OPTIONAL_PASSED + OPTIONAL_FAILED))

echo -e "Required Services: ${GREEN}$REQUIRED_PASSED${NC}/$TOTAL_REQUIRED passed"
echo -e "Optional Services: ${GREEN}$OPTIONAL_PASSED${NC}/$TOTAL_OPTIONAL available"

echo ""

if [ $REQUIRED_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All required services are ready!${NC}"
    echo ""
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Start backend:  cd backend && source venv/bin/activate && uvicorn main:app --reload"
    echo "2. Start frontend: cd frontend && npm run dev"
    echo "3. Open browser:   http://localhost:5173"
    exit 0
else
    echo -e "${RED}❌ Some required services are missing!${NC}"
    echo ""
    echo -e "${YELLOW}Please check SETUP.md for installation instructions.${NC}"
    exit 1
fi
