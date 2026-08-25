from __future__ import annotations

import re

from quote_assistant.domain.errors import InvalidAccount

MAX_USERNAME_LENGTH = 80
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 200

_USERNAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,79}$")


def normalize_quoter_username(username: str) -> str:
    stripped = username.strip()
    if not stripped:
        raise InvalidAccount("请填写账号")
    if len(stripped) > MAX_USERNAME_LENGTH:
        raise InvalidAccount(f"账号不能超过 {MAX_USERNAME_LENGTH} 个字")
    if _USERNAME.fullmatch(stripped) is None:
        raise InvalidAccount("账号只能使用字母、数字、点、下划线或连字符，且至少两个字符")
    return stripped


def validate_quoter_password(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise InvalidAccount(f"密码至少 {MIN_PASSWORD_LENGTH} 位")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise InvalidAccount(f"密码不能超过 {MAX_PASSWORD_LENGTH} 位")
    return password
