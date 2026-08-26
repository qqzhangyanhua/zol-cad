from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from quote_assistant.adapter.db.repositories import (
    SqlInFlightPartDrawingRepository,
    SqlPartDrawingEventRepository,
)
from quote_assistant.adapter.db.seed import seed_demo_data
from quote_assistant.adapter.db.session import (
    SqlAlchemyUnitOfWork,
    make_engine,
    make_session_factory,
)
from quote_assistant.adapter.extraction.factory import build_extraction_engine
from quote_assistant.adapter.pdf.renderer import PdfiumDrawingPageRenderer
from quote_assistant.adapter.storage.factory import build_object_storage
from quote_assistant.config import Settings, validate_runtime_settings
from quote_assistant.domain.errors import DomainError
from quote_assistant.interface.http.background import build_part_drawing_processor
from quote_assistant.interface.http.errors import domain_error_handler
from quote_assistant.interface.http.limits import RateLimitMiddleware, RequestSizeLimitMiddleware
from quote_assistant.interface.http.routes.admin import router as admin_router
from quote_assistant.interface.http.routes.auth import router as auth_router
from quote_assistant.interface.http.routes.correction_stats import router as correction_stats_router
from quote_assistant.interface.http.routes.object_store import router as object_store_router
from quote_assistant.interface.http.routes.part_drawings import router as part_drawings_router
from quote_assistant.interface.http.routes.processing_time import router as processing_time_router
from quote_assistant.interface.http.routes.quote_tasks import router as quote_tasks_router
from quote_assistant.logging_config import configure_logging
from quote_assistant.usecase.recover_stranded_part_drawings import RecoverStrandedPartDrawings

LOGGER = logging.getLogger("quote_assistant.startup")


def _recover_stranded_part_drawings(session_factory: sessionmaker[Session]) -> None:
    """Best-effort sweep. A failure here must not prevent the process from starting."""
    try:
        session = session_factory()
        try:
            recovered = RecoverStrandedPartDrawings(
                drawings=SqlInFlightPartDrawingRepository(session),
                events=SqlPartDrawingEventRepository(session),
                uow=SqlAlchemyUnitOfWork(session),
            ).execute()
            LOGGER.info("滞留零件图回收完成 recovered=%s", recovered)
        finally:
            session.close()
    except Exception:
        LOGGER.exception("滞留零件图回收失败，应用继续启动")


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()
    validate_runtime_settings(resolved)
    configure_logging(resolved.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = make_engine(resolved.database_url)
        session_factory = make_session_factory(engine)
        app.state.settings = resolved
        app.state.engine = engine
        app.state.session_factory = session_factory
        app.state.object_storage = build_object_storage(resolved)
        app.state.extraction_engine = build_extraction_engine(resolved)
        app.state.drawing_page_renderer = PdfiumDrawingPageRenderer()
        app.state.part_drawing_processor = build_part_drawing_processor(resolved, app)
        _recover_stranded_part_drawings(session_factory)
        if resolved.seed_demo_data:
            seed_demo_data(session_factory, resolved)
        yield
        shutdown = getattr(app.state.part_drawing_processor, "shutdown", None)
        if shutdown is not None:
            shutdown()
        engine.dispose()

    app = FastAPI(title="机加工报价辅助", lifespan=lifespan)
    app.state.settings = resolved
    app.state.object_storage = build_object_storage(resolved)
    app.state.extraction_engine = build_extraction_engine(resolved)
    app.state.drawing_page_renderer = PdfiumDrawingPageRenderer()
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=resolved.max_request_bytes)
    if not resolved.is_local:
        app.add_middleware(
            RateLimitMiddleware,
            login_per_minute=resolved.rate_limit_login_per_minute,
            upload_per_minute=resolved.rate_limit_upload_per_minute,
        )
    app.include_router(auth_router)
    app.include_router(part_drawings_router)
    app.include_router(correction_stats_router)
    app.include_router(processing_time_router)
    app.include_router(quote_tasks_router)
    app.include_router(admin_router)
    app.include_router(object_store_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        factory = getattr(app.state, "session_factory", None)
        if factory is None:
            raise HTTPException(status_code=503, detail="数据库未就绪")
        session = None
        try:
            session = factory()
            session.execute(text("SELECT 1"))
        except Exception:
            LOGGER.exception("健康检查：数据库不可用")
            raise HTTPException(status_code=503, detail="数据库不可用") from None
        finally:
            if session is not None:
                session.close()
        return {"status": "ok"}

    return app


app = create_app()
