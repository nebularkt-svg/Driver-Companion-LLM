# Driver Companion LLM

This repository contains the English dialogue module for CalmWheel, a companion component of the [Driver-Emotion-recognition project](https://github.com/nebularkt-svg/Driver-Emotion-recognition). It accepts an emotion label and optional speech transcript from upstream components, builds an emotion-aware prompt, and returns a response with trigger, model and latency information.

- [main.py](main.py) coordinates response generation and optional text-to-speech.
- [interface.py](interface.py) defines the input and output data classes.
- [prompt_builder.py](prompt_builder.py) and [emotion_strategy.py](emotion_strategy.py) turn an emotion label and conversation context into messages.
- [trigger_control.py](trigger_control.py) and [conversation.py](conversation.py) implement response gating, cooldowns and short conversation history.
- [llm_client.py](llm_client.py) supports OpenRouter online and Ollama locally, with an automatic fallback mode.
- [benchmark.py](benchmark.py) compares configured model backends.

## Quick start

Install dependencies with `python -m pip install -r requirements.txt`. For online mode, set `OPENROUTER_API_KEY` in your environment before running the sample. For offline mode, run Ollama locally and make the configured local model available. The default local model is `gemma3:4b`.

```python
from interface import LLMInput
from main import CalmWheelLLM

companion = CalmWheelLLM(mode="offline", tts=False)
result = companion.process(
    LLMInput(emotion="neutral", speech_text="I have a long drive ahead.")
)
if result:
    print(result.response_text)
```

Set `tts=True` to enable the original Edge TTS and pygame audio path. This module receives emotion and transcript inputs from callers, so it can be exercised without a camera or microphone.
