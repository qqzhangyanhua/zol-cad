from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore
from uuid import UUID

from fastapi import FastAPI

from quote_assistant.adapter.db.repositories import (
    SqlPartDrawingEventRepository,
    SqlPartDrawingRepository,
)
from quote_assistant.adapter.db.session import SqlAlchemyUnitOfWork
from quote_assistant.config import Settings
from quote_assistant.domain.entities import Actor, PartDrawing
from quote_assistant.usecase.process_part_drawing import ProcessPartDrawing

LOGGER = logging.getLogger("quote_assistant.background")

PROCESSOR_INLINE = "inline"
PROCESSOR_THREAD = "thread"


class ProcessPartDrawingJob:
    """Composition root for one 分级 + 读图取数 job.

    Engine, storage, and the page renderer are read from app.state at run time
    so 缝 1 can swap the 提取引擎 (and count fetch / rasterize) without
    rebuilding the processor.
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
                renderer=self._app.state.drawing_page_renderer,
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

    Deploy is a single uvicorn process: the startup sweep can treat leftover
    已上传 / 分级中 / 提取中 rows as stranded. Failures are logged per drawing
    so one bad 零件图 cannot take the rest of the batch down with it.

    The slot semaphore bounds (workers + queue) so a 50-drawing batch cannot
    grow an unbounded ThreadPoolExecutor queue.
    """

    def __init__(
        self,
        job: ProcessPartDrawingJob,
        workers: int,
        queue_max: int,
        enqueue_timeout_seconds: float = 30,
    ) -> None:
        if workers < 1:
            raise ValueError("part_drawing_processor_workers 必须 >= 1")
        if queue_max < 0:
            raise ValueError("part_drawing_processor_queue_max 必须 >= 0")
        self._job = job
        self._queue_max = queue_max
        self._enqueue_timeout_seconds = enqueue_timeout_seconds
        self._slots = BoundedSemaphore(workers + queue_max)
        self._pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="qa-extract")

    def submit(self, actor: Actor, drawing_id: UUID) -> PartDrawing | None:
        if not self._slots.acquire(timeout=self._enqueue_timeout_seconds):
            LOGGER.error(
                "零件图作业队列已满 part_drawing_id=%s queue_max=%s",
                drawing_id,
                self._queue_max,
            )
            return None
        try:
            self._pool.submit(self._run_quietly, actor, drawing_id)
        except Exception:
            self._slots.release()
            raise
        return None

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)

    def _run_quietly(self, actor: Actor, drawing_id: UUID) -> None:
        try:
            self._job.run(actor, drawing_id)
        except Exception:
            LOGGER.exception("零件图后台处理失败 part_drawing_id=%s", drawing_id)
        finally:
            self._slots.release()


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


def normalize_part_drawing_processor(value: str) -> str:
    kind = value.strip().lower()
    if kind in {PROCESSOR_INLINE, PROCESSOR_THREAD}:
        return kind
    raise ValueError(f"未知零件图作业实现：{value}（允许 inline / thread）")


def build_part_drawing_processor(
    settings: Settings,
    app: FastAPI,
) -> InlinePartDrawingProcessor | ThreadPartDrawingProcessor:
    job = ProcessPartDrawingJob(app)
    kind = normalize_part_drawing_processor(settings.part_drawing_processor)
    if kind == PROCESSOR_INLINE:
        return InlinePartDrawingProcessor(job)
    return ThreadPartDrawingProcessor(
        job,
        workers=settings.part_drawing_processor_workers,
        queue_max=settings.part_drawing_processor_queue_max,
    )
