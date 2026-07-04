"""API routes for chat and knowledge base management."""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from agentflow.database.sqlite import SQLiteStore
from agentflow.graph.workflow import build_workflow, run_workflow
from agentflow.knowledge.store import KnowledgeStore
from agentflow.models.chat import ChatRequest, ChatResponse
from agentflow.utils.logging import build_logger

router = APIRouter()
logger = build_logger("api")
store = SQLiteStore()
knowledge_store = KnowledgeStore(db=store)

# Directory for uploaded document files
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# -- Chat -------------------------------------------------------------------


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Handle chat requests through the workflow."""
    try:
        workflow = build_workflow()
        result = run_workflow(workflow, request.message)
        store.add_message("user", request.message)
        store.add_message("assistant", result["answer"])
        debug_data = {
            "category": result.get("category"),
            "workflow": result.get("workflow"),
            "search_results": result.get("search_results", []),
            "router": result.get("router", {}),
        }
        return ChatResponse(reply=result["answer"], metadata={"status": "ok"}, debug=debug_data)
    except Exception as exc:
        logger.exception("Chat error")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# -- Knowledge base: document management ------------------------------------


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
    """Upload a document, parse it, and index it into the knowledge base."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate file type
    allowed_types = {".pdf", ".docx", ".doc", ".txt", ".md", ".markdown"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(allowed_types)}",
        )

    # Save uploaded file temporarily
    temp_path = UPLOAD_DIR / file.filename
    try:
        content = await file.read()
        temp_path.write_bytes(content)
        logger.info("Saved uploaded file: %s (%d bytes)", file.filename, len(content))

        # Ingest into knowledge base
        doc_id = knowledge_store.add_document(temp_path, file.filename)
        return JSONResponse(
            content={
                "status": "ok",
                "document_id": doc_id,
                "filename": file.filename,
                "size": len(content),
            }
        )
    except Exception as exc:
        logger.exception("Upload ingestion failed for %s", file.filename)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        # Clean up temp file after indexing
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


@router.get("/knowledge/documents")
def list_documents() -> list[dict[str, object]]:
    """List all indexed documents."""
    return knowledge_store.list_documents()


@router.delete("/knowledge/documents/{doc_id}")
def delete_document(doc_id: int) -> JSONResponse:
    """Delete a document and its chunks/embeddings from the knowledge base."""
    knowledge_store.delete_document(doc_id)
    return JSONResponse(content={"status": "deleted", "document_id": doc_id})


@router.post("/knowledge/search")
def search_knowledge(query: str, top_k: int = 5) -> list[dict[str, object]]:
    """Search the knowledge base for relevant chunks."""
    return knowledge_store.search(query, top_k=top_k)


# -- Chat history ----------------------------------------------------------


@router.get("/history")
def history(limit: int = 20) -> list[dict[str, str]]:
    """Fetch recent chat history."""
    return store.list_messages(limit=limit)
