from __future__ import annotations

from datetime import timedelta

from quote_assistant.domain.entities import IssuedSession
from quote_assistant.domain.errors import InvalidCredentials
from quote_assistant.usecase.ports import PasswordAuthenticator, SessionRepository, UnitOfWork


class Login:
    def __init__(
        self,
        authenticator: PasswordAuthenticator,
        sessions: SessionRepository,
        uow: UnitOfWork,
        session_ttl: timedelta,
    ) -> None:
        self._authenticator = authenticator
        self._sessions = sessions
        self._uow = uow
        self._session_ttl = session_ttl

    def execute(self, username: str, password: str) -> IssuedSession:
        user = self._authenticator.authenticate(username=username, password=password)
        if user is None:
            raise InvalidCredentials()
        issued = self._sessions.create(user.id, self._session_ttl)
        self._uow.commit()
        return issued
