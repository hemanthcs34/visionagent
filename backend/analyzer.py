"""
analyzer.py – CogniSync vision + audio analysis module
Uses mediapipe 0.10.x Tasks API (mp.tasks.vision) with auto-downloaded model files.
Falls back gracefully to OpenCV-only analysis if model download fails.
"""

import cv2
import numpy as np
import os
import urllib.request
from pathlib import Path

# ── MediaPipe Tasks imports ──────────────────────────────────────────────────
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

# ── Model download cache directory ──────────────────────────────────────────
MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

FACE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)
POSE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)
FACE_MODEL_PATH = MODELS_DIR / "face_landmarker.task"
POSE_MODEL_PATH = MODELS_DIR / "pose_landmarker_lite.task"


def _download_model(url: str, path: Path) -> bool:
    """Download a mediapipe task model file if not already cached."""
    if path.exists():
        return True
    try:
        print(f"[CogniSync] Downloading model: {path.name} …")
        urllib.request.urlretrieve(url, path)
        print(f"[CogniSync] ✓ Downloaded {path.name}")
        return True
    except Exception as e:
        print(f"[CogniSync] ✗ Failed to download {path.name}: {e}")
        return False


# ── Initialize detectors ─────────────────────────────────────────────────────
_face_detector = None
_pose_detector = None
MEDIAPIPE_TASKS_READY = False

def _init_detectors():
    global _face_detector, _pose_detector, MEDIAPIPE_TASKS_READY

    face_ok = _download_model(FACE_MODEL_URL, FACE_MODEL_PATH)
    pose_ok = _download_model(POSE_MODEL_URL, POSE_MODEL_PATH)

    if face_ok:
        try:
            face_opts = mp_vision.FaceLandmarkerOptions(
                base_options=mp_python.BaseOptions(
                    model_asset_path=str(FACE_MODEL_PATH)
                ),
                running_mode=mp_vision.RunningMode.IMAGE,
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_face_presence_confidence=0.5,
                min_tracking_confidence=0.5,
                output_face_blendshapes=True,
            )
            _face_detector = mp_vision.FaceLandmarker.create_from_options(face_opts)
        except Exception as e:
            print(f"[CogniSync] FaceLandmarker init failed: {e}")

    if pose_ok:
        try:
            pose_opts = mp_vision.PoseLandmarkerOptions(
                base_options=mp_python.BaseOptions(
                    model_asset_path=str(POSE_MODEL_PATH)
                ),
                running_mode=mp_vision.RunningMode.IMAGE,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            _pose_detector = mp_vision.PoseLandmarker.create_from_options(pose_opts)
        except Exception as e:
            print(f"[CogniSync] PoseLandmarker init failed: {e}")

    MEDIAPIPE_TASKS_READY = _face_detector is not None

# Attempt initialization at import time
_init_detectors()

# Try optional DeepFace
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False

# OpenCV face cascade for fallback
_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
_face_cascade = cv2.CascadeClassifier(_cascade_path)


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_frame(frame_bytes: bytes) -> dict:
    """
    Analyze a single video frame.
    Returns: {emotion, confidence, posture, attention, movement, head_tilt}
    """
    nparr = np.frombuffer(frame_bytes, np.uint8)
    bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if bgr is None:
        return _default_signals()

    h, w = bgr.shape[:2]

    # Movement estimation (Laplacian variance)
    movement = _estimate_movement(bgr)

    if MEDIAPIPE_TASKS_READY:
        return _analyze_with_mediapipe_tasks(bgr, h, w, movement)
    else:
        return _analyze_fallback(bgr, h, w, movement)


def _analyze_with_mediapipe_tasks(bgr, h, w, movement) -> dict:
    """Full analysis using mediapipe Tasks API."""
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    # Face landmarks
    face_result = _face_detector.detect(mp_image)
    attention = "low"
    head_tilt = "unknown"
    emotion = "neutral"
    emo_confidence = 50.0

    if face_result.face_landmarks:
        lm = face_result.face_landmarks[0]
        attention, head_tilt = _compute_attention_from_landmarks(lm, w, h)

        # Use blendshapes for emotion if available
        if face_result.face_blendshapes:
            emotion, emo_confidence = _emotion_from_blendshapes(
                face_result.face_blendshapes[0]
            )
        elif DEEPFACE_AVAILABLE:
            emotion, emo_confidence = _deepface_emotion(bgr)
        else:
            emotion, emo_confidence = _heuristic_emotion_from_landmarks(lm, w, h)

    elif DEEPFACE_AVAILABLE:
        emotion, emo_confidence = _deepface_emotion(bgr)

    # Pose
    posture = "neutral"
    if _pose_detector:
        pose_result = _pose_detector.detect(mp_image)
        if pose_result.pose_landmarks:
            posture = _compute_posture_from_landmarks(pose_result.pose_landmarks[0], h)

    return {
        "emotion": emotion,
        "confidence": round(emo_confidence, 2),
        "posture": posture,
        "attention": attention,
        "movement": movement,
        "head_tilt": head_tilt,
    }


def _analyze_fallback(bgr, h, w, movement) -> dict:
    """OpenCV-only analysis when mediapipe models aren't available."""
    emotion = "neutral"
    emo_confidence = 50.0
    attention = "medium"
    head_tilt = "centered"

    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    faces = _face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))

    if len(faces) > 0:
        x, y, fw, fh = faces[0]
        # Face position as proxy for attention
        cx = x + fw / 2
        frame_cx = w / 2
        offset_ratio = abs(cx - frame_cx) / (w / 2)
        if offset_ratio < 0.2:
            attention = "high"
            head_tilt = "centered"
        elif offset_ratio < 0.4:
            attention = "medium"
            head_tilt = "slight_turn"
        else:
            attention = "low"
            head_tilt = "looking_away"

        if DEEPFACE_AVAILABLE:
            emotion, emo_confidence = _deepface_emotion(bgr)
        else:
            emotion, emo_confidence = _opencv_heuristic_emotion(bgr, x, y, fw, fh)

    return {
        "emotion": emotion,
        "confidence": round(emo_confidence, 2),
        "posture": "neutral",  # no pose landmarks in fallback
        "attention": attention,
        "movement": movement,
        "head_tilt": head_tilt,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _compute_attention_from_landmarks(landmarks, w, h) -> tuple:
    """Compute yaw/pitch from face landmarks list."""
    def pt(idx):
        lm = landmarks[idx]
        return np.array([lm.x * w, lm.y * h, lm.z * w])

    nose = pt(1)
    left_eye = pt(33)
    right_eye = pt(263)
    chin = pt(152)

    eye_mid_x = (left_eye[0] + right_eye[0]) / 2
    face_width = abs(right_eye[0] - left_eye[0]) or 1
    yaw_ratio = abs(nose[0] - eye_mid_x) / face_width

    forehead = pt(10)
    face_height = abs(forehead[1] - chin[1]) or 1
    pitch_ratio = (nose[1] - forehead[1]) / face_height

    if yaw_ratio < 0.15 and 0.3 < pitch_ratio < 0.7:
        return "high", "centered"
    elif yaw_ratio < 0.35:
        return "medium", "slight_turn"
    else:
        return "low", "looking_away"


def _emotion_from_blendshapes(blendshapes) -> tuple:
    """
    Estimate emotion from MediaPipe face blendshapes.
    Blendshapes include mouthSmile, eyeSquint, browDown, etc.
    """
    scores = {bs.category_name: bs.score for bs in blendshapes}

    mouth_smile_l = scores.get("mouthSmileLeft", 0)
    mouth_smile_r = scores.get("mouthSmileRight", 0)
    smile = (mouth_smile_l + mouth_smile_r) / 2

    brow_down_l = scores.get("browDownLeft", 0)
    brow_down_r = scores.get("browDownRight", 0)
    brow_down = (brow_down_l + brow_down_r) / 2

    brow_inner = scores.get("browInnerUp", 0)
    mouth_open = scores.get("jawOpen", 0)
    mouth_frown_l = scores.get("mouthFrownLeft", 0)
    mouth_frown_r = scores.get("mouthFrownRight", 0)
    frown = (mouth_frown_l + mouth_frown_r) / 2

    eye_wide = scores.get("eyeWideLeft", 0)

    if smile > 0.4:
        return "happy", min(100, smile * 130)
    elif mouth_open > 0.5 and eye_wide > 0.3:
        return "surprised", min(100, mouth_open * 120)
    elif brow_down > 0.4 and frown > 0.2:
        return "angry", min(100, brow_down * 120)
    elif frown > 0.35 and brow_inner > 0.3:
        return "sad", min(100, frown * 120)
    elif brow_down > 0.3 and eye_wide < 0.1:
        return "disgusted", 60.0
    elif brow_inner > 0.4 and brow_down < 0.2:
        return "fearful", min(100, brow_inner * 130)
    else:
        return "neutral", 55.0


def _heuristic_emotion_from_landmarks(landmarks, w, h) -> tuple:
    """Geometry-based emotion fallback from face landmarks."""
    def pt(idx):
        lm = landmarks[idx]
        return (lm.x * w, lm.y * h)

    left_corner = pt(61)
    right_corner = pt(291)
    upper_lip = pt(13)
    lower_lip = pt(14)
    left_brow = pt(105)
    left_eye = pt(159)

    mouth_width = abs(right_corner[0] - left_corner[0])
    face_w = abs(pt(234)[0] - pt(454)[0]) or 1
    smile_ratio = mouth_width / face_w
    mouth_open = abs(lower_lip[1] - upper_lip[1])
    brow_raise = abs(left_brow[1] - left_eye[1])

    if mouth_open > 15 and brow_raise > 10:
        return "surprised", 65.0
    elif smile_ratio > 0.55:
        return "happy", 70.0
    elif brow_raise < 6:
        return "sad", 58.0
    return "neutral", 52.0


def _deepface_emotion(bgr) -> tuple:
    try:
        result = DeepFace.analyze(
            bgr, actions=["emotion"], enforce_detection=False, silent=True
        )
        if isinstance(result, list):
            result = result[0]
        dominant = result.get("dominant_emotion", "neutral")
        score = result.get("emotion", {}).get(dominant, 50.0)
        return dominant, float(score)
    except Exception:
        return "neutral", 50.0


def _compute_posture_from_landmarks(landmarks, h) -> str:
    """Classify posture from pose landmarks."""
    def y(idx):
        return landmarks[idx].y * h

    def x(idx):
        return landmarks[idx].x

    # PoseLandmark indices in mediapipe tasks
    LEFT_SHOULDER = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP = 23
    RIGHT_HIP = 24
    NOSE = 0

    left_sh_y = y(LEFT_SHOULDER)
    right_sh_y = y(RIGHT_SHOULDER)
    hip_mid_y = (y(LEFT_HIP) + y(RIGHT_HIP)) / 2
    sh_mid_y = (left_sh_y + right_sh_y) / 2
    sh_diff = abs(landmarks[LEFT_SHOULDER].y - landmarks[RIGHT_SHOULDER].y)
    nose_x = x(NOSE)
    sh_mid_x = (x(LEFT_SHOULDER) + x(RIGHT_SHOULDER)) / 2

    if sh_diff < 0.04 and sh_mid_y < hip_mid_y - 0.15:
        return "upright"
    elif abs(nose_x - sh_mid_x) > 0.07:
        return "leaning_forward"
    elif sh_mid_y > hip_mid_y - 0.05:
        return "slouched"
    return "neutral"


def _opencv_heuristic_emotion(bgr, x, y, fw, fh) -> tuple:
    """Simple brightness/saturation heuristic on face ROI."""
    face_roi = bgr[y:y+fh, x:x+fw]
    if face_roi.size == 0:
        return "neutral", 50.0
    hsv = cv2.cvtColor(face_roi, cv2.COLOR_BGR2HSV)
    mean_sat = hsv[:, :, 1].mean()
    mean_val = hsv[:, :, 2].mean()
    if mean_sat > 80 and mean_val > 140:
        return "happy", 62.0
    elif mean_val < 90:
        return "sad", 58.0
    return "neutral", 52.0


def _estimate_movement(bgr) -> str:
    """Estimate motion via Laplacian sharpness variance."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if var > 200:
        return "still"
    elif var > 80:
        return "moderate"
    return "restless"


def _default_signals() -> dict:
    return {
        "emotion": "neutral",
        "confidence": 50.0,
        "posture": "neutral",
        "attention": "medium",
        "movement": "moderate",
        "head_tilt": "centered",
    }


def analyze_audio_features(audio_features: dict) -> dict:
    """Validate and normalize audio feature signals."""
    valid_speeds = {"fast", "normal", "slow", "silent"}
    valid_pauses = {"frequent", "minimal", "none"}
    valid_tones = {"stressed", "calm", "neutral", "excited"}

    speech_speed = audio_features.get("speech_speed", "normal")
    pauses = audio_features.get("pauses", "minimal")
    tone_indicator = audio_features.get("tone_indicator", "neutral")

    return {
        "speech_speed": speech_speed if speech_speed in valid_speeds else "normal",
        "pauses": pauses if pauses in valid_pauses else "minimal",
        "tone_indicator": tone_indicator if tone_indicator in valid_tones else "neutral",
    }
