"""Planner 准确率评估 — 测试 PlannerAgent 为目标生成正确任务的能力。"""

from __future__ import annotations

from agentflow.eval.common import BaseEvalDataset


class PlannerEvalDataset(BaseEvalDataset):
    """规划器评估数据集。

    每条样本包含用户问题、预置 goal_analysis、预期工具/动作等。
    """

    @staticmethod
    def _validate_sample(sample: dict, line_num: int) -> bool:
        required = ["question", "expected_tools", "expected_actions",
                     "expected_task_count_range", "expected_goal_type"]
        for key in required:
            if key not in sample:
                raise ValueError(f"Line {line_num}: missing required key '{key}'")
        if not isinstance(sample["question"], str) or not sample["question"].strip():
            raise ValueError(f"Line {line_num}: 'question' must be a non-empty string")
        if not isinstance(sample["expected_tools"], list):
            raise ValueError(f"Line {line_num}: 'expected_tools' must be a list")
        if not isinstance(sample["expected_actions"], list):
            raise ValueError(f"Line {line_num}: 'expected_actions' must be a list")
        r = sample["expected_task_count_range"]
        if not isinstance(r, list) or len(r) != 2:
            raise ValueError(f"Line {line_num}: 'expected_task_count_range' must be [min, max]")
        sample.setdefault("goal_analysis", {
            "goal": sample["question"],
            "goal_type": sample.get("expected_goal_type", "other"),
            "confidence": 0.9,
        })
        sample.setdefault("bypass_llm", False)
        sample.setdefault("mock_llm_response", None)
        sample.setdefault("expected_goal_completed", False)
        if "id" not in sample:
            from uuid import uuid4
            sample["id"] = f"plan_{uuid4().hex[:8]}"
        return True

    def add(
        self,
        question: str,
        expected_tools: list[str],
        expected_actions: list[str],
        expected_task_count_range: list[int],
        expected_goal_type: str,
        goal_analysis: dict | None = None,
        bypass_llm: bool = False,
        mock_llm_response: dict | None = None,
        expected_goal_completed: bool = False,
        sample_id: str | None = None,
        **extra,
    ) -> str:
        """添加一条规划器测试样本。"""
        return self.add_sample({
            "question": question,
            "goal_analysis": goal_analysis or {
                "goal": question,
                "goal_type": expected_goal_type,
                "confidence": 0.9,
            },
            "expected_tools": expected_tools,
            "expected_actions": expected_actions,
            "expected_task_count_range": expected_task_count_range,
            "expected_goal_type": expected_goal_type,
            "expected_goal_completed": expected_goal_completed,
            "bypass_llm": bypass_llm,
            "mock_llm_response": mock_llm_response,
            "id": sample_id,
            **extra,
        })

    def stats(self) -> dict:
        n = len(self.samples)
        if n == 0:
            return {"total_samples": 0}
        deterministic = sum(1 for s in self.samples if s.get("bypass_llm"))
        llm_driven = n - deterministic
        goal_types = set(s.get("expected_goal_type", "") for s in self.samples)
        tools = set()
        for s in self.samples:
            tools.update(s.get("expected_tools", []))
        return {
            "total_samples": n,
            "deterministic_samples": deterministic,
            "llm_driven_samples": llm_driven,
            "goal_types": sorted(goal_types),
            "tools_covered": sorted(tools),
        }
