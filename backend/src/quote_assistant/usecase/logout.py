from __future__ import annotations

from quote_assistant.usecase.ports import SessionRepository, UnitOfWork


class Logout:
    def __init__(self, sessions: SessionRepository, uow: UnitOfWork) -> None:
        self._sessions = sessions
        self._uow = uow

    def execute(self, token: str | None) -> None:
        if token:
            self._sessions.revoke(token)
            self._uow.commit()
