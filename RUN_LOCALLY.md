# 🚀 How to Run TwinSpark Chronicles Locally

## Quick Start (2 minutes)

```bash
# 1. Navigate to project
cd /Users/alexmarket/Desktop/gemini_idea/twinspark-chronicles

# 2. Activate virtual environment
source venv/bin/activate

# 3. Set environment variables (if not already in .env)
export GOOGLE_API_KEY="your_key_here"

# 4. Start backend server
python src/main.py

# 5. In a NEW terminal, start frontend (optional)
cd frontend
npm run dev
```

That's it! 🎉

---

## Detailed Instructions

### Step 1: Prerequisites Check

Make sure you have:
- ✅ Python 3.9+ installed (`python3 --version`)
- ✅ Node.js 16+ (for frontend) (`node --version`)
- ✅ Virtual environment set up (`venv/` folder exists)

### Step 2: Environment Setup

#### Option A: Use existing .env file

If you already have a `.env` file:
```bash
# Just activate your virtual environment
source venv/bin/activate
```

#### Option B: Create new .env file

```bash
# Copy the example
cp .env.development.example .env

# Edit with your API key
nano .env  # or use your favorite editor

# Add this line:
GOOGLE_API_KEY=your_actual_key_here
```

Get your API key from: https://makersuite.google.com/app/apikey

### Step 3: Install/Update Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install/update Python packages
pip install -r requirements.txt
```

### Step 4: Start the Backend

```bash
# From project root
python src/main.py
```

You should see:
```
INFO:__main__:⚙️ Initializing SessionManager orchestration...
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

**Backend is now running at:** http://localhost:8000

### Step 5: Start the Frontend (Optional)

In a **NEW terminal window**:

```bash
cd /Users/alexmarket/Desktop/gemini_idea/twinspark-chronicles/frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

**Frontend is now running at:** http://localhost:5173

---

## 🔧 Troubleshooting

### ❌ "Address already in use" Error

**Problem:** Port 8000 is occupied

**Solution:**

```bash
# Option 1: Kill the process using port 8000
lsof -ti :8000 | xargs kill -9

# Option 2: Use a different port
python src/main.py --port 8001
```

### ❌ "No module named 'google.generativeai'"

**Problem:** Dependencies not installed

**Solution:**

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### ❌ "GOOGLE_API_KEY not found"

**Problem:** Environment variable not set

**Solution:**

```bash
# Create .env file
echo "GOOGLE_API_KEY=your_key_here" > .env

# Or export it directly
export GOOGLE_API_KEY="your_key_here"
```

### ⚠️ Python Version Warnings

You're seeing warnings about Python 3.9 being end-of-life. These are **warnings only** - the app still works!

**To fix (optional):**

```bash
# Install Python 3.10+ from python.org
# Then recreate virtual environment:
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### ⚠️ "Image generation disabled: HUGGINGFACE_API_KEY not set"

**This is optional.** Image generation works with Hugging Face.

**To enable (optional):**

```bash
# Get API key from: https://huggingface.co/settings/tokens
# Add to .env:
echo "HUGGINGFACE_API_KEY=your_hf_key" >> .env
```

---

## 🎮 Testing the App

### Method 1: Browser (Recommended)

1. **Start backend:** `python src/main.py`
2. **Open browser:** http://localhost:8000
3. **Start frontend:** `cd frontend && npm run dev`
4. **Open browser:** http://localhost:5173

### Method 2: API Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test story generation
curl -X POST http://localhost:8000/api/story/start \
  -H "Content-Type: application/json" \
  -d '{"child1_name":"Ale","child2_name":"Sofi","theme":"adventure"}'
```

### Method 3: Integration Tests

```bash
# Run Phase 2 tests
python tests/test_phase2_integration.py

# Run Phase 3 tests
python tests/test_phase3_integration.py
```

---

## 📂 Project Structure

```
twinspark-chronicles/
├── src/
│   ├── main.py              ← START HERE (backend entry point)
│   ├── config.py            ← Configuration
│   ├── models.py            ← Data models
│   ├── ai/
│   │   └── twin_intelligence.py  ← Core AI engine
│   ├── api/
│   │   └── session_manager.py    ← FastAPI server
│   ├── story/
│   │   ├── story_generator.py    ← Story generation
│   │   └── image_generator.py    ← Image generation
│   ├── multimodal/
│   │   ├── camera_processor.py   ← Video input
│   │   ├── audio_processor.py    ← Audio input
│   │   └── emotion_detector.py   ← Emotion detection
│   └── utils/
│       ├── database.py           ← Database layer
│       └── state_manager.py      ← Session state
├── frontend/
│   ├── src/
│   │   └── App.jsx          ← React app
│   └── package.json
├── .env                     ← Your secrets (create this!)
└── requirements.txt         ← Python dependencies
```

---

## 🎯 Development Workflow

### 1. Daily Development

```bash
# Morning routine
cd twinspark-chronicles
source venv/bin/activate
python src/main.py

# In another terminal (for frontend)
cd frontend
npm run dev
```

### 2. Making Changes

- **Backend changes:** Server auto-reloads (thanks to `uvicorn --reload`)
- **Frontend changes:** Vite auto-reloads in browser

### 3. Testing Changes

```bash
# Run integration tests
python tests/test_phase2_integration.py

# Or test specific component
python -c "from src.ai.twin_intelligence import TwinIntelligence; print('✅ OK')"
```

---

## 🚀 Quick Commands Cheat Sheet

```bash
# Start backend
python src/main.py

# Start frontend
cd frontend && npm run dev

# Run tests
python tests/test_phase2_integration.py

# Kill processes on port 8000
lsof -ti :8000 | xargs kill -9

# Check what's running
ps aux | grep python

# View logs in real-time
tail -f server.log

# Activate venv
source venv/bin/activate

# Deactivate venv
deactivate

# Update dependencies
pip install -r requirements.txt

# Check Python version
python --version

# List installed packages
pip list
```

---

## 📊 What's Running?

When you start `python src/main.py`, you get:

1. **FastAPI Backend** on http://localhost:8000
   - WebSocket server for real-time updates
   - REST API endpoints
   - Story generation engine
   - Multimodal processing

2. **Endpoints Available:**
   - `GET /` - Welcome page
   - `GET /health` - Health check
   - `POST /api/story/start` - Start new story
   - `WS /ws` - WebSocket connection

3. **Services Running:**
   - Twin Intelligence Engine
   - Story Generator (Gemini)
   - Image Generator (Hugging Face)
   - Emotion Detector
   - State Manager

---

## 🎨 Frontend Details

The React frontend (http://localhost:5173) provides:

- **Character Setup** - Create child profiles
- **Dual Story Display** - Side-by-side narratives
- **Multimodal Controls** - Camera, audio, gestures
- **Alert/Exit Modals** - Session management

**Tech Stack:**
- React 18
- Vite (build tool)
- WebSocket connection to backend

---

## ⚡ Performance Tips

1. **Use SQLite for local dev** (already configured)
2. **Enable debug mode** in `.env`: `DEBUG=true`
3. **Disable image generation** if slow: `ENABLE_VIDEO_GENERATION=false`
4. **Use mock mode** for faster testing (in code)

---

## 🔐 Security Notes

- ✅ Never commit `.env` file (it's in `.gitignore`)
- ✅ API keys should be in `.env`, not in code
- ✅ Use `.env.development.example` as template

---

## 📚 Next Steps

1. **Explore Phase 3 features:**
   - Database layer: `src/utils/database.py`
   - Family photos: `src/story/family_integrator.py`
   - Voice recording: `src/multimodal/voice_recorder.py`
   - World persistence: `src/story/world_manager.py`

2. **Read documentation:**
   - Phase 3 Plan: `docs/PHASE3_PLAN.md`
   - Phase 4 Plan: `docs/PHASE4_PLAN.md`
   - GCP Deployment: `docs/GCP_DEPLOYMENT.md`

3. **Test Phase 3:**
   ```bash
   python tests/test_phase3_integration.py
   ```

---

## 💡 Pro Tips

- **Use `uvicorn --reload`** for auto-restart on code changes (already enabled)
- **Check `server.log`** for detailed error messages
- **Use browser DevTools** to inspect WebSocket messages
- **Enable debug logging** in `.env`: `LOG_LEVEL=DEBUG`

---

## 🆘 Getting Help

- **Check logs:** `tail -f server.log`
- **Check errors:** Look at terminal output
- **Read docs:** All documentation in `docs/` folder
- **Test components:** Run integration tests

---

**Ready to build something amazing!** 🚀

Run: `python src/main.py` and let's go! 🎉
