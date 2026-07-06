"""ConversationState — structured topic, entity, and focus tracking across turns.

Complements SessionState with higher-level conversation understanding.
SessionState tracks *what the system is doing* (goal, task, step, waiting).
ConversationState tracks *what the conversation is about* (topic, entities, focus).

This state accumulates across turns within a single task conversation and is
reset when a new task begins (via ``SessionState.reset``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConversationState:
    """Extended conversation tracking — topic, entities, focus, facts.

    Fields:
        topic: Current conversation topic (e.g. "IDA", "Python贪吃蛇").
        entities: Accumulated set of mentioned entities across turns.
        current_focus: Current focus item (e.g. "步骤2", "儿童教育").
        last_answer: The assistant's last full answer text.
        summary: Simple rule-based summary of recent conversation.
        facts: Key-value facts extracted during conversation.
        tool_result: Last tool execution result (if any).
    """

    topic: str = ""
    entities: set[str] = field(default_factory=set)
    current_focus: str = ""
    last_answer: str = ""
    summary: str = ""
    facts: dict[str, str] = field(default_factory=dict)
    tool_result: str = ""

    # ------------------------------------------------------------------
    # Mutators
    # ------------------------------------------------------------------

    def add_entity(self, entity: str) -> None:
        """Add an entity if it passes minimum length filtering."""
        if entity and len(entity) >= 2:
            self.entities.add(entity)

    def set_focus(self, focus: str) -> None:
        """Update the current focus.  No-op for empty strings."""
        if focus:
            self.current_focus = focus

    def reset(self) -> None:
        """Reset all fields to defaults."""
        self.topic = ""
        self.entities.clear()
        self.current_focus = ""
        self.last_answer = ""
        self.summary = ""
        self.facts.clear()
        self.tool_result = ""

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dict."""
        return {
            "topic": self.topic,
            "entities": list(self.entities),
            "current_focus": self.current_focus,
            "last_answer": self.last_answer,
            "summary": self.summary,
            "facts": dict(self.facts),
            "tool_result": self.tool_result,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ConversationState:
        """Restore from a dict produced by ``to_dict``."""
        if not data:
            return cls()
        return cls(
            topic=str(data.get("topic", "")),
            entities=set(data.get("entities", [])),
            current_focus=str(data.get("current_focus", "")),
            last_answer=str(data.get("last_answer", "")),
            summary=str(data.get("summary", "")),
            facts=dict(data.get("facts", {})),
            tool_result=str(data.get("tool_result", "")),
        )

    def __str__(self) -> str:
        """Human-readable summary for prompt injection."""
        parts = []
        if self.topic:
            parts.append(f"话题：{self.topic}")
        if self.current_focus:
            parts.append(f"焦点：{self.current_focus}")
        if self.entities:
            entities_str = "、".join(sorted(self.entities)[:8])
            parts.append(f"实体：{entities_str}")
        if self.summary:
            parts.append(f"摘要：{self.summary}")
        return "\n".join(parts) if parts else "(无跟踪信息)"
