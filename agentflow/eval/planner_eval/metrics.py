"""Planner 评估指标：工具选择、动作选择、任务数量、目标类型准确率。"""

from __future__ import annotations


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Jaccard 相似度：|A∩B| / |A∪B|。"""
    if not set_a and not set_b:
        return 1.0
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def tool_selection_accuracy(actual_tools: list[str], expected_tools: list[str]) -> float:
    """工具选择准确率 — Jaccard 相似度。"""
    return jaccard_similarity(set(actual_tools), set(expected_tools))


def action_selection_accuracy(actual_actions: list[str], expected_actions: list[str]) -> float:
    """动作选择准确率 — Jaccard 相似度。"""
    return jaccard_similarity(set(actual_actions), set(expected_actions))


def action_recall(actual_actions: list[str], expected_actions: list[str]) -> float:
    """动作召回率 — 预期动作中有多少被实际覆盖。"""
    if not expected_actions:
        return 1.0
    expected_set = set(expected_actions)
    actual_set = set(actual_actions)
    return len(expected_set & actual_set) / len(expected_set)


def task_count_accuracy(actual_count: int, expected_range: tuple[int, int]) -> float:
    """任务数量准确率 — 在预期范围内则为 1.0。"""
    return 1.0 if expected_range[0] <= actual_count <= expected_range[1] else 0.0


def goal_type_accuracy(actual_type: str, expected_type: str) -> float:
    """目标类型准确率 — 精确匹配。"""
    return 1.0 if actual_type == expected_type else 0.0


def goal_completed_accuracy(actual_completed: bool, expected_completed: bool) -> float:
    """goal_completed 准确率。"""
    return 1.0 if actual_completed == expected_completed else 0.0


def compute_all(
    actual_tools: list[str],
    actual_actions: list[str],
    actual_task_count: int,
    actual_goal_type: str,
    actual_goal_completed: bool,
    sample: dict,
) -> dict[str, float]:
    """计算单条样本的全部 Planner 指标。"""
    return {
        "tool_acc": tool_selection_accuracy(actual_tools, sample.get("expected_tools", [])),
        "action_acc": action_selection_accuracy(actual_actions, sample.get("expected_actions", [])),
        "action_recall": action_recall(actual_actions, sample.get("expected_actions", [])),
        "task_count_acc": task_count_accuracy(
            actual_task_count,
            tuple(sample.get("expected_task_count_range", [0, 999])),
        ),
        "goal_type_acc": goal_type_accuracy(actual_goal_type, sample.get("expected_goal_type", "")),
        "goal_completed_acc": goal_completed_accuracy(
            actual_goal_completed,
            sample.get("expected_goal_completed", False),
        ),
    }


def aggregate(per_sample_metrics: list[dict[str, float]]) -> dict[str, float]:
    """汇总多次运行的指标均值。"""
    if not per_sample_metrics:
        return {}
    keys = per_sample_metrics[0].keys()
    return {k: sum(m[k] for m in per_sample_metrics) / len(per_sample_metrics) for k in keys}
