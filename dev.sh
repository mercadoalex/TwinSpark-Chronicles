#!/bin/bash

# TwinSpark Chronicles - FAST DEV MODE
# Skips all dependency checks - use when you know everything is installed

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🚀 Fast Dev Mode - Starting TwinSpark Chronicles...${NC}"

# Activate venv
source venv/bin/activate 2>/dev/null || {
    echo "❌ Virtual environment not found. Run ./run-app.sh first."
    exit 1
}

# Source .env
source .env 2>/dev/null || {
    echo "❌ .env file not found. Run ./run-app.sh first."
    exit 1
}

# Kill existing processes
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :5173 | xargs kill -9 2>/dev/null || true

echo -e "${GREEN}✅ Starting backend (port 8000)...${NC}"
(cd src && uvicorn api.session_manager:app --host 0.0.0.0 --port 8000) > backend.log 2>&1 &
BACKEND_PID=$!

echo -e "${GREEN}✅ Starting frontend (port 5173)...${NC}"
(cd frontend && npm run dev) > frontend.log 2>&1 &
FRONTEND_PID=$!

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}   🎮 TwinSpark Chronicles READY!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  🌐 Frontend: ${CYAN}http://localhost:5173${NC}"
echo -e "  🔧 Backend:  ${CYAN}http://localhost:8000${NC}"
echo -e "  📊 API Docs: ${CYAN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${CYAN}Press Ctrl+C to stop both servers${NC}"
echo ""

# Trap Ctrl+C to kill both processes
trap "echo ''; echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

# Wait for both processes
wait
