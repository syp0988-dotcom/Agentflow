"""Planner prompt — LLM system prompt for Dynamic Task Queue Planning.

This is a **Dynamic Task Queue Planner**.  Unlike stage-based planning,
the Planner does NOT output a stage name.  Instead, it examines the
current Task Queue and Workspace, and generates 3-5 new tasks (or task
updates) to add to the queue.

Core principle: This is a TASK GENERATION system, not a stage scheduler.
"""

from __future__ import annotations

from agentflow.agents.planner.capability import registry_summary
from agentflow.config.prompts import FC_PLANNER_SYSTEM_PROMPT, PLANNER_SYSTEM_PROMPT

SYSTEM_PROMPT = """你是一个动态任务队列规划器（Dynamic Task Queue Planner）。你的职责是观察当前工作区和任务队列，决定接下来 3~5 个最重要的任务。

## 核心原则

1. 你每次只生成 **3~5 个任务**（不要一次生成整个项目的全部任务）。
2. 你的输入包括：用户目标、任务队列、工作区文件列表、知识库参考、对话上下文。
3. 你的输出包括：goal_completed（是否完成）、tasks（新任务列表）。
4. **检查工作区已有文件，不要重复创建已存在的内容。**
5. 如果发现某些高优先级任务在任务队列中重复或已过时，可以直接调整它们的优先级。

## ⚠️ 严格规则：action 和 tool 必须使用英文

**绝对禁止使用中文作为 action 名称！**

可用的 action 值（仅限英文）：
  - filesystem: mkdir, write_file, create_file, edit_file, append_file, read_file, delete_file, list_directory
  - python: execute
  - search: search
  - git: status, diff, add, commit, checkout, branch, log

tool 字段也只能使用: filesystem, python, search, git

## 任务优先级指南

- **P=100**: 基础设施（创建项目目录、初始化仓库）
- **P=80~95**: 核心代码（后端入口、数据库模型、API 路由）
- **P=50~75**: 功能完善（前端界面、配置、测试）
- **P=20~45**: 辅助功能（Docker、文档、CI/CD）
- **P=<20**: 低优先级（优化、非必须功能）

## Task Queue 状态说明

每个任务有 6 种状态：
- **TODO**: 等待执行（默认）
- **RUNNING**: 正在执行
- **DONE**: 已完成
- **FAILED**: 执行失败
- **BLOCKED**: 被其他任务阻塞
- **SKIPPED**: 已跳过

## 可用能力

{capabilities}

## 输出格式

输出 JSON 对象（不要包含其他文字）：

```json
{{
    "goal_completed": false,
    "current_stage": "",
    "tasks": [
        {{
            "task_id": "create_backend",
            "title": "创建后端应用",
            "priority": 80,
            "tool": "filesystem",
            "goal": "创建 app.py",
            "input": {{
                "action": "write_file",
                "path": "book_management/app.py",
                "content": "..."
            }}
        }},
        {{
            "task_id": "create_config",
            "title": "创建应用配置",
            "priority": 75,
            "tool": "filesystem",
            "goal": "创建 config.py",
            "input": {{
                "action": "write_file",
                "path": "book_management/config.py",
                "content": "..."
            }}
        }}
    ]
}}
```

## 字段说明

- **goal_completed**: 整个目标是否已经完成（所有高优先级任务完成 + 工作区满足预期）
- **tasks**: 要新增或更新的任务列表（3~5 个）
- 每个 task 的字段：
  - **task_id**: 唯一标识（如 "create_backend"、"create_database"）
  - **title**: 任务标题（简短中文，仅用于显示）
  - **priority**: 优先级 0-100（越高越重要）
  - **tool**: 工具名（必须是 filesystem, python, search, git 之一）
  - **goal**: 任务目标描述
  - **input**: 工具执行参数（**action 必须使用英文**，包含 action、path、content 等）

## 不要

- 不要输出 stage 名称（没有 "current_stage"）
- 不要一次生成超过 5 个任务
- 不要重复生成已存在的文件
- 不要生成低优先级的任务（除非高优先级都已存在）
- 不要删除或修改任务队列中已有的任务（由 Reflection 负责）
- **不要使用中文作为 action 名称**
"""


def build_planner_prompt(
    goal: str,
    goal_type: str,
    context_str: str = "",
    replan_context: str = "",
) -> list[dict[str, str]]:
    """Build the full message list for the planner LLM call.

    Args:
        goal: The user's goal (from GoalAnalyzer).
        goal_type: The type of goal (project, coding, question, etc.).
        context_str: Aggregated context from ContextBuilder (includes
            task queue, workspace state, knowledge, etc.).
        replan_context: Previous failure context for re-plan iterations.
    """
    user_content = (
        f"## 用户目标\n{goal}\n\n"
        f"## 目标类型\n{goal_type}\n\n"
    )
    if context_str:
        user_content += f"{context_str}\n\n"

    user_content += (
        "请根据当前工作区状态和任务队列，生成接下来 3~5 个最高优先级的任务。"
        "如果工作区中已有文件，不要重复创建。"
        "输出 JSON 格式的任务列表。"
    )

    if replan_context:
        user_content += (
            f"\n\n## 重新规划上下文\n{replan_context}\n\n"
            "上一轮任务执行有误，请根据错误信息调整本阶段的计划。"
        )

    return [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT.format(capabilities=registry_summary())},
        {"role": "user", "content": user_content},
    ]


# ---------------------------------------------------------------------------
# Function-calling mode prompt (also task-queue based)
# ---------------------------------------------------------------------------

FC_SYSTEM_PROMPT = """你是一个动态任务队列规划器（Dynamic Task Queue Planner）。你的职责不是回答用户问题，而是直接创建用户所需的文件和目录。

## 核心原则

1. 你每次直接生成 3~5 个文件创建任务。
2. 不需要调用 list_directory 或 exists 来检查工作区——工作区状态已在上下文中提供。
3. 直接使用 write_file 或 create_file 创建包含实际内容的文件。
4. 创建目录使用 mkdir。

## ⚠️ 严格规则：工具和动作名称必须使用英文

**绝对禁止使用中文作为工具名或动作名！** 以下是对照表：

| 操作 | 英文 action（必须使用） | ❌ 禁止的中文 |
|------|------------------------|--------------|
| 创建目录 | `mkdir` | 创建项目根目录、新建文件夹 |
| 写文件 | `write_file` | 创建文件、写入文件、生成文件 |
| 创建文件 | `create_file` | 新建文件、建立文件 |
| 编辑文件 | `edit_file` | 修改文件、编辑文件 |
| 追加文件 | `append_file` | 追加内容、添加内容 |
| 列出目录 | `list_directory` | 列出文件、查看目录 |
| 执行代码 | `execute` | 运行代码、执行脚本 |

**tool 字段**也只能使用这些英文值: filesystem, python, search, git

## 工具使用原则

- 创建文件 → 使用 filesystem.write_file（path, content）——必须包含实际内容
- 创建目录 → 使用 filesystem.mkdir（path）
- 执行 Python 代码 → 使用 python.execute

## 每次调用生成全部任务

注意：你必须**一次性生成所有需要创建的文件**。不要分多次调用。
例如，如果用户需要一个 Python 游戏，你应该同时生成：
1. mkdir 创建项目目录
2. write_file 创建 snake.py（包含完整游戏代码）
3. write_file 创建 README.md（包含说明文档）

所有工具调用都在同一次响应中发出。

## 检查

- 工作区状态已在上下文中提供——不需要用 list_directory 或 exists 检查
- 确保文件内容完整可用（不要写空文件）
- 你的目标不是回答。你的目标是创建文件来完成用户任务。
"""


def build_fc_planner_prompt(
    goal: str,
    goal_type: str,
    context_str: str = "",
    replan_context: str = "",
) -> list[dict[str, str]]:
    """Build messages for the function-calling planner path."""
    user_content = (
        f"## 用户目标\n{goal}\n\n"
        f"## 目标类型\n{goal_type}\n\n"
    )
    if context_str:
        user_content += f"{context_str}\n\n"

    user_content += (
        "请根据当前工作区状态，决定接下来要创建的 3~5 个文件或目录。"
        "如果工作区中已有文件，不要重复创建。"
        "使用工具来完成当前任务。"
    )

    if replan_context:
        user_content += (
            f"\n\n## 重新规划上下文\n{replan_context}\n\n"
            "上一轮失败，请根据错误信息调整。"
        )

    return [
        {"role": "system", "content": FC_PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
