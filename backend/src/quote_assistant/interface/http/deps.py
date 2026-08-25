from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from quote_assistant.adapter.db.repositories import (
    SqlCorrectionRecordRepository,
    SqlManualBaselineRepository,
    SqlPartDrawingEventRepository,
    SqlPartDrawingRepository,
    SqlPasswordAuthenticator,
    SqlQuoteSheetTemplateRepository,
    SqlQuoteTaskRepository,
    SqlSessionRepository,
    SqlUserRepository,
)
from quote_assistant.adapter.export.quote_sheet_writer import OpenpyxlQuoteSheetFileWriter
from quote_assistant.adapter.db.session import SqlAlchemyUnitOfWork
from quote_assistant.config import Settings
from quote_assistant.domain.entities import Actor
from quote_assistant.domain.errors import Unauthenticated
from quote_assistant.adapter.pdf.page_counter import PypdfPageCounter
from quote_assistant.usecase.assign_part_drawing_to_quote_task import (
    AssignPartDrawingToQuoteTask,
    RemovePartDrawingFromQuoteTask,
)
from quote_assistant.usecase.compare_processing_time import CompareProcessingTime
from quote_assistant.usecase.create_quote_task import CreateQuoteTask
from quote_assistant.usecase.export_quote_sheet import ExportQuoteSheet
from quote_assistant.usecase.get_quote_task import GetQuoteTask
from quote_assistant.usecase.list_quote_tasks import ListQuoteTasks
from quote_assistant.usecase.continue_despite_poor_quality import ContinueDespitePoorQuality
from quote_assistant.usecase.extract_part_drawing import ExtractPartDrawing
from quote_assistant.usecase.get_current_actor import GetCurrentActor
from quote_assistant.usecase.get_part_drawing import GetPartDrawing
from quote_assistant.usecase.issue_original_access_url import IssueOriginalAccessUrl
from quote_assistant.usecase.list_correction_records import ListCorrectionRecords
from quote_assistant.usecase.list_correction_stats import ListCorrectionStats
from quote_assistant.usecase.list_part_drawing_events import ListPartDrawingEvents
from quote_assistant.usecase.list_part_drawings import ListPartDrawings
from quote_assistant.usecase.login import Login
from quote_assistant.usecase.logout import Logout
from quote_assistant.usecase.record_manual_baseline import RecordManualBaseline
from quote_assistant.usecase.review_part_drawing import (
    AddCriticalDimension,
    CompleteReview,
    ConfirmExtractedField,
    IgnoreExtractedField,
    ReopenReview,
    UnignoreExtractedField,
    UpdateExtractedField,
)
from quote_assistant.usecase.upload_part_drawings import UploadPartDrawings

SESSION_COOKIE = "qa_session"


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request) -> Iterator[Session]:
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_login(
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Login:
    return Login(
        authenticator=SqlPasswordAuthenticator(session),
        sessions=SqlSessionRepository(session),
        uow=SqlAlchemyUnitOfWork(session),
        session_ttl=timedelta(hours=settings.session_ttl_hours),
    )


def get_logout(session: Session = Depends(get_db)) -> Logout:
    return Logout(sessions=SqlSessionRepository(session), uow=SqlAlchemyUnitOfWork(session))


def require_actor(
    request: Request,
    session: Session = Depends(get_db),
) -> Actor:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="未登录")
    issued = SqlSessionRepository(session).get_valid(token)
    if issued is None:
        raise HTTPException(status_code=401, detail="未登录")
    user = SqlUserRepository(session).get_by_id(issued.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="未登录")
    return Actor.from_user(user)


def get_list_part_drawings(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> ListPartDrawings:
    return ListPartDrawings(actor=actor, drawings=SqlPartDrawingRepository(session))


def get_get_part_drawing(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> GetPartDrawing:
    return GetPartDrawing(actor=actor, drawings=SqlPartDrawingRepository(session))


def get_upload_part_drawings(
    request: Request,
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> UploadPartDrawings:
    return UploadPartDrawings(
        actor=actor,
        drawings=SqlPartDrawingRepository(session),
        events=SqlPartDrawingEventRepository(session),
        storage=request.app.state.object_storage,
        pdf_pages=PypdfPageCounter(),
        engine=request.app.state.extraction_engine,
        uow=SqlAlchemyUnitOfWork(session),
    )


def get_continue_despite_poor_quality(
    request: Request,
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> ContinueDespitePoorQuality:
    return ContinueDespitePoorQuality(
        actor=actor,
        drawings=SqlPartDrawingRepository(session),
        events=SqlPartDrawingEventRepository(session),
        storage=request.app.state.object_storage,
        engine=request.app.state.extraction_engine,
        uow=SqlAlchemyUnitOfWork(session),
    )


def get_extract_part_drawing(
    request: Request,
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> ExtractPartDrawing:
    return ExtractPartDrawing(
        actor=actor,
        drawings=SqlPartDrawingRepository(session),
        events=SqlPartDrawingEventRepository(session),
        storage=request.app.state.object_storage,
        engine=request.app.state.extraction_engine,
        uow=SqlAlchemyUnitOfWork(session),
    )


def get_list_part_drawing_events(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> ListPartDrawingEvents:
    return ListPartDrawingEvents(
        actor=actor,
        drawings=SqlPartDrawingRepository(session),
        events=SqlPartDrawingEventRepository(session),
    )


def get_issue_original_access_url(
    request: Request,
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> IssueOriginalAccessUrl:
    return IssueOriginalAccessUrl(
        actor=actor,
        drawings=SqlPartDrawingRepository(session),
        storage=request.app.state.object_storage,
        ttl=timedelta(seconds=settings.signed_url_ttl_seconds),
    )


def _review_deps(
    session: Session,
) -> tuple[SqlPartDrawingRepository, SqlPartDrawingEventRepository, SqlAlchemyUnitOfWork]:
    return (
        SqlPartDrawingRepository(session),
        SqlPartDrawingEventRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def get_confirm_extracted_field(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> ConfirmExtractedField:
    drawings, events, uow = _review_deps(session)
    return ConfirmExtractedField(actor=actor, drawings=drawings, events=events, uow=uow)


def get_update_extracted_field(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> UpdateExtractedField:
    drawings, events, uow = _review_deps(session)
    return UpdateExtractedField(
        actor=actor,
        drawings=drawings,
        events=events,
        corrections=SqlCorrectionRecordRepository(session),
        uow=uow,
    )


def get_complete_review(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> CompleteReview:
    drawings, events, uow = _review_deps(session)
    return CompleteReview(actor=actor, drawings=drawings, events=events, uow=uow)


def get_ignore_extracted_field(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> IgnoreExtractedField:
    drawings, events, uow = _review_deps(session)
    return IgnoreExtractedField(actor=actor, drawings=drawings, events=events, uow=uow)


def get_unignore_extracted_field(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> UnignoreExtractedField:
    drawings, events, uow = _review_deps(session)
    return UnignoreExtractedField(actor=actor, drawings=drawings, events=events, uow=uow)


def get_add_critical_dimension(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> AddCriticalDimension:
    drawings, events, uow = _review_deps(session)
    return AddCriticalDimension(
        actor=actor,
        drawings=drawings,
        events=events,
        corrections=SqlCorrectionRecordRepository(session),
        uow=uow,
    )


def get_list_correction_records(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> ListCorrectionRecords:
    return ListCorrectionRecords(
        actor=actor,
        drawings=SqlPartDrawingRepository(session),
        corrections=SqlCorrectionRecordRepository(session),
    )


def get_list_correction_stats(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> ListCorrectionStats:
    return ListCorrectionStats(
        actor=actor,
        corrections=SqlCorrectionRecordRepository(session),
    )


def get_reopen_review(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> ReopenReview:
    drawings, events, uow = _review_deps(session)
    return ReopenReview(actor=actor, drawings=drawings, events=events, uow=uow)


def get_current_actor_use_case(
    actor: Actor = Depends(require_actor),
) -> GetCurrentActor:
    return GetCurrentActor(actor)


def get_compare_processing_time(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> CompareProcessingTime:
    return CompareProcessingTime(
        actor=actor,
        drawings=SqlPartDrawingRepository(session),
        events=SqlPartDrawingEventRepository(session),
        baselines=SqlManualBaselineRepository(session),
    )


def get_record_manual_baseline(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> RecordManualBaseline:
    return RecordManualBaseline(
        actor=actor,
        baselines=SqlManualBaselineRepository(session),
        uow=SqlAlchemyUnitOfWork(session),
    )


def _quote_task_repos(
    session: Session,
) -> tuple[SqlQuoteTaskRepository, SqlPartDrawingRepository, SqlAlchemyUnitOfWork]:
    return (
        SqlQuoteTaskRepository(session),
        SqlPartDrawingRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def get_create_quote_task(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> CreateQuoteTask:
    quote_tasks, _drawings, uow = _quote_task_repos(session)
    return CreateQuoteTask(actor=actor, quote_tasks=quote_tasks, uow=uow)


def get_list_quote_tasks(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> ListQuoteTasks:
    quote_tasks, drawings, _uow = _quote_task_repos(session)
    return ListQuoteTasks(actor=actor, quote_tasks=quote_tasks, drawings=drawings)


def get_get_quote_task(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> GetQuoteTask:
    quote_tasks, drawings, _uow = _quote_task_repos(session)
    return GetQuoteTask(actor=actor, quote_tasks=quote_tasks, drawings=drawings)


def get_assign_part_drawing_to_quote_task(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> AssignPartDrawingToQuoteTask:
    quote_tasks, drawings, uow = _quote_task_repos(session)
    return AssignPartDrawingToQuoteTask(
        actor=actor, quote_tasks=quote_tasks, drawings=drawings, uow=uow
    )


def get_remove_part_drawing_from_quote_task(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> RemovePartDrawingFromQuoteTask:
    quote_tasks, drawings, uow = _quote_task_repos(session)
    return RemovePartDrawingFromQuoteTask(
        actor=actor, quote_tasks=quote_tasks, drawings=drawings, uow=uow
    )


def get_export_quote_sheet(
    actor: Actor = Depends(require_actor),
    session: Session = Depends(get_db),
) -> ExportQuoteSheet:
    quote_tasks, drawings, _uow = _quote_task_repos(session)
    return ExportQuoteSheet(
        actor=actor,
        quote_tasks=quote_tasks,
        drawings=drawings,
        templates=SqlQuoteSheetTemplateRepository(session),
        writer=OpenpyxlQuoteSheetFileWriter(),
    )


def map_unauthenticated(exc: Unauthenticated) -> HTTPException:
    return HTTPException(status_code=401, detail="未登录")
