#!/bin/bash
echo "Starting TwinSpark Chronicles Demo..."
cd ..
source venv/bin/activate
echo "1. Starting Python AI Engine (Backend)..."
python src/api/session_manager.py &
BACKEND_PID=$!

echo "2. Starting React UI (Frontend)..."
cd frontend
npm run dev

kill $BACKEND_PID
