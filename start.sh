#!/bin/bash

# TwinSpark Chronicles - Local Development Startup Script
# Quick and easy way to run the app locally

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         🌟 TWINSPARK CHRONICLES - LOCAL DEV 🌟              ║
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

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    
    if [ -f ".env.development.example" ]; then
        echo -e "${YELLOW}Creating .env from template...${NC}"
        cp .env.development.example .env
        echo -e "${GREEN}✅ .env file created${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env and add your GOOGLE_API_KEY${NC}"
        echo ""
        read -p "Press Enter to edit .env now, or Ctrl+C to exit and edit manually: "
        ${EDITOR:-nano} .env
    else
        echo -e "${RED}❌ No .env template found${NC}"
        echo -e "${YELLOW}Creating minimal .env file...${NC}"
        cat > .env << 'ENVEOF'
# TwinSpark Chronicles - Environment Variables
GOOGLE_API_KEY=your_key_here
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO
ENVEOF
        echo -e "${GREEN}✅ .env file created${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env and add your GOOGLE_API_KEY${NC}"
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

# Install/update dependencies
echo -e "${YELLOW}📦 Checking dependencies...${NC}"
pip install -r requirements.txt > /dev/null 2>&1 &
PIP_PID=$!

# Show spinner while installing
spin='-\|/'
i=0
while kill -0 $PIP_PID 2>/dev/null; do
  i=$(( (i+1) %4 ))
  printf "\r${YELLOW}📦 Installing dependencies... ${spin:$i:1}${NC}"
  sleep .1
done
wait $PIP_PID
PIP_EXIT=$?

if [ $PIP_EXIT -eq 0 ]; then
    echo -e "\r${GREEN}✅ Dependencies OK          ${NC}"
else
    echo -e "\r${RED}❌ Dependency installation failed${NC}"
    echo -e "${YELLOW}Continuing anyway (dependencies may already be installed)${NC}"
fi

# Kill any existing process on port 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Port 8000 is in use. Killing existing process...${NC}"
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}✅ Port cleared${NC}"
fi

# Start the server
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}║                 🚀 STARTING BACKEND SERVER 🚀               ║${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}📍 Backend:${NC}  http://localhost:8000"
echo -e "${BLUE}📊 Health:${NC}   http://localhost:8000/health"
echo -e "${BLUE}📝 Logs:${NC}     tail -f server.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Run the server
python src/main.py
