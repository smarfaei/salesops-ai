from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.activity_routes import router as activity_router
from app.api.errors import install_exception_handlers
from app.api.intelligence_routes import router as intelligence_router
from app.api.dashboard_routes import router as dashboard_router
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(dashboard_router)
app.include_router(lead_router)
app.include_router(activity_router)
app.include_router(task_router)
app.include_router(intelligence_router)
