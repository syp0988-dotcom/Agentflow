# AI_DIRECTORY — 项目目录结构

---

## 完整目录树

```
g:/multi_agent/
│
├── .env                              # 环境变量 (DEEPSEEK_API_KEY 等)
├── .env.example                      # 环境变量示例
├── .gitignore                        # Git 忽略规则
├── pyproject.toml                    # 项目配置 (依赖、构建)
├── README.md                         # 项目说明
├── uv.lock                           # uv 依赖锁定文件
├── package-lock.json                 # 前端依赖锁定 (根目录遗留)
├── PROJECT_ARCHITECTURE.md           # 已有架构文档
│
├── start-frontend.cmd                # 前端启动脚本 (Windows)
│
├── agentflow/                        # ★ 核心后端包
│   ├── __init__.py                   # 包初始化 (OmniForge 兼容)
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py                   # FastAPI 应用入口
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py                 # ★ 所有 REST API 路由
│   │
│   ├── agents/                       # ★ 所有 Agent 实现
│   │   ├── __init__.py
│   │   ├── registry.py               # Agent 注册表 (元数据)
│   │   │
│   │   ├── answer/                   # 答案生成 Agent
│   │   │   ├── __init__.py
│   │   │   └── agent.py              # AnswerAgent + ContextBuilder
│   │   │
│   │   ├── knowledge/                # 知识库 Agent
│   │   │   ├── __init__.py
│   │   │   └── agent.py              # KnowledgeAgent
│   │   │
│   │   ├── memory/                   # 记忆 Agent
│   │   │   ├── __init__.py
│   │   │   └── agent.py              # MemoryAgent
│   │   │
│   │   ├── planner/                  # 任务规划 Agent
│   │   │   ├── __init__.py
│   │   │   ├── agent.py              # ★ PlannerAgent (LLM + 规则)
│   │   │   ├── capability.py         # Capability → Tool 映射
│   │   │   └── prompt.py             # Planner LLM 提示词
│   │   │
│   │   ├── python/                   # Python 执行 Agent
│   │   │   ├── __init__.py
│   │   │   └── agent.py              # PythonAgent
│   │   │
│   │   ├── report/                   # 报告生成 Agent (inactive)
│   │   │   ├── __init__.py
│   │   │   └── agent.py              # ReportAgent
│   │   │
│   │   ├── router/                   # 查询路由 Agent
│   │   │   ├── __init__.py
│   │   │   └── agent.py              # QueryRouterAgent
│   │   │
│   │   └── search/                   # 搜索 Agent
│   │       ├── __init__.py
│   │       └── agent.py              # SearchAgent
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py               # 中心化配置 (Settings 类)
│   │
│   ├── conversation/                 # ★ 对话运行时
│   │   ├── __init__.py
│   │   ├── manager.py                # ★ ConversationManager (入口)
│   │   ├── context.py                # ConversationContext (回合上下文)
│   │   ├── session_state.py          # SessionState (会话状态)
│   │   ├── state.py                  # ConversationState (话题实体追踪)
│   │   └── rewrite.py                # RewriteEngine (问题重写)
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── sqlite.py                 # ★ SQLiteStore (所有 DB 操作)
│   │   ├── agentflow.db              # SQLite 数据库文件
│   │   ├── agentflow.db-shm          # WAL 共享内存文件
│   │   └── agentflow.db-wal          # WAL 日志文件
│   │
│   ├── docker/
│   │   ├── Dockerfile                # Docker 镜像定义
│   │   └── docker-compose.yml        # Docker Compose 编排
│   │
│   ├── docs/                         # 遗留文档
│   │   ├── architecture.md
│   │   ├── development.md
│   │   └── workflow.md
│   │
│   ├── graph/                        # ★ LangGraph 工作流
│   │   ├── __init__.py
│   │   ├── workflow.py               # ★ 工作流定义 (节点/边)
│   │   ├── context.py                # WorkflowContext (dict 子类)
│   │   ├── event.py                  # EventBus (事件系统)
│   │   ├── executor.py               # Executor (Task 生命周期)
│   │   ├── plan.py                   # Plan (执行计划)
│   │   └── task.py                   # Task (工作单元)
│   │
│   ├── knowledge/                    # ★ RAG 知识库
│   │   ├── __init__.py
│   │   ├── store.py                  # KnowledgeStore (高级接口)
│   │   ├── embedder.py               # TfidfEmbedder (TF-IDF 向量化)
│   │   └── parser.py                 # 文档解析器
│   │
│   ├── models/                       # Pydantic 数据模型
│   │   ├── __init__.py
│   │   ├── chat.py                   # ChatRequest/ChatResponse/FileProposal
│   │   └── model_config.py           # LLM 配置 CRUD 模型
│   │
│   ├── prompts/                      # 遗留提示模板 (markdown)
│   │   ├── knowledge.md
│   │   ├── planner.md
│   │   ├── report.md
│   │   └── search.md
│   │
│   ├── services/                     # 业务逻辑服务
│   │   ├── __init__.py
│   │   ├── file_proposer.py          # 文件提案 (代码块提取)
│   │   ├── llm_service.py            # ★ LLM 调用服务
│   │   ├── search_provider.py        # DuckDuckGo 搜索提供者
│   │   └── search_service.py         # 搜索业务逻辑
│   │
│   ├── tools/                        # 可执行工具
│   │   ├── __init__.py
│   │   ├── base.py                   # BaseTool 抽象基类
│   │   ├── python_tool.py            # Python 沙箱执行
│   │   └── search_tool.py            # 网络搜索工具
│   │
│   └── utils/
│       ├── __init__.py
│       └── logging.py                # 日志工具
│
├── frontend/                         # ★ Vue 3 前端
│   ├── index.html                    # HTML 入口
│   ├── package.json                  # 前端依赖
│   ├── package-lock.json             # 前端锁定
│   ├── tsconfig.json                 # TypeScript 配置
│   ├── tsconfig.node.json
│   ├── vite.config.ts                # Vite 配置
│   ├── postcss.config.cjs            # PostCSS 配置
│   ├── tailwind.config.cjs           # TailwindCSS 配置
│   ├── README.md
│   ├── .env                          # 前端环境变量
│   │
│   └── src/
│       ├── main.ts                   # Vue 应用入口
│       ├── App.vue                   # 根组件
│       ├── env.d.ts                  # 类型声明
│       ├── style.css                 # 全局样式
│       │
│       ├── api/
│       │   └── client.ts             # ★ API 客户端 (axios)
│       │
│       ├── composables/
│       │   └── useChatState.ts       # ★ 聊天状态 (响应式单例)
│       │
│       ├── types/
│       │   └── index.ts              # ★ TypeScript 类型定义
│       │
│       └── components/
│           ├── AgentsView.vue         # Agent 列表视图
│           ├── ArtifactsView.vue      # 产物视图
│           │
│           ├── chat/                  # 聊天组件
│           │   ├── ChatInput.vue      # 聊天输入框
│           │   ├── ChatView.vue       # 聊天主视图
│           │   ├── FileProposalCard.vue  # 文件提案卡片
│           │   ├── MessageItem.vue    # 消息条目
│           │   ├── ModelSelector.vue  # 模型选择器
│           │   ├── QuickActions.vue   # 快捷操作
│           │   ├── ThinkingIndicator.vue # 思考指示器
│           │   ├── UploadButton.vue   # 上传按钮
│           │   └── WelcomeView.vue    # 欢迎页
│           │
│           ├── knowledge/             # 知识库组件
│           │   ├── DocumentList.vue   # 文档列表
│           │   ├── KnowledgeView.vue  # 知识库主视图
│           │   └── UploadZone.vue     # 上传区域
│           │
│           ├── layout/               # 布局组件
│           │   ├── MainContent.vue    # 主内容区
│           │   └── Sidebar.vue        # 侧边栏
│           │
│           ├── markdown/             # Markdown 渲染
│           │   ├── MarkdownRenderer.vue
│           │   └── SourceCard.vue
│           │
│           ├── projects/             # 项目管理
│           │   ├── FolderReminderModal.vue
│           │   └── ProjectsView.vue
│           │
│           ├── settings/             # 设置
│           │   └── ModelsSettings.vue
│           │
│           └── sidebar/              # 侧边栏子组件
│               ├── ChatHistory.vue       # 聊天历史列表
│               ├── ChatHistoryItem.vue   # 历史条目
│               ├── NavItem.vue           # 导航项
│               ├── SegmentedControl.vue  # 分段控制器
│               └── UserProfile.vue       # 用户头像
│
├── logs/                              # 运行时日志
│   ├── agentflow.log                 # 主日志
│   ├── answer.log                    # AnswerAgent 日志
│   ├── api.log                       # API 路由日志
│   ├── conversation.log / manager.log / rewrite_engine.log
│   ├── executor.log / workflow.log
│   ├── knowledge.log / knowledge.store.log
│   ├── llm.log / memory.log / memory_updater.log
│   ├── planner.log / router.log
│   ├── python.log / python_tool.log
│   ├── report.log / observer.log
│   ├── search.log / search_provider.log / search_service.log / search_tool.log
│   └── ...
│
├── outputs/                          # Agent 生成文件的输出目录
│   └── Python贪吃蛇游戏.py           # 示例输出
│
├── uploads/                          # 上传文件的临时目录
│
├── tests/                            # 测试
│   ├── test_conversation_runtime.py  # ★ 对话运行时完整测试 (1047行)
│   └── test_workflow.py              # 工作流集成测试
│
└── omniforge/                        # 兼容包 (legacy)
    └── __init__.py                   # 从 agentflow 重导入
```

---

## 目录说明

| 目录 | 类型 | 说明 |
|------|------|------|
| `agentflow/` | 核心后端 | 主 Python 包，所有后端代码 |
| `agentflow/app/` | 应用入口 | FastAPI 应用实例 |
| `agentflow/api/` | API 层 | 所有 REST 路由和处理函数 |
| `agentflow/agents/` | Agent 层 | 8 个 Agent 实现，每个独立子目录 |
| `agentflow/config/` | 配置 | Pydantic Settings 环境变量管理 |
| `agentflow/conversation/` | 对话运行时 | 会话状态、上下文理解、问题重写 |
| `agentflow/database/` | 持久化 | SQLite 存储层 |
| `agentflow/docker/` | 容器化 | Docker 构建文件 |
| `agentflow/docs/` | 文档 | 遗留的 markdown 文档 |
| `agentflow/graph/` | 工作流 | LangGraph 状态机、Executor、Task、Event |
| `agentflow/knowledge/` | RAG | TF-IDF 知识库（解析、嵌入、检索） |
| `agentflow/models/` | 数据模型 | Pydantic 请求/响应模型 |
| `agentflow/prompts/` | 提示模板 | 遗留的 markdown 提示模板 |
| `agentflow/services/` | 服务层 | 业务逻辑（LLM、搜索、文件提案） |
| `agentflow/tools/` | 工具层 | BaseTool 实现（搜索、Python 执行） |
| `agentflow/utils/` | 工具 | 日志等通用工具 |
| `frontend/` | 前端 | Vue 3 + Vite + TailwindCSS |
| `tests/` | 测试 | pytest 测试 |
| `logs/` | 日志 | 运行时日志输出目录 |
| `outputs/` | 输出 | Agent 生成文件 |
| `uploads/` | 上传 | 上传文件临时目录 |

---

## 核心文件详细说明

### `agentflow/graph/workflow.py` (⭐⭐⭐)
- **作用**: 整个系统的**核心编排器**
- **关键内容**:
  - `WorkflowState` TypedDict — 所有 Agent 间传递的数据结构
  - `build_workflow()` — 构建 8 节点 LangGraph 状态机
  - `run_workflow()` — 工作流入口函数
  - 3 个条件路由函数: `_route_after_conversation_manager`, `_route_after_router`, `_route_after_planner`
  - `get_executor()` — 全局 Executor 单例

### `agentflow/conversation/manager.py` (⭐⭐⭐)
- **作用**: 对话运行时核心入口
- **关键内容**: `resolve_question()`, `rewrite_question()`, `should_continue()`, `build_conversation_context()`, `finalize_turn()`, `_extract_options()`, `_extract_entities()`, `_update_tracking_from_question()`

### `agentflow/api/routes.py` (⭐⭐⭐)
- **作用**: 所有 REST API 端点
- **关键内容**: 22 个 API 端点，涵盖聊天、知识库、会话、文件、工作区、模型管理

### `agentflow/database/sqlite.py` (⭐⭐)
- **作用**: 所有数据库操作
- **关键内容**: 7 张表的 CRUD，session_state 持久化，embedding 存储，模型配置管理

### `agentflow/services/llm_service.py` (⭐⭐)
- **作用**: LLM 调用中心
- **关键内容**: OpenAI 客户端初始化、数据库驱动/环境变量双模式、complete() 方法、fallback 支持

---

## 前端核心文件

| 文件 | 说明 |
|------|------|
| `frontend/src/App.vue` | 根组件，提供 chatState |
| `frontend/src/api/client.ts` | 所有后端 API 调用 |
| `frontend/src/composables/useChatState.ts` | 全局响应式状态 + 操作 |
| `frontend/src/types/index.ts` | TypeScript 类型定义 |
| `frontend/src/components/chat/ChatView.vue` | 聊天主界面 |
| `frontend/src/components/layout/Sidebar.vue` | 侧边栏导航 |
| `frontend/src/components/knowledge/KnowledgeView.vue` | 知识库管理 |
