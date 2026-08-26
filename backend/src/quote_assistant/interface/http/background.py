from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from fastapi import FastAPI

from quote_assistant.adapter.db.repositories import (
    SqlPartDrawingEventRepository,
    SqlPartDrawingRepository,
)
from quote_assistant.adapter.db.session import SqlAlchemyUnitOfWork
from quote_assistant.adapter.pdf.renderer import PdfiumDrawingPageRenderer
from quote_assistant.config import Settings
from quote_assistant.domain.entities import Actor, PartDrawing
from quote_assistant.usecase.process_part_drawing import ProcessPartDrawing

LOGGER = logging.getLogger("quote_assistant.background")

PROCESSOR_INLINE = "inline"
PROCESSOR_THREAD = "thread"


class ProcessPartDrawingJob:
    """Composition root for one 分级 + 读图取数 job.

    Engine and storage are read from app.state at run time so 缝 1 can swap the
    提取引擎 without rebuilding the processor.
    """

    def __init__(self, app: FastAPI) -> None:
        self._app = app

    def run(self, actor: Actor, drawing_id: UUID) -> PartDrawing:
        session = self._app.state.session_factory()
        try:
            return ProcessPartDrawing(
                actor=actor,
                drawings=SqlPartDrawingRepository(session),
                events=SqlPartDrawingEventRepository(session),
                storage=self._app.state.object_storage,
                renderer=PdfiumDrawingPageRenderer(),
                engine=self._app.state.extraction_engine,
                uow=SqlAlchemyUnitOfWork(session),
            ).execute(drawing_id)
        finally:
            session.close()


class InlinePartDrawingProcessor:
    """Run 分级 + 读图取数 before the upload response. Used by 缝 1 and single-process dev."""

    def __init__(self, job: ProcessPartDrawingJob) -> None:
        self._job = job

    def submit(self, actor: Actor, drawing_id: UUID) -> PartDrawing | None:
        return self._job.run(actor, drawing_id)


class ThreadPartDrawingProcessor:
    """Run each 零件图 on a worker thread so the upload request returns immediately.

    Deliberately not a queue server: one factory's 报价员 team does not need Redis, and a
    stranded job after a restart is recovered by the startup sweep. Failures are logged
    per drawing so one bad 零件图 cannot take the rest of the batch down with it.
    """

    def __init__(self, job: ProcessPartDrawingJob, workers: int) -> None:
        self._job = job
        self._pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="qa-extract")

    def submit(self, actor: Actor, drawing_id: UUID) -> PartDrawing | None:
        self._pool.submit(self._run_quietly, actor, drawing_id)
        return None

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)

    def _run_quietly(self, actor: Actor, drawing_id: UUID) -> None:
        try:
            self._job.run(actor, drawing_id)
        except Exception:
            LOGGER.exception("零件图后台处理失败 part_drawing_id=%s", drawing_id)


class DeferredPartDrawingProcessor:
    """Hold submitted jobs until the test drains them. Not used in production."""

    def __init__(self, job: ProcessPartDrawingJob) -> None:
        self._job = job
        self.pending: list[tuple[Actor, UUID]] = []

    def submit(self, actor: Actor, drawing_id: UUID) -> PartDrawing | None:
        self.pending.append((actor, drawing_id))
        return None

    def run_pending(self) -> list[PartDrawing]:
        finished = [self._job.run(actor, drawing_id) for actor, drawing_id in self.pending]
        self.pending.clear()
        return finished


def build_part_drawing_processor(
    settings: Settings,
    app: FastAPI,
) -> InlinePartDrawingProcessor | ThreadPartDrawingProcessor:
    job = ProcessPartDrawingJob(app)
    if settings.part_drawing_processor == PROCESSOR_INLINE:
        return InlinePartDrawingProcessor(job)
    return ThreadPartDrawingProcessor(job, settings.part_drawing_processor_workers)
