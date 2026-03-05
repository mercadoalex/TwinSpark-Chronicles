#!/bin/bash

# TwinSpark Chronicles - Full Stack Startup
# Starts both backend (Python/FastAPI) and frontend (React/Vite)

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         🌟 TWINSPARK CHRONICLES - FULL STACK 🌟             ║
║              Backend + Frontend Launcher                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if we're in the right directory
if [ ! -f "src/main.py" ]; then
    echo -e "${RED}❌ Error: Not in project root directory${NC}"
    echo -e "${YELLOW}Please run from: twinspark-chronicles/${NC}"
    exit 1
fi

# ==================== BACKEND SETUP ====================

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}                    🔧 BACKEND SETUP                      ${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found${NC}"
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}🔧 Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    
    if [ -f ".env.development.example" ]; then
        cp .env.development.example .env
        echo -e "${GREEN}✅ .env file created from template${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env and add your GOOGLE_API_KEY${NC}"
        echo ""
        read -p "Press Enter to edit .env now, or Ctrl+C to exit: "
        ${EDITOR:-nano} .env
    else
        echo -e "${RED}❌ No .env template found${NC}"
        exit 1
    fi
fi

# Check if GOOGLE_API_KEY is set
source .env
if [ -z "$GOOGLE_API_KEY" ] || [ "$GOOGLE_API_KEY" = "your_key_here" ] || [ "$GOOGLE_API_KEY" = "your_gemini_api_key_here" ]; then
    echo -e "${RED}❌ GOOGLE_API_KEY not set in .env${NC}"
    echo -e "${YELLOW}Get your key from: https://makersuite.google.com/app/apikey${NC}"
    exit 1
fi

# Quick dependency check (skip reinstall if recent)
if [ ! -f "venv/.dependencies_installed" ] || [ "requirements.txt" -nt "venv/.dependencies_installed" ]; then
    echo -e "${YELLOW}📦 Installing/updating Python dependencies...${NC}"
    pip install -q -r requirements.txt
    touch venv/.dependencies_installed
    echo -e "${GREEN}✅ Python dependencies OK${NC}"
else
    echo -e "${GREEN}✅ Python dependencies already installed (use ./start.sh to force update)${NC}"
fi

# Kill any existing backend process
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Port 8000 in use. Killing existing backend...${NC}"
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✅ Port 8000 cleared${NC}"
fi

# ==================== FRONTEND SETUP ====================

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}                    🎨 FRONTEND SETUP                     ${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found${NC}"
    echo -e "${YELLOW}Please install Node.js 16+ from: https://nodejs.org/${NC}"
    echo -e "${YELLOW}Continuing with backend only...${NC}"
    SKIP_FRONTEND=true
else
    echo -e "${GREEN}✅ Node.js found: $(node --version)${NC}"
    SKIP_FRONTEND=false
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo -e "${YELLOW}⚠️  Frontend directory not found${NC}"
    echo -e "${YELLOW}Continuing with backend only...${NC}"
    SKIP_FRONTEND=true
fi

# Install frontend dependencies if needed
if [ "$SKIP_FRONTEND" = false ]; then
    cd frontend
    
    if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules/.installed" ]; then
        echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
        npm install
        touch node_modules/.installed
        echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
    else
        echo -e "${GREEN}✅ Frontend dependencies already installed${NC}"
    fi
    
    # Kill any existing frontend process
    if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}⚠️  Port 5173 in use. Killing existing frontend...${NC}"
        lsof -ti :5173 | xargs kill -9 2>/dev/null || true
        sleep 1
        echo -e "${GREEN}✅ Port 5173 cleared${NC}"
    fi
    
    cd ..
fi

# ==================== START SERVICES ====================

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}║                   🚀 STARTING SERVICES 🚀                   ║${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Create log directory
mkdir -p logs

# Start backend in background
echo -e "${BLUE}🔵 Starting Backend (FastAPI)...${NC}"
python src/main.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
echo -e "${BLUE}   URL: http://localhost:8000${NC}"
echo -e "${BLUE}   Logs: tail -f logs/backend.log${NC}"

# Wait for backend to be ready
echo -e "${YELLOW}⏳ Waiting for backend to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend is ready!${NC}"
        break
    fi
    sleep 1
    printf "."
done
echo ""

# Start frontend in background if not skipped
if [ "$SKIP_FRONTEND" = false ]; then
    echo ""
    echo -e "${BLUE}🎨 Starting Frontend (React/Vite)...${NC}"
    cd frontend
    npm run dev > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
    echo -e "${BLUE}   URL: http://localhost:5173${NC}"
    echo -e "${BLUE}   Logs: tail -f logs/frontend.log${NC}"
    
    # Wait for frontend to be ready
    echo -e "${YELLOW}⏳ Waiting for frontend to be ready...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost:5173 > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Frontend is ready!${NC}"
            break
        fi
        sleep 1
        printf "."
    done
    echo ""
fi

# ==================== SUMMARY ====================

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}║                   ✨ ALL SERVICES RUNNING ✨                ║${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}🔵 BACKEND (FastAPI):${NC}"
echo -e "   📍 URL:    ${BLUE}http://localhost:8000${NC}"
echo -e "   📊 Health: ${BLUE}http://localhost:8000/health${NC}"
echo -e "   📖 Docs:   ${BLUE}http://localhost:8000/docs${NC}"
echo -e "   📝 Logs:   ${YELLOW}tail -f logs/backend.log${NC}"
echo ""

if [ "$SKIP_FRONTEND" = false ]; then
    echo -e "${CYAN}🎨 FRONTEND (React):${NC}"
    echo -e "   📍 URL:  ${BLUE}http://localhost:5173${NC}"
    echo -e "   📝 Logs: ${YELLOW}tail -f logs/frontend.log${NC}"
    echo ""
fi

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}💡 Open in browser: ${BLUE}http://localhost:5173${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${RED}⚠️  Press Ctrl+C to stop all services${NC}"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping services...${NC}"
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Backend stopped${NC}"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Frontend stopped${NC}"
    fi
    
    # Kill any remaining processes
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    lsof -ti :5173 | xargs kill -9 2>/dev/null || true
    
    echo -e "${GREEN}👋 All services stopped. Goodbye!${NC}"
    exit 0
}

# Set up trap for Ctrl+C
trap cleanup INT TERM

# Keep script running and show logs
if [ "$SKIP_FRONTEND" = false ]; then
    echo -e "${CYAN}📋 Showing combined logs (Ctrl+C to stop):${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    tail -f logs/backend.log -f logs/frontend.log 2>/dev/null
else
    echo -e "${CYAN}📋 Showing backend logs (Ctrl+C to stop):${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    tail -f logs/backend.log 2>/dev/null
fi
