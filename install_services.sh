#!/bin/bash
# ICO Atlas V4 - Optional Services Installation Script
# Installs Redis and PostgreSQL on macOS using Homebrew

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   ICO Atlas V4 - Services Installation    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Check OS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ This script is for macOS only${NC}"
    echo "For Linux, see SETUP.md for manual installation instructions"
    exit 1
fi

# Check Homebrew
if ! command -v brew &> /dev/null; then
    echo -e "${RED}❌ Homebrew not found${NC}"
    echo "Install Homebrew first: https://brew.sh"
    exit 1
fi

echo -e "${GREEN}✅ Homebrew found${NC}"
echo ""

# ============================================
# REDIS INSTALLATION
# ============================================
echo -e "${BLUE}Installing Redis...${NC}"

if command -v redis-cli &> /dev/null; then
    echo -e "${YELLOW}⚠️  Redis already installed${NC}"
else
    echo "Installing Redis via Homebrew..."
    brew install redis
    echo -e "${GREEN}✅ Redis installed${NC}"
fi

# Start Redis
echo "Starting Redis service..."
brew services start redis

# Wait for Redis to start
sleep 2

# Test Redis
if redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis failed to start${NC}"
    exit 1
fi

echo ""

# ============================================
# POSTGRESQL INSTALLATION
# ============================================
echo -e "${BLUE}Installing PostgreSQL...${NC}"

if command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL already installed${NC}"
else
    echo "Installing PostgreSQL 16 via Homebrew..."
    brew install postgresql@16
    echo -e "${GREEN}✅ PostgreSQL installed${NC}"
fi

# Start PostgreSQL
echo "Starting PostgreSQL service..."
brew services start postgresql@16

# Wait for PostgreSQL to start
sleep 3

# Create database
echo "Creating database 'iluminati_db'..."
if createdb iluminati_db 2>/dev/null; then
    echo -e "${GREEN}✅ Database created${NC}"
else
    echo -e "${YELLOW}⚠️  Database may already exist${NC}"
fi

echo ""

# ============================================
# UPDATE .ENV FILE
# ============================================
echo -e "${BLUE}Updating .env configuration...${NC}"

ENV_FILE="backend/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Creating .env from template..."
    cp .env.example "$ENV_FILE"
fi

# Update DATABASE_URL
if grep -q "^DATABASE_URL=sqlite" "$ENV_FILE"; then
    echo "Updating DATABASE_URL to PostgreSQL..."
    sed -i '' "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://$(whoami)@localhost:5432/iluminati_db|" "$ENV_FILE"
    echo -e "${GREEN}✅ DATABASE_URL updated${NC}"
fi

# Add REDIS_URL if not present
if ! grep -q "^REDIS_URL=" "$ENV_FILE"; then
    echo "Adding REDIS_URL..."
    echo "" >> "$ENV_FILE"
    echo "# Redis Configuration" >> "$ENV_FILE"
    echo "REDIS_URL=redis://localhost:6379/0" >> "$ENV_FILE"
    echo -e "${GREEN}✅ REDIS_URL added${NC}"
fi

echo ""

# ============================================
# VERIFY INSTALLATION
# ============================================
echo -e "${BLUE}Verifying installation...${NC}"
echo ""

# Check Redis
if redis-cli ping &> /dev/null; then
    echo -e "${GREEN}✅ Redis: Running${NC}"
else
    echo -e "${RED}❌ Redis: Not running${NC}"
fi

# Check PostgreSQL
if psql -d iluminati_db -c "SELECT 1;" &> /dev/null; then
    echo -e "${GREEN}✅ PostgreSQL: Running and accessible${NC}"
else
    echo -e "${RED}❌ PostgreSQL: Not accessible${NC}"
fi

echo ""

# ============================================
# SUCCESS MESSAGE
# ============================================
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     ✅ Installation Complete!              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Services installed and configured:${NC}"
echo "  • Redis:      localhost:6379"
echo "  • PostgreSQL: localhost:5432"
echo "  • Database:   iluminati_db"
echo ""
echo -e "${BLUE}Configuration updated:${NC}"
echo "  • $ENV_FILE"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Restart backend to use new services:"
echo "   pkill -f uvicorn"
echo "   cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo ""
echo "2. Verify services are being used:"
echo "   curl http://localhost:8000/api/health | jq '.cache.redis_enabled'"
echo ""
echo -e "${BLUE}To stop services:${NC}"
echo "  brew services stop redis"
echo "  brew services stop postgresql@16"
echo ""
echo -e "${BLUE}To start services on boot:${NC}"
echo "  brew services start redis"
echo "  brew services start postgresql@16"
echo ""
