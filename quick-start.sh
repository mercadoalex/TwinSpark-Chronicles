#!/bin/bash

# TwinSpark Chronicles - Quick Start (No Dependency Check)
# Use this for faster startups after first run

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 TwinSpark Chronicles - Quick Start${NC}\n"

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    echo -e "${RED}❌ Error: Not in project root directory${NC}"
    exit 1
fi

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
else
    echo -e "${RED}❌ No virtual environment found. Run ./start.sh first${NC}"
    exit 1
fi

# Check for .env
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ No .env file found. Run ./start.sh first${NC}"
    exit 1
fi

# Kill any existing process on port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Killing process on port 8000...${NC}"
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 1
fi

# Start the server
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                 🚀 STARTING SERVER 🚀                       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📍 Backend:${NC}  http://localhost:8000"
echo -e "${BLUE}📊 Health:${NC}   http://localhost:8000/health"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}\n"

# Run the server
python src/main.py
