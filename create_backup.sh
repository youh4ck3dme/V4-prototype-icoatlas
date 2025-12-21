#!/bin/bash
# ICO Atlas V4 - Backup Script
# Creates a complete backup of the project

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   ICO Atlas V4 - Backup Script            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="V4-prototype-icoatlas-backup-${TIMESTAMP}"

# Backup directory
BACKUP_DIR="${HOME}/Desktop/ICO-Atlas-Backups"
mkdir -p "$BACKUP_DIR"

echo -e "${BLUE}Creating backup...${NC}"
echo "Timestamp: $TIMESTAMP"
echo "Backup location: $BACKUP_DIR"
echo ""

# Create compressed archive
echo -e "${BLUE}[1/3] Compressing project files...${NC}"
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
    --exclude='node_modules' \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='*.pyc' \
    --exclude='.DS_Store' \
    --exclude='dist' \
    --exclude='build' \
    --exclude='*.log' \
    --exclude='.coverage' \
    --exclude='htmlcov' \
    .

BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | awk '{print $1}')
echo -e "${GREEN}✅ Archive created: ${BACKUP_SIZE}${NC}"
echo ""

# Create backup info file
echo -e "${BLUE}[2/3] Creating backup info...${NC}"
cat > "${BACKUP_DIR}/${BACKUP_NAME}.info" <<EOF
# ICO Atlas V4 Backup Information
Backup Date: $(date)
Timestamp: $TIMESTAMP
Backup Size: $BACKUP_SIZE
Project Path: $(pwd)
Git Branch: $(git branch --show-current 2>/dev/null || echo "N/A")
Git Commit: $(git rev-parse HEAD 2>/dev/null || echo "N/A")

# Backup Contents:
- Backend (Python/FastAPI)
- Frontend (React/Vite)
- Documentation
- Configuration files
- Scripts
- Tests
- JSON Templates

# Excluded from backup:
- node_modules/
- venv/
- __pycache__/
- dist/
- *.log files

# To restore:
1. Extract archive: tar -xzf ${BACKUP_NAME}.tar.gz
2. Install dependencies:
   - Backend: cd backend && pip install -r requirements.txt
   - Frontend: cd frontend && npm install
3. Configure .env file
4. Run: ./start_dev.sh
EOF

echo -e "${GREEN}✅ Info file created${NC}"
echo ""

# Create quick restore script
echo -e "${BLUE}[3/3] Creating restore script...${NC}"
cat > "${BACKUP_DIR}/${BACKUP_NAME}-restore.sh" <<'RESTORE_SCRIPT'
#!/bin/bash
# Quick Restore Script

set -e

BACKUP_FILE="$(dirname "$0")/$(basename "$0" -restore.sh).tar.gz"
RESTORE_DIR="${HOME}/Downloads/V4-prototype-icoatlas-restored-$(date +%Y%m%d_%H%M%S)"

echo "╔════════════════════════════════════════════╗"
echo "║   ICO Atlas V4 - Restore Script           ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "Backup file: $BACKUP_FILE"
echo "Restore to: $RESTORE_DIR"
echo ""

# Create restore directory
mkdir -p "$RESTORE_DIR"

# Extract backup
echo "[1/4] Extracting backup..."
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"
echo "✅ Extracted"

# Install backend dependencies
echo "[2/4] Installing backend dependencies..."
cd "$RESTORE_DIR/backend"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1
deactivate
echo "✅ Backend dependencies installed"

# Install frontend dependencies
echo "[3/4] Installing frontend dependencies..."
cd "$RESTORE_DIR/frontend"
npm install > /dev/null 2>&1
echo "✅ Frontend dependencies installed"

# Setup environment
echo "[4/4] Setting up environment..."
cd "$RESTORE_DIR"
if [ ! -f "backend/.env" ]; then
    cp .env.example backend/.env 2>/dev/null || echo "Note: .env.example not found"
fi
echo "✅ Environment configured"

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║     ✅ Restore Complete!                   ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "Project restored to: $RESTORE_DIR"
echo ""
echo "Next steps:"
echo "1. cd $RESTORE_DIR"
echo "2. Configure backend/.env if needed"
echo "3. ./start_dev.sh"
echo ""
RESTORE_SCRIPT

chmod +x "${BACKUP_DIR}/${BACKUP_NAME}-restore.sh"
echo -e "${GREEN}✅ Restore script created${NC}"
echo ""

# Summary
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     ✅ Backup Complete!                    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Backup Files:${NC}"
echo "  📦 Archive:  ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz ($BACKUP_SIZE)"
echo "  📄 Info:     ${BACKUP_DIR}/${BACKUP_NAME}.info"
echo "  🔧 Restore:  ${BACKUP_DIR}/${BACKUP_NAME}-restore.sh"
echo ""
echo -e "${BLUE}To restore:${NC}"
echo "  ${BACKUP_DIR}/${BACKUP_NAME}-restore.sh"
echo ""
echo -e "${YELLOW}💡 Tip: Keep this backup in a safe location (cloud storage, external drive)${NC}"
echo ""

# List all backups
echo -e "${BLUE}All backups in ${BACKUP_DIR}:${NC}"
ls -lht "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -5 || echo "No previous backups found"
echo ""
