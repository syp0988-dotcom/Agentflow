"""LangGraph workflow definition for the multi-agent system."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from agentflow.agents.answer.agent import AnswerAgent
from agentflow.agents.knowledge.agent import KnowledgeAgent
from agentflow.agents.memory.agent import MemoryAgent
from agentflow.agents.planner.agent import PlannerAgent
from agentflow.agents.router.agent import QueryRouterAgent
from agentflow.agents.search.agent import SearchAgent


class WorkflowState(TypedDict, total=False):
    """Typed state container for workflow nodes."""

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
    router: dict[str, Any]


def build_workflow() -> Any:
    """Build the LangGraph workflow for the system."""
    router = QueryRouterAgent()
    planner = PlannerAgent()
    search = SearchAgent()
    answer = AnswerAgent()
    memory = MemoryAgent()
    knowledge = KnowledgeAgent()

    workflow = StateGraph(WorkflowState)

    workflow.add_node("router", router.run)
    workflow.add_node("planner", planner.run)
    workflow.add_node("search", search.run)
    workflow.add_node("answer", answer.run)
    workflow.add_node("memory", memory.run)
    workflow.add_node("knowledge", knowledge.run)

    workflow.set_entry_point("router")

    # Route to knowledge agent if the query is knowledge-related,
    # otherwise go directly to planner.
    workflow.add_conditional_edges(
        "router",
        _route_after_router,
        {
            "knowledge": "knowledge",
            "planner": "planner",
        },
    )

    workflow.add_edge("knowledge", "planner")
    workflow.add_edge("planner", "search")
    workflow.add_edge("search", "answer")
    workflow.add_edge("answer", "memory")
    workflow.add_edge("memory", END)

    return workflow.compile()


def _route_after_router(state: WorkflowState) -> str:
    """Determine the next node after routing based on the category."""
    category = state.get("category", "reasoning")
    if category == "knowledge":
        return "knowledge"
    return "planner"


def run_workflow(graph: Any, message: str) -> dict[str, Any]:
    """Run the workflow for a user message."""
    initial_state: WorkflowState = {"question": message, "workflow": []}
    result = graph.invoke(initial_state)
    return dict(result)
