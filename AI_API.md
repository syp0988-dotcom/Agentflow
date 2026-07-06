# AI_API — 完整 API、类、函数参考

> 所有源码位置均为相对于项目根目录 `g:/multi_agent/` 的路径。

---

## 一、REST API 端点

所有端点前缀：无独立前缀（FastAPI router 挂载在根路径 `/`）

### 聊天

#### POST `/chat`
| 项目 | 说明 |
|------|------|
| **文件** | `agentflow/api/routes.py:50` |
| **请求体** | `ChatRequest { message, history?, session_id? }` |
| **响应** | `ChatResponse { reply, metadata, debug?, proposed_files? }` |
| **用途** | 聊天请求，运行完整工作流 |
| **调用** | `frontend/src/api/client.ts` 中 `postChat()` |

### Agent 内省

#### GET `/agents`
| 项目 | 说明 |
|------|------|
| **文件** | `agentflow/api/routes.py:41` |
| **响应** | `list[AgentInfo]` — 所有注册 Agent 元数据 |
| **用途** | 前端获取 Agent 列表 |

### 知识库

#### POST `/upload`
| 项目 | 说明 |
|------|------|
| **文件** | `agentflow/api/routes.py:117` |
| **请求** | `multipart/form-data`, file |
| **允许类型** | .pdf, .docx, .doc, .txt, .md, .markdown |
| **用途** | 上传文档到知识库，自动解析索引 |

#### GET `/knowledge/documents`
| 项目 | 说明 |
|------|------|
| **文件** | `agentflow/api/routes.py:158` |
| **响应** | `list[document]` |
| **用途** | 列出所有索引文档 |

#### DELETE `/knowledge/documents/{doc_id}`
| 文件 | `agentflow/api/routes.py:164` |
|------
| **用途** | 删除文档及其块/嵌入 |

#### POST `/knowledge/search`
| 项目 | 说明 |
|------|------|
| **文件** | `agentflow/api/routes.py:171` |
| **参数** | `query: str`, `top_k: int=5` |
| **响应** | `list[{chunk_id, document_id, filename, content, score}]` |
| **用途** | 搜索知识库 |

### 会话管理

#### POST `/sessions/create`
| 文件 | `agentflow/api/routes.py:323` |
|------
| **用途** | 创建新会话 |

#### GET `/sessions`
| 文件 | `agentflow/api/routes.py:330` |
|------
| **参数** | `limit: int=50` |
| **用途** | 列出所有会话 |

#### GET `/sessions/{session_id}/messages`
| 文件 | `agentflow/api/routes.py:336` |
|------
| **用途** | 获取会话消息 |

#### PUT `/sessions/{session_id}/rename`
| 文件 | `agentflow/api/routes.py:345` |
|------
| **用途** | 重命名会话 |

#### DELETE `/sessions/{session_id}`
| 文件 | `agentflow/api/routes.py:357` |
|------
| **用途** | 删除会话 |

### 文件操作

#### POST `/files/create`
| 文件 | `agentflow/api/routes.py:195` |
|------
| **用途** | 创建 Agent 提议的文件 |

#### GET `/files`
| 文件 | `agentflow/api/routes.py:223` |
|------
| **用途** | 列出输出文件 |

### 工作区

#### GET `/workspace`
| 文件 | `agentflow/api/routes.py:252` |
|------
| **用途** | 检查工作区状态 |

#### POST `/workspace/set`
| 文件 | `agentflow/api/routes.py:262` |
|------
| **用途** | 设置工作区目录（含写权限测试） |

#### POST `/workspace/create-folder`
| 文件 | `agentflow/api/routes.py:285` |
|------
| **用途** | 创建文件夹 |

#### GET `/workspace/browse`
| 文件 | `agentflow/api/routes.py:304` |
|------
| **用途** | 浏览目录 |

### 模型配置

#### GET `/models`
| 文件 | `agentflow/api/routes.py:369` |
|------
| **用途** | 列出所有模型（不返回 API key） |

#### POST `/models`
| 文件 | `agentflow/api/routes.py:377` |
|------
| **用途** | 创建模型配置 |

#### PUT `/models/{model_id}`
| 文件 | `agentflow/api/routes.py:392` |
|------
| **用途** | 更新模型配置 |

#### DELETE `/models/{model_id}`
| 文件 | `agentflow/api/routes.py:401` |
|------
| **用途** | 删除模型配置 |

#### POST `/models/{model_id}/activate`
| 文件 | `agentflow/api/routes.py:410` |
|------
| **用途** | 激活模型（设为当前使用） |

### 健康检查

#### GET `/health`
| 文件 | `agentflow/app/main.py:32` |
|------
| **响应** | `{"status": "ok", "service": "OmniForge"}` |

---

## 二、核心类

### WorkflowState (`graph/workflow.py:27`)

```python
class WorkflowState(TypedDict, total=False):
    question: str
    workflow: list[str]
    category: str
    plan: dict[str, Any]
    search_results: list[dict[str, Any]]
    knowledge_results: list[dict[str, Any]]
    knowledge_context: str
    python_result: dict[str, Any]
    answer: str
    memory: dict[str, Any]
    history: list[dict[str, str]]
    router: dict[str, Any]
    session_state: dict[str, Any]
    _continue_mode: bool
    session_context: str
    rewritten_question: str
    conversation_context: Any
```

### WorkflowContext (`graph/context.py:25`)

**继承**: `dict`

| 属性/方法 | 类型 | 说明 |
|-----------|------|------|
| `version` | property | 上下文 schema 版本 ("1.0") |
| `question` | property | 用户原始问题 |
| `category` | property | 查询分类 |
| `answer` | property | 最终答案 |
| `plan` | property | 工作计划 |
| `workflow` | property | 工作流节点列表 |
| `history` | property | 对话历史 |
| `memory` | property | 记忆数据 |
| `search_results` | property | 搜索结果 |
| `knowledge_context` | property | 知识上下文 |
| `python_result` | property | Python 执行结果 |
| `router` | property | 路由元数据 |
| `conversation_context` | property | 回合上下文 |
| `session_state` | property | SessionState 对象 |
| `tasks` | property | 所有 Task 列表 |
| `events` | property | 所有事件列表 |
| `to_dict()` | method | 序列化为纯 dict |

### SessionState (`conversation/session_state.py:20`)

**类型**: dataclass

| 字段 | 类型 | 说明 |
|------|------|------|
| `current_goal` | str | 当前用户目标 |
| `current_task` | str | 当前执行任务 |
| `current_step` | str | 当前步骤 |
| `status` | str | idle / waiting_user / processing |
| `waiting_for` | str | 等待用户提供的输入 |
| `pending_options` | dict[str,str] | 待选选项 |
| `slots` | dict[str,Any] | 槽位 |
| `metadata` | dict[str,Any] | 扩展元数据 |
| `tracking` | ConversationState\|None | 话题实体追踪 |

| 方法 | 说明 |
|------|------|
| `resolve_option(input)` | 解析用户选项选择 |
| `fill_slot(name, value)` | 填充槽位 |
| `start_waiting(what)` | 进入等待用户模式 |
| `resume()` | 从等待恢复 |
| `reset()` | 重置所有字段 |
| `to_dict()` / `from_dict()` | 序列化/反序列化 |

**属性**: `is_waiting`, `has_pending_options`, `has_unfilled_slots`

### ConversationState (`conversation/state.py:17`)

**类型**: dataclass

| 字段 | 类型 | 说明 |
|------|------|------|
| `topic` | str | 当前话题 |
| `entities` | set[str] | 累积实体 |
| `current_focus` | str | 当前焦点 |
| `last_answer` | str | 上轮回答 |
| `summary` | str | 规则摘要 |
| `facts` | dict[str,str] | 关键事实 |
| `tool_result` | str | 工具执行结果 |

### ConversationContext (`conversation/context.py:23`)

**类型**: dataclass

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | str | 回合类型（6种常量） |
| `original_question` | str | 原始输入 |
| `rewritten_question` | str | 重写后问题 |
| `current_goal` | str | 当前目标 |
| `last_topic` | str | 上轮话题 |
| `waiting_for` | str | 等待输入 |
| `entities` | list[str] | 实体列表 |
| `summary` | str | 对话摘要 |

**回合类型常量**: `NEW_TASK`, `FOLLOW_UP`, `OPTION_SELECTION`, `WAITING_REPLY`, `CLARIFICATION`, `QUESTION_REWRITE`

### Task (`graph/task.py:47`)

**类型**: dataclass

| 字段 | 类型 | 说明 |
|------|------|------|
| `goal` | str | 任务目标 |
| `capability` | str | 所需能力 |
| `agent` | str | 创建 Agent |
| `tool` | str | 执行工具 |
| `status` | TaskStatus | 生命周期状态 |
| `parent_id` | str\|None | 父任务 ID |
| `input` | dict | 工具参数 |
| `result` | Any | 执行结果 |
| `error` | str\|None | 错误信息 |
| `id` | str | 唯一 ID (12-char hex) |

**方法**: `mark_ready()`, `mark_running()`, `complete()`, `fail()`, `skip()`, `cancel()`, `to_dict()`

**TaskStatus 枚举**: PENDING, READY, RUNNING, WAITING, RETRYING, COMPLETED, FAILED, CANCELLED, SKIPPED

### Plan (`graph/plan.py:22`)

**类型**: dataclass

| 字段 | 类型 | 说明 |
|------|------|------|
| `goal` | str | 计划目标 |
| `category` | str | 查询分类 |
| `tasks` | list[Task] | 任务序列 |
| `direct_answer` | bool | 是否直接回答 |
| `priority` | str | normal/high/low |
| `reasoning` | str | 选择理由 |

### Event (`graph/event.py:52`)

**类型**: dataclass

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | EventType | 事件类型 |
| `timestamp` | str | ISO-8601 时间戳 |
| `task_id` | str | 关联 Task ID |
| `agent` | str | 触发 Agent |
| `tool` | str | 关联工具 |
| `data` | dict | 负载数据 |

**EventType 枚举**: TASK_CREATED, TASK_STARTED, TASK_FINISHED, TASK_FAILED, TOOL_STARTED, TOOL_FINISHED

---

## 三、Agent 类

### ConversationManager (`conversation/manager.py:65`)

| 方法 | 输入 | 输出 | 说明 |
|------|------|------|------|
| `should_continue(ss)` | SessionState | bool | 判断是否需要继续模式 |
| `resolve_question(q, ss)` | str, SessionState | str | 解析选项/槽/指代 |
| `rewrite_question(q, ss, memory)` | str, SessionState, dict | str | 重写问题 |
| `build_conversation_context(orig, rewritten, ss, memory)` | ... | ConversationContext | 构建回合上下文 |
| `finalize_turn(state, ss, answer)` | dict, SessionState, str | None | 回合结束时更新状态 |

### PlannerAgent (`agents/planner/agent.py:59`)

| 方法 | 说明 |
|------|------|
| `run(state)` | 主入口：LLM 规划 → 规则回退 → 能力解析 |
| `_llm_plan(question, category)` | LLM 规划路径 |
| `_parse_json(raw)` | 鲁棒 JSON 解析（3 种策略） |
| `_build_plan_from_json(data)` | JSON → Plan 对象 |
| `_resolve_capabilities(plan)` | capability → tool 名 |
| `_build_plan(question, category)` | 规则回退规划 |

### QueryRouterAgent (`agents/router/agent.py:9`)

| 方法 | 说明 |
|------|------|
| `run(state)` | 分类并设置 category |
| `classify(question)` | 正则匹配，返回 category |
| `match_any(text, patterns)` | 静态方法，匹配任意模式 |

**分类模式**: IDENTITY_PATTERNS, SEARCH_PATTERNS, CODING_PATTERNS, WRITING_PATTERNS, REASONING_PATTERNS, KNOWLEDGE_PATTERNS, PYTHON_PATTERNS

### AnswerAgent (`agents/answer/agent.py:164`)

| 方法 | 说明 |
|------|------|
| `run(state)` | 生成最终答案 |
| `build_prompt(...)` | 后向兼容构建 prompt |
| `clean_answer(text)` | 去除 LLM 输出噪音 |
| `_system_prompt(continue_mode)` | 构建系统提示 |
| `_format_search_context(results)` | 格式化搜索结果 |

### ContextBuilder (`agents/answer/agent.py:31`)

| 方法 | 说明 |
|------|------|
| `build_system_prompt()` | 构建系统提示（含 continue 感知） |
| `build_user_prompt()` | 组装所有上下文的用户提示 |
| `_format_conversation_context()` | 格式化回合上下文 |
| `_format_history()` | 格式化历史对话 |

### MemoryAgent (`agents/memory/agent.py:14`)

| 方法 | 说明 |
|------|------|
| `run(state)` | 维护历史、更新 session_state、构建摘要 |
| `_update_memory_meta(...)` | 更新记忆元数据（goal, topic, summary, type） |

### SearchAgent (`agents/search/agent.py:9`) / KnowledgeAgent (`agents/knowledge/agent.py:11`) / PythonAgent (`agents/python/agent.py:21`)

各有一个 `run(state)` 方法，职责明确。

---

## 四、Tool 类

### BaseTool (`tools/base.py:20`)

```python
class BaseTool(ABC):
    name: str = ""
    @abstractmethod
    def execute(**kwargs) -> Any: ...
```

### SearchTool (`tools/search_tool.py:17`)

| 方法 | 签名 | 说明 |
|------|------|------|
| `execute(query, **kwargs)` | `(query="") → list[dict]` | 执行搜索 |
| `search(query)` | `(query) → list[dict]` | 遗留接口 |
| `clean_url(url)` | 静态方法 | 解码 DuckDuckGo 重定向 URL |

**Provider 注入**: 构造函数接受 `BaseSearchProvider`

### PythonTool (`tools/python_tool.py:18`)

| 方法 | 签名 | 说明 |
|------|------|------|
| `execute(code, **kwargs)` | `(code="") → dict` | 执行 Python 代码 |

**返回 dict**: `{status, stdout, stderr, return_code, duration}`

**安全措施**: ast.parse 语法校验 → 空白 subprocess env → tempfile 目录 → 30s timeout → 10K 输出截断

---

## 五、Service 类

### LLMService (`services/llm_service.py:14`)

| 方法 | 说明 |
|------|------|
| `complete(prompt, messages)` | LLM 补全，支持 prompt 或 messages |
| `use_model(model_config)` | 运行时切换模型 |
| `_init_client(api_key, base_url)` | 初始化 OpenAI 客户端 |
| `_try_load_active_model()` | 从数据库加载活跃模型 |

**全局实例**: `_llm_service` (单例), `get_llm_service()` 用于获取

### SearchService (`services/search_service.py:55`)

| 方法 | 说明 |
|------|------|
| `search(query) → SearchResult` | 参数验证 → 执行 → 标准化 |

### DuckDuckGoProvider (`services/search_provider.py:48`)

| 方法 | 说明 |
|------|------|
| `search(query) → list[dict]` | 爬取 DuckDuckGo HTML |
| `_parse_results(html)` | 解析搜索结果 |
| `_clean_url(url)` | 解码重定向 URL |

### FileProposer (`services/file_proposer.py:49`)

| 函数 | 说明 |
|------|------|
| `propose_files(answer_text) → list[dict]` | 提取代码块并提案文件 |

---

## 六、Knowledge 类

### KnowledgeStore (`knowledge/store.py:22`)

| 方法 | 说明 |
|------|------|
| `add_document(file_path, filename) → int` | 解析 → 分块 → 嵌入 → 存储 |
| `delete_document(doc_id)` | 删除文档及对应嵌入 |
| `list_documents()` | 列出所有文档 |
| `search(query, top_k, min_score)` | 余弦相似度搜索 |

### TfidfEmbedder (`knowledge/embedder.py:56`)

| 方法 | 说明 |
|------|------|
| `add_chunk(tokens)` | 更新词汇表和文档频率 |
| `remove_chunk(tokens)` | 减少文档频率 |
| `vectorize(tokens) → np.ndarray` | 计算 TF-IDF 向量 |
| `cosine_similarity(a, b) → float` | 余弦相似度 |
| `batch_cosine_similarity(query, candidates)` | 批量排序 |

### parser.py (`knowledge/parser.py`)

| 函数 | 说明 |
|------|------|
| `parse_document(path, file_type) → list[str]` | 解析文档为文本块 |
| `chunk_text(text, size=500, overlap=50)` | 按段落分块 |
| `_read_pdf(path)` | PDF 解析 (pypdf) |
| `_read_docx(path)` | Word 解析 (python-docx) |
| `_read_markdown(path)` | Markdown 解析（去除 frontmatter） |

---

## 七、Graph 类

### Executor (`graph/executor.py:28`)

| 方法 | 说明 |
|------|------|
| `register_tool(name, tool)` | 注册工具 |
| `list_tools() → list[str]` | 列出所有工具 |
| `get_tool(name) → BaseTool\|None` | 获取工具 |
| `execute(ctx, task) → Task` | 执行 Task 全生命周期 |

### EventBus (`graph/event.py:95`)

| 静态方法 | 触发时机 |
|----------|----------|
| `task_created(ctx, task)` | Task 创建 |
| `task_started(ctx, task)` | Task 开始执行 |
| `task_finished(ctx, task)` | Task 成功完成 |
| `task_failed(ctx, task)` | Task 失败 |
| `tool_started(ctx, task, input)` | 工具开始执行 |
| `tool_finished(ctx, task, result)` | 工具完成执行 |

---

## 八、Conversation 类

### RewriteEngine (`conversation/rewrite.py:79`)

| 静态方法 | 说明 |
|----------|------|
| `needs_rewrite(question) → bool` | 判断是否需要重写 |
| `rewrite(question, session_state, memory) → str` | 重写问题 |

**重写类型**: 序数选择、修改意图、追问、指示引用、短输入

---

## 九、重要 TypedDict / Pydantic 模型

### SQLiteStore 关键方法 (`database/sqlite.py`)

**Session 操作**: `create_session`, `get_session`, `list_sessions`, `update_session_title`, `update_session_state`, `get_session_state`, `delete_session`

**Chat 操作**: `add_message`, `list_messages`, `get_session_messages`

**Document 操作**: `add_document`, `get_all_documents`, `delete_document_cascade`

**Chunk 操作**: `add_chunk`, `get_chunks_by_document`, `get_chunk_with_document`

**Embedding 操作**: `add_embedding`, `get_all_embeddings_with_chunk`

**Model 操作**: `add_model`, `get_all_models`, `get_model`, `update_model`, `delete_model`, `get_active_model`, `set_active_model`

### ChatRequest (`models/chat.py:17`)
```python
class ChatRequest(BaseModel):
    message: str        # min_length=1
    history: list[ChatMessage]
    session_id: int | None
```

### ChatResponse (`models/chat.py:35`)
```python
class ChatResponse(BaseModel):
    reply: str
    metadata: dict
    debug: dict | None
    proposed_files: list[FileProposal]
```

### AgentInfo (`agents/registry.py:16`)
```python
@dataclass
class AgentInfo:
    key: str                     # 唯一标识
    name: str                    # 显示名称
    description: str             # 描述
    category: str                # 分类 (routing/planning/...)
    status: str                  # active/inactive
    capabilities: list[str]      # 能力列表
    module_path: str             # 模块路径
```

---

## 十、日志工具

### build_logger (`utils/logging.py:9`)

```python
def build_logger(name: str) -> logging.Logger:
    # 创建 logs/{name}.log 文件 + 控制台输出
    # 格式: "时间 | 级别 | 名称 | 消息"
```

每个模块独立日志文件：`logs/{agentflow,answer,api,planner,...}.log`

---

## 十一、前端 API 客户端

文件: `frontend/src/api/client.ts`

| 函数 | HTTP | 路径 |
|------|------|------|
| `postChat(message, history?, sessionId?)` | POST | `/chat` |
| `uploadDocument(file)` | POST | `/upload` |
| `getDocuments()` | GET | `/knowledge/documents` |
| `deleteDocument(docId)` | DELETE | `/knowledge/documents/{id}` |
| `searchKnowledge(query, topK)` | POST | `/knowledge/search` |
| `getAgents()` | GET | `/agents` |
| `createSession()` | POST | `/sessions/create` |
| `listSessions(limit)` | GET | `/sessions` |
| `getSessionMessages(sessionId)` | GET | `/sessions/{id}/messages` |
| `renameSession(sessionId, title)` | PUT | `/sessions/{id}/rename` |
| `deleteSession(sessionId)` | DELETE | `/sessions/{id}` |
| `getHistory(limit)` | GET | `/history` |
| `createFile(filename, content, workspacePath?)` | POST | `/files/create` |
| `getOutputFiles(workspacePath?)` | GET | `/files` |
| `setWorkspace(path)` | POST | `/workspace/set` |
| `createServerFolder(parentPath, folderName)` | POST | `/workspace/create-folder` |
| `browseDirectory(path)` | GET | `/workspace/browse` |
| `getModels()` | GET | `/models` |
| `createModel(data)` | POST | `/models` |
| `updateModel(id, data)` | PUT | `/models/{id}` |
| `deleteModel(id)` | DELETE | `/models/{id}` |
| `activateModel(id)` | POST | `/models/{id}/activate` |
