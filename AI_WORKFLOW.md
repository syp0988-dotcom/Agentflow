# AI_WORKFLOW — 项目流程图

---

## 1. 完整聊天流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant FE as 前端 (Vue 3)
    participant API as FastAPI 路由
    participant WF as LangGraph 工作流
    participant CM as ConversationManager
    participant Router as QueryRouterAgent
    participant Planner as PlannerAgent
    participant LLM as LLM Service
    participant Tools as Search/PythonAgent
    participant Answer as AnswerAgent
    participant Memory as MemoryAgent
    participant DB as SQLite

    User->>FE: 输入消息
    FE->>FE: useChatState.handleSend()
    FE->>API: POST /chat {message, history, session_id}
    
    API->>DB: 获取 session_state
    API->>API: build_workflow() → 编译 StateGraph
    API->>WF: run_workflow(graph, message, history, session_state)
    
    Note over WF: === LangGraph 工作流开始 ===
    
    WF->>CM: conversation_manager 节点
    
    CM->>CM: resolve_question()
    Note over CM: 1. 选项解析: "选项一" → 儿童教育
    Note over CM: 2. 槽填充: "北京" → slots.city
    Note over CM: 3. 继续信号: "继续"/"好的" → resume
    Note over CM: 4. 指代消解: "改成 Java" → 加上上下文
    
    CM->>CM: rewrite_question()
    Note over CM: 短/指代输入 → 上下文增强后完整问题
    
    CM->>CM: should_continue()
    CM->>CM: build_conversation_context()
    
    alt 继续模式 (_continue_mode=true)
        CM->>WF: 路由到 answer 节点
        WF->>Answer: AnswerAgent.run()
        Answer->>Answer: ContextBuilder 组装上下文
        Answer->>LLM: complete() 生成回答
        LLM-->>Answer: 原始回答
        Answer->>Answer: clean_answer()
        Answer-->>WF: {answer, ...}
        
    else 新任务
        CM->>WF: 路由到 router 节点
        WF->>Router: QueryRouterAgent.run()
        Router->>Router: classify()
        Note over Router: 正则匹配 7 种分类
        Router-->>WF: {category, router}
        
        alt category 不是 identity/search
            WF->>WF: 路由 → knowledge → planner
            WF->>KnowledgeAgent: knowledge 节点
            KnowledgeAgent->>DB: store.search(query)
            DB-->>KnowledgeAgent: 相关文档块
            KnowledgeAgent-->>WF: {knowledge_context, knowledge_results}
        else
            WF->>WF: 路由 → planner (跳过知识检索)
        end
        
        WF->>Planner: PlannerAgent.run()
        
        alt LLM 规划成功
            Planner->>LLM: build_planner_prompt() (系统提示+用户问题)
            LLM-->>Planner: JSON 格式计划
            Planner->>Planner: _parse_json() → _build_plan_from_json()
        else LLM 失败
            Planner->>Planner: _build_plan() 规则回退
            Note over Planner: 基于 category 生成预设 Plan
        end
        
        Planner->>Planner: _resolve_capabilities()
        Note over Planner: capability → tool 名称映射
        
        Planner-->>WF: {plan, workflow}
        
        alt plan.direct_answer=true
            WF->>WF: 路由到 answer
        else category=search
            WF->>Tools: SearchAgent
            Tools->>Tools: SearchService.search()
            Tools->>Tools: SearchTool.execute()
            Tools->>Tools: DuckDuckGoProvider.search()
            Tools-->>WF: {search_results}
        else category=python
            WF->>Tools: PythonAgent
            Tools->>Tools: _extract_code() → PythonTool.execute()
            Tools-->>WF: {python_result}
        end
        
        WF->>Answer: AnswerAgent.run()
        Answer->>LLM: complete(messages)
        LLM-->>Answer: 最终回答
        Answer-->>WF: {answer}
    end
    
    WF->>Memory: MemoryAgent.run()
    Memory->>Memory: 追加历史 (question + answer)
    Memory->>Memory: _update_memory_meta()
    Memory->>Memory: ConversationManager.finalize_turn()
    Note over Memory: 检测选项/提问 → 更新 session_state
    Memory-->>WF: {memory, session_state}
    
    Note over WF: === 工作流结束 ===
    
    WF-->>API: 结果 dict
    
    API->>API: WorkflowContext(result).to_dict()
    API->>DB: 持久化 session_state
    API->>DB: add_message(user) + add_message(assistant)
    API->>API: propose_files() 提取代码块
    API-->>FE: ChatResponse {reply, metadata, debug, proposed_files}
    
    FE->>FE: 更新 messages 列表
    
    alt 有 proposed_files
        FE->>FE: 显示文件提案卡片
        User->>FE: 点击创建
        FE->>API: POST /files/create
        API-->>FE: 创建成功
    end
    
    FE-->>User: 显示回答
```

---

## 2. Tool Calling 流程

```mermaid
sequenceDiagram
    participant Planner as PlannerAgent
    participant Exec as Executor
    participant Task as Task 对象
    participant Event as EventBus
    participant Tool as BaseTool 实现
    participant Context as WorkflowContext

    Planner->>Planner: _resolve_capabilities(plan)
    Note over Planner: 遍历 Task, capability → tool 名称
    
    Planner->>Context: add_task(task)
    
    Exec->>Context: 获取 tasks
    loop 每个 Task
        Exec->>Task: 当前状态 = PENDING
        
        Event->>Event: task_created()
        Exec->>Task: mark_ready() → READY
        Exec->>Task: mark_running() → RUNNING
        Event->>Event: task_started()
        
        Exec->>Exec: _tools.get(task.tool)
        
        alt 工具未注册
            Exec->>Task: fail("No tool registered")
            Event->>Event: task_failed()
        else 工具已注册
            Event->>Event: tool_started()
            Exec->>Tool: execute(**task.input)
            
            alt 执行成功
                Tool-->>Exec: 结果
                Exec->>Task: complete(result) → COMPLETED
                Event->>Event: tool_finished()
                Event->>Event: task_finished()
            else 执行失败
                Tool-->>Exec: 异常
                Exec->>Task: fail(error) → FAILED
                Event->>Event: task_failed()
            end
        end
    end

    Note over Exec: Task 状态流转:
    Note over Exec: PENDING → READY → RUNNING → COMPLETED
    Note over Exec:                                    → FAILED
```

---

## 3. 对话运行时流程

```mermaid
flowchart TD
    A["用户输入"] --> B{"SessionState<br/>有 pending_options?"}
    
    B -->|是| C["SessionState.resolve_option()"]
    C --> D{"匹配成功?"}
    D -->|是| E["清除 pending_options<br/>resume()"]
    D -->|否| F["保持等待"]
    
    B -->|否| G{"SessionState.is_waiting?"}
    
    G -->|是| H{"匹配继续模式?<br/>(继续/好的/嗯/ok)"}
    H -->|是| I["resume()<br/>使用 waiting_for 作为问题"]
    H -->|否| J{"有未填充槽位?"}
    
    J -->|是| K["fill_slot()<br/>填充第一个空槽"]
    K --> L{"所有槽位已填?"}
    L -->|是| M["resume()"]
    L -->|否| N["等待更多输入"]
    
    J -->|否| O{"有 current_goal<br/>且输入非自包含?"}
    
    G -->|否| O
    
    O -->|是| P["_enrich_with_context()"]
    P --> Q["更新 ConversationTracking<br/>(实体/话题/焦点)"]
    
    O -->|否| R{"是自包含问题?<br/>(>15字/介绍/搜索/翻译...)"}
    R -->|是| S["保持原问题"]
    R -->|否| T["需要 RewriteEngine 重写"]
    T --> U["RewriteEngine.rewrite()"]
    
    Q --> V["返回解析后的问题"]
    S --> V
    U --> V
    
    V --> W["build_conversation_context()"]
    W --> X["确定回合类型<br/>(NEW_TASK/FOLLOW_UP/OPTION_SELECTION/WAITING_REPLY/QUESTION_REWRITE)"]
    X --> Y["提取实体"]
    Y --> Z["构建 ConversationContext"]
    
    Z --> AA["设置 _continue_mode<br/>和 rewritten_question"]
```

---

## 4. Memory 更新流程

```mermaid
flowchart TD
    A["MemoryAgent.run()"] --> B["从 state['memory']<br/>获取现有 history"]
    B --> C["添加当前用户问题"]
    C --> D["添加当前助手回答"]
    D --> E["截断到 max_turns*2 (20条)"]
    E --> F["构建 context_str (格式化文本)"]
    
    F --> G["state['memory'] = {history, context_str}"]
    
    G --> H["ConversationManager.finalize_turn()"]
    
    H --> I{"回答包含编号选项?<br/>(1. X\\n2. Y)"}
    I -->|是| J["设置 pending_options"]
    J --> K["start_waiting('选择选项')"]
    
    I -->|否| L{"回答是提问句式?<br/>(请选择/请问/哪个?)"}
    L -->|是| M["start_waiting('提供更多信息')"]
    
    L -->|否| N["status = idle"]
    
    K --> O["_update_memory_meta()"]
    M --> O
    N --> O
    
    O --> P["设置 last_topic"]
    O --> Q["设置 current_goal (来自 session_state 或首条消息)"]
    O --> R["构建规则摘要 (最近2轮)"]
    O --> S["确定 conversation_type<br/>(single/follow_up/multi_turn)"]
    
    S --> T["返回更新后的 state"]
```

---

## 5. RAG 知识库流程

```mermaid
flowchart TD
    subgraph "文档入库"
        A["上传文件"] --> B{"文件类型"}
        B -->|PDF| C["pypdf 解析"]
        B -->|DOCX| D["python-docx 解析"]
        B -->|MD| E["Markdown 解析 (去除frontmatter)"]
        B -->|TXT| F["UTF-8/GBK 自动检测读取"]
        
        C --> G["按段落分块<br/>chunk_text(size=500, overlap=50)"]
        D --> G
        E --> G
        F --> G
        
        G --> H["tokenize()<br/>中文单字+英文单词"]
        H --> I["TfidfEmbedder.add_chunk()"]
        I --> J["vectorize() → numpy TF-IDF 向量"]
        J --> K["serialize_vector() → BLOB"]
        K --> L["SQLite 存储:<br/>documents + chunks + embeddings"]
        L --> M["_save_embedder_state()"]
    end

    subgraph "检索查询"
        N["用户查询"] --> O["tokenize()"]
        O --> P["vectorize() → 查询向量"]
        P --> Q["从 SQLite 读取所有嵌入向量"]
        Q --> R["batch_cosine_similarity()"]
        R --> S["按相似度排序"]
        S --> T["过滤 min_score=0.05"]
        T --> U["取 top_k 结果"]
        U --> V["查询 chunk+document 信息"]
        V --> W["返回 {chunk_id, filename, content, score}"]
    end

    subgraph "文档删除"
        X["delete_document(id)"] --> Y["获取所有 chunks"]
        Y --> Z["对每个 chunk: remove_chunk(tokens)"]
        Z --> AA["delete_document_cascade()"]
        AA --> AB["_save_embedder_state()"]
    end
```

---

## 6. Planner 任务规划流程

```mermaid
flowchart TD
    A["PlannerAgent.run()"] --> B["接收 question + category"]
    
    B --> C["_llm_plan() 尝试 LLM 规划"]
    
    C --> D["build_planner_prompt()"]
    D --> E["LLMService.complete()"]
    E --> F{"返回空或异常?"}
    F -->|是| G["返回 None → 触发回退"]
    F -->|否| H["_parse_json()"]
    
    H --> I{"JSON 解析成功?"}
    I -->|否| G
    I -->|是| J["_build_plan_from_json()"]
    
    J --> K{"验证通过?"}
    K -->|否| G
    K -->|是| L["Plan 对象"]
    
    G --> M["_build_plan() 规则回退"]
    
    M --> N{"category"}
    N -->|search| O["搜索计划<br/>web.search + 综合回答 + 记忆"]
    N -->|identity| P["身份计划<br/>direct_answer=true"]
    N -->|python| Q["Python 执行计划<br/>python.execute + 综合回答 + 记忆"]
    N -->|其他| R["通用计划<br/>direct_answer=true"]
    
    O --> S["_resolve_capabilities()"]
    P --> S
    Q --> S
    R --> S
    
    L --> S
    S --> T["遍历 Task: capability → tool"]
    
    T --> U["设置 plan + workflow"]
    U --> V["注册 Task 到 WorkflowContext"]
    V --> W["返回 state"]
```

---

## 7. API 路由概览

```mermaid
graph TD
    subgraph "聊天"
        POST_CHAT["POST /chat"]
    end

    subgraph "Agent 内省"
        GET_AGENTS["GET /agents"]
    end

    subgraph "知识库管理"
        POST_UPLOAD["POST /upload"]
        GET_DOCS["GET /knowledge/documents"]
        DEL_DOC["DELETE /knowledge/documents/{id}"]
        POST_SEARCH["POST /knowledge/search"]
    end

    subgraph "会话管理"
        POST_SESS_CREATE["POST /sessions/create"]
        GET_SESS["GET /sessions"]
        GET_SESS_MSGS["GET /sessions/{id}/messages"]
        PUT_SESS_RENAME["PUT /sessions/{id}/rename"]
        DEL_SESS["DELETE /sessions/{id}"]
    end

    subgraph "文件操作"
        POST_FILE_CREATE["POST /files/create"]
        GET_FILES["GET /files"]
    end

    subgraph "工作区"
        GET_WS["GET /workspace"]
        POST_WS_SET["POST /workspace/set"]
        POST_WS_FOLDER["POST /workspace/create-folder"]
        GET_WS_BROWSE["GET /workspace/browse"]
    end

    subgraph "模型配置"
        GET_MODELS["GET /models"]
        POST_MODEL["POST /models"]
        PUT_MODEL["PUT /models/{id}"]
        DEL_MODEL["DELETE /models/{id}"]
        POST_ACTIVATE["POST /models/{id}/activate"]
    end

    subgraph "系统"
        GET_HEALTH["GET /health"]
    end

    POST_CHAT -->|调用| RUN_WF["run_workflow()"]
    RUN_WF --> LANG_GRAPH["LangGraph StateGraph"]
    
    POST_UPLOAD -->|解析| PARSE["knowledge/parser.py"]
    PARSE -->|嵌入| EMBED["TfidfEmbedder"]
    EMBED -->|存储| DB["SQLite"]
    
    GET_DOCS --> DB
    DEL_DOC --> DB
    POST_SEARCH -->|检索| EMBED
```

---

## 8. 数据流分层图

```mermaid
flowchart LR
    subgraph "表现层"
        VUE["Vue 3 前端"]
        AXIOS["API Client (axios)"]
    end

    subgraph "接口层"
        FASTAPI["FastAPI"]
        ROUTER["API Router"]
        CORS["CORS Middleware"]
    end

    subgraph "编排层"
        LANGGRAPH["LangGraph StateGraph"]
        CM["ConversationManager"]
        EXEC["Executor"]
        EVT["EventBus"]
    end

    subgraph "决策层"
        ROUTER_AG["QueryRouterAgent"]
        PLAN["PlannerAgent"]
    end

    subgraph "执行层"
        SEARCH_AG["SearchAgent"]
        KNOW_AG["KnowledgeAgent"]
        PYTHON_AG["PythonAgent"]
        ANSWER_AG["AnswerAgent"]
        MEM_AG["MemoryAgent"]
    end

    subgraph "基础设施层"
        TOOLS["Tools<br/>(SearchTool, PythonTool)"]
        LLM["LLMService"]
        KNOW["KnowledgeStore + TfidfEmbedder"]
        DB["SQLiteStore"]
        LOG["Logging"]
        SEARCH_PROV["SearchProvider<br/>(DuckDuckGo)"]
    end

    VUE --> AXIOS
    AXIOS --> FASTAPI
    FASTAPI --> CORS
    CORS --> ROUTER
    ROUTER --> LANGGRAPH
    
    LANGGRAPH --> CM
    CM --> ROUTER_AG
    ROUTER_AG --> PLAN
    PLAN --> EXEC
    
    EXEC --> SEARCH_AG
    EXEC --> KNOW_AG
    EXEC --> PYTHON_AG
    
    SEARCH_AG --> ANSWER_AG
    KNOW_AG --> ANSWER_AG
    PYTHON_AG --> ANSWER_AG
    
    ANSWER_AG --> MEM_AG
    
    MEM_AG -.->|回写 session_state| CM
    
    SEARCH_AG --> TOOLS
    PYTHON_AG --> TOOLS
    TOOLS --> SEARCH_PROV
    
    ANSWER_AG --> LLM
    PLAN --> LLM
    
    KNOW_AG --> KNOW
    
    LLM --> DB
    KNOW --> DB
    MEM_AG --> DB
    ROUTER --> DB
    
    EVT -.-> LANGGRAPH
    LOG -.-> 所有层
```

---

## 9. 模块依赖关系图

```mermaid
graph TD
    %% 各层颜色
    classDef api fill:#e1d5e7,stroke:#9673a6
    classDef agent fill:#dae8fc,stroke:#6c8ebf
    classDef graph fill:#d5e8d4,stroke:#82b366
    classDef service fill:#ffe6cc,stroke:#d79b00
    classDef tool fill:#f8cecc,stroke:#b85450
    classDef infra fill:#fff2cc,stroke:#d6b656

    subgraph "API 层"
        MAIN["main.py"] :::api
        ROUTES["routes.py"] :::api
    end

    subgraph "Agent 层" 
        REG["registry.py"] :::agent
        CM["manager.py"] :::agent
        ROUTER["router/agent.py"] :::agent
        PLANNER["planner/agent.py"] :::agent
        SEARCH["search/agent.py"] :::agent
        KNOW["knowledge/agent.py"] :::agent
        PYTHON["python/agent.py"] :::agent
        ANSWER["answer/agent.py"] :::agent
        MEMORY["memory/agent.py"] :::agent
    end

    subgraph "对话运行时"
        SS["session_state.py"] :::agent
        CTX_STATE["state.py"] :::agent
        CC["context.py"] :::agent
        REWRITE["rewrite.py"] :::agent
    end

    subgraph "Graph 层"
        WF["workflow.py"] :::graph
        WFC["context.py"] :::graph
        EXEC["executor.py"] :::graph
        TASK["task.py"] :::graph
        PLAN["plan.py"] :::graph
        EVT["event.py"] :::graph
    end

    subgraph "Service 层"
        LLM_SVC["llm_service.py"] :::service
        SEARCH_SVC["search_service.py"] :::service
        SEARCH_PROV["search_provider.py"] :::service
        FILE_PROP["file_proposer.py"] :::service
    end

    subgraph "Tool 层"
        BASE["base.py"] :::tool
        ST["search_tool.py"] :::tool
        PT["python_tool.py"] :::tool
    end

    subgraph "基础设施"
        DB["sqlite.py"] :::infra
        SETTINGS["settings.py"] :::infra
        LOG["logging.py"] :::infra
        KNOW_STORE["knowledge/store.py"] :::infra
        EMBEDDER["knowledge/embedder.py"] :::infra
        PARSER["knowledge/parser.py"] :::infra
    end

    %% API 依赖
    MAIN --> ROUTES
    ROUTES --> REG
    ROUTES --> WF
    ROUTES --> DB
    ROUTES --> CHAT["models/chat.py"]
    
    %% Workflow 依赖 (Agent 编排)
    WF --> CM
    WF --> ROUTER
    WF --> PLANNER
    WF --> SEARCH
    WF --> KNOW
    WF --> PYTHON
    WF --> ANSWER
    WF --> MEMORY
    WF --> EXEC
    WF --> WFC
    
    %% Executor 依赖
    EXEC --> WFC
    EXEC --> TASK
    EXEC --> EVT
    EXEC --> BASE
    BASE --> ST
    BASE --> PT
    
    %% Planner 依赖
    PLANNER --> LLM_SVC
    PLANNER --> CAP["planner/capability.py"]
    PLANNER --> PROMPT["planner/prompt.py"]
    PLANNER --> PLAN
    
    %% Answer 依赖
    ANSWER --> LLM_SVC
    
    %% Search 依赖
    SEARCH --> SEARCH_SVC
    SEARCH_SVC --> ST
    ST --> SEARCH_PROV
    
    %% Python 依赖
    PYTHON --> PT
    
    %% Knowledge 依赖
    KNOW --> KNOW_STORE
    KNOW_STORE --> DB
    KNOW_STORE --> EMBEDDER
    KNOW_STORE --> PARSER
    
    %% Conversation Manager 依赖
    CM --> SS
    CM --> CTX_STATE
    CM --> CC
    CM --> REWRITE
    
    %% Memory 依赖
    MEMORY --> SS
    MEMORY --> CM
    
    %% LLM Service 依赖
    LLM_SVC --> DB
    LLM_SVC --> SETTINGS
    
    %% 基础设施
    DB --> SETTINGS
    LOG --> SETTINGS
