"""SessionState — tracks what the system is currently doing across turns.

Unlike conversation history (a log of what was said), SessionState captures
the *runtime context*: what goal is being worked on, what step we're on,
what we're waiting for from the user, and any pending choices or slots.

This is the core data structure that enables "continue planning" — the system
knows what it was doing before the user's latest message.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agentflow.conversation.context import ORDINAL_MAP
from agentflow.conversation.state import ConversationState

_SCHEMA_VERSION = "1"


@dataclass
class SessionState:
    """Runtime session state that persists across turns.

    Fields:
        current_goal: High-level goal the user wants to accomplish
            (e.g. "生成数据分析报告", "帮我订酒店").
        current_task: Specific task being executed
            (e.g. "搜索儿童教育数据", "执行 Python 脚本").
        current_step: Current step within the task
            (e.g. "收集数据", "生成图表").
        status: Lifecycle status — ``"idle"`` | ``"waiting_user"`` | ``"processing"``.
        waiting_for: Describes what we need from the user
            (e.g. "选择报告主题", "提供城市名称", "确认").
        pending_options: Mapping of user-friendly keys to resolved values.
            When the assistant presents numbered choices, this stores them
            so ``"选项一"`` → ``"儿童教育"`` automatically.
            Example: ``{"1": "儿童教育", "2": "公共卫生"}``
        slots: Named parameters being collected incrementally (slot-filling).
            Example: ``{"city": "北京", "date": ""}`` shows city is filled,
            date is still needed.
        metadata: Extensible key-value store for agent-specific state.
    """

    current_goal: str = ""
    current_task: str = ""
    current_step: str = ""
    status: str = "idle"
    waiting_for: str = ""
    pending_options: dict[str, str] = field(default_factory=dict)
    slots: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    # Token usage tracking (cumulative input+output across the session)
    token_usage: int = 0

    # Conversation tracking (Phase 8) — topic, entities, focus across turns
    tracking: ConversationState | None = None

    # ------------------------------------------------------------------
    # Predicates
    # ------------------------------------------------------------------

    @property
    def is_waiting(self) -> bool:
        """Whether the system is waiting for user input."""
        return self.status == "waiting_user"

    @property
    def has_pending_options(self) -> bool:
        """Whether there are pending options the user can choose from."""
        return bool(self.pending_options)

    @property
    def has_unfilled_slots(self) -> bool:
        """Whether any required slots are still empty."""
        return any(v == "" for v in self.slots.values())

    # ------------------------------------------------------------------
    # Mutators
    # ------------------------------------------------------------------

    def resolve_option(self, user_input: str) -> str | None:
        """Resolve a user's choice against pending_options.

        Handles both key forms:
          - ``"选项一"`` → ``"儿童教育"``  (Chinese ordinal)
          - ``"1"``     → ``"儿童教育"``  (direct key)
          - ``"儿童教育"`` → ``"儿童教育"``  (exact value match)

        Returns the resolved value, or *None* if no match.
        """
        if not self.pending_options:
            return None

        # Direct key lookup (e.g. user typed "1")
        if user_input in self.pending_options:
            return self.pending_options[user_input]

        # Chinese ordinal lookup: "选项一" → "1", "选项二" → "2"
        for ch, digit in ORDINAL_MAP.items():
            if user_input in (f"选项{ch}", f"第{ch}个", f"{ch}", f"{digit}"):
                if digit in self.pending_options:
                    return self.pending_options[digit]

        # Exact value match — no substring matching to avoid ambiguity
        for value in self.pending_options.values():
            if user_input == value:
                return value

        return None

    def add_token_usage(self, count: int) -> None:
        """Accumulate token usage for this session."""
        self.token_usage += count

    def budget_remaining(self, max_budget: int) -> int:
        """Return remaining token budget."""
        return max(0, max_budget - self.token_usage)

    def fill_slot(self, slot_name: str, value: str) -> None:
        """Fill a single slot.  No-op if the slot doesn't exist."""
        if slot_name in self.slots:
            self.slots[slot_name] = value

    def start_waiting(self, for_what: str) -> None:
        """Put the session into waiting-user mode."""
        self.status = "waiting_user"
        self.waiting_for = for_what

    def resume(self) -> None:
        """Resume from waiting state back to processing."""
        self.status = "processing"
        self.waiting_for = ""

    def reset(self) -> None:
        """Reset all fields to defaults (new task begins)."""
        self.current_goal = ""
        self.current_task = ""
        self.current_step = ""
        self.status = "idle"
        self.waiting_for = ""
        self.pending_options.clear()
        self.slots.clear()
        self.metadata.clear()
        self.tracking = None

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a JSON-safe dict."""
        result = {
            "_schema_version": _SCHEMA_VERSION,
            "current_goal": self.current_goal,
            "current_task": self.current_task,
            "current_step": self.current_step,
            "status": self.status,
            "waiting_for": self.waiting_for,
            "pending_options": dict(self.pending_options),
            "slots": dict(self.slots),
            "metadata": dict(self.metadata),
            "token_usage": self.token_usage,
        }
        if self.tracking is not None:
            result["tracking"] = self.tracking.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> SessionState:
        """Restore from a dict produced by ``to_dict``."""
        if not data:
            return cls()
        # _schema_version reserved for future migration logic
        tracking = None
        tracking_raw = data.get("tracking")
        if isinstance(tracking_raw, dict):
            tracking = ConversationState.from_dict(tracking_raw)
        return cls(
            current_goal=str(data.get("current_goal", "")),
            current_task=str(data.get("current_task", "")),
            current_step=str(data.get("current_step", "")),
            status=str(data.get("status", "idle")),
            waiting_for=str(data.get("waiting_for", "")),
            pending_options=dict(data.get("pending_options", {})),
            slots=dict(data.get("slots", {})),
            metadata=dict(data.get("metadata", {})),
            token_usage=int(data.get("token_usage", 0)),
            tracking=tracking,
        )

    def __str__(self) -> str:
        """Human-readable summary for prompt injection."""
        parts = []
        if self.current_goal:
            parts.append(f"当前目标：{self.current_goal}")
        if self.current_task:
            parts.append(f"当前任务：{self.current_task}")
        if self.current_step:
            parts.append(f"当前步骤：{self.current_step}")
        if self.is_waiting:
            parts.append(f"等待用户：{self.waiting_for}")
        if self.pending_options:
            lines = ["当前选项："]
            for key, val in self.pending_options.items():
                lines.append(f"  {key}. {val}")
            parts.append("\n".join(lines))
        if self.slots:
            filled = {k: v for k, v in self.slots.items() if v}
            if filled:
                parts.append(f"已填写参数：{filled}")
        if self.tracking is not None:
            if self.tracking.current_focus:
                parts.append(f"当前焦点：{self.tracking.current_focus}")
            if self.tracking.topic:
                parts.append(f"当前话题：{self.tracking.topic}")
            if self.tracking.entities:
                entities_str = "、".join(sorted(self.tracking.entities)[:8])
                parts.append(f"实体：{entities_str}")
            if self.tracking.last_answer:
                truncated = self.tracking.last_answer[:120]
                if len(self.tracking.last_answer) > 120:
                    truncated += "…"
                parts.append(f"上轮回答：{truncated}")
        return "\n".join(parts) if parts else "(无活跃任务)"
