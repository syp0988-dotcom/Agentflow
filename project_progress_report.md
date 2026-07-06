# OmniForge (AgentFlow) 项目进度报告

> 报告日期: 2026-07-06 | 版本: v0.1.0 | 项目周期: 3 天

---

## 一、项目概览

OmniForge 是一个基于 LangGraph 的多智能体 AI 协作平台，支持工作流编排、知识库 RAG、联网搜索、Python 代码执行和持续对话。

| 维度 | 数据 |
|------|------|
| 总 Python 文件 | 65 个 |
| Python 代码行数 | 8,277 行 |
| 前端文件（Vue + TypeScript） | ~30 个 |
| 测试文件 | 3 个 |
| 测试用例数 | ~160+ 用例 |
| Git 提交数 | 17 次（3 天内） |
| 贡献者 | 1 人 |

---

## 二、项目架构完成度

### 2.1 整体架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │  API层   │→ │ Workflow │→ │ Agents   │→ │ Services/Tools  │  │
│  │ routes   │  │ LangGraph│  │ 8 agents │  │ LLM/Search/Py   │  │
│  └──────────┘  └──────────┘  └──────────┘  └─────────────────┘  │
│                      ↓                                           │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────────────────┐  │
│  │ 会话管理  │  │ 知识库RAG │  │ 持久化(SQLite)                 │  │
│  │ Manager  │  │ Store    │  │ 7张表 + 索引                   │  │
│  └──────────┘  └──────────┘  └────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────┤
│                        Vue 3 Frontend                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────┐  │
│  │ Chat     │  │Knowledge │  │ Projects │  │ Settings/Models │  │
│  │ 会话/消息 │  │ 知识库管理 │  │ 工作区    │  │ 模型配置        │  │
│  └──────────┘  └──────────┘  └──────────┘  └─────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 模块完成度矩阵

| 模块 | 完成度 | 状态 | 说明 |
|------|--------|------|------|
| **FastAPI 后端骨架** | 100% | ✅ 完成 | main.py + CORS + /health |
| **REST API 端点** | 100% | ✅ 完成 | 24 个端点覆盖所有功能 |
| **LangGraph 工作流** | 100% | ✅ 完成 | 8 节点 + 条件边 + 编译缓存 |
| **QueryRouterAgent** | 100% | ✅ 完成 | 正则分类 7 种意图 |
| **PlannerAgent** | 100% | ✅ 完成 | LLM 规划 + 规则回退 |
| **KnowledgeAgent** | 100% | ✅ 完成 | TF-IDF 向量检索 |
| **SearchAgent** | 100% | ✅ 完成 | 支持 DuckDuckGo + Tavily |
| **PythonAgent** | 100% | ✅ 完成 | 子进程沙箱执行 |
| **AnswerAgent** | 100% | ✅ 完成 | ContextBuilder 多源合成 |
| **MemoryAgent** | 100% | ✅ 完成 | 滑动窗口 + 摘要 |
| **ConversationManager** | 100% | ✅ 完成 | 选项解析/Slot-filling/重写/续答 |
| **SessionState** | 100% | ✅ 完成 | 带版本号的序列化 |
| **RewriteEngine** | 100% | ✅ 完成 | 指代消解 + 问题重写 |
| **QueryRewriter** | 100% | ✅ 完成 | 搜索查询优化（最新） |
| **AgentProtocol** | 100% | ✅ 完成 | 接口契约 + @safe_run |
| **LLMService 重试** | 100% | ✅ 完成 | 指数退避 + jitter |
| **搜索多 Provider** | 100% | ✅ 完成 | DuckDuckGo + Tavily 自动切换 |
| **Python 安全沙箱** | 100% | ✅ 完成 | 保留安全环境变量 |
| **数据库索引** | 100% | ✅ 完成 | sessions/chats 索引 |
| **遗留 prompt 清理** | 100% | ✅ 完成 | 4 个 .md 文件已删除 |
| **Observer 目录清理** | 100% | ✅ 完成 | 已移除 |
| **前端 Chat 视图** | 100% | ✅ 完成 | 消息列表 + 输入 + Markdown |
| **前端知识库视图** | 100% | ✅ 完成 | 文档管理 + 上传 |
| **前端项目/工作区** | 100% | ✅ 完成 | 文件浏览 + 文件夹提醒 |
| **前端 Agent 视图** | 100% | ✅ 完成 | Agent 元数据展示 |
| **前端模型配置** | 100% | ✅ 完成 | LLM 模型 CRUD |
| **前端 Artifacts** | 100% | ✅ 完成 | 文件提案展示 |
| **ReportAgent** | 90% | ⏸️ 已实现未激活 | 注册为 inactive，与 AnswerAgent 重叠 |
| **流式传输 SSE/WebSocket** | 0% | ❌ 未开始 | 所有 API 同步请求/响应 |
| **知识库性能优化** | 0% | ❌ 未开始 | 全表扫描，无倒排索引/FAISS |
| **语义嵌入** | 0% | ❌ 未开始 | 仅 TF-IDF |
| **知识库 re-ranking** | 0% | ❌ 未开始 | 无二次精排 |
| **Token 窗口管理** | 0% | ❌ 未开始 | 仅按轮数截断 |
| **跨会话长期记忆** | 0% | ❌ 未开始 | 仅 session 内记忆 |
| **多 LLM Provider** | 0% | ❌ 未开始 | 仅单 Provider |
| **前端状态管理拆分** | 0% | ❌ 未开始 | 330+ 行单文件 |
| **缓存层 Redis** | 0% | ❌ 未开始 | P3 |
| **用户认证系统** | 0% | ❌ 未开始 | P3 |
| **可观测性体系** | 0% | ❌ 未开始 | P3 |
| **Docker 沙箱** | 0% | ❌ 未开始 | P3 |
| **Workflow UI** | 0% | ❌ 未开始 | P3 |
| **知识图谱** | 0% | ❌ 未开始 | P3 |

---

## 三、各层级完成度详情

### 3.1 Agent 层（7/8 激活）

| Agent | 代码 | Protocol | @safe_run | 测试 |
|-------|------|----------|-----------|------|
| QueryRouterAgent | ✅ | ✅ | ✅ | ❌ |
| PlannerAgent | ✅ | 隐式符合 | ✅ | ❌ |
| KnowledgeAgent | ✅ | ✅ | ✅ | ❌ |
| SearchAgent | ✅ | ✅ | ✅ | ❌ |
| PythonAgent | ✅ | ✅ | ✅ | ❌ |
| AnswerAgent | ✅ | 隐式符合 | ✅ | ❌ |
| MemoryAgent | ✅ | 隐式符合 | ✅ | ❌ |
| ReportAgent | ✅ 代码 | 隐式符合 | ✅ | ❌ |

Agent 层完成度：**100% 代码实现，0% 单测覆盖**

### 3.2 服务层

| 服务 | 代码 | 重试/容错 | 多 Provider | 测试 |
|------|------|-----------|-------------|------|
| LLMService | ✅ | ✅ 指数退避 | ❌ 单 Provider | ❌ |
| SearchService | ✅ | ✅ | ✅ Tavily+DDG | ❌ |
| FileProposer | ✅ | ✅ | N/A | ❌ |

服务层完成度：**100% 代码实现，0% 单测覆盖**

### 3.3 工具层

| 工具 | 代码 | 沙箱 | 测试 |
|------|------|------|------|
| SearchTool | ✅ | N/A | ❌ |
| PythonTool | ✅ | ✅ 安全环境 | ❌ |

工具层完成度：**100% 代码实现，0% 单测覆盖**

### 3.4 知识库层

| 组件 | 代码 | 性能 | 质量 |
|------|------|------|------|
| KnowledgeStore | ✅ 增删改查 | ❌ 全表扫描 | ⚠️ 待优化 |
| TfidfEmbedder | ✅ | ❌ 暴力计算 | ⚠️ 仅词法 |
| DocumentParser | ✅ PDF/DOCX/TXT/MD | N/A | ⚠️ 无表格/OCR |

知识库层完成度：**100% 基础功能，0% 性能优化**

### 3.5 会话管理层

| 组件 | 代码 | 状态 |
|------|------|------|
| ConversationManager | ✅ 完整实现 | ✅ |
| SessionState | ✅ 带版本号 | ✅ |
| RewriteEngine | ✅ 完整实现 | ✅ |
| ConversationState | ✅ 实体/话题追踪 | ✅ |
| QueryRewriter | ✅ 新增模块 | ✅ |

会话管理层完成度：**100%**

### 3.6 前端层

| 组件 | 实现 | 测试 |
|------|------|------|
| ChatView + ChatInput + MessageItem | ✅ | ❌ |
| WelcomeView | ✅ | ❌ |
| ThinkingIndicator + WorkflowPanel | ✅ | ❌ |
| KnowledgeView + DocumentList + UploadZone | ✅ | ❌ |
| ProjectsView | ✅ | ❌ |
| AgentsView | ✅ | ❌ |
| ArtifactsView | ✅ | ❌ |
| ModelsSettings | ✅ | ❌ |
| Sidebar + ChatHistory | ✅ | ❌ |
| 错误处理 | ✅ console.warn | ❌ |

前端完成度：**100% UI 实现，0% 测试覆盖**

---

## 四、测试覆盖状况

| 测试文件 | 位置 | 用例数 | 覆盖模块 |
|---------|------|--------|---------|
| test_conversation_runtime.py | `tests/` | ~116 | SessionState, ConversationManager, WorkflowContext |
| test_query_rewriter.py | `tests/` | ~26 | QueryRewriter 全路径 |
| test_workflow.py | `tests/` | ~3 | 工作流集成 + /health |

### 未覆盖的核心模块

| 模块 | 风险等级 | 关键测试点 |
|------|---------|-----------|
| PlannerAgent | 🔴 高 | JSON 解析异常、规则回退、capability 解析 |
| LLMService | 🔴 高 | 重试逻辑、fallback、模型切换 |
| KnowledgeStore | 🔴 高 | 增删文档、搜索排序、embedding 序列化 |
| PythonTool | 🟡 中 | 代码执行、超时、语法校验 |
| SearchTool | 🟡 中 | 多 Provider 响应解析、空结果 |
| 各 Agent run() | 🟡 中 | 输入验证、错误路径 |
| 前端组件 | 🟢 低 | 组件渲染、用户交互 |

---

## 五、项目总体看板

### 按优先级汇总

```
P0（核心功能）    ■■■■■■□□□□  67%  ✅ LLM重试  ✅ 错误处理  ❌ 知识库性能
P1（产品化关键）  ■■■■■□□□□□  71%  5/7 已完成
P2（质量改进）    ■□□□□□□□□□  30%  3/10 已完成
P3（长期规划）    □□□□□□□□□□   0%  0/8 已完成

总计：28 项中 10 项完成（36%）
```

### 迭代进度时间线

```
07-04 │■■■■■■■■■■■■■■■■■■■■■■■■■
     │ AgentFlow 骨架 / LangGraph 工作流 / Vue3 前端
     │ 知识库 RAG / LLM 集成 / 搜索集成
     │
07-05 │■■■■■■■■■■■■■■■■■■
     │ Planner 智能规划 / 会话管理 Phase 7/8
     │ SessionState / RewriteEngine / Memory
     │ ConversationManager / 多轮记忆
     │
07-06 │■■■■■■■■■■■■
     │ AgentProtocol / safe_run 装饰器
     │ LLM 重试 / Tavily Provider
     │ QueryRewriter / 安全沙箱
     │ 数据库索引 / prompt 清理
     │
现在  │ → 进入 P1 产品化阶段
```

---

## 六、下一步建议

### 立即可以做（P1 剩余项）

| 任务 | 工作量 | 说明 |
|------|--------|------|
| **知识库倒排索引优化** | 1 天 | 解决全表扫描性能瓶颈 |
| **流式传输 SSE** | 3 天 | EventBus + WebSocket 端点 |
| **Token 窗口管理** | 1 天 | 用 tiktoken 替代轮数截断 |

### 推荐的执行顺序

```
Week 1: 知识库性能优化 → Token 管理 → 测试覆盖（Planner/LLM/Knowledge）
Week 2: 流式传输 SSE → 前端适配 → 知识库语义嵌入
Week 3: 跨会话记忆 → re-ranking → 多 LLM Provider
Week 4: 前端拆分 → 端到端测试 → 文档完善
```
