"""Mock Tool Eval Runner — 使用 Mock 工具运行评估，适合 CI 和快速验证。"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from agentflow.eval.common import MockWriteTool, save_results
from agentflow.eval.tool_eval.dataset import ToolEvalDataset
from agentflow.eval.tool_eval.metrics import compute_all
from agentflow.tools.registry import ToolRegistry

logger = logging.getLogger("tool_eval.mock")


class MockToolEvalRunner:
    """使用 Mock 工具运行评估，无需真实文件系统和外部依赖。"""

    def __init__(self, dataset: ToolEvalDataset) -> None:
        self.dataset = dataset
        self.registry = self._build_mock_registry()
        self.per_sample: list[dict[str, Any]] = []
        self.summary: dict[str, Any] = {}

    def _build_mock_registry(self) -> ToolRegistry:
        """扫描数据集中出现的 tool，为每个创建对应的 Mock 工具。"""
        registry = ToolRegistry()
        tool_actions: dict[str, set[str]] = {}

        for sample in self.dataset:
            tool_name = sample.get("tool", "")
            action = sample.get("action", "execute")
            if tool_name not in tool_actions:
                tool_actions[tool_name] = set()
            tool_actions[tool_name].add(action)

        for tool_name, actions in tool_actions.items():
            if tool_name == "filesystem":
                registry.register(MockWriteTool())
            else:
                registry.register(_create_generic_mock(tool_name, actions))

        return registry

    def run(self, verbose: bool = True) -> dict[str, Any]:
        """遍历数据集，用 mock 工具执行。"""
        results: list[dict] = []

        for i, sample in enumerate(self.dataset, 1):
            sid = sample.get("id", f"mock_{i}")
            if verbose:
                print(f"[{i}/{len(self.dataset)}] MOCK {sample['tool']}.{sample['action']} ...", end=" ")

            try:
                params = dict(sample["input_params"])
                result = self.registry.execute_task(
                    sample["tool"],
                    action=sample["action"],
                    **params,
                )
                result_dict = result.to_dict()
                results.append(result_dict)

                # 检查预期
                actual_success = result.success
                expected_ok = actual_success == sample["expected_success"]

                if verbose:
                    status = "OK" if expected_ok else "FAIL"
                    print(status)

                self.per_sample.append({
                    "sample_id": sid,
                    "tool": sample["tool"],
                    "action": sample["action"],
                    "expected_success": sample["expected_success"],
                    "actual_success": actual_success,
                    "result": result_dict.get("result"),
                    "error": result_dict.get("error"),
                    "expected_match": expected_ok,
                })

            except Exception as exc:
                logger.warning("Mock execution exception: %s", exc)
                results.append({
                    "success": False, "tool": sample["tool"],
                    "action": sample["action"], "error": str(exc),
                })
                self.per_sample.append({
                    "sample_id": sid,
                    "tool": sample["tool"],
                    "action": sample["action"],
                    "expected_success": sample["expected_success"],
                    "actual_success": False,
                    "error": str(exc),
                })
                if verbose:
                    print(f"EXCEPTION: {exc}")

        self.summary = compute_all(
            [s for s in self.dataset],
            [self._result_to_dict(r) for r in results],
        )
        return {
            "summary": self.summary,
            "per_sample": self.per_sample,
            "config": {
                "total_samples": len(self.dataset),
                "mode": "mock",
            },
        }

    def _result_to_dict(self, r: dict) -> dict:
        return {
            "success": r.get("success", False),
            "tool": r.get("tool", ""),
            "action": r.get("action", ""),
            "result": r.get("result"),
            "message": r.get("message", ""),
            "error": r.get("error"),
        }

    def save_results(self, path: str | Path) -> None:
        save_results(path, self.summary, self.per_sample, {
            "total_samples": len(self.dataset),
            "mode": "mock",
        })


def _create_generic_mock(tool_name: str, action_names: set[str] | None = None):
    """为未知工具创建通用 mock，动态注册所有需要的 action。"""
    from agentflow.tools.base import BaseTool
    from agentflow.tools.result import ToolResult

    actions_set = action_names or {"execute"}

    class _GenericMock(BaseTool):
        name = tool_name
        description = f"Mock {tool_name} for eval"

        def actions(self) -> dict[str, dict]:
            result = {}
            for act in actions_set:
                result[act] = {
                    "description": f"Mock {tool_name}.{act}",
                    "parameters": {},
                    "required": [],
                }
            return result

        def execute(self, **kwargs) -> ToolResult:
            action = kwargs.pop("action", next(iter(actions_set)))
            return ToolResult.ok(tool_name, action, result={"mock": True, "tool": tool_name})

    return _GenericMock()
