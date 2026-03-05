# 🚀 TwinSpark Chronicles - Complete App Launcher

## ✨ Run the Complete App (Backend + Frontend)

### One Command:
```bash
./run-app.sh
```

That's it! This starts:
- ✅ **Backend** (Python/FastAPI) on http://localhost:8000
- ✅ **Frontend** (React/Vite) on http://localhost:5173
- ✅ Shows combined logs in terminal
- ✅ Handles graceful shutdown with Ctrl+C

---

## 🌐 Access Points

Once running, open your browser:

**👉 Main App:** http://localhost:5173

**Backend API:**
- REST API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## 📱 What's Running?

### 🔵 Backend (Port 8000)
- FastAPI REST API
- WebSocket server for real-time updates
- Twin Intelligence Engine (AI)
- Story Generator (Gemini)
- Emotion Detector
- Image Generator
- State Manager
- Database layer (SQLite)

### 🎨 Frontend (Port 5173)
- React 18 application
- Vite dev server with hot reload
- Character setup interface
- Dual-perspective story display
- Multimodal controls (camera, audio)
- WebSocket connection to backend
- Beautiful animations and UI

---

## 🛑 Stopping the App

Press **Ctrl+C** in the terminal

The script will automatically:
- Stop backend server
- Stop frontend server
- Kill processes on ports 8000 and 5173
- Clean up gracefully

---

## 🔧 Alternative Launch Options

| Script | What It Does | When to Use |
|--------|--------------|-------------|
| `./run-app.sh` | **Full stack** (backend + frontend) | **Normal development** ✨ |
| `./quick-start.sh` | Backend only (fast) | API testing, no UI needed |
| `./start.sh` | Backend only (with checks) | First-time setup |
| Manual | See below | Debugging, advanced use |

---

## 📖 Manual Start (Advanced)

### Backend Only:
```bash
source venv/bin/activate
python src/main.py
```

### Frontend Only:
```bash
cd frontend
npm run dev
```

### Both Manually (2 terminals):
```bash
# Terminal 1 - Backend
source venv/bin/activate
python src/main.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

---

## 🔍 Viewing Logs

When using `./run-app.sh`, logs are shown in the terminal.

**Separate log files:**
```bash
# Backend logs
tail -f logs/backend.log

# Frontend logs
tail -f logs/frontend.log

# Both together
tail -f logs/backend.log -f logs/frontend.log
```

---

## ⚠️ Troubleshooting

### "Address already in use" (Port 8000 or 5173)

```bash
# Kill processes on both ports
lsof -ti :8000 :5173 | xargs kill -9

# Then restart
./run-app.sh
```

### "Node.js not found"

Install Node.js 16+ from: https://nodejs.org/

### "GOOGLE_API_KEY not set"

1. Create `.env` file (or edit existing)
2. Add: `GOOGLE_API_KEY=your_actual_key`
3. Get key from: https://makersuite.google.com/app/apikey

### Python dependencies missing

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend dependencies missing

```bash
cd frontend
npm install
```

---

## 🎮 Testing the App

### 1. Open Browser
```
http://localhost:5173
```

### 2. Character Setup
- Enter names for both children
- Select ages and personalities
- Choose story theme

### 3. Start Story
- Click "Start Adventure"
- Watch dual-perspective narratives
- See emotions detected in real-time
- Make choices that affect the story

### 4. Try Features
- Toggle camera for emotion detection
- Enable audio for voice input
- Use gestures for interaction
- Generate keepsake images

---

## 🚀 Quick Reference

```bash
# Start everything
./run-app.sh

# Stop everything
Press Ctrl+C

# View logs
tail -f logs/backend.log
tail -f logs/frontend.log

# Check if running
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# Kill specific ports
lsof -ti :8000 | xargs kill -9
lsof -ti :5173 | xargs kill -9
```

---

## 📊 System Requirements

### Backend:
- Python 3.9+
- 2GB RAM minimum
- macOS/Linux/Windows

### Frontend:
- Node.js 16+
- npm 7+
- Modern browser (Chrome, Firefox, Safari, Edge)

---

## 🎯 Development Workflow

### Daily Development:
```bash
# Morning
./run-app.sh

# Make changes (auto-reload enabled)
# - Backend: uvicorn --reload
# - Frontend: Vite HMR

# Evening
Ctrl+C to stop
```

### Making Changes:
- **Backend**: Edit files in `src/`, server auto-reloads
- **Frontend**: Edit files in `frontend/src/`, browser auto-updates
- **No restart needed!** Both use hot reload

---

## 📁 Project Structure

```
twinspark-chronicles/
├── run-app.sh          ← USE THIS! (full stack)
├── quick-start.sh      ← Backend only (fast)
├── start.sh            ← Backend only (with checks)
├── src/                ← Backend code
│   └── main.py         ← Backend entry point
├── frontend/           ← Frontend code
│   └── src/
│       └── App.jsx     ← Frontend entry point
├── logs/               ← Log files (auto-created)
│   ├── backend.log
│   └── frontend.log
└── .env                ← Your secrets (create this!)
```

---

## 💡 Pro Tips

1. **Use `./run-app.sh` for normal development** - it's the easiest!
2. **Logs appear in terminal** - you see everything happening
3. **Both servers auto-reload** - no need to restart
4. **Press Ctrl+C once** - graceful shutdown of everything
5. **Check logs/** folder if issues - detailed error messages

---

## 🎨 What You'll See

### Terminal Output:
```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         🌟 TWINSPARK CHRONICLES - FULL STACK 🌟             ║
║              Backend + Frontend Launcher                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

🔧 BACKEND SETUP
✅ Virtual environment activated
✅ Python dependencies OK

🎨 FRONTEND SETUP
✅ Node.js found: v18.x.x
✅ Frontend dependencies installed

╔══════════════════════════════════════════════════════════════╗
║                   ✨ ALL SERVICES RUNNING ✨                ║
╚══════════════════════════════════════════════════════════════╝

🔵 BACKEND: http://localhost:8000
🎨 FRONTEND: http://localhost:5173

💡 Open in browser: http://localhost:5173
⚠️  Press Ctrl+C to stop all services
```

### Browser (http://localhost:5173):
- Beautiful animated landing page
- Character setup interface
- Dual-perspective story display
- Real-time emotion tracking
- Interactive story choices

---

## 🆘 Getting Help

1. **Check logs:** `tail -f logs/backend.log logs/frontend.log`
2. **Kill and restart:** Ctrl+C then `./run-app.sh`
3. **Read documentation:**
   - `RUN_LOCALLY.md` - Detailed guide
   - `docs/QUICKSTART.md` - Quick start
   - `README.md` - Project overview

---

## ✨ You're Ready!

Run this command and you're good to go:

```bash
./run-app.sh
```

Then open: **http://localhost:5173** 🚀

Enjoy building TwinSpark Chronicles! 🌟
