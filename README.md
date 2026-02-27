# CogniSync – Real-Time Social Intelligence Agent

> 🏆 Built for the **Vision Possible: Agent Protocol** hackathon  
> A multi-modal AI agent that watches live video, listens to audio, understands behavior, and delivers real-time strategic advice.

---

## 🗂️ Project Structure

```
visionagent/
├── backend/
│   ├── main.py           # FastAPI server + /analyze endpoint
│   ├── analyzer.py       # MediaPipe face/pose + audio analysis
│   ├── reasoning.py      # OpenAI / Gemini LLM advice engine
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx                      # Main dashboard
    │   ├── main.jsx
    │   ├── index.css                    # Cyberpunk styling
    │   ├── hooks/useAnalysis.js         # Webcam + audio capture hook
    │   └── components/
    │       ├── VideoStream.jsx          # Live camera feed
    │       ├── MetricsPanel.jsx         # Engagement/Stress/Confidence gauges
    │       ├── SignalPanel.jsx          # Raw signal display
    │       ├── AdvicePanel.jsx          # LLM advice output
    │       ├── AlertSystem.jsx          # Behavioral alerts
    │       └── EngagementChart.jsx      # Timeline graph
    ├── package.json
    ├── vite.config.js
    └── tailwind.config.js
```

---

## ⚙️ Environment Variables

Create `backend/.env` from the example:

```bash
cp backend/.env.example backend/.env
```

Then fill in **one** LLM key:

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (GPT-4o-mini) |
| `GEMINI_API_KEY` | Google Gemini API key (1.5 Flash) |

> If neither key is provided, a rule-based fallback generates advice automatically.

---

## 🚀 Installation & Run

### Backend (Python 3.10+)

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
copy .env.example .env
# Edit .env and add your API key

# Start backend
python main.py
# → Running on http://localhost:8000
```

> **Optional:** For better emotion detection, uncomment `deepface` and `tf-keras` in `requirements.txt` and reinstall.

### Frontend (Node.js 18+)

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
# → Running on http://localhost:5173
```

Open **http://localhost:5173** in your browser.

---

## 🎯 How It Works

```
Webcam ──► Frame (JPEG/base64) ──► POST /analyze
Mic ────► Audio features        ──► (same request)
                                        │
                                        ▼
                   MediaPipe FaceMesh → emotion, attention
                   MediaPipe Pose     → posture
                   Sharpness metric   → movement
                   Audio RMS/ZCR      → speech speed, tone
                                        │
                                        ▼
                   Score Engine → engagement%, stress%, confidence%
                   Memory       → last 5 states (short-term history)
                   Alert Engine → behavioral event detection
                   LLM (GPT/Gemini) → 1–2 line strategic advice
                                        │
                                        ▼
                   Frontend UI updates every ~1 second
```

---

## 🔌 API Reference

### `POST /analyze`

**Request:**
```json
{
  "frame_base64": "<JPEG base64 string>",
  "audio_features": {
    "speech_speed": "normal|fast|slow|silent",
    "pauses": "minimal|frequent|none",
    "tone_indicator": "neutral|calm|stressed|excited"
  }
}
```

**Response:**
```json
{
  "emotion": "happy",
  "posture": "upright",
  "attention": "high",
  "engagement_score": 82.5,
  "stress_score": 15.0,
  "confidence_score": 75.0,
  "movement": "still",
  "advice": "Strong engagement detected. This is the right moment to deepen the key message.",
  "alerts": [],
  "processing_time_ms": 340.2
}
```

### `GET /health`
Returns `{"status": "ok", "version": "1.0.0"}`.

---

## 🧠 AI Features

| Feature | Implementation |
|---|---|
| Emotion detection | DeepFace (if installed) → MediaPipe landmark heuristic fallback |
| Head orientation / attention | MediaPipe FaceMesh yaw/pitch estimation |
| Body posture | MediaPipe Pose shoulder-hip-nose geometry |
| Movement | Laplacian sharpness variance as motion proxy |
| Audio speech rate | Zero-crossing rate (ZCR) of microphone signal |
| Audio tone | RMS amplitude + ZCR classification |
| Score fusion | Weighted multi-modal signal combination |
| Agent reasoning | GPT-4o-mini / Gemini 1.5 Flash with behavioral context prompt |
| Short-term memory | Last 5 analysis states for trend detection |
| Event detection | Engagement drop / stress spike / attention loss alerts |

---

## ✅ Performance

- Frame capture: every **1 second** (configurable)
- API response target: **< 2 seconds** end-to-end
- LLM calls: **GPT-4o-mini** (fastest OpenAI model) or **Gemini 1.5 Flash**
- Frame compression: **JPEG @ 70% quality** for minimal payload

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite + Tailwind CSS |
| Video capture | WebRTC (`getUserMedia`) |
| Charts | Recharts |
| Backend | FastAPI + Uvicorn |
| Computer Vision | MediaPipe (FaceMesh + Pose) |
| Emotion | DeepFace (optional) / MediaPipe heuristic |
| Audio | Web Audio API (browser-side) |
| LLM | OpenAI GPT-4o-mini / Google Gemini 1.5 Flash |
