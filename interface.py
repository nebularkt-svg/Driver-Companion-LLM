# interface.py
from dataclasses import dataclass, field
from typing import Optional, Literal

EmotionLabel = Literal["angry", "sad", "fear", "happy", "neutral", "disgust", "surprise"]
TriggerReason = Literal["speech", "emotion_intervention", "companionship"]

@dataclass
class LLMInput:
    """
    Input format from FER team + STT team.

    Usage:
        inp = LLMInput(emotion="angry", speech_text="What is that driver doing!")
        inp = LLMInput(emotion="sad")   # No speech input
    """
    emotion: EmotionLabel
    speech_text: Optional[str] = None
    confidence: float = 1.0

@dataclass
class LLMOutput:
    """
    Output format from LLM module to TTS team.
    """
    response_text: str
    emotion_in: EmotionLabel
    triggered_by: TriggerReason
    model_used: str
    latency_ms: float
