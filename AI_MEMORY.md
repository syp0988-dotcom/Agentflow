# AI Memory — 项目交接文档

> 阅读此文档后，新的 AI 开发者可以快速接手项目开发，
> 无需阅读全部源码即可理解整体架构和核心约定。

---

## 项目身份卡片

- **项目名**: OmniForge（曾用名 AgentFlow）
- **版本**: 0.1.0
- **描述**: 模块化多智能体 AI 工作台
- **语言**: Python 3.12+, TypeScript (Vue 3)
- **包名**: `omniforge` (pyproject.toml), `agentflow` (代码包名)
- **构建**: hatchling, uv

---

## 核心架构原则

### 1. 多 Agent 架构

项目采用 **LangGraph 状态机** 编排多个专业化 Agent。每个 Agent 是一个纯函数（`run(state) → state`），通过共享的 `WorkflowState` TypedDict 通信。

**永远不要直接调用另一个 Agent**。Agent 之间只能通过 WorkflowState 传递数据。

**添加新 Agent 的步骤**:
1. 实现 Agent 类，必须有 `run(self, state: dict) -> dict` 方法
2. 在 `agentflow/agents/registry.py` 注册元数据
3. 在 `agentflow/graph/workflow.py` 的 `build_workflow()` 中添加节点和边

### 2. 对话运行时优先

`ConversationManager` 是 **工作流唯一入口**。所有输入必须先经过它。
它处理：选项解析、槽填充、指代消解、继续模式判定。

**继续模式**（`_continue_mode`）直接跳过 Router/Planner/Tools，进入 Answer 节点。
这是实现自然连续对话的关键机制。

### 3. LLM 优先，规则回退

PlannerAgent 采用"LLM 主路径 + 规则回退"的双路径设计：
- LLM 成功 → 解析 JSON → 生成 Plan
- LLM 失败 → 基于 category 的规则 Plan

### 4. 能力驱动规划

Planner 永远使用 **capability**（如 `web.search`）规划，不直接写 tool 名。
`CapabilityRegistry` 是能力到工具名的唯一映射源。
添加新工具时需要在 `capability.py` 中注册 capability。

---

## 目录约定

| 目录 | 用途 | 规则 |
|------|------|------|
| `agentflow/agents/` | Agent 实现 | 每个 Agent 一个子目录，含 `__init__.py` 和 `agent.py` |
| `agentflow/conversation/` | 对话运行时 | 状态、重写、上下文管理 |
| `agentflow/graph/` | LangGraph 工作流 | 节点、边、Task、Plan、Event、Executor |
| `agentflow/services/` | 业务逻辑 | 无状态服务，可被多个 Agent 调用 |
| `agentflow/tools/` | 可执行工具 | 实现 BaseTool 接口 |
| `agentflow/knowledge/` | RAG 知识库 | 解析、嵌入、存储、检索 |
| `agentflow/database/` | 持久化 | SQLite 存储层 |
| `agentflow/config/` | 配置 | 环境变量中心化 |
| `agentflow/models/` | Pydantic 模型 | 请求/响应模型 |
| `agentflow/prompts/` | 提示模板 | 旧式 markdown 模板（当前嵌入在代码中） |
| `frontend/` | Vue 3 前端 | TypeScript + TailwindCSS |
| `tests/` | 测试 | pytest |

---

## 关键命名规范

- **所有 Agent 类** 以 `Agent` 结尾（`PlannerAgent`, `SearchAgent`）
- **Agent 的入口方法** 统一为 `run(state) -> dict`
- **Tool 类** 实现 `BaseTool`，`execute(**kwargs)` 方法
- **工作流节点函数** 在 `workflow.py` 中定义
- **配置** 通过 `Settings` 类（Pydantic）从环境变量加载
- **日志** 用 `build_logger(name)` 创建，输出到 `logs/{name}.log`
- **中文为主**：项目主要面向中文用户，Prompt、注释、界面均为中文

---

## 关键数据流

```
用户输入 → API路由 → build_workflow() → 
  ConversationManager (解析/重写/路由) →
    (继续模式) → AnswerAgent → MemoryAgent → 结束
    (新任务) → QueryRouterAgent → KnowledgeAgent → PlannerAgent →
      (search) → SearchAgent → AnswerAgent
      (python) → PythonAgent → AnswerAgent
      (direct) → AnswerAgent
    → MemoryAgent → 结束
→ 结果写入DB → 返回前端
```

---

## 数据库 Schema

```sql
-- 会话
sessions (id, title, created_at, updated_at, session_state TEXT)
  
-- 聊天消息
chats (id, session_id FK, role, content, created_at)

-- 知识库文档
documents (id, filename, file_type, file_size, doc_metadata, created_at)

-- 文档块
chunks (id, document_id FK, content, chunk_index, created_at)

-- 嵌入向量
embeddings (id, chunk_id FK UNIQUE, embedding BLOB)

-- 知识库元数据
knowledge_meta (key PK, value)

-- LLM 模型配置
llm_models (id, name, provider, base_url, api_key, model_name, 
            temperature, max_tokens, is_active, created_at, updated_at)
```

数据库路径: `agentflow/database/agentflow.db` (WAL 模式)

---

## 哪些地方**不能**修改

1. **工作流节点入口** - `conversation_manager` 节点是唯一入口，不能绕过
2. **SessionState 序列化格式** - 前后端和数据库都依赖 `to_dict()`/`from_dict()` 格式
3. **CapabilityRegistry 的 resolve API** - Planner 依赖固定的 capability → tool 映射接口
4. **app/main.py 的 CORS 配置** - 前端开发服务器端口 5173/5174
5. **`_continue_mode` 字段名** - 多个组件依赖此标志
6. **MemoryAgent 的 state["memory"] 格式** - 各组件依赖 `history`/`summary`/`context_str` 等字段
7. **`base.py` 的 BaseTool 接口** - Executor 依赖统一的 `execute(**kwargs)` 签名

---

## 哪些地方可以扩展

### 1. 添加新 Tool
- 实现 `BaseTool` 子类
- 在 `capability.py` 注册 capability
- 在 `Executor._build_executor()` 注册

### 2. 添加新 Search Provider
- 实现 `BaseSearchProvider` 子类
- 在 `SearchTool` 构造函数注入

### 3. 添加新 Agent
- 在 `agents/` 下创建子目录
- 注册到 `registry.py`
- 在 `workflow.py` 添加节点和边

### 4. 扩展对话类型
- 在 `context.py` 添加新的 turn type 常量
- 在 `ConversationManager.build_conversation_context()` 处理

### 5. 添加新的文档解析格式
- 在 `knowledge/parser.py` 添加 `_read_xxx()` 函数
- 在 `_read_raw()` 中添加分支

---

## 哪些地方以后要开发

详见 [AI_TODO.md](AI_TODO.md)

---

## 关键约定

### 代码约定
- 所有 import 使用 `from __future__ import annotations`
- 类型注解优先用 `| None` 而非 `Optional`
- Agent 的 `run()` 参数/返回类型为 `dict`（LangGraph 兼容）
- 使用 `TypedDict` (total=False) 定义 WorkflowState
- 所有数据类支持 `to_dict()` / `from_dict()` 序列化

### 工作流约定
- 新任务流程: CM → Router → (Knowledge) → Planner → (Tool) → Answer → Memory
- 继续流程: CM → Answer → Memory
- 路由后的条件分支:
  - identity/search 跳过 Knowledge
  - identity/search/coding/writing/knowledge 进入 Planner 的 direct_answer
  - search → SearchAgent
  - python → PythonAgent

### 错误处理约定
- Agent 不抛出异常，而是将错误信息写入 state
- LLM 调用失败应有回退（fallback）路径
- API 层用 HTTPException 返回错误
- 所有 LLMService.complete() 调用有 fallback 返回值

### 日志约定
- 每个文件顶层创建 logger: `logger = build_logger("模块名")`
- 日志文件输出到 `logs/{name}.log`
- 日志格式: `时间 | 级别 | 模块名 | 消息`

---

## 快速调试指南

```bash
# 启动后端
uv run uvicorn agentflow.app.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
uv run pytest -q

# 运行特定测试
uv run pytest tests/test_conversation_runtime.py -q -k "test_session_state"

# 查看日志
tail -f logs/agentflow.log

# 检查 API
curl http://localhost:8000/health
```

---

## 重要文件索引

| 文件 | 行数 | 重要性 |
|------|------|--------|
| `agentflow/graph/workflow.py` | 314 | ⭐⭐⭐ 核心 - 工作流定义 |
| `agentflow/conversation/manager.py` | 592 | ⭐⭐⭐ 核心 - 对话入口 |
| `agentflow/agents/planner/agent.py` | 408 | ⭐⭐⭐ 核心 - 任务规划 |
| `agentflow/agents/answer/agent.py` | 321 | ⭐⭐⭐ 核心 - 答案生成 |
| `agentflow/api/routes.py` | 418 | ⭐⭐⭐ 核心 - API 接口 |
| `agentflow/conversation/session_state.py` | 214 | ⭐⭐⭐ 核心 - 会话状态 |
| `agentflow/database/sqlite.py` | 496 | ⭐⭐ 重要 - 持久化 |
| `agentflow/graph/executor.py` | 118 | ⭐⭐ 重要 - 执行器 |
| `agentflow/services/llm_service.py` | 120 | ⭐⭐ 重要 - LLM 服务 |

---

## 修改代码前的检查清单

1. [ ] 是否理解了 LangGraph 状态机如何传递状态？
2. [ ] 是否检查了 `build_workflow()` 中的节点和边？
3. [ ] 新增 Agent 是否注册到 `registry.py`？
4. [ ] 新增 Tool 是否注册到 `Executor` 和 `capability.py`？
5. [ ] 修改 SessionState 格式是否同步更新了前端类型定义？
6. [ ] 数据库 schema 变更是否需要 migration？
7. [ ] 是否同时更新了 `to_dict()` 和 `from_dict()`？

---

## 相关文档

- [AI_PROJECT.md](AI_PROJECT.md) - 完整项目架构
- [AI_DIRECTORY.md](AI_DIRECTORY.md) - 目录结构
- [AI_API.md](AI_API.md) - API/类/函数参考
- [AI_WORKFLOW.md](AI_WORKFLOW.md) - 流程图
- [AI_TODO.md](AI_TODO.md) - 未来开发计划
