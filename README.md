# 🌟 TwinSpark Chronicles

**The World's First AI Agent That Understands Sibling Dynamics**

An AI-powered interactive storytelling platform that creates personalized dual-protagonist narratives for siblings, using multimodal inputs (video, audio, gestures) and generating synchronized video/image outputs through Google's Live API.

![TwinSpark Chronicles](/TwinSpark.png "AI That Understands Sibling Dynamics")   

## 🚀 Project Vision

TwinSpark Chronicles doesn't just tell stories—it observes, learns, and nurtures the unique bond between siblings by creating experiences that celebrate their differences, strengthen their connection, and evolve with their individual personalities over time.

## 🎯 Core Features

- **Twin Intelligence Engine**: AI that models sibling relationships as dynamic systems
- **Dual-Perspective Narratives**: Synchronized parallel storytelling from different viewpoints
- **Emotion Mirror**: Real-time mood detection and adaptive storytelling
- **Family Universe**: Persistent world that integrates family history and culture
- **Personality Evolution**: Characters that grow based on real-world behavior

## 🛠️ Tech Stack

- **Python 3.11+**: Core application
- **Google Live API**: Multimodal understanding
- **Google Veo 2**: Video generation
- **Google Imagen 3**: Image generation
- **MediaPipe**: Gesture and pose recognition
- **WebRTC**: Real-time video streaming
- **FastAPI**: Backend API
- **React**: Frontend UI (future)

## 📁 Project Structure

```
twinpark-chronicles/
├── src/
│   ├── ai/              # AI models and intelligence engine
│   ├── multimodal/      # Video, audio, gesture processing
│   ├── story/           # Story generation and narrative engine
│   ├── api/             # Backend API
│   └── utils/           # Helper functions
├── docs/                # Documentation
├── tests/               # Unit and integration tests
├── assets/              # Sample data, images, videos
└── requirements.txt     # Python dependencies
```

## 🎬 Development Phases

### ✅ Phase 1: Twin Intelligence Foundation (COMPLETE)
- ✅ Personality detection system
- ✅ Relationship dynamic analyzer
- ✅ Basic story branching
- ✅ Pydantic data models
- ✅ Configuration management

### ✅ Phase 2: Multimodal Prototype (COMPLETE)
- ✅ Camera integration with face detection
- ✅ Audio processing with voice recognition
- ✅ Real-time emotion detection
- ✅ Image generation (Hugging Face FLUX.1)
- ✅ WebSocket server for real-time updates
- ✅ Input Manager orchestration
- ✅ Keepsake generation
- ✅ State persistence

### 🔄 Phase 3: Family Universe (IN PLANNING)
- Database layer with SQLAlchemy
- Family photo integration
- Voice recording system
- Persistent story world
- See [docs/PHASE3_PLAN.md](docs/PHASE3_PLAN.md)

### ⏳ Phase 4: Polish & Production (PLANNED)
- Parent dashboard
- Child-friendly UI/UX
- Safety & content filtering
- Performance optimization
- See [docs/PHASE4_PLAN.md](docs/PHASE4_PLAN.md)

## 🚦 Getting Started

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/main.py
```

## 🔐 Environment Variables

Create a `.env` file with:
```
GOOGLE_API_KEY=your_api_key_here
GOOGLE_PROJECT_ID=your_project_id
```

## 📚 Documentation

See [docs/](docs/) folder for detailed documentation on:
- Architecture design
- API documentation
- Personality modeling algorithms
- Story generation logic

![...under construction](/TwinSpark_02.png "TwinSpark Chronicles UI") 

## 🤝 Contributing

This is a personal project for my daughters, but ideas and feedback are welcome!

## 📝 License

Private project - All rights reserved

---

*Built with love for Ale and Sofi* 💕✨
