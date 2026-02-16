from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, List


@dataclass
class ConversationMemory:
    max_turns: int

    def __post_init__(self):
        self.turns: Deque[Dict] = deque(maxlen=self.max_turns)

    def add_turn(self, role: str, content: str) -> None:
        self.turns.append({"role": role, "content": content})

    def list_turns(self) -> List[Dict]:
        return list(self.turns)
