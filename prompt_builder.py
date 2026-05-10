# prompt_builder.py
from typing import Optional, List, Dict
from emotion_strategy import build_system_prompt


def build_messages(
    emotion: str,
    speech_text: Optional[str],
    trigger_reason: str,
    conversation_history: Optional[List[Dict]] = None
) -> List[Dict]:
    """
    Build the full messages list to send to the LLM.

    Args:
        emotion:              emotion label
        speech_text:          STT transcription, None if driver didn't speak
        trigger_reason:       "speech" | "emotion_intervention" | "companionship"
        conversation_history: past turns for multi-turn memory (optional)

    Returns:
        OpenAI-format messages list
    """
    system_prompt = build_system_prompt(emotion)

    if trigger_reason == "speech" and speech_text:
        user_content = f'The driver said: "{speech_text}"'

    elif trigger_reason == "emotion_intervention":
        intervention_hints = {
            "angry":   "The driver hasn't spoken, but strong anger is detected. Proactively offer a calming response.",
            "sad":     "The driver hasn't spoken, but low mood is detected. Gently express companionship.",
            "fear":    "The driver hasn't spoken, but anxiety is detected. Provide a grounding, stabilizing response.",
            "disgust": "The driver hasn't spoken, but irritation is detected. Proactively offer a brief calming response.",
            "surprise":"The driver hasn't spoken, but a sudden emotional shift is detected. Check in on them.",
        }
        user_content = intervention_hints.get(
            emotion,
            f"The driver hasn't spoken. Emotion detected: {emotion}. Respond according to strategy."
        )

    else:
        # companionship — neutral/happy state, anti-fatigue
        user_content = "The driver is calm and has been driving for a while. Offer a brief, natural companion message."

    messages = [{"role": "system", "content": system_prompt}]

    if conversation_history:
        messages.extend(conversation_history)

    messages.append({"role": "user", "content": user_content})
    return messages
