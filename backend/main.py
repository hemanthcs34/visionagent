import os
import base64
import asyncio
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from analyzer import analyze_frame, analyze_audio_features
from reasoning import get_agent_advice
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="CogniSync API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Short-term memory: last 5 analysis states
state_memory: list[dict] = []

class AnalyzeRequest(BaseModel):
    frame_base64: str          # base64-encoded JPEG frame
    audio_features: Optional[dict] = None  # {speech_speed, pauses, tone_indicator}

class AnalyzeResponse(BaseModel):
    emotion: str
    posture: str
    attention: str
    engagement_score: float
    stress_score: float
    confidence_score: float
    movement: str
    advice: str
    alerts: list[str]
    processing_time_ms: float

def compute_scores(vision_signals: dict, audio_signals: dict) -> tuple[float, float, float]:
    """
    Derive engagement, stress, and confidence scores from multi-modal signals.
    All scores are 0.0–100.0.
    """
    emotion = vision_signals.get("emotion", "neutral")
    attention = vision_signals.get("attention", "medium")
    posture = vision_signals.get("posture", "neutral")
    movement = vision_signals.get("movement", "moderate")

    speech_speed = audio_signals.get("speech_speed", "normal") if audio_signals else "normal"
    pauses = audio_signals.get("pauses", "minimal") if audio_signals else "minimal"
    tone = audio_signals.get("tone_indicator", "neutral") if audio_signals else "neutral"

    # --- Engagement Score ---
    engagement = 50.0
    attention_map = {"high": 30.0, "medium": 10.0, "low": -20.0}
    engagement += attention_map.get(attention, 0.0)
    emotion_eng_map = {
        "happy": 15.0, "surprised": 10.0, "neutral": 0.0,
        "sad": -10.0, "angry": -5.0, "disgusted": -15.0, "fearful": -10.0
    }
    engagement += emotion_eng_map.get(emotion, 0.0)
    posture_map = {"upright": 10.0, "leaning_forward": 15.0, "neutral": 0.0, "slouched": -15.0}
    engagement += posture_map.get(posture, 0.0)
    speech_map = {"fast": -5.0, "normal": 5.0, "slow": 0.0, "silent": -10.0}
    engagement += speech_map.get(speech_speed, 0.0)
    engagement = max(0.0, min(100.0, engagement))

    # --- Stress Score ---
    stress = 20.0
    emotion_stress_map = {
        "fearful": 40.0, "angry": 35.0, "disgusted": 25.0,
        "sad": 20.0, "surprised": 15.0, "neutral": 5.0, "happy": -10.0
    }
    stress += emotion_stress_map.get(emotion, 0.0)
    tone_stress_map = {"stressed": 25.0, "calm": -10.0, "neutral": 0.0, "excited": 10.0}
    stress += tone_stress_map.get(tone, 0.0)
    pause_stress_map = {"frequent": 15.0, "minimal": 0.0, "none": 5.0}
    stress += pause_stress_map.get(pauses, 0.0)
    movement_stress_map = {"restless": 20.0, "moderate": 5.0, "still": -5.0}
    stress += movement_stress_map.get(movement, 0.0)
    stress = max(0.0, min(100.0, stress))

    # --- Confidence Score ---
    confidence = 50.0
    confidence += attention_map.get(attention, 0.0) * 0.5
    conf_posture_map = {"upright": 20.0, "leaning_forward": 15.0, "neutral": 0.0, "slouched": -20.0}
    confidence += conf_posture_map.get(posture, 0.0)
    conf_emotion_map = {
        "happy": 15.0, "neutral": 5.0, "surprised": -5.0,
        "angry": -10.0, "fearful": -25.0, "sad": -15.0, "disgusted": -10.0
    }
    confidence += conf_emotion_map.get(emotion, 0.0)
    conf_speech_map = {"fast": -5.0, "normal": 10.0, "slow": -5.0, "silent": -15.0}
    confidence += conf_speech_map.get(speech_speed, 0.0)
    confidence = max(0.0, min(100.0, confidence))

    return engagement, stress, confidence


def detect_alerts(current: dict, memory: list[dict]) -> list[str]:
    """Detect behavioral events by comparing current state to history."""
    alerts = []
    if len(memory) < 2:
        return alerts

    prev_states = memory[-3:]

    # Engagement drop
    prev_avg_eng = sum(s["engagement_score"] for s in prev_states) / len(prev_states)
    if current["engagement_score"] < prev_avg_eng - 20:
        alerts.append("⚠️ Engagement dropping significantly")

    # Stress spike
    prev_avg_stress = sum(s["stress_score"] for s in prev_states) / len(prev_states)
    if current["stress_score"] > prev_avg_stress + 20:
        alerts.append("⚠️ Stress level spiking")

    # Low engagement threshold
    if current["engagement_score"] < 30:
        alerts.append("🔴 Very low engagement detected")

    # High stress threshold
    if current["stress_score"] > 75:
        alerts.append("🔴 High stress detected")

    # Attention drop
    if current["attention"] == "low":
        alerts.append("⚠️ Attention lost – subject is disengaged")

    return alerts


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    start_time = time.time()

    # Decode base64 frame
    try:
        frame_bytes = base64.b64decode(request.frame_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 frame data")

    # Run vision and audio analysis concurrently
    vision_task = asyncio.create_task(
        asyncio.to_thread(analyze_frame, frame_bytes)
    )

    audio_signals = request.audio_features or {}

    vision_signals = await vision_task
    audio_signals_processed = analyze_audio_features(audio_signals)

    # Compute unified scores
    engagement, stress, confidence = compute_scores(vision_signals, audio_signals_processed)

    current_state = {
        "emotion": vision_signals["emotion"],
        "posture": vision_signals["posture"],
        "attention": vision_signals["attention"],
        "movement": vision_signals["movement"],
        "engagement_score": engagement,
        "stress_score": stress,
        "confidence_score": confidence,
        "audio": audio_signals_processed,
    }

    # Detect behavioral alerts
    alerts = detect_alerts(current_state, state_memory)

    # Add to memory (keep last 5)
    state_memory.append(current_state)
    if len(state_memory) > 5:
        state_memory.pop(0)

    # Get LLM advice asynchronously
    advice = await asyncio.to_thread(
        get_agent_advice,
        current_state,
        state_memory[:-1],
        alerts
    )

    elapsed_ms = (time.time() - start_time) * 1000

    return AnalyzeResponse(
        emotion=vision_signals["emotion"],
        posture=vision_signals["posture"],
        attention=vision_signals["attention"],
        engagement_score=round(engagement, 1),
        stress_score=round(stress, 1),
        confidence_score=round(confidence, 1),
        movement=vision_signals["movement"],
        advice=advice,
        alerts=alerts,
        processing_time_ms=round(elapsed_ms, 1)
    )


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
