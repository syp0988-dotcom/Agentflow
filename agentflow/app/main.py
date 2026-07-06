from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentflow.api.routes import router
from agentflow.config.settings import settings
from agentflow.utils.logging import build_logger

logger = build_logger("agentflow")

app = FastAPI(title=settings.app_name, debug=settings.debug)

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
