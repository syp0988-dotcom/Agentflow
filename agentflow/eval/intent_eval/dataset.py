"""Intent evaluation dataset — tests GoalAnalyzer intent classification."""

from __future__ import annotations

from agentflow.eval.common import BaseEvalDataset


class IntentEvalDataset(BaseEvalDataset):
    """Dataset for evaluating goal_type classification accuracy.

    Each sample: question -> expected_goal_type (coding/project/question/search/tool/chat/other).
    """

    VALID_GOAL_TYPES = frozenset({
        "coding", "project", "question", "search", "tool_use",
        "chat", "other", "translation", "editing", "analysis", "document",
    })

    @staticmethod
    def _validate_sample(sample: dict, line_num: int) -> bool:
        required = ["question", "expected_goal_type"]
        for key in required:
            if key not in sample:
                raise ValueError(f"Line {line_num}: missing required key '{key}'")
        if not isinstance(sample["question"], str):
            raise ValueError(f"Line {line_num}: 'question' must be a string")
        gt = sample["expected_goal_type"]
        if gt not in IntentEvalDataset.VALID_GOAL_TYPES:
            raise ValueError(f"Line {line_num}: invalid goal_type '{gt}'")
        if "id" not in sample:
            from uuid import uuid4
            sample["id"] = f"intent_{uuid4().hex[:8]}"
        sample.setdefault("expected_confidence_min", 0.0)
        sample.setdefault("note", "")
        return True

    def add(
        self,
        question: str,
        expected_goal_type: str,
        expected_confidence_min: float = 0.0,
        note: str = "",
        sample_id: str | None = None,
        **extra,
    ) -> str:
        return self.add_sample({
            "question": question,
            "expected_goal_type": expected_goal_type,
            "expected_confidence_min": expected_confidence_min,
            "note": note,
            "id": sample_id,
            **extra,
        })

    def stats(self) -> dict:
        n = len(self.samples)
        if n == 0:
            return {"total_samples": 0}
        from collections import Counter
        dist = Counter(s.get("expected_goal_type", "") for s in self.samples)
        return {
            "total_samples": n,
            "goal_type_distribution": dict(dist),
        }
