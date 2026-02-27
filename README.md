# 🧠 CogniSync – Real-Time Social Intelligence Agent

**Winner / Entry – Vision Possible: Agent Protocol Hackathon**

CogniSync is a production-ready, multi-modal AI agent designed to augment human intelligence during high-stakes interactions (negotiations, sales, interviews, high-pressure conversations). 

It acts as a real-time "CIA analyst" sitting on your shoulder: watching the live video feed of your counterpart, analyzing their micro-expressions, posture, and attention, processing their vocal tone and speech patterns, and giving you **live, tactical psychological advice** on what to say or do next.

![CogniSync Dashboard Demo](./frontend/public/vite.svg) *(Replace with actual screenshot)*

## 🌟 Core Capabilities

*   **Real-Time Multi-Modal Analysis**: Fuses vision (MediaPipe) and audio feature data in real-time under low latency.
*   **Behavioral Intelligence Scoring**: Continuously calculates 0-100 scores for:
    *   **Engagement**: Are they cognitively invested or zoning out?
    *   **Stress**: Is their amygdala hijacked, or are they processing cleanly?
    *   **Confidence**: Are they operating from a position of power or submissiveness?
*   **Deep Psychology Advice Engine**: Powered by **Google Gemini 2.5 Flash**, the intelligence engine is grounded in elite frameworks:
    *   *FBI Hostage Negotiation (Chris Voss)*: Tactical empathy, mirroring, labeling.
    *   *Cialdini's Principles of Influence*: Scarcity, social proof, commitment.
    *   *Emotional Intelligence (Daniel Goleman)*.
*   **Crisis Alerts**: Instantly flags critical behavioral shifts like "Attention Lost," "Stress Spikes," or "Behavioral Inconsistencies" (e.g., smiling but stress is rising).

## 🚀 The Tech Stack

Optimized for real-time performance to maximize demo impact.

**Frontend:**
*   React 18 + Vite (for lightning-fast HMR and bundling)
*   Tailwind CSS (Vibrant, dark-mode, glassmorphism UI)
*   Recharts (Live streaming data visualization)
*   Lucide React (Icons)
*   *Architecture*: Uses the `useAnalysis` hook to capture webcam/mic streams natively, sample frames efficiently, and poll the backend without blocking the main UI thread.

**Backend:**
*   Python 3.13 + FastAPI + Uvicorn (High-concurrency async server)
*   Google Gemini API (`gemini-2.5-flash` via direct REST API for ultra-low latency)
*   MediaPipe Tasks API (0.10.32) for on-device CPU-based Face Landmarker (blendshapes) and Pose Landmarker operations.
*   OpenCV (`opencv-python-headless`) for image decoding and geometric fallbacks.

## ⚙️ Installation & Setup

### Prerequisites
*   Node.js (v18+)
*   Python 3.13+

### 1. Backend Setup

Open a terminal and navigate to the `backend` directory:

```bash
cd backend
python -m venv venv

# Windows formatting:
.\venv\Scripts\activate
# Mac/Linux formatting:
# source venv/bin/activate

# Install requirements (handles Python 3.13 wheel resolution)
pip install -r requirements.txt
```

**Environment Variables:**
Create a `.env` file in the `backend` directory:
```env
# Required for real-time tactical advice generation
GEMINI_API_KEY=your_gemini_api_key_here
```

**Start the Server:**
```bash
python main.py
```
*(The server will download the ~20MB MediaPipe .task models automatically on the first run).*

### 2. Frontend Setup

Open a new terminal and navigate to the `frontend` directory:

```bash
cd frontend
npm install

# Start the development server
npm run dev
```

### 3. Usage
1. Open your browser to `http://localhost:5173`.
2. Click **Start Analysis**.
3. Grant camera and microphone permissions when prompted.
4. Watch the live scores, behavioral alerts, and dynamic tactical advice cycle as your expressions and movements change!

## 🧠 How the Advice Engine Works

CogniSync does not give generic advice like "maintain your approach." It cross-references four dimensions simultaneously: **Emotion × Attention × Stress Zone × Engagement Zone**.

*   If **Attention = Low** + **Stress = High**: *“They're mentally elsewhere under pressure. Stop all content. Ask: What's the one thing that needs to be resolved for you to stay present here?”*
*   If **Emotion = Angry** + **Stress = High**: *“Anger spike detected. Do NOT match energy. Lower your volume 30%, let them finish, then label: 'It sounds like this has been frustrating for a long time.'”*

When connected to the Gemini API, it dynamically injects these frameworks into the LLM context along with the live metric stream to generate perfectly tailored conversational counter-measures.

## �️ License
Built for the Vision Possible Hackathon.
