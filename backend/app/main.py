from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.activity_routes import router as activity_router
from app.api.errors import install_exception_handlers
from app.api.intelligence_routes import router as intelligence_router
from app.api.dashboard_routes import router as dashboard_router
from app.api.routes import router as lead_router
from app.api.task_routes import router as task_router
from app.core.config import Settings, settings
from app.core.logging import configure_logging
from app.core.rate_limit import DemoWriteRateLimitMiddleware

configure_logging()


def create_app(app_settings: Settings | None = None) -> FastAPI:
    active_settings = app_settings or settings
    demo_schema_url = None if active_settings.demo_mode else "/openapi.json"
    app = FastAPI(
        title="SalesOps AI API",
        description="Lead qualification and sales automation backend.",
        version="1.0.0",
        debug=active_settings.debug,
        docs_url=None if active_settings.demo_mode else "/docs",
        redoc_url=None if active_settings.demo_mode else "/redoc",
        openapi_url=demo_schema_url,
    )
    app.state.settings = active_settings
    install_exception_handlers(app)
    if active_settings.demo_mode:
        app.add_middleware(
            DemoWriteRateLimitMiddleware,
            requests=active_settings.demo_rate_limit_requests,
            window_seconds=active_settings.demo_rate_limit_window_seconds,
        )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.allowed_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(dashboard_router)
    app.include_router(lead_router)
    app.include_router(activity_router)
    app.include_router(task_router)
    app.include_router(intelligence_router)
    return app


app = create_app()
