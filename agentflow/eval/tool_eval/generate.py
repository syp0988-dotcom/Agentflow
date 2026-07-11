"""LLM 驱动的工具测试用例生成器。

从 ToolRegistry 中注册的工具获取 action 定义，
使用 LLM 自动生成多样化的测试用例（成功 + 失败 + 边界）。
"""

from __future__ import annotations

import json
import logging
import re
import time

from agentflow.eval.tool_eval.dataset import ToolEvalDataset
from agentflow.services.llm_service import LLMService

logger = logging.getLogger("tool_eval.generator")

_GENERATE_PROMPT = """\
根据以下工具 "{tool_name}" 的 {action_name} 操作定义，生成 {count} 个测试用例。

操作说明: {action_desc}
参数定义: {params}

要求：
1. 返回纯 JSON 数组（从 [ 开始，到 ] 结束）
2. 每个元素是一个测试用例对象，包含以下字段：
   - input_params: 对象，给操作的参数
   - expected_success: true（正常用例）或 false（错误用例）
   - expected_result_checks: 对象（可选），如 {{"message_contains": "mkdir"}}
   - description_cn: 字符串，中文描述这个用例测什么

3. 覆盖这几类场景：
   - {success_ratio}% 正常用例（合法参数，expected_success=true）
   - {error_ratio}% 错误用例（缺失必填参数、非法路径、路径穿越等，expected_success=false）

4. 正常用例中，path 参数使用 test_{tool_name} 作为基础路径，避免真实项目路径
5. 内容参数（如 file content）使用真实但无害的代码/文本

参数类型提示：
{param_hints}

JSON:"""


def _extract_json_array(text: str) -> list[dict]:
    """从 LLM 回复中提取 JSON 数组，与 RAG 生成器同款健壮解析。"""
    # 尝试直接解析
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # 搜索 JSON 数组块
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            result = json.loads(match.group())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    logger.warning("Could not extract JSON array from LLM response")
    return []


def generate_from_registry(
    registry,
    actions_per_tool: int = 10,
    llm: LLMService | None = None,
    batch_size: int = 3,
    sleep_interval: float = 0.3,
) -> ToolEvalDataset:
    """从 ToolRegistry 中已注册的工具自动生成测试用例。

    Parameters
    ----------
    registry : ToolRegistry
        已注册工具的注册表。
    actions_per_tool : int
        每个 action 生成的测试用例数。
    llm : LLMService | None
        LLM 服务实例，为 None 则自动创建。
    batch_size : int
        每批处理的 action 数。
    sleep_interval : float
        每批之间的等待时间（秒）。

    Returns
    -------
    ToolEvalDataset
    """
    if llm is None:
        llm = LLMService()

    if not llm.client:
        raise RuntimeError("LLM client not configured. Cannot generate test cases.")

    dataset = ToolEvalDataset()

    for tool_name in registry.list_tools():
        tool = registry.get(tool_name)
        if tool is None:
            continue

        actions = tool.actions()
        if not actions:
            continue

        for action_name, action_def in actions.items():
            # 计算正常/错误比例
            success_count = max(1, int(actions_per_tool * 0.7))
            error_count = actions_per_tool - success_count

            # 构建参数提示
            params = action_def.get("parameters", {})
            required = action_def.get("required", [])
            desc = action_def.get("description", action_name)

            param_hints = []
            for pname, pdef in params.items():
                ptype = pdef.get("type", "string")
                pdesc = pdef.get("description", "")
                is_required = "必填" if pname in required else "可选"
                param_hints.append(f"  - {pname} ({ptype}, {is_required}): {pdesc}")

            # 构建 prompt
            prompt = _GENERATE_PROMPT.format(
                tool_name=tool_name,
                action_name=action_name,
                count=actions_per_tool,
                action_desc=desc,
                params=json.dumps(params, ensure_ascii=False, indent=2),
                success_ratio=int(success_count / actions_per_tool * 100),
                error_ratio=int(error_count / actions_per_tool * 100),
                param_hints="\n".join(param_hints) if param_hints else "无额外参数",
            )

            logger.info("Generating %d test cases for %s.%s", actions_per_tool, tool_name, action_name)

            try:
                response = llm.complete(prompt=prompt)
                cases = _extract_json_array(response)

                added = 0
                for case in cases:
                    if not isinstance(case, dict):
                        continue
                    input_params = case.get("input_params", {})
                    expected_success = case.get("expected_success", True)
                    if not isinstance(input_params, dict):
                        continue

                    dataset.add(
                        tool=tool_name,
                        action=action_name,
                        input_params=input_params,
                        expected_success=expected_success,
                        expected_result_checks=case.get("expected_result_checks", {}),
                        description_cn=case.get("description_cn", ""),
                    )
                    added += 1

                logger.info("  Added %d/%d cases for %s.%s", added, actions_per_tool, tool_name, action_name)

            except Exception as exc:
                logger.warning("Failed to generate cases for %s.%s: %s", tool_name, action_name, exc)
                continue

            time.sleep(sleep_interval)

    return dataset


def generate_filesystem_cases(target_count: int = 40) -> ToolEvalDataset:
    """为 filesystem 工具快速生成指定数量的测试用例。

    这是最常用的工具，单独提供便捷函数。
    """
    from agentflow.tools.registry import ToolRegistry
    from agentflow.tools.filesystem_tool import FileSystemTool

    registry = ToolRegistry()
    registry.register(FileSystemTool())

    actions = list(FileSystemTool().actions().keys())
    per_action = max(2, target_count // len(actions))

    return generate_from_registry(registry, actions_per_tool=per_action)
