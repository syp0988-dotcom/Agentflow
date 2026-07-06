# AI_TODO — 未来开发指南

> 优先级: P0(紧急) → P1(重要) → P2(建议) → P3(未来)
> 分析基于 2026-07-06 的源码状态 v0.1.0

---

## P0 — 紧急 (Bug 风险或缺失功能)

### 0.1 知识检索能力未绑定工具

**文件**: `agentflow/agents/planner/capability.py:30`

**问题**: `knowledge.retrieve` 能力已注册但 `tool_name=None`，没有绑定任何工具。

```python
("knowledge.retrieve", None, "从本地知识库检索文档资料"),
```

这意味着 Planner 永远无法让 Executor 执行知识检索。当前 KnowledgeAgent 是直接在工作流中作为节点调用的（绕过 Executor）。如果未来要统一走 Executor，需要创建 `KnowledgeTool`。

**建议**: P2 — 当前设计是显式的（KnowledgeAgent 作为工作流节点），不是 Bug，但需要注意此不一致。

### 0.2 SessionState 并发写风险

**文件**: `agentflow/api/routes.py:81-84`

**问题**: `run_workflow()` 完成后立即持久化 session_state，之后 MemoryAgent 也修改了 session_state（通过 `finalize_turn()`）。实际的持久化顺序是：

```
1. run_workflow() 完成 → result["session_state"] 被 MemoryAgent 更新
2. API 层 persist 这个 session_state → 正确
```

当前代码正确，但如果未来添加异步处理，必须注意 session_state 的写时序。

### 0.3 LLMService 无请求级别重试

**文件**: `agentflow/services/llm_service.py:96-111`

**问题**: `complete()` 方法在 LLM 调用失败时只记录异常并返回 fallback，没有重试机制。对于临时网络问题，一次失败就回退可能导致 Planner 走规则路径（次优结果）。

**建议**: P1 — 添加指数退避重试（1次重试即可）。

### 0.4 KnowledgeStore.search 全表扫描

**文件**: `agentflow/knowledge/store.py:127-136`

**问题**: `get_all_embeddings_with_chunk()` 加载**所有**嵌入向量到内存并逐一计算余弦相似度。文档数量增多时性能会急剧下降。

**建议**: P1 — 当文档量较大时，考虑：
1. 添加 TF-IDF 倒排索引初步筛选候选块
2. 或使用近似最近邻搜索库

### 0.5 Python 子进程空环境

**文件**: `agentflow/tools/python_tool.py:73`

**问题**: 使用 `env={}` 执行 Python 子进程，完全清空了环境变量。这可能会破坏某些 Python 库的正常运行（如需要系统 PATH 或 SSL 证书）。

**建议**: P2 — 应保留基本环境变量（如 PATH），但清除敏感变量。

---

## P1 — 重要 (优化/功能缺失)

### 1.1 实时流式传输 (SSE/WebSocket)

**文件**: `agentflow/api/routes.py:50`

**需求**: 当前 POST /chat 是同步请求，用户需要等待完整工作流结束。对于搜索等耗时操作，用户体验差。

**建议**: 
1. 添加 WebSocket 端点 `/ws/chat`
2. 工作流节点完成时通过 EventBus 发射事件
3. 前端逐步显示各阶段结果

### 1.2 对话历史无窗口管理

**文件**: `agentflow/agents/answer/agent.py:258-269`

**问题**: `_build_history()` 只取最近 N 轮对话，但 LLM context window 没有主动管理。当历史很长时可能超出 token 限制。

**建议**: P1 — 添加 token 计数和智能截断，优先保留系统提示和搜索结果。

### 1.3 更多搜索提供商

**文件**: `agentflow/services/search_provider.py:48`

**需求**: 当前只支持 DuckDuckGo HTML 爬取。搜索结果质量和稳定性受限。

**建议**: P1 — 实现 `BraveProvider`, `TavilyProvider`, `SerperProvider` 等，通过配置切换。

### 1.4 ReportAgent 未集成到工作流

**文件**: `agentflow/agents/report/agent.py`

**问题**: ReportAgent 已实现但标记为 `inactive`，未在 `build_workflow()` 中使用。它与 AnswerAgent 功能重叠。

**建议**: P1 — 决定是否用 ReportAgent 替换 AnswerAgent，或让 Planner 选择使用哪个。

### 1.5 错误处理不够健壮

**各 Agent 文件**: 当前 Agent 的 `run()` 方法很少用 try/except 包裹。如果某个 Agent 抛出异常，整个工作流崩溃。

**建议**: P1 — 在每个 Agent 的 `run()` 中添加错误捕获，将错误写入 state 而非抛出。

### 1.6 前端文件提案状态持久化

**文件**: `frontend/src/composables/useChatState.ts`

**问题**: 文件提案状态（`fileProposalStatuses`）存在内存中，刷新页面后丢失。

**建议**: P1 — 使用 localStorage 持久化提案状态。

---

## P2 — 建议 (改进/重构)

### 2.1 添加语义嵌入支持

**文件**: `agentflow/knowledge/embedder.py`

**需求**: TF-IDF 无法理解语义。当用户问"机器学习算法有哪些"时，无法匹配"监督学习、无监督学习"等语义相关但词不匹配的内容。

**建议**: 可选集成 sentence-transformers，settings 中通过 `knowledge_embedder = "semantic"` 切换。

### 2.2 多 LLM Provider 支持

**文件**: `agentflow/services/llm_service.py`

**需求**: 当前仅支持 OpenAI 兼容 API。应支持多 Provider 路由（如某些任务用 Claude，某些用 DeepSeek）。

**建议**: 实现 RouterLLMService，根据任务类型选择不同模型。

### 2.3 跨会话记忆

**需求**: 当前记忆只在一个 session 内有效。没有跨会话的长期记忆。

**建议**: 实现 LongTermMemory，存储用户偏好、常用话题、重要事实到 SQLite。

### 2.4 测试覆盖提升

**测试现状**: 仅 `test_conversation_runtime.py` (1047行) 和 `test_workflow.py` 有测试。

**需要补充测试的模块**:
- `test_planner.py` — PlannerAgent（特别是 JSON 解析和规则回退）
- `test_knowledge.py` — KnowledgeStore 增删搜索
- `test_services.py` — LLMService 回退、SearchService 标准化
- `test_tools.py` — PythonTool 语法错误/超时、SearchTool
- `test_agents.py` — 各 Agent run() 方法

### 2.5 前端组件测试

**需求**: 当前无前端测试。至少应为 ChatView、Sidebar 等核心组件添加单元测试。

### 2.6 Docker 优化

**文件**: `agentflow/docker/Dockerfile`

**问题**: Dockerfile 中 `COPY pyproject.toml README.md ./` 会因 README.md 在项目根目录而失败。

**建议**: 修复 Dockerfile 路径问题，并添加 `.dockerignore`。

### 2.7 文档解析增强

**文件**: `agentflow/knowledge/parser.py`

**需求**: 当前 PDF 展示用 pypdf 文本提取，缺少：
- 表格提取
- 图片 OCR
- 多列布局处理

---

## P3 — 未来 (长期规划)

### 3.1 Redis 支持

**需求**: 当前所有状态存 SQLite，不支持水平扩展。添加 Redis 支持：
- Session 缓存
- 消息队列（工作流事件）
- 速率限制
- 跨进程记忆共享

### 3.2 Agent 间通信的事件驱动架构

**需求**: 当前 Agent 通过共享状态耦合。未来可以用事件驱动架构让 Agent 异步通信：
- Agent 订阅感兴趣的事件
- EventBus 支持异步路由
- 支持并行 Agent 执行

### 3.3 用户认证和权限

**需求**: 当前无用户系统。未来：
- 用户注册/登录
- API 认证 (JWT)
- 多用户隔离的数据
- 团队协作

### 3.4 沙箱增强

**文件**: `agentflow/tools/python_tool.py`

**需求**: 当前 Python 执行只用了空环境隔离。未来：
- Docker 容器级沙箱
- 资源限制 (CPU/内存)
- 文件系统白名单
- 网络访问控制
- 代码审计日志

### 3.5 工作流可视化

**需求**: 在 UI 上实时显示工作流执行状态（当前节点、已完成节点、耗时）。

### 3.6 可观测性

**需求**:
- Prometheus 指标
- OpenTelemetry 分布式追踪
- Grafana 仪表板
- LLM 调用审计日志

### 3.7 Agent 市场/插件系统

**需求**: 允许第三方开发者编写 Agent 并动态加载，无需修改核心代码。

### 3.8 知识图谱

**需求**: 从对话中自动构建知识图谱，支持：
- 实体关系提取
- 可视化浏览
- 基于图谱的问答

---

## 代码质量清单

### 需要关注的技术债务

| 问题 | 位置 | 说明 |
|------|------|------|
| 遗留 prompt 模板 | `agentflow/prompts/*.md` | Markdown 提示模板未被代码引用，可能与代码中 prompt 不同步 |
| 前后端重复类型 | `frontend/src/types/index.ts` 和 `agentflow/models/` | TypeScript 和 Python 类型定义需要手工同步 |
| 过多的"silently fail" | `frontend/src/composables/useChatState.ts` | 多处 catch 块静默失败，调试困难 |
| `_TOOL_TO_NODE` 硬编码 | `agentflow/graph/workflow.py:53-56` | Tool 到 LangGraph 节点名的映射需要随新 Tool 手动更新 |
| session_state 类型处理不一致 | `graph/workflow.py:143-169` | `_make_conversation_manager_node` 中 session_state 处理逻辑（dict/SessionState 互转）散布在多个方法中 |
| `match_any` 方法名误导 | `agents/router/agent.py:137-139` | 名为 match_any 实际是 search 而非 re.fullmatch |

### 重构候选

| 重构 | 动机 | 难度 |
|------|------|------|
| Agent 基类抽取 | 所有 Agent 有 `run(state)` 但无统一基类 | 低 |
| session_state 类型统一 | Workflow 中混用 dict 和 SessionState 对象 | 中 |
| 错误处理装饰器 | 为所有 Agent.run() 添加统一错误捕获 | 低 |
| Workflow 节点配置化 | 将节点/边配置从代码移到 YAML/JSON | 高 |
| 前端状态管理分离 | useChatState 超过 470 行，应拆分 | 中 |
