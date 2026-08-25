from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from quote_assistant.adapter.db.seed import seed_demo_data
from quote_assistant.adapter.db.session import make_engine, make_session_factory
from quote_assistant.adapter.extraction.fake import FixtureExtractionEngine
from quote_assistant.adapter.storage.factory import build_object_storage
from quote_assistant.config import Settings
from quote_assistant.interface.http.routes.auth import router as auth_router
from quote_assistant.interface.http.routes.correction_stats import router as correction_stats_router
from quote_assistant.interface.http.routes.object_store import router as object_store_router
from quote_assistant.interface.http.routes.part_drawings import router as part_drawings_router
from quote_assistant.interface.http.routes.processing_time import router as processing_time_router
from quote_assistant.interface.http.routes.quote_tasks import router as quote_tasks_router


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = make_engine(resolved.database_url)
        session_factory = make_session_factory(engine)
        app.state.settings = resolved
        app.state.engine = engine
        app.state.session_factory = session_factory
        app.state.object_storage = build_object_storage(resolved)
        app.state.extraction_engine = FixtureExtractionEngine()
        if resolved.seed_demo_data:
            seed_demo_data(session_factory, resolved)
        yield
        engine.dispose()

    app = FastAPI(title="机加工报价辅助", lifespan=lifespan)
    app.state.settings = resolved
    app.state.object_storage = build_object_storage(resolved)
    app.state.extraction_engine = FixtureExtractionEngine()
    app.include_router(auth_router)
    app.include_router(part_drawings_router)
    app.include_router(correction_stats_router)
    app.include_router(processing_time_router)
    app.include_router(quote_tasks_router)
    app.include_router(object_store_router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
