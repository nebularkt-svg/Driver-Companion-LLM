# conversation.py
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Turn:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    emotion: Optional[str] = None


class ConversationMemory:
    """
    Stores conversation history for a single driving session.
    Call reset() at the start of a new trip.
    """

    def __init__(self, max_turns: int = 6):
        self.max_turns = max_turns
        self.turns: List[Turn] = []

    def add_user(self, content: str, emotion: str = None):
        self.turns.append(Turn(role="user", content=content, emotion=emotion))
        self._trim()

    def add_assistant(self, content: str):
        self.turns.append(Turn(role="assistant", content=content))
        self._trim()

    def get_history(self) -> List[Dict]:
        return [{"role": t.role, "content": t.content} for t in self.turns]

    def reset(self):
        self.turns = []

    def _trim(self):
        max_messages = self.max_turns * 2
        if len(self.turns) > max_messages:
            self.turns = self.turns[-max_messages:]

    def summary(self) -> str:
        lines = [f"[Memory] {len(self.turns)} turns stored"]
        for t in self.turns:
            preview    = t.content[:40] + "..." if len(t.content) > 40 else t.content
            emotion_tag = f" [{t.emotion}]" if t.emotion else ""
            lines.append(f"  {t.role}{emotion_tag}: {preview}")
        return "\n".join(lines)
