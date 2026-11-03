#!/usr/bin/env bash
# iCOAtlas V4 - One-click E2E and Integrity Test Runner

cd "$(dirname "$0")/.."

if [ -f "backend/venv/bin/activate" ]; then
    source backend/venv/bin/activate
else
    echo "Virtual environment not found in backend/venv."
    exit 1
fi

export PYTHONPATH=$PYTHONPATH:.:backend

python3 scripts/e2e_playwright_test.py "$@"
