# TwinSpark Chronicles - Quick Start Guide

## 🚀 Phase 1: Twin Intelligence Foundation

You're looking at the **CORE DIFFERENTIATOR** of TwinSpark Chronicles - the Twin Intelligence Engine that models sibling relationships as dynamic systems.

## 📦 Installation

### 1. Set up Python environment

```bash
cd twinpark-chronicles

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate  # On Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Google API key
# Get one from: https://makersuite.google.com/app/apikey
```

### 4. Run the demo

```bash
python src/main.py
```

## 🎯 What You'll See

The demo showcases the **Twin Intelligence Engine** in action:

1. **Personality Profiles**: See how the AI models each child's unique traits
2. **Relationship Dynamics**: Watch it analyze sibling interactions
3. **Complementary Powers**: See how it assigns abilities that require teamwork
4. **Dual Perspectives**: Experience the same story from different viewpoints
5. **Emotional Adaptation**: Notice how story difficulty adjusts to moods

## 🧠 Key Components Built (Phase 1)

### ✅ Twin Intelligence Engine (`src/ai/twin_intelligence.py`)

The revolutionary AI system with 4 layers:

- **Layer 1**: Individual Profile Learning
  - Voice pattern analysis
  - Gesture recognition
  - Decision-making patterns

- **Layer 2**: Relationship Dynamic Mapping
  - Leadership balance tracking
  - Complementary strengths detection
  - Communication effectiveness

- **Layer 3**: Complementary Skills Discovery
  - Power assignment algorithm
  - Ensures fairness and growth
  - Requires teamwork, not competition

- **Layer 4**: Adaptive Narrative Generation
  - Role flipping to prevent dominance
  - Difficulty adjustment based on emotion
  - Story directives for narrative engine

### ✅ Story Generator (`src/story/story_generator.py`)

- Integration with Google Gemini API
- Dual-perspective narrative generation
- Context-aware story continuation
- Mock mode for development

### ✅ Data Models (`src/models.py`)

- Type-safe structures with Pydantic
- Personality traits and emotional states
- Session tracking and analytics
- Multimodal input processing

## 🎮 Try It Out

The demo creates two fictional children:

- **Mia**: Bold, Creative, Playful
- **Sofia**: Thoughtful, Analytical, Empathetic

You'll see how the Twin Intelligence Engine:

1. Recognizes their different personalities
2. Assigns complementary powers (Ale gets action powers, Sofia gets thinking powers)
3. Creates a story where BOTH feel heroic
4. Adapts to their emotional states
5. Balances leadership roles

## 🔧 Customization

### Add Your Daughters' Real Profiles

Edit `src/main.py` in the `create_demo_profiles()` method:

```python
# Replace with your daughters' names and traits
mia = ChildProfile(
    id="your_daughter1_id",
    name="Your Daughter's Name",
    age=6,
    personality_traits=[
        PersonalityTrait.BOLD,  # Adjust based on observation
        PersonalityTrait.CREATIVE,
        PersonalityTrait.PLAYFUL
    ],
    # ... customize other fields
)
```

### Adjust Story Themes

In `src/models.py`, you can add more story themes:

```python
class StoryTheme(str, Enum):
    FANTASY = "fantasy"
    ADVENTURE = "adventure"
    # Add more themes your daughters love!
    UNICORNS = "unicorns"
    SPACE = "space"
    OCEAN = "ocean"
```

## 🚦 Next Steps (Phase 2)

To build the **Dual-Perspective Prototype**:

1. **Multimodal Input Processing**:
   - Add camera integration (MediaPipe for face/gesture detection)
   - Add microphone input (speech recognition)
   - Emotion detection from video

2. **Video Generation**:
   - Integrate Google Veo 2 API (when available)
   - Generate synchronized dual-stream video
   - Face integration for characters

3. **Real-time Interaction**:
   - WebRTC for video streaming
   - WebSocket for real-time communication
   - React frontend for UI

## 📊 Understanding the Output

When you run the demo, pay attention to:

### Personality Analysis
Shows detected traits that drive story decisions

### Assigned Powers
Notice how powers are complementary (action + thinking)

### Role Distribution
See how the engine flips roles to prevent dominance

### Emotional Adaptation
Watch difficulty adjust based on current mood

## 💡 Key Insights

**What Makes This Different:**

1. **No other AI treats siblings as a system** - they're all single-user
2. **Personality modeling happens through play** - not questionnaires
3. **Stories adapt to relationship dynamics** - not just individual preferences
4. **Powers require teamwork** - not competition
5. **Dual perspectives teach empathy** - through immersive experience

## 🐛 Troubleshooting

### "No Google API key found"
- The demo will still work with mock data
- To get real AI generation, add your API key to `.env`

### Import errors
- Make sure you're in the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

### Module not found
- Make sure you're running from the project root: `cd twinpark-chronicles`
- Check Python path: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`

## 📚 Code Structure

```
src/
├── main.py                      # Entry point - START HERE
├── config.py                    # Configuration management
├── models.py                    # Data structures
├── ai/
│   └── twin_intelligence.py    # ⭐ CORE INNOVATION
└── story/
    └── story_generator.py      # Story generation with Gemini
```

## 🎉 Success!

If you see the story demo running, **Phase 1 is complete!**

You now have the foundation of the world's first AI that understands and nurtures sibling relationships. 

The Twin Intelligence Engine is working, modeling personalities, and creating balanced, adaptive narratives.

---

**Next**: Let's build Phase 2 and add real multimodal inputs! 🚀
