from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from quote_assistant.domain.errors import (
    AccountDisabled,
    AdminRequired,
    DomainError,
    DuplicateUsername,
    ExtractedFieldNotFound,
    IllegalPartDrawingTransition,
    IncompleteQuoteTaskReview,
    IncompleteReview,
    InvalidCredentials,
    PartDrawingNotFound,
    QuoteTaskNotFound,
    Unauthenticated,
    UserNotFound,
)

_STATUS_BY_TYPE: dict[type[DomainError], int] = {
    Unauthenticated: 401,
    InvalidCredentials: 401,
    AccountDisabled: 401,
    AdminRequired: 403,
    PartDrawingNotFound: 404,
    ExtractedFieldNotFound: 404,
    UserNotFound: 404,
    QuoteTaskNotFound: 404,
    IllegalPartDrawingTransition: 409,
    IncompleteReview: 409,
    IncompleteQuoteTaskReview: 409,
    DuplicateUsername: 409,
}


def domain_error_status(exc: DomainError) -> int:
    for cls, status in _STATUS_BY_TYPE.items():
        if isinstance(exc, cls):
            return status
    return 400


def domain_error_detail(exc: DomainError) -> str:
    text = str(exc).strip()
    return text or exc.__class__.__name__


async def domain_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Uncaught DomainError becomes a stable JSON error, not 500 + traceback."""
    if not isinstance(exc, DomainError):
        raise exc
    return JSONResponse(
        status_code=domain_error_status(exc),
        content={"detail": domain_error_detail(exc)},
    )
