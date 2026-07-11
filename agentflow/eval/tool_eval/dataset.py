"""Tool 成功率评估 — 独立测试每个 Tool Action 的执行成功率。"""

from __future__ import annotations

from agentflow.eval.common import BaseEvalDataset


class ToolEvalDataset(BaseEvalDataset):
    """工具评估数据集。

    每条样本描述一次独立的 Tool Action 调用及其预期结果。
    """

    # -- Subclass contract --------------------------------------------------

    @staticmethod
    def _validate_sample(sample: dict, line_num: int) -> bool:
        required = ["tool", "action", "input_params", "expected_success"]
        for key in required:
            if key not in sample:
                raise ValueError(f"Line {line_num}: missing required key '{key}'")
        if not isinstance(sample["tool"], str) or not sample["tool"].strip():
            raise ValueError(f"Line {line_num}: 'tool' must be a non-empty string")
        if not isinstance(sample["action"], str) or not sample["action"].strip():
            raise ValueError(f"Line {line_num}: 'action' must be a non-empty string")
        if not isinstance(sample["input_params"], dict):
            raise ValueError(f"Line {line_num}: 'input_params' must be a dict")
        if not isinstance(sample["expected_success"], bool):
            raise ValueError(f"Line {line_num}: 'expected_success' must be a bool")
        # 默认值
        sample.setdefault("setup", [])
        sample.setdefault("teardown", [])
        sample.setdefault("expected_result_checks", {})
        if "id" not in sample:
            from uuid import uuid4
            sample["id"] = f"tool_{uuid4().hex[:8]}"
        return True

    def add(
        self,
        tool: str,
        action: str,
        input_params: dict,
        expected_success: bool,
        setup: list | None = None,
        teardown: list | None = None,
        expected_result_checks: dict | None = None,
        sample_id: str | None = None,
        **extra,
    ) -> str:
        """添加一条工具测试样本。"""
        return self.add_sample({
            "tool": tool,
            "action": action,
            "input_params": input_params,
            "expected_success": expected_success,
            "setup": setup or [],
            "teardown": teardown or [],
            "expected_result_checks": expected_result_checks or {},
            "id": sample_id,
            **extra,
        })

    def stats(self) -> dict:
        n = len(self.samples)
        if n == 0:
            return {"total_samples": 0}
        tools = set(s.get("tool", "") for s in self.samples)
        actions = set(f"{s.get('tool','')}.{s.get('action','')}" for s in self.samples)
        success_count = sum(1 for s in self.samples if s.get("expected_success", True))
        error_count = n - success_count
        return {
            "total_samples": n,
            "tools_covered": sorted(tools),
            "actions_covered": len(actions),
            "success_cases": success_count,
            "error_cases": error_count,
        }
