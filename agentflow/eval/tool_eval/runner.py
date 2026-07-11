"""Tool Eval Runner — 使用真实工具运行评估。"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from agentflow.eval.common import save_results
from agentflow.eval.tool_eval.dataset import ToolEvalDataset
from agentflow.eval.tool_eval.metrics import compute_all

logger = logging.getLogger("tool_eval")


class ToolEvalRunner:
    """使用真实 ToolRegistry 运行工具评估数据集。

    对 filesystem 工具使用临时 workspace 隔离，
    对 git 工具使用临时 git 仓库。
    """

    def __init__(self, registry, dataset: ToolEvalDataset) -> None:
        from tempfile import mkdtemp

        self.registry = registry
        self.dataset = dataset
        self.per_sample: list[dict[str, Any]] = []
        self.summary: dict[str, Any] = {}

        # 为需要文件系统的工具创建临时 workspace
        self._workspace = Path(mkdtemp(prefix="tool_eval_"))
        logger.info("Tool eval workspace: %s", self._workspace)

    def run(self, verbose: bool = True) -> dict[str, Any]:
        """遍历数据集，逐条执行并收集结果。"""
        results: list[dict] = []

        for i, sample in enumerate(self.dataset, 1):
            sid = sample.get("id", f"sample_{i}")
            if verbose:
                print(f"[{i}/{len(self.dataset)}] {sample['tool']}.{sample['action']} ...", end=" ")

            # Setup
            setup_ok = self._run_setup(sample.get("setup", []))
            if not setup_ok:
                results.append({
                    "success": False, "tool": sample["tool"], "action": sample["action"],
                    "result": None, "message": "setup failed", "error": "setup step failed",
                })
                self.per_sample.append({
                    "sample_id": sid, "tool": sample["tool"], "action": sample["action"],
                    "expected_success": sample["expected_success"], "actual_success": False,
                    "result": None, "skipped": True, "skip_reason": "setup failed",
                })
                print("SKIP (setup failed)")
                continue

            # Execute
            try:
                params = dict(sample["input_params"])
                tool_name = params.pop("_tool", sample["tool"])
                action = params.pop("_action", sample["action"])

                start = time.time()
                result = self.registry.execute_task(tool_name, **{**params, "action": action})
                duration = time.time() - start

                result_dict = result.to_dict()
                result_dict["duration"] = duration
                results.append(result_dict)

                check_passed = _check_expected(result, sample)
                actual_success = result.success

                if verbose:
                    status = "OK" if actual_success == sample["expected_success"] and check_passed else "FAIL"
                    if actual_success:
                        print(f"{status} ({duration:.3f}s)")
                    else:
                        print(f"{status} error={result.error}")

                self.per_sample.append({
                    "sample_id": sid,
                    "tool": sample["tool"],
                    "action": sample["action"],
                    "input_params": sample["input_params"],
                    "expected_success": sample["expected_success"],
                    "actual_success": actual_success,
                    "result": result_dict.get("result"),
                    "error": result_dict.get("error"),
                    "message": result_dict.get("message"),
                    "duration": duration,
                    "checks_passed": check_passed,
                    "skipped": False,
                })

            except Exception as exc:
                logger.warning("Tool execution exception: %s", exc)
                results.append({
                    "success": False, "tool": sample["tool"], "action": sample["action"],
                    "error": str(exc),
                })
                self.per_sample.append({
                    "sample_id": sid, "tool": sample["tool"], "action": sample["action"],
                    "expected_success": sample["expected_success"], "actual_success": False,
                    "error": str(exc), "skipped": False,
                })
                print(f"EXCEPTION: {exc}")

            # Teardown
            self._run_setup(sample.get("teardown", []))

        self.summary = compute_all(
            [s for s in self.dataset],
            [self._result_to_dict(r) for r in results],
        )
        return {
            "summary": self.summary,
            "per_sample": self.per_sample,
            "config": {
                "total_samples": len(self.dataset),
                "workspace": str(self._workspace),
            },
        }

    def _run_setup(self, steps: list) -> bool:
        """执行 setup/teardown 步骤，失败返回 False。"""
        for step in steps:
            if not step:
                continue
            try:
                if isinstance(step, list) and len(step) >= 2:
                    action = step[0]
                    params = step[1] if len(step) > 1 else {}
                elif isinstance(step, dict):
                    action = step.get("action", "")
                    params = {k: v for k, v in step.items() if k != "action"}
                else:
                    continue
                result = self.registry.execute_task("filesystem", action=action, **params)
                if not result.success:
                    logger.warning("Setup/teardown step failed: %s %s: %s", action, params, result.error)
                    return False
            except Exception as exc:
                logger.warning("Setup/teardown exception: %s", exc)
                return False
        return True

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
            "workspace": str(self._workspace),
        })


def _check_expected(result, sample: dict) -> bool:
    """检查 ToolResult 是否符合预期。"""
    success_match = result.success == sample["expected_success"]
    if not success_match:
        return False
    checks = sample.get("expected_result_checks", {})
    if not checks:
        return True
    actual = result.result if isinstance(result.result, dict) else {}
    for key, expected_val in checks.items():
        if key == "message_contains":
            if expected_val not in result.message:
                return False
        elif key.startswith("result."):
            field = key[len("result."):]
            if actual.get(field) != expected_val:
                return False
        else:
            if isinstance(actual, dict) and actual.get(key) != expected_val:
                return False
    return True
