#!/bin/bash

# ILUMINATI SYSTEM - Stop Script
# Zastaví všetky bežiace servery

echo "🛑 Zastavujem ILUMINATI SYSTEM servery..."

# Zastaviť backend
pkill -f 'python.*main.py' 2>/dev/null
echo "✅ Backend zastavený"

# Zastaviť frontend
pkill -f 'vite' 2>/dev/null
echo "✅ Frontend zastavený"

# Uvoľniť porty
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:8009 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

echo ""
echo "✅ Všetky servery zastavené!"

