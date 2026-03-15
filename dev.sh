#!/bin/bash
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}🚀 TwinSpark Chronicles — Dev Mode${NC}"

# Kill existing processes
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
lsof -ti :5173 | xargs kill -9 2>/dev/null || true

echo -e "${GREEN}Starting backend (port 8000)...${NC}"
(cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000) &
BACKEND_PID=$!

echo -e "${GREEN}Starting frontend (port 5173)...${NC}"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

echo ""
echo -e "  🌐 Frontend: ${CYAN}http://localhost:5173${NC}"
echo -e "  🔧 Backend:  ${CYAN}http://localhost:8000${NC}"
echo -e "  📊 API Docs: ${CYAN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${CYAN}Press Ctrl+C to stop${NC}"

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait
