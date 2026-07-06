# OmniForge (AgentFlow) 项目问题与不完善模块报告

> 分析时间: 2026-07-06 | 项目版本: v0.1.0

---

## 一、核心架构问题

### 1.1 Agent 无统一基类/接口契约

**位置**: `agentflow/agents/*/agent.py`

**问题**: 所有 Agent 都实现了 `run(state) -> dict` 方法，但没有抽象基类或 Protocol 约束。签名全靠开发约定保障，类型系统无法校验。新增 Agent 时容易遗漏方法或参数类型不匹配。

**影响**: 中等。当前 8 个 Agent 签名一致，但缺乏编译期检查，重构/扩展时风险高。

**建议**: 抽取 `BaseAgent` 抽象基类或 `AgentProtocol`，定义 `run(state: dict) -> dict` 接口。

---

### 1.2 `session_state` 类型混用

**位置**: 
- [agentflow/graph/workflow.py:155-160](agentflow/graph/workflow.py#L155-L160)
- [agentflow/graph/workflow.py:143-169](agentflow/graph/workflow.py#L143-L169)
- [agentflow/graph/workflow.py:237-255](agentflow/graph/workflow.py#L237-L255)

**问题**: `session_state` 在 WorkflowState 中定义为 `dict[str, Any]`，但实际代码中有时是 `dict`、有时是 `SessionState` 对象，多处需要通过 `isinstance`/`hasattr` 做运行时判断：

```python
if isinstance(raw, dict):
    return raw.get("status") == "waiting_user"
elif hasattr(raw, "is_waiting"):
    return raw.is_waiting
```

**影响**: 高。运行时类型不确定性是 Bug 的常见来源，且导致大量样板代码。

**建议**: 统一 WorkflowState 中 `session_state` 的类型，全部使用 `SessionState` 对象传递，仅在序列化/反序列化边界转为 dict。

---

### 1.3 ReportAgent 不完整

**位置**: [agentflow/agents/report/agent.py](agentflow/agents/report/agent.py)

**问题**: ReportAgent 已完整实现但注册为 `inactive`，未集成到 LangGraph 工作流中。它与 AnswerAgent 功能重叠（都是生成最终回答），项目目前对二者关系没有明确定义。

**影响**: 低（未使用）。但属于未完成的功能模块，造成困惑。

**建议**: 明确决策 —— 要么删除，要么改造成长文本/报告专用生成器，由 Planner 按需选择。

---

### 1.4 `observer/` 目录为空

**位置**: [agentflow/agents/observer/](agentflow/agents/observer/)

**问题**: 目录下只有 `__pycache__`，没有任何源码文件。说明这是一个有计划但从未启动的 Agent 模块。

**影响**: 低。但属于项目中的"幽灵模块"。

**建议**: 如果短期内不开发，移除该目录以避免混淆。

---

### 1.5 知识检索能力未绑定工具

**位置**: [agentflow/agents/planner/capability.py:30](agentflow/agents/planner/capability.py#L30)

**问题**: `knowledge.retrieve` 能力已注册但 `tool_name=None`，没有绑定任何 Tool。KnowledgeAgent 当前是作为工作流节点直接调用的（绕过 Executor），与统一 Tool 调度体系不一致。

```python
("knowledge.retrieve", None, "从本地知识库检索文档资料"),
```

**影响**: 中。限制了 Executor 的统一调度能力，如果未来要让 Planner 灵活选择是否使用知识库，需要修复。

**建议**: 创建 `KnowledgeTool(BaseTool)`，将知识检索纳入 Executor 体系。

---

## 二、性能问题

### 2.1 KnowledgeStore 搜索全表扫描

**位置**: [agentflow/knowledge/store.py:127-136](agentflow/knowledge/store.py#L127-L136)

**问题**: `get_all_embeddings_with_chunk()` 每次搜索时从 SQLite 加载**所有** embedding 向量到内存，逐一计算余弦相似度。文档量增大时性能和内存消耗会线性增长。

```python
def get_all_embeddings_with_chunk(self) -> list[dict]:
    # 加载所有 embeddings → 全量暴力计算
```

**影响**: 高。这是知识库模块最严重的性能瓶颈，文档一多就不可用。

**建议**: 
1. 添加 TF-IDF 倒排索引初步筛选候选块（P1）
2. 或使用近似最近邻搜索（ANN）库如 `faiss`（P2）
3. 至少限制每次加载的最大 embedding 数量

---

### 2.2 无流式传输 (SSE/WebSocket)

**位置**: [agentflow/api/routes.py:50](agentflow/api/routes.py#L50)

**问题**: POST `/chat` 是同步请求/响应模式，用户需要等待整个工作流（Router → Planner → Search/Execute → Answer → Memory）完成才能看到结果。对于搜索、Python 执行等耗时操作，等待时间可达数秒甚至数十秒。

**影响**: 高。直接影响用户体验，是 v0.1.0 最明显的产品化短板。

**建议**: 
1. 添加 WebSocket 端点 `/ws/chat`
2. 工作流节点完成时通过 EventBus 发射事件
3. 前端逐步显示各阶段结果（思考过程、搜索进度等）

---

### 2.3 对话历史无 Token 窗口管理

**位置**: [agentflow/agents/answer/agent.py:258-269](agentflow/agents/answer/agent.py#L258-L269)

**问题**: `_build_history()` 只按轮数（最近 N 轮）截断历史，没有 token 计数机制。当某轮对话包含长文本（如代码、搜索结果）时，实际 token 数可能远超模型 context window 限制。

**影响**: 中。长对话中容易出现 token 超限导致的截断异常或 LLM 调用失败。

**建议**: 添加 token 计数（使用 `tiktoken`），按 token 数智能截断，优先保留系统提示和搜索结果。

---

### 2.4 无缓存层

**位置**: 全局

**问题**: 整个项目没有任何缓存机制。每次 LLM 调用、每次知识库搜索都是实时计算。不支持水平扩展。

**影响**: 中（当前单用户场景下可接受，面向产品化不足）。

**建议**: P3 引入 Redis，支持 session 缓存、消息队列、速率限制。

---

## 三、代码质量问题

### 3.1 LLMService 无重试机制

**位置**: [agentflow/services/llm_service.py:96-111](agentflow/services/llm_service.py#L96-L111)

**问题**: `complete()` 方法在 LLM 调用异常时仅记录日志并直接返回 fallback，没有任何重试。一次网络抖动即导致 Planner 走规则回退路径，生成次优结果。

```python
except Exception as exc:
    logger.exception("LLM request failed: %s", exc)
    return f"[fallback] {prompt[:160]}"
```

**影响**: 高。极小改动（加 1-2 次指数退避重试）就能大幅提升稳定性。

**建议**: 添加指数退避重试（至少 1 次重试），配合超时配置。

---

### 3.2 Agent 层错误处理几乎空白

**位置**: 各 Agent 的 `run()` 方法

**问题**: 大部分 Agent 的 `run()` 方法没有 try/except 包裹。任何一个 Agent 抛出未捕获异常都会导致整个 LangGraph 工作流崩溃。当前仅 Executor 的 `execute()` 有异常捕获。

**影响**: 高。工作流的关键路径上缺乏容错能力。

**建议**: 
1. 抽取统一错误处理装饰器 `@safe_run` 或 `@handle_errors`
2. 在 `build_workflow()` 层面添加全局错误捕获节点

---

### 3.3 前端大量静默失败

**位置**: [frontend/src/composables/useChatState.ts](frontend/src/composables/useChatState.ts)

**问题**: `catch` 块大量使用空语句或仅注释 `// silently fail`。用户操作失败时没有任何反馈，调试也需要依赖浏览器控制台。

```typescript
} catch {
    // silently fail
}
```

第 39、79、89、195、196、221、222、233、242、243、293 行等。

**影响**: 中。用户体验差，调试困难。

**建议**: 
- 至少显示 toast 提示
- 开发模式下打印错误详情
- 区分"可静默"（如会话列表刷新）和"需反馈"（如消息发送）错误

---

### 3.4 Python 子进程空环境

**位置**: [agentflow/tools/python_tool.py:73](agentflow/tools/python_tool.py#L73)

**问题**: 使用 `env={}` 执行 Python 子进程，完全清空环境变量。这会破坏某些 Python 库的正常运行（如需要系统 PATH 或 SSL 证书的库，例如 `requests`、`ssl` 模块）。

**影响**: 中。沙箱安全性提升有限，但功能破坏却很显著。

**建议**: 保留基本环境变量（`PATH`、`HOME`），仅清除敏感变量（`API_KEY`、`SECRET` 等）。

---

### 3.5 `match_any` 方法名误导

**位置**: [agentflow/agents/router/agent.py:137-139](agentflow/agents/router/agent.py#L137-L139)

**问题**: 方法名 `match_any` 暗示使用 `re.fullmatch`（完全匹配），但实际实现使用 `re.search`（子串搜索），行为与命名不符。

**影响**: 低。但属于代码可读性债务，容易让后续开发者误用。

**建议**: 重命名为 `search_any` 或修正为实际需要的匹配语义。

---

### 3.6 前端状态管理臃肿

**位置**: [frontend/src/composables/useChatState.ts](frontend/src/composables/useChatState.ts)

**问题**: 单个文件超过 470 行，集成了聊天、知识库、工作区、文件、Agent 等所有状态管理逻辑。职责过多，不利于维护和测试。

**影响**: 中。新增功能时需要修改大文件，易产生冲突。

**建议**: 按关注点拆分为多个 composable：
- `useChat.ts` — 消息发送/接收/历史
- `useKnowledge.ts` — 知识库文档管理
- `useWorkspace.ts` — 工作区状态
- `useSession.ts` — 会话管理

---

## 四、功能不完善模块

### 4.1 知识库 RAG（最需要完善的模块）

| 问题 | 位置 | 说明 |
|------|------|------|
| 仅 TF-IDF 词法匹配 | `knowledge/embedder.py` | 中文单字切分，无法理解语义；"机器学习算法"匹配不到"监督学习" |
| 全表扫描性能问题 | `knowledge/store.py:127-136` | 每次搜索加载所有向量 |
| 无 re-ranking | 全局 | 一次 TF-IDF 排序即输出，没有二次精排 |
| 无增量索引 | 全局 | 每次新增文档后需重建整个词汇表 |
| 文档解析弱 | `knowledge/parser.py` | PDF 无表格提取、无图片 OCR、无多列布局处理 |

**影响**: 高。知识检索质量直接影响答案质量。

---

### 4.2 搜索服务

| 问题 | 位置 | 说明 |
|------|------|------|
| 单一 Provider | `services/search_provider.py:48` | 仅 DuckDuckGo HTML 爬取，稳定性差 |
| 无备选降级 | 全局 | DuckDuckGo 被封或限流时搜索完全不可用 |
| 搜索结果无缓存 | 全局 | 相同查询重复搜索 |

**影响**: 中高。搜索是核心功能之一，单一依赖风险大。

**建议**: 实现 BraveSearch / Tavily / Serper 等 Provider，通过配置切换。

---

### 4.3 LLM 服务

| 问题 | 位置 | 说明 |
|------|------|------|
| 单 Provider | `services/llm_service.py` | 仅 OpenAI 兼容 API |
| 无多模型路由 | 全局 | 不能按任务类型分配不同模型（如简单任务用小模型、复杂任务用大模型） |
| 无流式支持 | 全局 | 不支持 SSE 输出 |
| 无重试 | `llm_service.py:96-111` | 无任何重试机制 |

**影响**: 高。LLM 是系统的智能核心，当前封装过于简单。

---

### 4.4 对话记忆

| 问题 | 位置 | 说明 |
|------|------|------|
| 会话内记忆有限 | `agents/memory/agent.py` | 仅维持最近 `max_turns*2` 条消息 |
| 无跨会话长期记忆 | 全局 | 用户偏好、常用话题、重要事实无法跨 session 持久化 |
| 无 Token 管理 | `answer/agent.py:258-269` | 无 token 计数和智能截断 |

**影响**: 中。多轮对话体验受影响，跨 session 记忆是产品差异化功能。

---

### 4.5 测试覆盖严重不足

| 应测模块 | 状态 |
|---------|------|
| `PlannerAgent`（JSON 解析、规则回退） | ❌ 无测试 |
| `KnowledgeStore`（增删搜索、embedding 序列化） | ❌ 无测试 |
| `LLMService`（fallback、模型切换） | ❌ 无测试 |
| `SearchTool` / `PythonTool` | ❌ 无测试 |
| 各 Agent 的 `run()` 方法 | ❌ 无测试 |
| 前端组件 | ❌ 无测试 |
| 已覆盖 | `test_conversation_runtime.py`、`test_workflow.py` |

**影响**: 高。核心模块无测试保障，重构风险大。

---

## 五、基础设施短板

| 问题 | 说明 |
|------|------|
| **数据库索引缺失** | `sessions` 表仅主键索引，按 `updated_at` 排序查询无索引；`chats` 表按 `session_id` 查询无索引 |
| **Dockerfile 路径问题** | `COPY pyproject.toml README.md ./` 因 README.md 在根目录位置问题会失败 |
| **无用户认证系统** | 无注册/登录/JWT，只适合本地单用户 |
| **无可观测性** | 无 Prometheus 指标、OpenTelemetry 追踪、Grafana 仪表板、LLM 调用审计日志 |
| **无沙箱增强** | Python 执行仅 `env={}` 隔离，无 Docker 容器级沙箱、无 CPU/内存资源限制 |

---

## 六、技术债务清单

| 问题 | 位置 | 说明 | 优先级 |
|------|------|------|--------|
| 遗留 prompt 模板 | `agentflow/prompts/*.md` | Markdown 提示模板未被代码引用，与代码中 prompt 不同步 | P2 |
| 前后端重复类型定义 | `frontend/src/types/index.ts` ↔ `agentflow/models/` | TypeScript 和 Python 类型需手工同步 | P2 |
| `_TOOL_TO_NODE` 硬编码 | `agentflow/graph/workflow.py:53-56` | Tool→节点名映射需随新 Tool 手动更新 | P2 |
| session_state 类型不一致 | `graph/workflow.py:143-169` | dict/SessionState 互转散布在多个方法中 | P1 |
| `match_any` 命名误导 | `agents/router/agent.py:137-139` | 实为 `re.search` 而非 `re.fullmatch` | P3 |
| 前端 `useChatState` 臃肿 | `frontend/src/composables/useChatState.ts` | 470+ 行，应拆分 | P2 |

---

## 七、会话管理模块专项问题

> 涉及文件: `agentflow/conversation/`（manager.py、session_state.py、state.py、context.py、rewrite.py）
> 以及 `agentflow/agents/memory/agent.py`、`agentflow/agents/answer/agent.py`、`agentflow/graph/workflow.py`

---

### 7.1 Bug — `pending_options` 清除后引发死分支

**位置**: [agentflow/conversation/manager.py:131](agentflow/conversation/manager.py#L131) → [agentflow/conversation/manager.py:314](agentflow/conversation/manager.py#L314)

**问题**: `resolve_question()` 在成功解析选项后立即清除 `pending_options`（第 131 行）：

```python
session_state.pending_options.clear()  # 被清除
```

随后 `build_conversation_context()` 在第 314 行检查 `ss.has_pending_options`：

```python
elif ss.has_pending_options and is_continue:  # 永远为 False
    ctx_type = OPTION_SELECTION
```

这个分支永不可能执行，全靠下一个 `_is_option_selection()` 分支来补偿。这是**脆弱的时序耦合**——两个方法之间的隐性顺序依赖，重构时极易破坏。

**影响**: 中。类型检测依赖意外地绕过，而非正常逻辑。

---

### 7.2 Bug — `CLARIFICATION` 类型是死常量

**位置**: [agentflow/conversation/context.py:19](agentflow/conversation/context.py#L19) + [agentflow/conversation/manager.py:312-323](agentflow/conversation/manager.py#L312-L323)

**问题**: `CLARIFICATION = "CLARIFICATION"` 已定义，但 `build_conversation_context()` 中的类型判定逻辑永远不会输出 `CLARIFICATION`。所有可能路径只产生 `NEW_TASK` / `FOLLOW_UP` / `OPTION_SELECTION` / `WAITING_REPLY` / `QUESTION_REWRITE` 五种。

**影响**: 低。属于未使用的枚举值。

---

### 7.3 Bug — 搜索结果展示受 `category == "search"` 限制

**位置**: [agentflow/agents/answer/agent.py:92-95](agentflow/agents/answer/agent.py#L92-L95)

**问题**: `ContextBuilder.build_user_prompt()` 只在 `category == "search"` 时将搜索结果注入 prompt：

```python
if self.category == "search" and self.search_results:
```

但通过 Planner 规划的搜索任务，category 可能是 `reasoning`、`writing` 等。此时即使 `search_results` 有数据，LLM 也看不到搜索结果。

**影响**: 高。这是功能 Bug——搜索结果可能被 LLM 忽略。

---

### 7.4 Bug — `RewriteEngine.needs_rewrite` 对短自包含句误判

**位置**: [agentflow/conversation/rewrite.py:120-129](agentflow/conversation/rewrite.py#L120-L129)

**问题**: 长度 4-14 字符的输入，若不匹配已知前缀列表（如 `"你好"`、`"帮我"`），会被错误标记为"需要重写"。实际内容可能是自包含的话题名（如 `"Python贪吃蛇"`、`"机器学习入门"`），改写后反而画蛇添足。

```python
if len(q) < 15:
    if not any(p.search(q) for p in _MODIFIER_PATTERNS):
        if q.startswith(("你好", "你是谁", "你能", "今天", "帮我", ...)):
            return False
        return True  # 误判
```

**影响**: 中。会导致部分短问题被不必要地加长。

---

### 7.5 Bug — `resolve_question` 混合返回值与副作用

**位置**: [agentflow/conversation/manager.py:94-197](agentflow/conversation/manager.py#L94-L197)

**问题**: `resolve_question()` 既通过 `return` 返回处理后的字符串，又在方法内部**直接修改** `session_state`（清除 `pending_options`、填充 `slots`、更新 `tracking`）。调用方无法区分哪些变化发生了、哪些没发生。

```python
def resolve_question(self, question: str, session_state: SessionState) -> str:
    # 修改 session_state（副作用）
    session_state.pending_options.clear()
    session_state.fill_slot(...)
    session_state.tracking.add_entity(...)
    # 返回 str（返回值）
    return enriched_question
```

**影响**: 中。这种混合模式使单元测试和调试复杂化。

---

### 7.6 Bug — `finalize_turn` 检测到选项后跳过 tracking 更新

**位置**: [agentflow/conversation/manager.py:228-233](agentflow/conversation/manager.py#L228-L233)

**问题**: 当 `_extract_options(answer)` 检测到选项时，`finalize_turn` 直接 return，跳过后面的所有 tracking 更新（`last_answer`、`add_entity`、`summary`）：

```python
if options:
    session_state.pending_options = options
    session_state.start_waiting("选择一个选项")
    return  # ← 跳过后面的 tracking 更新
```

**影响**: 中。包含选项的回答不会被记录到 tracking 中，跨轮跟踪能力受损。

---

### 7.7 Bug — 多处死代码

| 死代码 | 文件行 | 说明 |
|--------|--------|------|
| `ConversationContext.from_dict()` | `context.py:63-76` | 完整实现但从未被调用 |
| `ContextBuilder._format_history()` | `answer/agent.py:152-173` | 完整实现但 `build_user_prompt()` 内部未调用它 |
| `ConversationState.facts` 字段 | `state.py:36` | 定义但从未写入 |
| `ConversationState.tool_result` 字段 | `state.py:37` | 定义但从未写入 |
| `ConversationManager.build_continue_context()` | `manager.py:199-210` | 定义但从未被调用 |

**影响**: 中。死代码增加维护负担，也可能误导后续开发者。

---

### 7.8 设计问题 — AnswerAgent prompt 中 context 信息冗余

**位置**: [agentflow/agents/answer/agent.py:205-218](agentflow/agents/answer/agent.py#L205-L218)

**问题**: `AnswerAgent.run()` 构造 messages 时做了一个"三明治"结构：

```python
messages = [system_prompt]          # 1. System prompt
messages.extend(_build_history())   # 2. 历史消息（独立 role）
messages.append(user_prompt)        # 3. User prompt（可能含 "对话摘要"/"会话状态" 等）
```

但 `build_user_prompt()` 内部又有自己的历史格式化代码（`_format_conversation_context` 含 goal/entities/summary）。导致 LLM 看到的信息有重叠：历史消息在 `_build_history()` 中作为独立消息传入，同时 session_state 的摘要又在 user_prompt 中以文本形式出现。

**影响**: 低。不产生错误但浪费 token。

---

### 7.9 设计问题 — AnswerAgent 与 ContextBuilder 的 system prompt 重复

**位置**: [agentflow/agents/answer/agent.py:43-57](agentflow/agents/answer/agent.py#L43-L57) vs [agentflow/agents/answer/agent.py:254-267](agentflow/agents/answer/agent.py#L254-L267)

**问题**: ContextBuilder 有 `build_system_prompt()`，AnswerAgent 有 `_system_prompt()`。两者功能几乎完全重复——构建相似的 system prompt。但 `run()` 方法使用的是 `_system_prompt()`，不使用 `build_system_prompt()`。

**影响**: 低。两处 prompt 如不同步可能导致不一致的 LLM 行为。

---

### 7.10 设计问题 — 实体提取过于简单

**位置**: [agentflow/conversation/manager.py:371-383](agentflow/conversation/manager.py#L371-L383)

**问题**: 实体提取仅靠 `re.findall(r"[一-鿿]{2,6}", text)` 匹配 CJK 字符：

- **无命名实体识别（NER）** — 无法识别人名、地名、组织名
- **2 字符下限太低** — 大量"什么"、"怎么"、"这个"等停用词需额外过滤
- **6 字符上限太短** — "北京大学计算机学院"等长实体被截断
- **无领域特定实体类型** — 所有实体混为一谈

```python
stop_words = {"什么", "怎么", "为什么", "如何", "哪个", "这个", "那个", ...}
```

影响: 中。导致下游 tracking 的质量受限。

---

### 7.11 设计问题 — Slots 无 schema 定义

**位置**: [agentflow/conversation/session_state.py:48](agentflow/conversation/session_state.py#L48)

**问题**: `slots` 是简单的 `dict[str, Any]`：

```python
slots: dict[str, Any] = field(default_factory=dict)
```

任何字符串键、任何值都可以放入。没有：
- 哪些 slot 是必须的
- 值的类型约束（"date" 字段填 "北京" 也能通过）
- 验证逻辑
- 多轮对话中部分已填、部分待填的状态追踪

**影响**: 中。slot-filling 功能过于原始，复杂多步表单无法实现。

---

### 7.12 设计问题 — continue mode 跳过了 KnowledgeAgent

**位置**: [agentflow/graph/workflow.py:100-109](agentflow/graph/workflow.py#L100-L109)

**问题**: 当 `_continue_mode=True` 时，流程为 `CM → Answer → Memory`，完全跳过 KnowledgeAgent。这意味着在"继续模式"的多轮对话中，用户后续的问题无法利用知识库内容，即使重写后的问题明确需要知识检索。

**影响**: 中。连续对话中知识库不可用。

---

### 7.13 设计问题 — `session_state` 在 workflow 各阶段类型不统一

**问题总结**:

| 阶段 | session_state 的类型 | 位置 |
|------|---------------------|------|
| `run_workflow()` 入口 | `dict \| None` | [workflow.py:319-320](agentflow/graph/workflow.py#L319-L320) |
| `_conversation_manager_node` 内部 | `SessionState` | [workflow.py:175-178](agentflow/graph/workflow.py#L175-L178) |
| MemoryAgent.run() 内部 | `dict \| SessionState`（需 isinstance 判断） | [memory/agent.py:68-76](agentflow/agents/memory/agent.py#L68-L76) |
| `WorkflowContext.to_dict()` 输出 | `dict` | [graph/context.py:72-73](agentflow/graph/context.py#L72-L73) |
| `routes.py` 接收后 | `dict \| SessionState`（需 isinstance 判断） | [api/routes.py:82-84](agentflow/api/routes.py#L82-L84) |

**影响**: 高。每次访问 session_state 都需要防御性的类型检查，是 bug 的常见来源。

---

### 7.14 健壮性问题 — SessionState 无版本号/乐观锁

**位置**: [agentflow/conversation/session_state.py](agentflow/conversation/session_state.py)

**问题**:
1. **无版本号** — `to_dict()`/`from_dict()` 没有 schema 版本字段。如果新增/删除字段，老数据反序列化会静默丢失字段
2. **无乐观锁** — 用户在前端快速连发两条消息，两个请求的 session_state 基于同一个旧版本修改，后一个请求会覆盖前一个的更新
3. **`from_dict` 静默忽略未知 key** — `data.get("unknown_field", "")` 不会给出任何警告

**影响**: 中。并发场景和 schema 演化时存在隐患。

---

### 7.15 健壮性问题 — `metadata` 无清理策略

**位置**: [agentflow/conversation/session_state.py:50](agentflow/conversation/session_state.py#L50)

**问题**: `metadata: dict[str, Any]` 允许任何 Agent 写入任意数据，但没有超时机制或清理策略。长时间运行的 session 中，metadata 会持续累积无用数据。

**影响**: 低。但量大的 metadata 会随 `session_state` 序列化到 DB，占用存储。

---

### 7.16 健壮性问题 — pending_options 的 key/value 歧义

**位置**: [agentflow/conversation/session_state.py:78-110](agentflow/conversation/session_state.py#L78-L110)

**问题**: `resolve_option` 中，当用户输入恰好等于某个 option 的 value 时也会匹配：

```python
for key, value in self.pending_options.items():
    if user_input == value or user_input in value:
        return value  # value 匹配
```

如果 value 恰好是 `"1"`、`"2"` 等数字字符串（常见于编号选项），就和 key 的匹配路径产生歧义。

**影响**: 低。边缘场景。

---

### 7.17 健壮性问题 — 无会话超时/过期处理

**问题**: `SessionState` 没有记录最后活跃时间，也没有"会话过期"的概念。如果一个 session 闲置数小时后回来，旧的 `current_goal`、`tracking` 等信息仍然生效，"继续模式"可能会引向已过时的任务。

**影响**: 中。长时间闲置后用户体验下降。

---

### 7.18 健壮性问题 — 重写规则在多处重复

**问题**: 相同的正则表达式模式（ordinal、option 检测等）在 `manager.py`、`rewrite.py`、`session_state.py` 中重复出现。例如：

| 模式 | 出现在 |
|------|--------|
| `选项[一二三四五六七八九十]` | `manager.py:584`、`rewrite.py:32`、`session_state.py:101` |
| `第[一二三四五六七八九十]个` | `manager.py:584`、`rewrite.py:31` |
| 序数到数字映射 | `manager.py:39-41`、`session_state.py:96-99` |

**影响**: 中。修改一处容易漏掉另一处，导致行为不一致。

### P0 — 立即处理（影响核心功能）

| # | 问题 | 预计工作量 |
|---|------|-----------|
| 1 | LLMService 添加重试机制 | 0.5 天 |
| 2 | Agent 层统一错误处理 | 1 天 |
| 3 | 知识库搜索全表扫描优化 | 2 天 |

### P1 — 重要（产品化关键）

| # | 问题 | 预计工作量 |
|---|------|-----------|
| 1 | 流式传输 SSE/WebSocket | 3 天 |
| 2 | session_state 类型统一 | 1 天 |
| 3 | 对话历史 Token 窗口管理 | 1 天 |
| 4 | 添加更多搜索 Provider | 2 天 |
| 5 | 前端错误反馈完善 | 1 天 |
| 6 | Python 子进程环境修复 | 0.5 天 |

### P2 — 建议（质量改进）

| # | 问题 | 预计工作量 |
|---|------|-----------|
| 1 | Agent 统一基类抽取 | 0.5 天 |
| 2 | 语义嵌入支持 | 3 天 |
| 3 | 多 LLM Provider 支持 | 2 天 |
| 4 | 跨会话长期记忆 | 2 天 |
| 5 | 知识库 re-ranking | 1 天 |
| 6 | 测试覆盖补充（Planner/LLM/Knowledge/Tool） | 3 天 |
| 7 | 前端状态管理拆分 | 1 天 |
| 8 | Dockerfile 修复 | 0.5 天 |
| 9 | 数据库索引添加 | 0.5 天 |
| 10 | 清理遗留 prompt 模板 | 0.5 天 |

### P3 — 未来（长期规划）

| # | 问题 |
|---|------|
| 1 | Redis 缓存/消息队列 |
| 2 | Agent 间事件驱动架构 |
| 3 | 用户认证与权限系统 |
| 4 | Docker 容器级沙箱 |
| 5 | 可观测性（Prometheus/OpenTelemetry） |
| 6 | Agent 市场/插件系统 |
| 7 | 知识图谱自动构建 |
| 8 | 工作流 UI 可视化 |
