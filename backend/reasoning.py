"""
reasoning.py – CogniSync Agent Reasoning Engine

Deep psychology-based advice using:
- FBI / Scotland Yard negotiation (Chris Voss: tactical empathy, mirroring, labeling)
- Cialdini's 6 Principles of Influence
- Emotional Intelligence (Goleman)
- Nonverbal dominance / submission signals (Navarro, Cuddy)
- OCEAN personality inference from real-time behavior
- Cognitive Behavioral Signal Interpretation
"""
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    LLM_PROVIDER = "gemini"
elif OPENAI_API_KEY:
    LLM_PROVIDER = "openai"
else:
    LLM_PROVIDER = "fallback"

if LLM_PROVIDER == "openai":
    from openai import OpenAI
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
elif LLM_PROVIDER == "gemini":
    from google import genai as google_genai
    gemini_client = google_genai.Client(api_key=GEMINI_API_KEY)


SYSTEM_PROMPT = """You are CogniSync, an elite real-time behavioral intelligence agent trained in FBI hostage negotiation (Chris Voss), Cialdini's influence principles, emotional intelligence (Goleman), and nonverbal signal analysis (Navarro).

Your task: analyze live multi-modal signals and give ONE sharp, specific, actionable tactical intervention — 1 to 2 sentences max.

RULES:
1. NEVER say generic things like "maintain your approach" or "watch for shifts."
2. Always reference the SPECIFIC signal you're responding to.
3. Suggest a SPECIFIC action: a question to ask, phrase to say, silence to hold, or body language to mirror.
4. If the same state has persisted for multiple frames, suggest a DIFFERENT technique than a basic rapport-builder.
5. Be direct, tactical, think like an intelligence analyst.
6. Reference the trend if something changed across the last 2-3 states.
"""


def _build_prompt(current: dict, history: list, alerts: list) -> str:
    audio = current.get("audio", {})
    emotion = current["emotion"]
    posture = current["posture"]
    attention = current["attention"]
    movement = current["movement"]
    engagement = current["engagement_score"]
    stress = current["stress_score"]
    confidence = current["confidence_score"]

    trend_text = ""
    if len(history) >= 2:
        prev = history[-1]
        eng_delta = engagement - prev["engagement_score"]
        stress_delta = stress - prev["stress_score"]
        conf_delta = confidence - prev["confidence_score"]
        trend_text = (
            f"\nTREND: Engagement {'+' if eng_delta>=0 else ''}{eng_delta:.0f}% "
            f"| Stress {'+' if stress_delta>=0 else ''}{stress_delta:.0f}% "
            f"| Confidence {'+' if conf_delta>=0 else ''}{conf_delta:.0f}%"
        )
    if len(history) >= 3:
        past_emotions = [h["emotion"] for h in history[-3:]]
        trend_text += f"\nEmotion sequence: {' → '.join(past_emotions)} → {emotion}"

    alert_text = f"\nACTIVE ALERTS: {'; '.join(alerts)}" if alerts else ""

    return (
        f"LIVE SIGNALS:\n"
        f"Emotion: {emotion} | Posture: {posture} | Attention: {attention} | Movement: {movement}\n"
        f"Speech: {audio.get('speech_speed','normal')} | Pauses: {audio.get('pauses','minimal')} | Tone: {audio.get('tone_indicator','neutral')}\n"
        f"Engagement: {engagement:.0f}% | Stress: {stress:.0f}% | Confidence: {confidence:.0f}%"
        f"{trend_text}{alert_text}\n\n"
        f"Provide ONE tactical intervention (1-2 sentences). Be specific, psychological, actionable."
    )


def get_agent_advice(current: dict, history: list, alerts: list) -> str:
    prompt = _build_prompt(current, history, alerts)
    if LLM_PROVIDER == "openai":
        return _call_openai(prompt)
    elif LLM_PROVIDER == "gemini":
        return _call_gemini(prompt, current, history, alerts)
    return _psychology_fallback(current, history, alerts)


def _call_openai(prompt: str) -> str:
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=120,
            temperature=0.85,
            timeout=5.0,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None  # caller will use psychology fallback


def _call_gemini(prompt: str, current: dict, history: list, alerts: list) -> str:
    """
    Call Gemini via direct REST API (works with AI Studio AIza... keys).
    The google-genai SDK v1.64 returns NOT_FOUND for AI Studio keys with v1beta endpoint.
    """
    import httpx
    key = GEMINI_API_KEY
    full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash:generateContent?key={key}"
    )
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 120,
            "temperature": 0.85,
        },
    }
    try:
        r = httpx.post(url, json=payload, timeout=8.0)
        if r.status_code == 200:
            data = r.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        # Non-200: log and fall through to psychology engine
        print(f"[CogniSync] Gemini API error {r.status_code}: {r.text[:120]}")
    except Exception as e:
        print(f"[CogniSync] Gemini request failed: {e}")
    # Always fall back with REAL signal data, not empty dicts
    return _psychology_fallback(current, history, alerts)



# ─────────────────────────────────────────────────────────────────────────────
# DEEP PSYCHOLOGY FALLBACK ENGINE
# ─────────────────────────────────────────────────────────────────────────────

# Rotation: each TACTICS key maps to a LIST of 3 tactics.
# Every ROTATION_EVERY frames of the same key, the next tactic in the list is used.
ROTATION_EVERY = 4

_key_hit_counts: dict = {}
_last_key = [None]


def _get_tactic(key) -> str:
    """Return the next rotating tactic for this key."""
    if _last_key[0] != key:
        # State changed — reset old key's counter
        if _last_key[0]:
            _key_hit_counts.pop(_last_key[0], None)
        _last_key[0] = key

    hits = _key_hit_counts.get(key, 0)
    _key_hit_counts[key] = hits + 1

    entry = TACTICS.get(key)
    if entry is None:
        return None
    if isinstance(entry, str):
        return entry
    idx = (hits // ROTATION_EVERY) % len(entry)
    return entry[idx]


def _zone(val: float, low: float = 35, high: float = 65) -> str:
    if val < low:
        return "low"
    if val > high:
        return "high"
    return "mid"


# Each entry: list of 3 tactics [initial → deeper → escalation]
TACTICS = {

    # ── LOW ATTENTION ─────────────────────────────────────────────────────────
    ("neutral", "low", "low", "low"): [
        "Gaze drifted + engagement collapsed — pattern interrupt: call their name, hold 3 seconds of silence, then ask ONE question: 'What's actually on your mind right now?'",
        "Still disengaged after the interrupt. Abandon the current frame entirely. Ask: 'If we set aside everything discussed so far — what do YOU think the real issue is?'",
        "Prolonged disengagement with calm signals = boredom. Use the Ben Franklin effect: ask them to help you with something small. Requested effort re-activates investment.",
    ],
    ("neutral", "low", "mid", "low"): [
        "Attention lost under stress — they're mentally elsewhere under pressure. Stop all content. Ask: 'What's the one thing that needs to be resolved for you to stay present here?'",
        "Still distracted under stress. Their working memory is saturated. Strip down to ONE sentence, then stay silent — give their brain space to surface what's blocking them.",
        "Sustained stress-distraction. Name it directly: 'It feels like something outside this conversation is competing for your attention.' Naming the distraction often dissolves it.",
    ],
    ("neutral", "low", "low", "mid"): [
        "Mild attention drift. Deploy the Ben Franklin effect: ask a small favor or genuine opinion to re-activate investment. Effort creates engagement.",
        "Still wandering. Introduce a surprising fact or unexpected reframe to trigger a novelty response and pull focus back.",
        "Try an information gap hook: reveal one piece of information they don't know yet, then pause. The gap creates an itch that re-engages attention automatically.",
    ],
    ("neutral", "low", "mid", "mid"): [
        "Attention fracturing under moderate stress. Ask: 'If you had to rank the priorities right now, what comes first?' Decision-making forces re-engagement.",
        "Still split-attention. Strip your message to ONE sentence, hold silence, don't fill it. Let them break the silence — what they say next is your real intelligence.",
        "Still distracted. Reframe by asking for their story from the beginning: narrative mode re-engages the prefrontal cortex.",
    ],

    # ── NEUTRAL / ANALYTICAL ──────────────────────────────────────────────────
    ("neutral", "high", "low", "high"): [
        "Peak analytical state — focused gaze, calm signals. Introduce your strongest data point and follow with: 'What specific outcome matters most to you?'",
        "Still in analytical mode. Use the 'Columbo technique': ask a deceptively simple question about a complex topic. Their detailed answer reveals exactly what they care about.",
        "Sustained high focus. Deploy your core message and hold silence. Analytically-dominant people perceive silence as confidence, not weakness.",
    ],
    ("neutral", "high", "low", "mid"): [
        "Low stress, high attention — clean slate. Deploy 'commitment and consistency': ask a small yes-question first: 'Would you agree that X is the main priority here?'",
        "Still focused and calm. Use authority anchoring: cite a specific credible source before your point. Authority cues double retention in calm attentive listeners.",
        "Sustained attentive baseline. Introduce a contrast: show where things could be different. Contrast drives decisions even when emotional arousal is low.",
    ],
    ("neutral", "medium", "low", "high"): [
        "Good engagement with calm physiology — ideal for rapport deepening. Mirror their vocabulary, sentence length, and pace precisely.",
        "Sustained high engagement. Use progressive disclosure — one new piece of information at a time. Scarcity of information increases perceived value.",
        "Long-duration high-engagement state. Ask your most important question now — they are mentally ready to engage at depth.",
    ],
    ("neutral", "medium", "low", "mid"): [
        "Stable moderate engagement — rapport territory. Use strategic mirroring: repeat their last 2-3 words as a question to deepen their explanation and signal deep listening.",
        "Continued stable baseline. Ask: 'How does this connect to what matters most to you?' Open-ended questions build psychological intimacy and increase investment.",
        "Sustained stable state. Deploy a label: 'It seems like you're carefully considering the implications here.' A well-placed label makes them feel deeply understood.",
    ],
    ("neutral", "medium", "mid", "mid"): [
        "Moderate stress with partial engagement — say less, ask more. Questions generate lower cognitive load than statements.",
        "Continued mid-stress. Use a 'no'-oriented question: 'Would it be unreasonable to say you'd prefer to slow down here?' Gives them control and releases pressure.",
        "Persisting mid-stress. Try reframing entirely: introduce a third perspective neither of you has discussed. Novel frames release cognitive tension.",
    ],
    ("neutral", "high", "mid", "high"): [
        "High attention + rising stress = cognitive load building. FBI technique: slow your speech 20%, drop pitch, label: 'It seems like you're weighing something carefully…'",
        "High engagement under moderate stress. Ask expansively: 'If pressure weren't a factor at all, what would you do?' Removes the stress frame momentarily.",
        "Sustained stress under high attention. Use the 'accusation audit': name every objection you think they have before they voice it. Anticipating resistance disarms it.",
    ],

    # ── HAPPY ─────────────────────────────────────────────────────────────────
    ("happy", "high", "low", "high"): [
        "Buying signal — smile, upright posture, full attention. This is your close window. Use the assumptive close: 'So the next step would be…' — transition as if agreement is made.",
        "Still at peak positive state. Switch to a choice close: 'Would you prefer to start with X or Y?' Either answer advances things forward.",
        "Sustained happiness + high engagement. Activate social proof NOW: 'Others in your exact situation chose this path because…' Positive states make social proof 3× more effective.",
    ],
    ("happy", "high", "low", "mid"): [
        "Positive affect + focused attention = likability peak. Activate reciprocity: share something exclusive or personal to cement the connection before your key ask.",
        "Still at likability peak. Express a genuine point of commonality — perceived similarity is one of the fastest compliance triggers known.",
        "Sustained positive engagement. Tell a relevant success story about someone similar to them. Story activates mirror neurons and bypasses analytical resistance.",
    ],
    ("happy", "medium", "low", "high"): [
        "Relaxed happiness + high engagement — perfect for social proof. Reference: 'Others in this situation have found that…' to anchor your proposal in consensus.",
        "Positive state, moderate attention. Ask for their gut reaction: 'What's your instinct on this?' Gut-level questions deepen investment in outcomes.",
        "Sustained positive state. Use future-pacing: 'Imagine six months from now this worked — what changed?' Future projection in a positive state is highly generative.",
    ],
    ("happy", "high", "mid", "high"): [
        "Joy + slight stress — excitement or performance anxiety. Channel it: 'If this worked perfectly, what would that look like for you?'",
        "Continued positive arousal. Use 'foot in the door': make your smallest possible ask first. Success with small asks primes compliance for larger ones.",
        "Sustained excited state. Connect to their identity: 'This fits someone who values X — and from everything you've said, that's exactly who you are.' Identity framing is deeply motivating.",
    ],

    # ── SURPRISED ─────────────────────────────────────────────────────────────
    ("surprised", "high", "low", "high"): [
        "Peak curiosity window — elevated brows, wide eyes. Deliver your single strongest point RIGHT NOW while the dopamine spike is active. Hesitation closes this window in 8 seconds.",
        "Still in curiosity state. Stack a second surprise layer: 'And what makes this even more compelling is…' Stacked surprises compound the dopamine response.",
        "Sustained surprise = genuine fascination. Transition to co-creation: 'What would YOU do with this information?' Co-creation in curiosity state is extremely productive.",
    ],
    ("surprised", "high", "mid", "mid"): [
        "Surprise + moderate stress — new information is creating cognitive dissonance. Hold silence for 5 seconds, then ask: 'What's your first reaction to that?'",
        "Still processing. Ask: 'What part of this is most unexpected to you?' Surfaces their actual objection or point of fascination — critical intelligence.",
        "Continued surprise-processing. Use an accusation audit: name all the doubts you think they're having. Naming eliminates resistance faster than overcoming it.",
    ],
    ("surprised", "medium", "mid", "mid"): [
        "Mild surprise with moderate engagement — processing is happening. Use the accusation audit: preemptively name their concern before they voice it.",
        "Still processing mildly. Ask: 'What would need to be true for this to make complete sense to you?' Question converts surprise into a solvable frame.",
        "Sustained mild surprise. Introduce additional supporting evidence — people in a curiosity state absorb information more quickly than in any other state.",
    ],

    # ── FEARFUL ───────────────────────────────────────────────────────────────
    ("fearful", "low", "high", "low"): [
        "Fight-or-flight activated — body withdrawal, speech pauses. STOP all arguments. Label: 'It seems like this feels overwhelming right now.' Then wait silently.",
        "Still in fear state — amygdala hijacked, logic inaccessible. Offer an off-ramp: 'We don't need to solve this right now. What would make this feel less urgent?'",
        "Prolonged fear. Match your pace to a calm FM DJ voice: very slow, warm, deliberate. Their nervous system will entrain to your calm signals within 90 seconds.",
    ],
    ("fearful", "medium", "high", "low"): [
        "Stress flooding with partial attention. Ask a 'no'-oriented question: 'Would it be wrong to say you need more time on this?' Restores control.",
        "Fear persisting. Label the internal experience: 'It seems like there's a concern that hasn't been voiced yet.' Creates permission to surface the real objection.",
        "Sustained fear-partial-attention mix. Validate completely BEFORE introducing any counter-information. Validation before information is the FBI protocol.",
    ],
    ("fearful", "low", "high", "mid"): [
        "Fear state with moderate engagement — they want to engage but feel unsafe. Validate fully: 'That concern makes complete sense given what you've described.'",
        "Still fearful but engaged. Create psychological safety: 'There's no wrong answer here — I'm genuinely trying to understand your perspective.' Safety unlocks re-engagement.",
        "Prolonged fear-engagement mix. Ask: 'What specifically would need to be true for you to feel confident moving forward?' Converts anxiety into a solvable problem.",
    ],
    ("fearful", "medium", "mid", "mid"): [
        "Mild anxiety — this is buying anxiety, not rejection. Use 'That's right': summarize their position so accurately they feel completely understood.",
        "Continued mild anxiety. Introduce future certainty: describe a specific positive future involving them. Certainty of outcome reduces anxiety biologically.",
        "Persistent low-grade anxiety. Ask: 'What's the one thing that would eliminate that concern?' Directs their energy toward solutions rather than problems.",
    ],

    # ── ANGRY ─────────────────────────────────────────────────────────────────
    ("angry", "medium", "high", "low"): [
        "Anger spike — jaw tension, restless movement. Do NOT match energy. Lower your volume 30%, let them finish, then label: 'It sounds like this has been frustrating for a long time.'",
        "Anger persisting. Use minimal encouragers — say only 'go on' or 'tell me more'. People cannot sustain anger while feeling genuinely heard.",
        "Sustained anger + low engagement: a core need is unmet. Ask: 'What do you actually need from this situation?' — shift from positions to underlying needs.",
    ],
    ("angry", "low", "high", "low"): [
        "Hot anger + disengagement — they've mentally left. Emergency pivot: 'Help me understand — what would have to change for this to work for you?' Ask ONLY about their perspective.",
        "Still angry and gone. Acknowledge without defending: 'I hear that this is not working. That matters.' Pure acknowledgment without defense.",
        "Prolonged anger-disengagement. Give them power: 'What would you do differently if you were in charge of this?' Positions them as the expert.",
    ],
    ("angry", "medium", "high", "mid"): [
        "Irritation + partial engagement — they feel unheard. Mirror their last key phrase as a question. Mirroring reduces defensiveness by 40% in under 60 seconds.",
        "Still irritated but present. Use the power of apology: take responsibility for something — even small — related to their frustration. Accountability deflates anger.",
        "Continued irritation-engagement mix. Ask: 'What's the most important thing I've missed about your position?' Positions them as expert, you as student.",
    ],
    ("angry", "high", "mid", "mid"): [
        "Agitation + attention still present — channel this energy. Ask a challenge question: 'What's the one thing that would change your mind?' Resistance hides high investment.",
        "Continued engagement under agitation. Name the strength behind their anger: 'The fact you feel this strongly shows how much you care about getting this right.'",
        "Sustained engaged-agitation. Give them a win: 'You're right about X — completely right. Given that, how do we move forward?' Partial agreement creates momentum.",
    ],

    # ── SAD ───────────────────────────────────────────────────────────────────
    ("sad", "low", "low", "low"): [
        "Withdrawal state — low energy, downward gaze. Activate reciprocity through vulnerability: share a relevant personal struggle BEFORE asking anything.",
        "Still withdrawn. Ask for their story: 'What happened that brought you to this point?' Listen for 2 full minutes without interjecting.",
        "Prolonged withdrawal. Introduce possibility slowly: 'If things were just 10% better — what would that look like?' Small future-pacing reopens possibility without pressure.",
    ],
    ("sad", "medium", "low", "low"): [
        "Mild sadness with partial attention. Ask for their story: 'What happened that brought you to this point?' People in sadness bond through narrative.",
        "Continued sad-partial engagement. Deepen empathy: 'What's the hardest part of all of this for you?' The hardest part is where the real need lives.",
        "Sustained ambivalent-sad state. Use the miracle question: 'If you woke up tomorrow and the problem was gone — how would you know?' Bypasses resistance and activates motivation.",
    ],
    ("sad", "low", "mid", "low"): [
        "Subdued affect signaling low confidence. Use Late Night FM DJ voice: slow, warm, measured. Reflect their emotion before any content: 'This clearly matters to you deeply.'",
        "Still subdued. Introduce possibility: 'What would need to change for this to feel different?' Asking about change implies change is possible — a powerful reframe.",
        "Prolonged subdued state. Ask about the best version of the situation: 'When has this worked well in the past?' Access to positive memory resources often shifts affect.",
    ],
    ("sad", "medium", "mid", "mid"): [
        "Sadness + moderate engagement — ambivalence. Use contrast principle: paint the gap between where they are and where they could be. Emotion follows vision.",
        "Persistent sadness with partial engagement. Deepen empathy: 'What's the hardest part of all of this for you?' Then listen fully without adding content.",
        "Sustained ambivalent-sad state. Use the miracle question: 'If you woke up and the problem was solved — how would you know?' Activates motivation directly.",
    ],

    # ── DISGUSTED ─────────────────────────────────────────────────────────────
    ("disgusted", "low", "mid", "low"): [
        "Value mismatch — micro-disgust + low attention. Pivot immediately: 'I sense that landed differently than intended — what part concerns you most?'",
        "Value mismatch persisting. Don't defend the previous frame. Ask what matters most to them and rebuild your position from their anchor point.",
        "Persistent value misalignment. Use inversion: present the OPPOSITE position and ask them to critique it. They'll often argue themselves into your actual position.",
    ],
    ("disgusted", "medium", "mid", "mid"): [
        "Subtle rejection — framing isn't resonating. Framing reboot: present the same idea through a completely different lens — individual vs. team, process vs. results.",
        "Continued value friction. Use 'the third story': how would a neutral third party see this situation? Outside perspective breaks in-frame deadlocks.",
        "Sustained misalignment. Find ONE point of genuine agreement and anchor everything else to it. Agreement on any shared value creates a psychological bridge.",
    ],

    # ── CRISIS TACTICS (alert-driven, rotate through 3 approaches) ────────────
    "__engagement_drop__": [
        "Engagement dropping fast. Pattern interrupt: ask their opinion directly, or call it out openly: 'I can see we've hit something — what's on your mind?'",
        "Engagement still falling. Abandon your current agenda. Ask: 'What would make this conversation worth your time?' Let their answer restructure everything.",
        "Engagement collapse continuing. Radical transparency: 'I feel like I've lost you somewhere — where did this stop working?' Meta-commentary often resets the conversation.",
    ],
    "__stress_spike__": [
        "Stress cascading across all signals. Drop to one sentence, slow your breathing visibly, then give them a choice: 'What feels right to you?' Agency dissolves stress.",
        "Stress still elevated. Remove all demands: 'We don't have to solve this today — what would feel manageable to discuss right now?'",
        "Sustained stress spike. Use the paradoxical injunction: 'Take as long as you need — there's no rush at all.' Removing time pressure often accelerates resolution.",
    ],
    "__inconsistency__": [
        "Mixed signals — smiling but stress rising. Leakage event. Deploy: 'What aren't we talking about that we should be?' Name the meta-level directly.",
        "Behavioral inconsistency persisting. Ask: 'Your body seems to be saying something your words aren't — what's the real concern here?'",
        "Continued signal contradiction. Try a soft confrontation: 'I notice you say X but I'm getting a different sense — am I reading that wrong?'",
    ],
    "__attention_lost__": [
        "Attention has left — gaze and posture confirm cognitive disengagement. Stop all content. Call their name once, ask: 'What's the most important thing you need from this conversation right now?' Hold 10 seconds of silence.",
        "Still disengaged. Full pattern interrupt: physically reposition, lower your voice to near-whisper, and say only: 'Let me start over.' Novelty and humility together reset attention.",
        "Prolonged disengagement. This conversation needs an exit and restart. Say: 'Let's pause — when would be a better time to continue this?' Graceful exits preserve future access.",
    ],
}

# Rotating fallback pool for purely stable baseline readings
_default_pool = [
    "Stable baseline — all signals calm. Deploy strategic silence: stop talking for 5 seconds and observe micro-reactions. Silence reveals resistance that speech hides.",
    "Neutral baseline. Use the 'summary label': restate their key position verbatim and ask '…is that right?' It triggers the 'That's right' trust response.",
    "Stable environment. Plant a calibrated question: 'What matters most to you in making this decision?' Then listen without interrupting for 90 seconds.",
    "Baseline stable. Apply Cialdini's scarcity principle: introduce a genuine constraint — time or availability. Scarcity elevates perceived value even in calm states.",
    "Consistent stable signals. Use progressive disclosure — share your second most compelling point now, saving the strongest for when engagement peaks.",
    "Clean baseline. Use behavioral mirroring: match their posture, gesture frequency, and breathing pace. Synchrony increases trust by 32% and compliance by 26%.",
    "Signals stable. Deploy an I-statement: 'I'm trying to understand your perspective fully before forming my own.' Epistemic humility paradoxically builds authority.",
    "Sustained neutral. Ask a genuine curiosity question — something you actually don't know the answer to about their situation. Authentic curiosity is one of the rarest and most disarming interpersonal signals.",
]
_default_idx = [0]


def _psychology_fallback(current: dict, history: list, alerts: list) -> str:
    """Deep psychology rule-based advice engine with per-state rotation."""
    emotion = current.get("emotion", "neutral")
    attention = current.get("attention", "medium")
    stress = current.get("stress_score", 20.0)
    engagement = current.get("engagement_score", 50.0)

    s_zone = _zone(stress)
    e_zone = _zone(engagement)

    # ── 1. Alert-based tactics (highest priority) ─────────────────────────────
    if alerts:
        if any(kw in a for a in alerts for kw in ("Attention", "attention", "disengaged", "Disengaged")):
            return _get_tactic("__attention_lost__")
        if any("Engagement dropping" in a or "Very low engagement" in a for a in alerts):
            return _get_tactic("__engagement_drop__")
        if any("Stress" in a or "stress" in a.lower() for a in alerts):
            return _get_tactic("__stress_spike__")
        if any("Inconsistent" in a for a in alerts):
            return _get_tactic("__inconsistency__")

    # ── 2. Cross-state trend detection ───────────────────────────────────────
    if len(history) >= 3:
        eng_trend = engagement - history[-3].get("engagement_score", engagement)
        stress_trend = stress - history[-3].get("stress_score", stress)
        if eng_trend < -15:
            return _get_tactic("__engagement_drop__")
        if stress_trend > 15:
            return _get_tactic("__stress_spike__")
        emotions = [h.get("emotion", "neutral") for h in history[-3:]] + [emotion]
        if len(set(emotions)) >= 3:
            return _get_tactic("__inconsistency__")

    # ── 3. Hard overrides before TACTICS lookup ───────────────────────────────
    if attention == "low":
        key = (emotion, "low", s_zone, e_zone)
        result = _get_tactic(key)
        if result:
            return result
        # Fallback for low-attention states not in dict
        return _get_tactic("__attention_lost__")

    if stress > 65:
        key = (emotion, attention, "high", e_zone)
        result = _get_tactic(key)
        if result:
            return result
        return _get_tactic("__stress_spike__")

    if engagement < 30:
        return _get_tactic("__engagement_drop__")

    # ── 4. Exact TACTICS lookup then fuzzy match ──────────────────────────────
    key = (emotion, attention, s_zone, e_zone)
    result = _get_tactic(key)
    if result:
        return result

    # Fuzzy: preserve attention level first, then relax one dimension at a time
    for fuzzy_key in [
        (emotion, attention, "mid", e_zone),
        (emotion, attention, s_zone, "mid"),
        (emotion, attention, "mid", "mid"),
        (emotion, "medium", s_zone, e_zone),
        (emotion, "medium", "mid", e_zone),
        (emotion, "medium", "mid", "mid"),
    ]:
        result = _get_tactic(fuzzy_key)
        if result:
            return result

    # ── 5. Optimal state shortcut ─────────────────────────────────────────────
    if engagement > 70 and stress < 35:
        return (
            "You're in the 'flow state' window — emotional safety and cognitive engagement "
            "are both high. This is your highest-leverage moment. Make your most important "
            "ask or deliver your key message NOW."
        )

    # ── 6. Rotating default ───────────────────────────────────────────────────
    idx = _default_idx[0] % len(_default_pool)
    _default_idx[0] += 1
    return _default_pool[idx]
