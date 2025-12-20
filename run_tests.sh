#!/usr/bin/env bash

# Navigate to backend directory and activate virtual environment
# Navigate to project root
cd "$(dirname "$0")"

if [ -f "backend/venv/bin/activate" ]; then
  source backend/venv/bin/activate
else
  echo "Virtual environment not found. Please ensure you have set up the backend environment."
  exit 1
fi

# Set PYTHONPATH to include project root and backend dir so imports work correctly
export PYTHONPATH=$PYTHONPATH:.:backend

# Run pytest with any passed arguments
pytest "$@"
