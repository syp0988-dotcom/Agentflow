"""FastAPI application entry point with background cleanup task."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentflow.api.routes import get_store, router
from agentflow.config.settings import settings
from agentflow.utils.logging import build_logger

logger = build_logger("agentflow")

# ------------------------------------------------------------------
# Background cleanup task
# ------------------------------------------------------------------


async def _cleanup_loop() -> None:
    """Periodically delete expired sessions and memories."""
    interval = settings.cleanup_interval_minutes
    logger.info(
        "Cleanup task started: interval=%dmin, session_ttl=%dh, memory_ttl=%dd",
        interval, settings.session_ttl_hours, settings.memory_ttl_days,
    )
    while True:
        try:
            await asyncio.sleep(interval * 60)
            store = get_store()

            sess_count = store.delete_sessions_older_than(settings.session_ttl_hours)
            mem_count = store.delete_old_memories(settings.memory_ttl_days)

            if sess_count or mem_count:
                logger.info("Cleanup: removed %d sessions, %d memories", sess_count, mem_count)
        except asyncio.CancelledError:
            logger.info("Cleanup task cancelled")
            return
        except Exception:
            logger.exception("Cleanup task error (non-fatal)")


_cleanup_task: asyncio.Task[None] | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> None:
    """Manage startup/shutdown lifecycle."""
    global _cleanup_task
    _cleanup_task = asyncio.create_task(_cleanup_loop())
    logger.info("AgentFlow started (debug=%s)", settings.debug)
    yield
    if _cleanup_task:
        _cleanup_task.cancel()
        logger.info("Cleanup task stopped")


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

# Enable CORS for local frontend development (Vite ports).
# In production you should restrict origins appropriately.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    """Basic health endpoint."""
    return {"status": "ok", "service": settings.app_name}
