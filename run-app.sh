#!/bin/bash
ROOT="/Users/alexmarket/Desktop/gemini_idea/twinspark-chronicles"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

cleanup() {
  echo -e "\n${YELLOW}🛑 Shutting down...${NC}"
  [ ! -z "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null && echo -e "${GREEN}✅ Backend stopped${NC}"
  [ ! -z "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null && echo -e "${GREEN}✅ Frontend stopped${NC}"
  exit 0
}
trap cleanup SIGINT SIGTERM

mkdir -p "$ROOT/logs"
echo -e "${GREEN}🪄  TwinSpark Chronicles — Starting up...${NC}\n"

# ── Backend ──────────────────────────────────────────────────
echo -e "${BLUE}🐍 Starting Backend...${NC}"
source "$ROOT/venv/bin/activate"
PYTHONPATH="$ROOT/src" python "$ROOT/src/api/session_manager.py" > "$ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!

echo -n "   Waiting for backend"
for i in {1..20}; do
  sleep 1; echo -n "."
  curl -s http://localhost:8000/docs > /dev/null 2>&1 && echo -e "\n${GREEN}✅ Backend ready!${NC}" && break
done

# ── Frontend ─────────────────────────────────────────────────
echo -e "\n${BLUE}⚛️  Starting Frontend...${NC}"
cd "$ROOT/frontend" && npm run dev > "$ROOT/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!

echo -n "   Waiting for frontend"
FRONTEND_PORT=""
for i in {1..20}; do
  sleep 1; echo -n "."
  for port in 3000 3001 3002 3003 3004 5173; do
    curl -s http://localhost:$port > /dev/null 2>&1 && FRONTEND_PORT=$port && break 2
  done
done

echo -e "\n"
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  🎉 TwinSpark Chronicles is RUNNING!      ${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "  🌐 Frontend  → ${BLUE}http://localhost:${FRONTEND_PORT:-3003}${NC}"
echo -e "  🔧 Backend   → ${BLUE}http://localhost:8000${NC}"
echo -e "  🔌 WebSocket → ${BLUE}ws://localhost:8000/ws/session${NC}"
echo -e "\n  📋 Logs:"
echo -e "     Backend  → tail -f $ROOT/logs/backend.log"
echo -e "     Frontend → tail -f $ROOT/logs/frontend.log"
echo -e "\n${YELLOW}  Press Ctrl+C to stop${NC}\n"
wait
