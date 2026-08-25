from __future__ import annotations

from collections.abc import Iterator
from datetime import timedelta

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from quote_assistant.adapter.db.repositories import (
    SqlPartDrawingRepository,
    SqlPasswordAuthenticator,
    SqlSessionRepository,
    SqlUserRepository,
)
from quote_assistant.adapter.db.session import SqlAlchemyUnitOfWork
from quote_assistant.config import Settings
from quote_assistant.domain.entities import Actor
from quote_assistant.domain.errors import Unauthenticated
from quote_assistant.usecase.get_current_actor import GetCurrentActor
from quote_assistant.usecase.list_part_drawings import ListPartDrawings
from quote_assistant.usecase.login import Login
from quote_assistant.usecase.logout import Logout

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


def get_current_actor_use_case(
    actor: Actor = Depends(require_actor),
) -> GetCurrentActor:
    return GetCurrentActor(actor)


def map_unauthenticated(exc: Unauthenticated) -> HTTPException:
    return HTTPException(status_code=401, detail="未登录")
