"""ProjectConfigurator — auto-derive project variables from user goal.

Uses rule-based extraction first, then optionally rounds through the LLM
to fill in blueprint-specific variables (database choice, auth, etc.).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from agentflow.blueprints.models import Blueprint, VariableDef
from agentflow.utils.logging import build_logger

logger = build_logger("blueprint_config")

# ---------------------------------------------------------------------------
# Heuristic patterns for extracting project info from a user goal
# ---------------------------------------------------------------------------

# "创建图书管理系统"  →  project_name="book_management"
_PROJECT_NAME_PATTERNS = [
    # Chinese: "创建一个图书管理系统" → "图书管理"
    re.compile(r"(?:创建|开发|做|实现|搭建|构建|写)\s*(?:一个|个)?\s*(.*?)(?:系统|项目|应用|网站|平台|工具|服务)"),
    re.compile(r"(?:叫|名为|叫做)\s*['\"“”]?(.+?)['\"”]?\s*(?:的|项目|系统)"),
    # English: "create a blog system" → "blog"
    re.compile(r"(?:create|build|make|write|develop|new)\s+(?:a|an|the)?\s*(.*?)(?:\s+(?:system|app|application|project|service|tool|website|site|api))"),
    # English fallback: "a blog system with FastAPI" → "blog"
    re.compile(r"(?:a|an|the)\s+(\w+)\s+(?:system|app|application|project|service|tool)"),
]

# "用 FastAPI 写一个 REST API" →  frameworks=["fastapi"]
_FRAMEWORK_MAP: dict[str, list[str]] = {
    "fastapi": ["fastapi"],
    "flask": ["flask"],
    "django": ["django"],
    "react": ["react"],
    "next": ["nextjs"],
    "vue": ["vue"],
    "svelte": ["svelte"],
}

# Common keywords →  tech tags
_TECH_TAGS: dict[str, list[str]] = {
    "rest": ["rest"],
    "api": ["rest"],
    "graphql": ["graphql"],
    "cli": ["cli"],
    "命令行": ["cli"],
    "博客": ["blog"],
    "电商": ["ecommerce"],
    "管理": ["admin"],
    "聊天": ["chat"],
    "实时": ["realtime"],
}


@dataclass
class ProjectConfig:
    """Derived project configuration passed to the Jinja2 render step."""

    project_name: str
    """Filesystem-safe slug, e.g. ``"book_management"``."""

    package_name: str
    """Python import-safe name, e.g. ``"book_management"`` (same as project_name)."""

    app_name: str
    """Human-readable app name, e.g. ``"Book Management"``."""

    goal: str = ""
    """Original user goal."""

    detected_frameworks: list[str] = field(default_factory=list)
    """Frameworks detected from the goal text."""

    detected_tags: list[str] = field(default_factory=list)
    """Tech tags detected from the goal text."""

    extra: dict[str, Any] = field(default_factory=dict)
    """Extra blueprint-specific variables (filled by LLM step)."""

    def to_dict(self) -> dict[str, Any]:
        """Flatten into the variable dict used by Jinja2 rendering."""
        return {
            "project_name": self.project_name,
            "package_name": self.package_name,
            "app_name": self.app_name,
            "goal": self.goal,
            **self.extra,
        }


class ProjectConfigurator:
    """Auto-derive project configuration from a user goal string."""

    @staticmethod
    def from_goal(goal: str) -> ProjectConfig:
        """Rule-based extraction — always works, no LLM needed."""
        project_name = _extract_project_name(goal)
        app_name = project_name.replace("_", " ").replace("-", " ").title()
        frameworks = _detect_frameworks(goal)
        tags = _detect_tags(goal)

        return ProjectConfig(
            project_name=project_name,
            package_name=project_name,
            app_name=app_name,
            goal=goal,
            detected_frameworks=frameworks,
            detected_tags=tags,
        )

    @staticmethod
    def with_llm(
        goal: str,
        blueprint: Blueprint,
        base_config: ProjectConfig | None = None,
    ) -> ProjectConfig:
        """Use the LLM to fill in blueprint-specific variables.

        Only required variables with no default are sent to the LLM.
        If the LLM call fails, defaults are used for all variables.
        """
        if base_config is None:
            base_config = ProjectConfigurator.from_goal(goal)

        # Collect variables the LLM should decide
        llm_vars = [
            v for v in blueprint.variables
            if v.required and v.default is None
        ]
        if not llm_vars:
            # No variables need LLM help
            return base_config

        try:
            return ProjectConfigurator._llm_fill(goal, blueprint, base_config, llm_vars)
        except Exception as exc:
            logger.warning("LLM variable filling failed: %s", exc)
            # Fall back to defaults
            return base_config

    @staticmethod
    def _llm_fill(
        goal: str,
        blueprint: Blueprint,
        base: ProjectConfig,
        required_vars: list[VariableDef],
    ) -> ProjectConfig:
        """Call the LLM to fill in required blueprint variables."""
        from agentflow.services.llm_service import get_llm_service
        import json

        llm = get_llm_service()
        var_descriptions = "\n".join(
            f"  - {v.name}: {v.description}" +
            (f" (choices: {v.choices})" if v.choices else "")
            for v in required_vars
        )

        prompt = (
            f"用户目标：{goal}\n\n"
            f"项目名称：{base.project_name}\n"
            f"检测到的框架：{', '.join(base.detected_frameworks) or '无'}\n\n"
            f"请根据用户目标为以下变量选择最合适的值，只输出 JSON 对象：\n"
            f"{var_descriptions}\n"
        )

        raw = llm.complete(messages=[
            {"role": "system", "content": "你是一个项目配置助手。根据用户的项目目标，为蓝图变量选择最合适的值。只输出 JSON，不要其他文字。"},
            {"role": "user", "content": prompt},
        ])
        raw = raw.strip()
        # Strip markdown fences if present
        for marker in ("```json", "```JSON", "```"):
            if marker in raw:
                raw = raw.split(marker, 1)[-1]
                raw = raw.rsplit("```", 1)[0]
                raw = raw.strip()

        parsed: dict[str, Any] = json.loads(raw)

        base.extra.update(parsed)
        return base


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_project_name(goal: str) -> str:
    """Extract a safe project directory name from the user goal."""
    goal_clean = goal.strip()

    for pattern in _PROJECT_NAME_PATTERNS:
        m = pattern.search(goal_clean)
        if m:
            raw = m.group(1).strip()
            raw = re.sub(r"^(?:一个|个)", "", raw).strip()
            if raw:
                return _to_slug(raw)

    # Fallback: take first ~20 chars
    name = goal_clean[:24].replace(" ", "_").lower()
    return re.sub(r"[^a-z0-9_]", "", name) or "my_project"


def _detect_frameworks(goal: str) -> list[str]:
    """Detect frameworks mentioned in the goal."""
    goal_lower = goal.lower()
    found: list[str] = []
    for keyword, frameworks in _FRAMEWORK_MAP.items():
        if keyword in goal_lower:
            found.extend(frameworks)
    return list(set(found))


def _detect_tags(goal: str) -> list[str]:
    """Detect tech tags from the goal."""
    goal_lower = goal.lower()
    found: list[str] = []
    for keyword, tags in _TECH_TAGS.items():
        if keyword in goal_lower:
            found.extend(tags)
    return list(set(found))


def _to_slug(text: str) -> str:
    """Convert arbitrary text to a filesystem-safe snake_case slug.

    Preserves Chinese characters and other Unicode word characters
    so that ``"图书管理"`` becomes ``"图书管理"``, not ``"my_project"``.
    """
    slug = text.replace(" ", "_").replace("-", "_")
    slug = re.sub(r"[^\w]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"_+", "_", slug)
    slug = slug.strip("_")
    return slug or "my_project"
