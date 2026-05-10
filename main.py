# main.py
import time
import asyncio
import os
import threading
from typing import Optional

import edge_tts
import pygame

from interface import LLMInput, LLMOutput
from prompt_builder import build_messages
from llm_client import call_llm
from trigger_control import TriggerController
from conversation import ConversationMemory

# ── TTS config ───────────────────────────────────────────────
VOICE = "en-US-AriaNeural"   # change to en-US-GuyNeural for male voice
TTS_FILE = "response.mp3"


async def _synthesize(text: str):
    """Convert text to mp3 using edge-tts."""
    communicate = edge_tts.Communicate(text, voice=VOICE)
    await communicate.save(TTS_FILE)


def speak(text: str):
    """Synthesize and play TTS audio (blocking)."""
    try:
        asyncio.run(_synthesize(text))
        pygame.mixer.init()
        pygame.mixer.music.load(TTS_FILE)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.music.unload()
    except Exception as e:
        print(f"[TTS] Error: {e}")


def speak_async(text: str):
    """Speak in background thread so it doesn't block the CLI."""
    threading.Thread(target=speak, args=(text,), daemon=True).start()


# ── Main LLM class ───────────────────────────────────────────
class CalmWheelLLM:
    """
    Main LLM module class.

    Teammate usage:
        llm = CalmWheelLLM()
        output = llm.process(LLMInput(emotion="angry", speech_text="What is that driver doing!"))
        if output:
            tts.speak(output.response_text)
    """

    def __init__(self, mode: str = "online", model_key: str = None, tts: bool = True):
        """
        Args:
            mode:      "online" | "offline" | "auto"
            model_key: specific model to use, None = default
            tts:       enable voice output
        """
        self.mode      = mode
        self.model_key = model_key
        self.tts       = tts
        self.trigger   = TriggerController()
        self.memory    = ConversationMemory(max_turns=6)

    def process(self, inp: LLMInput) -> Optional[LLMOutput]:
        """
        Main entry point. Returns None if cooldown is active.
        """
        should, reason = self.trigger.should_trigger(inp.emotion, inp.speech_text)
        if not should:
            return None

        messages = build_messages(
            emotion=inp.emotion,
            speech_text=inp.speech_text,
            trigger_reason=reason,
            conversation_history=self.memory.get_history(),
        )

        start = time.time()
        try:
            response_text, model_used = call_llm(
                messages=messages,
                model_key=self.model_key,
                mode=self.mode,
            )
        except Exception as e:
            print(f"[CalmWheelLLM] Call failed: {e}")
            return None

        latency_ms = (time.time() - start) * 1000

        self.trigger.record_trigger(inp.emotion)
        if inp.speech_text:
            self.memory.add_user(inp.speech_text, emotion=inp.emotion)
        self.memory.add_assistant(response_text)

        # Speak the response
        if self.tts:
            speak_async(response_text)

        return LLMOutput(
            response_text=response_text,
            emotion_in=inp.emotion,
            triggered_by=reason,
            model_used=model_used,
            latency_ms=round(latency_ms, 1),
        )

    def new_trip(self):
        """Call this at the start of a new driving session."""
        self.trigger.reset()
        self.memory.reset()
        print("[CalmWheelLLM] New trip started — memory cleared")


# ── Interactive CLI test ─────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("CalmWheel LLM Module — Interactive Test")
    print("=" * 50)
    print("Input format:  <emotion> [spoken text]")
    print("Emotions:      angry / sad / fear / happy / neutral / disgust / surprise")
    print("Examples:")
    print("  >> angry  What is that driver doing!")
    print("  >> sad")
    print("  >> happy  Great day today!")
    print("Commands:      reset = new trip  |  mute = toggle voice  |  quit = exit")
    print("=" * 50 + "\n")

    llm = CalmWheelLLM(mode="online", tts=True)

    while True:
        try:
            raw = input(">> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if raw == "quit":
            break
        if raw == "reset":
            llm.new_trip()
            continue
        if raw == "mute":
            llm.tts = not llm.tts
            state = "ON" if llm.tts else "OFF"
            print(f"[Voice {state}]\n")
            continue
        if not raw:
            continue

        parts   = raw.split(maxsplit=1)
        emotion = parts[0].lower()
        speech  = parts[1] if len(parts) > 1 else None

        valid = {"angry", "sad", "fear", "happy", "neutral", "disgust", "surprise"}
        if emotion not in valid:
            print(f"Invalid emotion. Choose from: {valid}\n")
            continue

        inp    = LLMInput(emotion=emotion, speech_text=speech)
        output = llm.process(inp)

        if output is None:
            print("[Skipped] Cooldown active — no response triggered\n")
        else:
            print(f"\nCalmWheel [{output.triggered_by} | {output.model_used} | {output.latency_ms}ms]:")
            print(f"  {output.response_text}\n")
            print(llm.memory.summary() + "\n")
