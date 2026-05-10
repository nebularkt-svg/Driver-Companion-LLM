# trigger_control.py
import time
from typing import Optional

# Cooldown per emotion (seconds)
# Dangerous emotions = shorter cooldown (more urgent intervention)
COOLDOWN_BY_EMOTION = {
    "angry":    20,
    "fear":     15,
    "sad":      30,
    "disgust":  25,
    "surprise": 15,
    "happy":    60,
    "neutral":  90,
}

# Emotions that trigger proactive intervention even without speech
INTERVENTION_EMOTIONS = {"angry", "fear", "sad", "disgust", "surprise"}


class TriggerController:

    def __init__(self):
        self.last_trigger_time: float = 0
        self.last_emotion: Optional[str] = None
        self.trigger_count: int = 0

    def should_trigger(self, emotion: str, speech_text: Optional[str]) -> tuple[bool, str]:
        """
        Decide whether to trigger the LLM and why.

        Returns:
            (should_trigger, reason)
            reason: "speech" | "emotion_intervention" | "companionship" | "skip"
        """
        now = time.time()

        # Driver spoke — always respond
        if speech_text:
            return True, "speech"

        cooldown      = COOLDOWN_BY_EMOTION.get(emotion, 60)
        elapsed       = now - self.last_trigger_time
        still_cooling = elapsed < cooldown
        emotion_changed = emotion != self.last_emotion

        # Emotion just changed to a dangerous one — intervene immediately
        if emotion_changed and emotion in INTERVENTION_EMOTIONS:
            return True, "emotion_intervention"

        # Still within cooldown — skip
        if still_cooling:
            return False, "skip"

        # Cooldown passed, dangerous emotion — proactive intervention
        if emotion in INTERVENTION_EMOTIONS:
            return True, "emotion_intervention"

        # Cooldown passed, calm emotion — companionship
        return True, "companionship"

    def record_trigger(self, emotion: str):
        self.last_trigger_time = time.time()
        self.last_emotion = emotion
        self.trigger_count += 1

    def reset(self):
        self.last_trigger_time = 0
        self.last_emotion = None
        self.trigger_count = 0
