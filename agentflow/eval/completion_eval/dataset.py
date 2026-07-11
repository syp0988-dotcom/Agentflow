"""任务完成率评估 — 端到端测试多轮任务完成流程。"""

from __future__ import annotations

from agentflow.eval.common import BaseEvalDataset


class CompletionEvalDataset(BaseEvalDataset):
    """任务完成率评估数据集。

    每条样本定义完整的端到端场景：用户问题 → Planner 多轮 Mock 响应
    → Reflector 多轮 Mock 响应 → 预期完成状态。
    """

    @staticmethod
    def _validate_sample(sample: dict, line_num: int) -> bool:
        required = ["question", "expected_completed", "goal_analysis"]
        for key in required:
            if key not in sample:
                raise ValueError(f"Line {line_num}: missing required key '{key}'")
        if not isinstance(sample["question"], str) or not sample["question"].strip():
            raise ValueError(f"Line {line_num}: 'question' must be a non-empty string")
        if not isinstance(sample["expected_completed"], bool):
            raise ValueError(f"Line {line_num}: 'expected_completed' must be a bool")
        if not isinstance(sample["goal_analysis"], dict):
            raise ValueError(f"Line {line_num}: 'goal_analysis' must be a dict")
        sample.setdefault("min_expected_tasks_done", 0)
        sample.setdefault("planner_responses", [])
        sample.setdefault("reflection_responses", [])
        sample.setdefault("expected_actions", [])
        if "id" not in sample:
            from uuid import uuid4
            sample["id"] = f"comp_{uuid4().hex[:8]}"
        return True

    def add(
        self,
        question: str,
        expected_completed: bool,
        goal_analysis: dict,
        planner_responses: list[dict] | None = None,
        reflection_responses: list[dict] | None = None,
        min_expected_tasks_done: int = 0,
        expected_actions: list[str] | None = None,
        sample_id: str | None = None,
        **extra,
    ) -> str:
        """添加一条任务完成率测试样本。"""
        return self.add_sample({
            "question": question,
            "expected_completed": expected_completed,
            "goal_analysis": goal_analysis,
            "planner_responses": planner_responses or [],
            "reflection_responses": reflection_responses or [],
            "min_expected_tasks_done": min_expected_tasks_done,
            "expected_actions": expected_actions or [],
            "id": sample_id,
            **extra,
        })

    def stats(self) -> dict:
        n = len(self.samples)
        if n == 0:
            return {"total_samples": 0}
        completion_count = sum(1 for s in self.samples if s.get("expected_completed"))
        avg_turns = sum(len(s.get("planner_responses", [])) for s in self.samples) / n
        return {
            "total_samples": n,
            "expected_completions": completion_count,
            "expected_failures": n - completion_count,
            "avg_planned_turns": round(avg_turns, 1),
        }
