from fastapi import FastAPI

from app.api.activity_routes import router as activity_router
from app.api.errors import install_exception_handlers
from app.api.routes import router as lead_router
from app.api.task_routes import router as task_router
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title="SalesOps AI API",
    description="Lead qualification and sales automation backend.",
    version="1.0.0",
    debug=settings.debug,
)
install_exception_handlers(app)
app.include_router(lead_router)
app.include_router(activity_router)
app.include_router(task_router)
