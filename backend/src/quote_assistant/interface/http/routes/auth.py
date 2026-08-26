from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from quote_assistant.config import Settings
from quote_assistant.domain.errors import AccountDisabled, InvalidCredentials
from quote_assistant.interface.http.deps import (
    SESSION_COOKIE,
    get_current_actor_use_case,
    get_login,
    get_logout,
    get_settings,
)
from quote_assistant.interface.http.schemas import CurrentUserResponse, LoginRequest, OkResponse
from quote_assistant.usecase.get_current_actor import GetCurrentActor
from quote_assistant.usecase.login import Login
from quote_assistant.usecase.logout import Logout

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=OkResponse)
def login(
    body: LoginRequest,
    response: Response,
    use_case: Login = Depends(get_login),
    settings: Settings = Depends(get_settings),
) -> OkResponse:
    try:
        issued = use_case.execute(username=body.username, password=body.password)
    except AccountDisabled as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except InvalidCredentials as exc:
        raise HTTPException(status_code=401, detail="账号或密码不正确") from exc
    response.set_cookie(
        key=SESSION_COOKIE,
        value=issued.token,
        httponly=True,
        samesite="lax",
        secure=settings.effective_session_cookie_secure,
        max_age=settings.session_ttl_hours * 3600,
        path="/",
    )
    return OkResponse()


@router.post("/logout", response_model=OkResponse)
def logout(
    request: Request,
    response: Response,
    use_case: Logout = Depends(get_logout),
    settings: Settings = Depends(get_settings),
) -> OkResponse:
    use_case.execute(request.cookies.get(SESSION_COOKIE))
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        secure=settings.effective_session_cookie_secure,
    )
    return OkResponse()


@router.get("/me", response_model=CurrentUserResponse)
def me(use_case: GetCurrentActor = Depends(get_current_actor_use_case)) -> CurrentUserResponse:
    actor = use_case.execute()
    return CurrentUserResponse(
        username=actor.username,
        factory_name=actor.factory_name,
        role=actor.role,
    )
