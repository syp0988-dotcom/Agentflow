"""Answer Agent — finalises agent outputs into user-facing responses.

In the goal-driven architecture, AnswerAgent has two modes:

1. **Summary mode** (for project/coding/refactor/workflow goals):
   Reports what was created, the project structure, and next steps.
   Does NOT generate code or content — only summarises.

2. **Answer mode** (for question/translation/search goals):
   Generates a natural language answer using available context
   (knowledge references, search results, memory).
"""

from __future__ import annotations

from agentflow.agents.base import AgentProtocol
from agentflow.graph.context_builder import ContextBuilder
from agentflow.services.llm_service import get_llm_service
from agentflow.utils.decorators import safe_run
from agentflow.utils.logging import build_logger

logger = build_logger("answer")

# Goal types that produce summary output (not LLM-generated answers)
_SUMMARY_GOAL_TYPES = frozenset({
    "project", "coding", "refactor", "workflow", "debug", "tool_use",
})


class AnswerAgent(AgentProtocol):
    """Produce a user-facing response from workflow state.

    - For project/completion goals: outputs a structured summary of what was done.
    - For question/search goals: generates an LLM-powered answer with context.
    """

    @safe_run
    def run(self, state: dict[str, object]) -> dict[str, object]:
        """Produce a user-facing response from workflow state.

        Three knowledge-source modes (dual-framework RAG + LLM Wiki):
          - ``"general"`` → direct LLM answer, no RAG context (fast path)
          - ``"local"``   → RAG-only, use knowledge_context exclusively
          - ``"hybrid"``  → fuse RAG context + LLM own knowledge
        """
        is_continue = bool(state.get("_continue_mode", False))
        goal_analysis = state.get("goal_analysis", {})
        degraded = bool(state.get("_degraded", False))
        llm_error = str(state.get("_llm_error", ""))

        if isinstance(goal_analysis, dict):
            goal_type = goal_analysis.get("goal_type", "other")
            goal = goal_analysis.get("goal", state.get("question", ""))
            knowledge_source = goal_analysis.get("knowledge_source", "hybrid")
        else:
            goal_type = "other"
            goal = state.get("question", "")
            knowledge_source = "hybrid"

        # ── Degraded mode: LLM unavailable, produce fallback message ──
        if degraded:
            from agentflow.services.llm_service import classify_error, get_fallback_message
            error_type = classify_error(Exception(llm_error)) if llm_error else "unknown"
            fallback = get_fallback_message(error_type, goal_type)
            state["answer"] = self._degraded_answer(goal, error_type, fallback, goal_type)
            logger.warning("Answer: degraded mode (error_type=%s)", error_type)
            return state

        # ── Summary mode: project / coding / refactor / workflow / debug ──
        if goal_type in _SUMMARY_GOAL_TYPES:
            state["answer"] = self._build_completion_summary(state, goal, goal_type)
            logger.info("Answer: summary mode (goal_type=%s)", goal_type)
            return state

        # ── Answer mode: question / search / translation / editing ──────
        llm_service = get_llm_service()
        logger.info(
            "Answer: LLM answer mode (goal_type=%s, knowledge=%s, continue=%s)",
            goal_type, knowledge_source, is_continue,
        )

        messages: list[dict[str, str]] = [
            {"role": "system", "content": self._system_prompt(
                is_continue=is_continue,
                knowledge_source=knowledge_source,
            )},
        ]

        builder = ContextBuilder(state)
        user_prompt = builder.format_planner_prompt()
        messages.append({"role": "user", "content": user_prompt})

        answer = llm_service.complete(messages=messages)
        logger.info("Answer: LLM returned %d chars: %s", len(answer), answer[:100])
        state["answer"] = self.clean_answer(answer)
        return state

    # ------------------------------------------------------------------
    # Summary mode
    # ------------------------------------------------------------------

    def _build_completion_summary(
        self,
        state: dict[str, object],
        goal: str,
        goal_type: str,
    ) -> str:
        """Build a completion summary for project/coding/refactor goals."""
        plan = state.get("plan", {})
        tool_results = state.get("tool_results", [])
        reflection_msg = str(state.get("_reflection_message", ""))

        # Collect tasks info
        if isinstance(plan, dict):
            tasks = plan.get("tasks", [])
        else:
            tasks = getattr(plan, "tasks", [])

        # Collect created paths from tool results
        created = []
        for r in (tool_results or []):
            if isinstance(r, dict) and r.get("success"):
                res = r.get("result", {}) or {}
                path = res.get("path", "")
                if path:
                    created.append(path)
                inp = r.get("input", {})
                if isinstance(inp, dict):
                    path2 = inp.get("path", "")
                    if path2 and path2 not in created:
                        created.append(path2)

        lines = [f"✅ 目标完成：**{goal}**", ""]

        if created:
            tree = self._build_path_tree(created)
            lines.append("**已创建的文件结构：**\n")
            lines.append("```")
            lines.extend(tree)
            lines.append("```")
            lines.append("")

        # Task summary
        completed = sum(1 for t in tasks if isinstance(t, dict) and t.get("status") == "completed"
                        or not isinstance(t, dict) and hasattr(t, "is_finished") and t.is_finished)
        total = len(tasks)
        if total > 0:
            lines.append(f"**执行统计：** {completed}/{total} 个任务完成")

        if reflection_msg:
            lines.append("")
            lines.append(reflection_msg)

        # Next steps (for project goals)
        if goal_type == "project":
            lines.extend([
                "",
                "---",
                "**下一步：**",
                "1. 进入项目目录检查生成的文件",
                "2. 查看 README 获取项目说明",
                "3. 如有需要，告诉我进行修改或扩展",
            ])

        return "\n".join(lines)

    @staticmethod
    def _build_path_tree(paths: list[str]) -> list[str]:
        """Build a simple tree view from a list of file paths."""
        if not paths:
            return []

        parts_list = [p.replace("\\", "/").strip("/").split("/") for p in paths]
        tree: dict[str, set[str]] = {}
        for parts in parts_list:
            for i, part in enumerate(parts):
                parent = "/".join(parts[:i]) if i > 0 else ""
                tree.setdefault(parent, set()).add(part)

        result: list[str] = []

        def _emit(parent: str, prefix: str = "") -> None:
            children = sorted(tree.get(parent, set()))
            for i, child in enumerate(children):
                child_path = f"{parent}/{child}" if parent else child
                is_last = i == len(children) - 1
                is_dir = child_path in tree
                connector = "└── " if is_last else "├── "
                suffix = "/" if is_dir else ""
                result.append(f"{prefix}{connector}{child}{suffix}")
                if is_dir:
                    ext = "    " if is_last else "│   "
                    _emit(child_path, prefix + ext)

        _emit("")
        return result if result else paths

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def clean_answer(text: str) -> str:
        """Remove residual noise from the raw LLM output."""
        return text.strip()

    @staticmethod
    def _system_prompt(continue_mode: bool = False, knowledge_source: str = "hybrid") -> str:
        """System prompt for answer mode, adapted to knowledge source.

        Three prompts for the dual-framework (RAG + LLM Wiki):
          - ``"general"``: LLM answers from its own parametric knowledge.
            No RAG context needed — faster and cheaper.
          - ``"local"``:   RAG-only. Strictly answer from provided context.
            Prevents hallucination on project-specific queries.
          - ``"hybrid"``:  Fuse RAG context with LLM's own knowledge.
            Best for questions that need both local docs and general knowledge.
        """
        if continue_mode:
            base = (
                "你是一个专业、准确的 AI 助手。这是一次连续对话，"
                "用户的消息可能很短或依赖上下文（例如「继续」「第二个」「优化一下」"
                "「展开」「为什么」）。请结合会话上下文自动理解用户意图并继续回答。"
                "不要要求用户重新描述。"
            )
        else:
            base = "你是一个专业、准确的 AI 助手。请根据以下指引回答用户问题。"

        if knowledge_source == "general":
            return base + (
                "\n\n你正在使用「通用知识模式」。请直接利用你自身掌握的"
                "知识回答用户问题，不需要参考任何外部资料。回答要准确、"
                "简洁、有条理。如果不确定，请如实告知。"
            )
        if knowledge_source == "local":
            return base + (
                "\n\n你正在使用「本地知识模式」。你必须严格基于下方提供的"
                "知识库资料和搜索结果来回答。不要添加知识库中没有的信息。"
                "如果提供的资料不足以回答问题，请如实告知用户。"
            )
        # hybrid (default)
        return base + (
            "\n\n你正在使用「混合知识模式」。下方可能提供了知识库资料"
            "（来自项目文档）和搜索结果。请将它们与你自身掌握的通用知识"
            "相结合来回答。知识库资料优先（项目文档比通用知识更权威），"
            "但你的通用知识可以用来补充和解释。回答要体现两者的融合。"
        )

    def _degraded_answer(
        self, goal: str, error_type: str, fallback: str, goal_type: str,
    ) -> str:
        """Produce a fallback answer when the LLM is unavailable."""
        lines = [f"**{fallback}**", ""]

        if error_type == "budget_exceeded":
            lines.append("请开启一个新会话继续提问。")
        elif error_type == "auth_error":
            lines.append("请到设置页面检查 API 密钥配置。")
        elif error_type == "rate_limit":
            lines.append("请稍等片刻后重试。")
        elif error_type == "network":
            lines.append("请检查后端服务和网络连接状态。")
        elif goal_type in _SUMMARY_GOAL_TYPES:
            lines.append(
                "系统处于受限模式，此前已完成的部分任务结果可能仍可用。"
            )
        else:
            lines.append("系统处于受限模式，部分功能暂时不可用。")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Preserved backward compat interfaces
    # ------------------------------------------------------------------

    def build_prompt(
        self, category: str, question: str,
        search_results: object, knowledge_context: str = "",
    ) -> str:
        """Preserved interface for backward compatibility."""
        return ""

    def format_search_results(self, results: object) -> str:
        """Preserved interface for backward compatibility."""
        return ""
